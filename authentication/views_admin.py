from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.db.models import Q, Sum, Count, Prefetch
from django.utils import timezone
from datetime import timedelta
from .models import Payment, PaymentStatus, Booking, BookingStatus, Room, CustomUser, UserRole, AuditLog, Testimonial
from .forms_admin import PaymentApprovalForm
from .views_rooms import room_delete_view
from .utils import confirm_booking_after_completed_payment, get_occupancy_chart_context, is_two_fa_configured, log_audit
import json
import csv


def admin_required(view_func):
    """
    Decorator to ensure only admins can access
    Also ensures terms and conditions are accepted
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            return HttpResponseForbidden("You don't have permission to access this page.")
        
        # Check if admin has accepted terms
        if not request.user.has_accepted_terms():
            return redirect('auth:accept_terms')

        if not is_two_fa_configured(request.user):
            messages.warning(request, 'Two-factor authentication is required for admin accounts.')
            return redirect('auth:setup_2fa')
        
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def admin_dashboard(request):
    """Admin Dashboard with overview statistics"""
    today = timezone.now().date()
    audit_action_filter = request.GET.get('audit_action', '').strip()
    
    # Basic stats
    total_bookings = Booking.objects.count()
    pending_payments_count = Payment.objects.filter(status=PaymentStatus.PENDING).count()
    confirmed_bookings = Booking.objects.filter(status=BookingStatus.CONFIRMED).count()
    
    # Revenue calculations
    completed_payments = Payment.objects.filter(status=PaymentStatus.COMPLETED)
    total_revenue = completed_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Today's stats
    today_check_ins = Booking.objects.filter(
        check_in=today,
        status=BookingStatus.CONFIRMED
    ).count()
    today_check_outs = Booking.objects.filter(
        check_out=today,
        status=BookingStatus.CONFIRMED
    ).count()
    
    # This month revenue
    first_day_of_month = today.replace(day=1)
    month_revenue = completed_payments.filter(
        completed_at__date__gte=first_day_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Occupancy rate
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(is_available=False).count()
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    # Recent bookings (QuerySet for template iteration)
    recent_bookings = Booking.objects.select_related('room', 'guest').order_by('-created_at')[:5]
    
    # Pending payments list (QuerySet for template iteration)
    pending_payments = Payment.objects.select_related('booking__room', 'booking__guest').filter(
        status=PaymentStatus.PENDING
    ).order_by('-created_at')[:5]
    pending_testimonials = Testimonial.objects.select_related('guest').filter(
        status=Testimonial.Status.PENDING
    ).order_by('created_at')[:10]

    audit_logs = AuditLog.objects.select_related('actor', 'affected_user').order_by('-created_at')
    if audit_action_filter:
        audit_logs = audit_logs.filter(action=audit_action_filter)
    
    context = {
        'total_bookings': total_bookings,
        'pending_payments_count': pending_payments_count,
        'confirmed_bookings': confirmed_bookings,
        'total_revenue': total_revenue,
        'today_check_ins': today_check_ins,
        'today_check_outs': today_check_outs,
        'month_revenue': month_revenue,
        'occupancy_rate': occupancy_rate,
        'total_rooms': total_rooms,
        'recent_bookings': recent_bookings,
        'pending_payments': pending_payments,
        'recent_audit_logs': audit_logs[:50],
        'audit_action_filter': audit_action_filter,
        'audit_action_choices': AuditLog.ACTION_CHOICES,
        'pending_testimonials': pending_testimonials,
        'two_fa': request.user.two_factor_auth,
    }
    context.update(get_occupancy_chart_context(today))
    
    return render(request, 'admin/dashboard.html', context)


def _send_testimonial_approval_email(testimonial):
    recipient = testimonial.guest.email if testimonial.guest and testimonial.guest.email else testimonial.guest_email
    if not recipient:
        return False

    send_mail(
        'Your Cebu Mini Hotel review is published',
        'Your review has been published on Cebu Mini Hotel!',
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=True,
    )
    return True


@login_required
@admin_required
@require_http_methods(["POST"])
def approve_testimonial(request, testimonial_id):
    testimonial = get_object_or_404(Testimonial, id=testimonial_id, status=Testimonial.Status.PENDING)
    testimonial.status = Testimonial.Status.APPROVED
    testimonial.is_approved = True
    testimonial.reviewed_by = request.user
    testimonial.reviewed_at = timezone.now()
    testimonial.save(update_fields=['status', 'is_approved', 'reviewed_by', 'reviewed_at', 'updated_at'])
    _send_testimonial_approval_email(testimonial)
    messages.success(request, f'Testimonial from {testimonial.guest_name} approved.')
    return redirect('admin_panel:dashboard')


@login_required
@admin_required
@require_http_methods(["POST"])
def reject_testimonial(request, testimonial_id):
    testimonial = get_object_or_404(Testimonial, id=testimonial_id, status=Testimonial.Status.PENDING)
    testimonial.status = Testimonial.Status.REJECTED
    testimonial.is_approved = False
    testimonial.reviewed_by = request.user
    testimonial.reviewed_at = timezone.now()
    testimonial.save(update_fields=['status', 'is_approved', 'reviewed_by', 'reviewed_at', 'updated_at'])
    messages.success(request, f'Testimonial from {testimonial.guest_name} rejected.')
    return redirect('admin_panel:dashboard')


@login_required
@admin_required
def payment_management(request):
    """Manage all pending payments with approval/rejection"""
    
    # Filter by payment status (default to empty to show all if not specified)
    status_filter = request.GET.get('status', '')
    payment_method_filter = request.GET.get('method', '')
    
    payments = Payment.objects.select_related(
        'booking__room',
        'booking__guest'
    ).order_by('-created_at')
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    if payment_method_filter:
        payments = payments.filter(payment_method=payment_method_filter)
    
    # Statistics
    pending_count = Payment.objects.filter(status=PaymentStatus.PENDING).count()
    completed_count = Payment.objects.filter(status=PaymentStatus.COMPLETED).count()
    failed_count = Payment.objects.filter(status=PaymentStatus.FAILED).count()
    
    context = {
        'payments': payments,
        'status_filter': status_filter,
        'payment_method_filter': payment_method_filter,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'failed_count': failed_count,
        'pending_payments_count': pending_count,
        'payment_statuses': PaymentStatus.choices,
        'payment_methods': Payment._meta.get_field('payment_method').choices,
        'show_pending_by_default': not status_filter,  # Show pending filter tab if no status specified
    }
    
    return render(request, 'admin/payment_management.html', context)


@login_required
@login_required
@admin_required
def payment_detail(request, payment_id):
    """View payment details and approve/reject"""
    print(f"\n{'='*80}")
    print(f"PAYMENT_DETAIL VIEW CALLED")
    print(f"Method: {request.method}")
    print(f"Payment ID: {payment_id}")
    
    payment = get_object_or_404(Payment, id=payment_id)
    booking = payment.booking
    guest = booking.guest
    
    # Initialize form for all cases
    form = PaymentApprovalForm(instance=payment)
    
    if request.method == 'POST':
        print(f"\n>>> POST REQUEST RECEIVED <<<")
        print(f"POST data: {dict(request.POST)}")
        print(f"POST keys: {list(request.POST.keys())}")
        
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        print(f"Action: '{action}'")
        print(f"Notes: '{notes}'")
        
        if action == 'approve':
            print(f"\n>>> PROCESSING APPROVE <<<")
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = timezone.now()
            booking.status = BookingStatus.CONFIRMED
            payment.save()
            booking.save()
            print(f"✓ Payment saved - Status: {payment.status}")
            print(f"✓ Booking saved - Status: {booking.status}")
            messages.success(request, f'Payment #{payment.id} approved successfully. Booking confirmed.')
            print(f">>> REDIRECTING TO DASHBOARD <<<")
            return redirect('admin_panel:dashboard')
        
        elif action == 'reject':
            print(f"\n>>> PROCESSING REJECT <<<")
            payment.status = PaymentStatus.FAILED
            payment.notes = notes or 'Payment rejected by admin'
            payment.save()
            print(f"✓ Payment saved - Status: {payment.status}")
            messages.success(request, f'Payment #{payment.id} rejected successfully.')
            print(f">>> REDIRECTING TO DASHBOARD <<<")
            return redirect('admin_panel:dashboard')
        
        elif action == 'pending':
            print(f"\n>>> PROCESSING PENDING <<<")
            payment.notes = notes
            payment.save()
            print(f"✓ Payment notes updated")
            messages.info(request, f'Payment #{payment.id} notes updated.')
            print(f">>> REDIRECTING TO DASHBOARD <<<")
            return redirect('admin_panel:dashboard')
        else:
            print(f"\n>>> ERROR: No matching action <<<")
            print(f"Expected 'approve' or 'reject', got: '{action}'")
    
    # Get pending payments count for sidebar
    pending_payments_count = Payment.objects.filter(status=PaymentStatus.PENDING).count()
    
    context = {
        'payment': payment,
        'booking': booking,
        'guest': guest,
        'form': form,
        'pending_payments_count': pending_payments_count,
        'payment_statuses': PaymentStatus.choices,
    }
    
    print(f">>> RENDERING TEMPLATE <<<")
    print(f"{'='*80}\n")
    return render(request, 'admin/payment_detail.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def approve_payment(request, payment_id):
    """Quick approve payment via AJAX"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status != PaymentStatus.PENDING:
        return JsonResponse({'error': 'Payment is not pending'}, status=400)
    
    # Approve payment
    payment.status = PaymentStatus.COMPLETED
    payment.completed_at = timezone.now()
    payment.save()
    
    # Confirm booking
    booking = payment.booking
    booking.status = BookingStatus.CONFIRMED
    booking.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Payment #{payment.id} approved successfully',
        'payment_status': payment.get_status_display(),
        'booking_status': booking.get_status_display()
    })


