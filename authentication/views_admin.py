from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Payment, PaymentStatus, Booking, BookingStatus, Room, CustomUser, UserRole
from .forms_admin import PaymentApprovalForm
import json


def admin_required(view_func):
    """Decorator to ensure only admins can access"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            return HttpResponseForbidden("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def admin_dashboard(request):
    """Admin Dashboard with overview statistics"""
    today = timezone.now().date()
    
    # Basic stats
    total_bookings = Booking.objects.count()
    pending_payments = Payment.objects.filter(status=PaymentStatus.PENDING).count()
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
    
    # Recent bookings
    recent_bookings = Booking.objects.select_related('room', 'guest').order_by('-created_at')[:5]
    
    # Pending payments list
    pending = Payment.objects.select_related('booking__room', 'booking__guest').filter(
        status=PaymentStatus.PENDING
    ).order_by('-created_at')[:5]
    
    context = {
        'total_bookings': total_bookings,
        'pending_payments': pending_payments,
        'confirmed_bookings': confirmed_bookings,
        'total_revenue': total_revenue,
        'today_check_ins': today_check_ins,
        'today_check_outs': today_check_outs,
        'month_revenue': month_revenue,
        'occupancy_rate': occupancy_rate,
        'total_rooms': total_rooms,
        'recent_bookings': recent_bookings,
        'pending_payments_list': pending,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required
@admin_required
def payment_management(request):
    """Manage all pending payments with approval/rejection"""
    
    # Filter by payment status
    status_filter = request.GET.get('status', 'PENDING')
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
        'payment_statuses': PaymentStatus.choices,
        'payment_methods': Payment._meta.get_field('payment_method').choices,
    }
    
    return render(request, 'admin/payment_management.html', context)


@login_required
@admin_required
def payment_detail(request, payment_id):
    """View payment details and approve/reject"""
    payment = get_object_or_404(Payment, id=payment_id)
    booking = payment.booking
    guest = booking.guest
    
    if request.method == 'POST':
        form = PaymentApprovalForm(request.POST, instance=payment)
        if form.is_valid():
            action = request.POST.get('action')
            
            if action == 'approve':
                payment.status = PaymentStatus.COMPLETED
                payment.completed_at = timezone.now()
                booking.status = BookingStatus.CONFIRMED
                payment.save()
                booking.save()
                return redirect('admin_panel:payment_management')
            
            elif action == 'reject':
                payment.status = PaymentStatus.FAILED
                payment.notes = form.cleaned_data.get('notes', 'Payment rejected by admin')
                payment.save()
                return redirect('admin_panel:payment_management')
            
            elif action == 'pending':
                payment.notes = form.cleaned_data.get('notes', '')
                payment.save()
                return redirect('admin_panel:payment_management')
    else:
        form = PaymentApprovalForm(instance=payment)
    
    context = {
        'payment': payment,
        'booking': booking,
        'guest': guest,
        'form': form,
        'payment_statuses': PaymentStatus.choices,
    }
    
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
    
    context = {
        'rooms': rooms,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
    }
    
    return render(request, 'admin/room_management.html', context)


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
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'booking_statuses': BookingStatus.choices,
    }
    
    return render(request, 'admin/booking_management.html', context)


@login_required
@admin_required
def user_management(request):
    """Manage users and staff accounts"""
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    
    users = CustomUser.objects.all().order_by('-created_at')
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Statistics
    total_users = CustomUser.objects.count()
    admin_users = CustomUser.objects.filter(role=UserRole.ADMIN).count()
    guest_users = CustomUser.objects.filter(role=UserRole.GUEST).count()
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'total_users': total_users,
        'admin_users': admin_users,
        'guest_users': guest_users,
        'user_roles': UserRole.choices,
    }
    
    return render(request, 'admin/user_management.html', context)


@login_required
@admin_required
def admin_reports(request):
    """Generate and view reports"""
    today = timezone.now().date()
    
    # Revenue reports
    all_payments = Payment.objects.filter(status=PaymentStatus.COMPLETED)
    total_revenue = all_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # This month
    first_day = today.replace(day=1)
    month_payments = all_payments.filter(completed_at__date__gte=first_day)
    month_revenue = month_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # This week
    week_ago = today - timedelta(days=7)
    week_payments = all_payments.filter(completed_at__date__gte=week_ago)
    week_revenue = week_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Today
    today_payments = all_payments.filter(completed_at__date=today)
    today_revenue = today_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Payment method breakdown
    payment_methods = all_payments.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount')
    )
    
    # Room type revenue
    room_revenue = all_payments.values('booking__room__room_type').annotate(
        count=Count('id'),
        total=Sum('amount'),
        avg=Sum('amount') / Count('id')
    )
    
    context = {
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'week_revenue': week_revenue,
        'today_revenue': today_revenue,
        'payment_methods': payment_methods,
        'room_revenue': room_revenue,
        'month_payments_count': month_payments.count(),
        'week_payments_count': week_payments.count(),
        'today_payments_count': today_payments.count(),
    }
    
    return render(request, 'admin/reports.html', context)