@login_required
@admin_required
@require_http_methods(["POST"])
def reject_payment(request, payment_id):
    """Quick reject payment via AJAX"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status != PaymentStatus.PENDING:
        return JsonResponse({'error': 'Payment is not pending'}, status=400)
    
    data = json.loads(request.body)
    reason = data.get('reason', 'Payment rejected by admin')
    
    payment.status = PaymentStatus.FAILED
    payment.notes = reason
    payment.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Payment #{payment.id} rejected',
        'payment_status': payment.get_status_display()
    })


@login_required
@admin_required
def room_management(request):
    """Manage rooms - view, edit, add"""
    rooms = Room.objects.all().order_by('room_number')
    
    # Statistics
    total_rooms = rooms.count()
    available_rooms = rooms.filter(is_available=True).count()
    occupied_rooms = total_rooms - available_rooms
    pending_payments_count = Payment.objects.filter(status=PaymentStatus.PENDING).count()
    
    context = {
        'rooms': rooms,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
        'pending_payments_count': pending_payments_count,
    }
    
    return render(request, 'admin/room_management.html', context)


@login_required
@admin_required
def room_detail_admin(request, room_id):
    """Display room details for admin"""
    room = get_object_or_404(Room, id=room_id)
    
    context = {
        'room': room,
    }
    
    return render(request, 'admin/room_detail_admin.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def room_delete_admin(request, room_id):
    """Delete room from the admin panel"""
    return room_delete_view(request, room_id)


@login_required
@admin_required
def booking_management(request):
    """Manage all bookings"""
    
    # Filter by booking status
    status_filter = request.GET.get('status', '')
    
    bookings = Booking.objects.select_related(
        'room',
        'guest'
    ).order_by('-created_at')
    
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Statistics
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status=BookingStatus.PENDING).count()
    confirmed_bookings = Booking.objects.filter(status=BookingStatus.CONFIRMED).count()
    cancelled_bookings = Booking.objects.filter(status=BookingStatus.CANCELLED).count()
    pending_payments_count = Payment.objects.filter(status=PaymentStatus.PENDING).count()
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'pending_payments_count': pending_payments_count,
        'booking_statuses': BookingStatus.choices,
    }
    
    return render(request, 'admin/booking_management.html', context)


@login_required
@admin_required
def booking_detail(request, booking_id):
    """View booking details"""
    booking = get_object_or_404(Booking, id=booking_id)
    guest = booking.guest
    room = booking.room
    payment = Payment.objects.filter(booking=booking).first()
    pending_payments_count = Payment.objects.filter(status=PaymentStatus.PENDING).count()
    
    context = {
        'booking': booking,
        'guest': guest,
        'room': room,
        'payment': payment,
        'pending_payments_count': pending_payments_count,
        'booking_statuses': BookingStatus.choices,
    }
    
    return render(request, 'admin/booking_detail.html', context)


@login_required
@admin_required
def booking_edit(request, booking_id):
    """Edit booking status and details"""
    booking = get_object_or_404(Booking, id=booking_id)
    guest = booking.guest
    room = booking.room
    payment = Payment.objects.filter(booking=booking).first()
    pending_payments_count = Payment.objects.filter(status=PaymentStatus.PENDING).count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'confirm':
            if booking.status == BookingStatus.PENDING:
                completed_payment = booking.payments.filter(status=PaymentStatus.COMPLETED).order_by('-completed_at', '-created_at').first()
                if not completed_payment:
                    messages.error(request, 'Booking cannot be confirmed until payment is completed.')
                    return redirect('admin_panel:booking_detail', booking_id=booking.id)
                confirm_booking_after_completed_payment(completed_payment)
                messages.success(request, 'Booking has been confirmed and the guest has been notified.')
            else:
                messages.error(request, 'Only pending bookings can be confirmed.')
                return redirect('admin_panel:booking_detail', booking_id=booking.id)

            return redirect('admin_panel:booking_detail', booking_id=booking.id)

        elif action == 'checkin':
            if booking.status == BookingStatus.CONFIRMED:
                checklist = {
                    'reference_verified': request.POST.get('reference_verified') == 'on',
                    'id_verified': request.POST.get('id_verified') == 'on',
                    'contact_verified': request.POST.get('contact_verified') == 'on',
                    'payment_verified': request.POST.get('payment_verified') == 'on',
                }
                errors = booking.complete_check_in_verification(
                    request.user,
                    request.POST.get('booking_reference'),
                    checklist,
                    request.POST.get('verification_notes', '')
                )
                if errors:
                    for error in errors:
                        messages.error(request, error)
                else:
                    messages.success(request, 'Guest identity and booking proof verified. Guest has been checked in successfully.')
            else:
                messages.error(request, 'Only confirmed bookings can be checked in.')
            return redirect('admin_panel:booking_detail', booking_id=booking.id)

        elif action == 'checkout':
            if booking.status == BookingStatus.CHECKED_IN:
                booking.status = BookingStatus.CHECKED_OUT
                booking.save()
                messages.success(request, 'Guest has been checked out successfully.')
            else:
                messages.error(request, 'Only checked-in bookings can be checked out.')
            return redirect('admin_panel:booking_detail', booking_id=booking.id)

        elif action == 'undo_checkin':
            if booking.status == BookingStatus.CHECKED_IN:
                booking.status = BookingStatus.CONFIRMED
                booking.save()
                messages.info(request, 'Check-in has been reversed.')
            else:
                messages.error(request, 'Only checked-in bookings can be reverted.')
            return redirect('admin_panel:booking_detail', booking_id=booking.id)

        elif action == 'undo_checkout':
            if booking.status == BookingStatus.CHECKED_OUT:
                booking.status = BookingStatus.CONFIRMED
                booking.save()
                messages.info(request, 'Check-out has been reversed.')
            else:
                messages.error(request, 'Only checked-out bookings can be reverted.')
            return redirect('admin_panel:booking_detail', booking_id=booking.id)

        elif action == 'cancel':
            if booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
                booking.status = BookingStatus.CANCELLED
                booking.cancelled_at = timezone.now()
                booking.cancellation_reason = notes or booking.cancellation_reason
                booking.save()

                if payment and payment.status == PaymentStatus.COMPLETED:
                    payment.status = PaymentStatus.REFUND_PENDING
                    payment.save()

                messages.warning(request, 'Booking has been cancelled.')
                return redirect('admin_panel:booking_management')
            else:
                messages.error(request, 'Only pending or confirmed bookings can be cancelled.')
                return redirect('admin_panel:booking_detail', booking_id=booking.id)

        elif action == 'restore':
            if booking.status == BookingStatus.CANCELLED:
                booking.status = BookingStatus.CONFIRMED
                booking.cancelled_at = None
                booking.cancellation_reason = ''
                booking.save()
                messages.info(request, 'Booking has been restored to Confirmed.')
            else:
                messages.error(request, 'Only cancelled bookings can be restored.')
            return redirect('admin_panel:booking_detail', booking_id=booking.id)

        else:
            messages.error(request, 'Invalid action.')
            return redirect('admin_panel:booking_detail', booking_id=booking.id)
    
    return redirect('admin_panel:booking_detail', booking_id=booking.id)


@login_required
@admin_required
def user_management(request):
    """Manage users and staff accounts"""

    if request.method == 'POST':
        action = request.POST.get('action')
        target_user = get_object_or_404(CustomUser, id=request.POST.get('user_id'))

        if target_user.id == request.user.id and action in {'update_user', 'toggle_status'}:
            requested_role = request.POST.get('role', target_user.role)
            requested_active = request.POST.get('is_active', 'true') == 'true'
            if requested_role != UserRole.ADMIN or not requested_active:
                messages.error(request, 'You cannot demote or deactivate your own admin account.')
                return redirect('admin_panel:user_management')

        if action == 'update_user':
            old_role = target_user.role
            old_active = target_user.is_active
            new_role = request.POST.get('role', target_user.role)
            new_active = request.POST.get('is_active', 'true') == 'true'

            valid_roles = {choice[0] for choice in UserRole.choices}
            if new_role not in valid_roles:
                messages.error(request, 'Invalid role selected.')
                return redirect('admin_panel:user_management')

            target_user.role = new_role
            target_user.is_active = new_active
            target_user.is_staff = new_role in {UserRole.ADMIN, UserRole.MANAGER, UserRole.STAFF}
            target_user.is_superuser = new_role == UserRole.ADMIN
            target_user.save(update_fields=['role', 'is_active', 'is_staff', 'is_superuser'])

            changes = {
                'role': {'old': old_role, 'new': new_role},
                'is_active': {'old': old_active, 'new': new_active},
            }
            log_audit(
                request,
                request.user,
                'USER_ROLE_CHANGED',
                'CustomUser',
                target_user.id,
                affected_user=target_user,
                description=f'Admin updated account settings for {target_user.email}',
                changes=changes
            )
            messages.success(request, f'Updated {target_user.email}.')
            return redirect('admin_panel:user_management')

        if action == 'toggle_status':
            old_active = target_user.is_active
            target_user.is_active = not target_user.is_active
            target_user.save(update_fields=['is_active'])
            log_audit(
                request,
                request.user,
                'STAFF_DEACTIVATED' if old_active else 'USER_ROLE_CHANGED',
                'CustomUser',
                target_user.id,
                affected_user=target_user,
                description=f'Admin {"deactivated" if old_active else "reactivated"} account {target_user.email}',
                changes={'is_active': {'old': old_active, 'new': target_user.is_active}}
            )
            messages.success(request, f'{"Deactivated" if old_active else "Reactivated"} {target_user.email}.')
            return redirect('admin_panel:user_management')

    role_filter = request.GET.get('role', '').upper()
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '').strip()

    users = CustomUser.objects.all().order_by('-created_at')

    if role_filter:
        users = users.filter(role=role_filter)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Statistics
    total_users = CustomUser.objects.count()
    admin_users = CustomUser.objects.filter(role=UserRole.ADMIN).count()
    guest_users = CustomUser.objects.filter(role=UserRole.GUEST).count()
    staff_users = CustomUser.objects.filter(role=UserRole.STAFF).count()
    manager_users = CustomUser.objects.filter(role=UserRole.MANAGER).count()
    verified_users = CustomUser.objects.filter(is_email_verified=True).count()
    pending_payments_count = Payment.objects.filter(status=PaymentStatus.PENDING).count()

    context = {
        'users': users,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_users': total_users,
        'admin_users': admin_users,
        'guest_users': guest_users,
        'guest_count': guest_users,
        'staff_count': staff_users + manager_users + admin_users,
        'manager_users': manager_users,
        'verified_users': verified_users,
        'pending_payments_count': pending_payments_count,
        'user_roles': UserRole.choices,
    }

    return render(request, 'admin/user_management.html', context)


@login_required
@admin_required
def admin_reports(request):
    """Admin reports and analytics dashboard."""
    today = timezone.now().date()
    total_rooms = Room.objects.count()
    checked_in_rooms = Booking.objects.filter(
        status=BookingStatus.CHECKED_IN
    ).values('room').distinct().count()
    occupancy_rate_today = (checked_in_rooms / total_rooms * 100) if total_rooms else 0

    completed_payments = Payment.objects.filter(status=PaymentStatus.COMPLETED)
    total_revenue = completed_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_bookings = Booking.objects.count()
    total_guests = CustomUser.objects.filter(role=UserRole.GUEST).count()
    pending_payments_count = Payment.objects.filter(status=PaymentStatus.PENDING).count()

    def add_months(date_value, offset):
        month_index = date_value.month - 1 + offset
        year = date_value.year + month_index // 12
        month = month_index % 12 + 1
        return date_value.replace(year=year, month=month, day=1)

    current_month = today.replace(day=1)
    monthly_revenue_labels = []
    monthly_revenue_values = []
    for i in range(5, -1, -1):
        first_day = add_months(current_month, -i)
        next_month = add_months(first_day, 1)
        revenue = completed_payments.filter(
            completed_at__date__gte=first_day,
            completed_at__date__lt=next_month,
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_revenue_labels.append(first_day.strftime('%b %Y'))
        monthly_revenue_values.append(float(revenue))

    booking_status_rows = []
    for status, label in [
        (BookingStatus.PENDING, 'Pending'),
        (BookingStatus.CONFIRMED, 'Confirmed'),
        (BookingStatus.CHECKED_IN, 'Checked In'),
        (BookingStatus.CHECKED_OUT, 'Checked Out'),
        (BookingStatus.CANCELLED, 'Cancelled'),
    ]:
        booking_status_rows.append({
            'status': label,
            'count': Booking.objects.filter(status=status).count(),
        })

    recent_bookings_queryset = (
        Booking.objects
        .select_related('guest', 'room')
        .prefetch_related(Prefetch('payments', queryset=Payment.objects.order_by('-created_at'), to_attr='recent_payments'))
        .order_by('-created_at')[:10]
    )
    recent_bookings = []
    for booking in recent_bookings_queryset:
        payment = booking.recent_payments[0] if booking.recent_payments else None
        recent_bookings.append({
            'booking': booking,
            'payment_status': payment.get_status_display() if payment else 'No payment',
        })

    top_rooms = (
        Room.objects
        .annotate(
            total_bookings=Count('bookings', distinct=True),
            total_revenue=Sum(
                'bookings__payments__amount',
                filter=Q(bookings__payments__status=PaymentStatus.COMPLETED)
            ),
        )
        .order_by('-total_bookings', 'room_number')[:10]
    )

    context = {
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'occupancy_rate_today': occupancy_rate_today,
        'checked_in_rooms': checked_in_rooms,
        'total_rooms': total_rooms,
        'total_guests': total_guests,
        'monthly_revenue_labels_json': json.dumps(monthly_revenue_labels),
        'monthly_revenue_values_json': json.dumps(monthly_revenue_values),
        'booking_status_rows': booking_status_rows,
        'recent_bookings': recent_bookings,
        'top_rooms': top_rooms,
        'pending_payments_count': pending_payments_count,
    }
    context.update(get_occupancy_chart_context(today))

    return render(request, 'admin/reports.html', context)


def _csv_response(filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _user_display_name(user):
    return user.get_full_name() or user.username


def _format_datetime(value):
    if not value:
        return ''
    return timezone.localtime(value).strftime('%Y-%m-%d %H:%M:%S')


@login_required
@admin_required
def export_bookings_csv(request):
    response = _csv_response('bookings.csv')
    writer = csv.writer(response)
    writer.writerow([
        'Booking ID',
        'Guest Name',
        'Email',
        'Room',
        'Check-in',
        'Check-out',
        'Nights',
        'Total Amount',
        'Payment Status',
        'Booking Status',
        'Created At',
    ])

    bookings = (
        Booking.objects
        .select_related('guest', 'room')
        .prefetch_related(Prefetch('payments', queryset=Payment.objects.order_by('-created_at'), to_attr='recent_payments'))
        .order_by('-created_at')
    )
    for booking in bookings:
        payment = booking.recent_payments[0] if booking.recent_payments else None
        writer.writerow([
            booking.id,
            _user_display_name(booking.guest),
            booking.guest.email,
            f'Room {booking.room.room_number}',
            booking.check_in.isoformat(),
            booking.check_out.isoformat(),
            booking.number_of_nights,
            booking.total_price,
            payment.get_status_display() if payment else 'No payment',
            booking.get_status_display(),
            _format_datetime(booking.created_at),
        ])

    return response


@login_required
@admin_required
def export_payments_csv(request):
    response = _csv_response('payments.csv')
    writer = csv.writer(response)
    writer.writerow([
        'Payment ID',
        'Booking ID',
        'Guest Name',
        'Amount',
        'Method',
        'Status',
        'Transaction ID',
        'Completed At',
    ])

    payments = (
        Payment.objects
        .select_related('booking__guest')
        .order_by('-created_at')
    )
    for payment in payments:
        writer.writerow([
            payment.id,
            payment.booking_id,
            _user_display_name(payment.booking.guest),
            payment.amount,
            payment.get_payment_method_display(),
            payment.get_status_display(),
            payment.transaction_id or payment.reference_number or '',
            _format_datetime(payment.completed_at),
        ])

    return response


@login_required
@admin_required
def export_guests_csv(request):
    response = _csv_response('guests.csv')
    writer = csv.writer(response)
    writer.writerow([
        'User ID',
        'Full Name',
        'Email',
        'Date Joined',
        'Total Bookings',
        'Total Spent',
    ])

    guests = (
        CustomUser.objects
        .filter(role=UserRole.GUEST)
        .annotate(
            total_bookings=Count('bookings', distinct=True),
            total_spent=Sum(
                'bookings__payments__amount',
                filter=Q(bookings__payments__status=PaymentStatus.COMPLETED),
            ),
        )
        .order_by('-date_joined')
    )
    for guest in guests:
        writer.writerow([
            guest.id,
            _user_display_name(guest),
            guest.email,
            _format_datetime(guest.date_joined),
            guest.total_bookings,
            guest.total_spent or 0,
        ])

    return response
