"""
Staff Views - Handle housekeeping and front desk operations
Staff members can manage room status, check-ins, check-outs, and maintenance
"""

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum, Avg
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from decimal import Decimal

from .decorators import staff_required, staff_or_admin_required, staff_manager_or_admin_required
from .models import (
    Booking,
    BookingStatus,
    Complaint,
    ComplaintStatus,
    CustomUser,
    HousekeepingTask,
    HousekeepingTaskStatus,
    Payment,
    PaymentStatus,
    RefundRequestStatus,
    Room,
    RoomHousekeepingLog,
    RoomStatus,
    UserRole,
)
from .forms_bookings import ContactForm
from .emails import send_checkin_email, send_checkout_email
from .utils import confirm_booking_after_completed_payment, get_occupancy_chart_context, log_activity, log_audit


@login_required(login_url='auth:login')
@staff_or_admin_required
def staff_dashboard(request):
    """Staff Dashboard with daily tasks and room status"""
    today = timezone.now().date()
    
    # Get today's bookings
    today_check_ins = Booking.objects.filter(
        check_in=today,
        status=BookingStatus.CONFIRMED
    ).select_related('guest', 'room').prefetch_related('payments')
    
    today_check_outs = Booking.objects.filter(
        check_out=today,
        status=BookingStatus.CHECKED_IN
    ).select_related('guest', 'room')
    
    # Get current bookings (checked in but not checked out yet)
    current_bookings = Booking.objects.filter(
        check_in__lte=today,
        status=BookingStatus.CHECKED_IN
    ).select_related('guest', 'room')
    
    # Room statistics
    total_rooms = Room.objects.count()
    occupied_rooms = current_bookings.values('room').distinct().count()
    available_rooms = total_rooms - occupied_rooms
    
    # Upcoming check-ins (next 7 days)
    upcoming_check_ins = Booking.objects.filter(
        check_in__gt=today,
        check_in__lte=today + timedelta(days=7),
        status=BookingStatus.CONFIRMED
    ).select_related('guest', 'room').order_by('check_in')

    pending_onsite_payments = Payment.objects.filter(
        status=PaymentStatus.PENDING_ONSITE
    ).select_related(
        'booking__guest',
        'booking__room',
    ).order_by('booking__check_in', 'booking__room__room_number')

    todays_arrivals = list(today_check_ins.order_by('check_in', 'room__room_number'))
    for booking in todays_arrivals:
        booking.dashboard_payment = booking.payments.first()

    active_guests = Booking.objects.filter(
        status=BookingStatus.CHECKED_IN
    ).select_related('guest', 'room').order_by('check_out', 'room__room_number')

    housekeeping_tasks = HousekeepingTask.objects.filter(
        assigned_to=request.user
    ).select_related('room').order_by('status', 'due_date', '-created_at')

    rooms = Room.objects.all().order_by('room_number')
    room_status_choices = [
        status for status in RoomStatus.choices if status[0] != RoomStatus.OCCUPIED
    ]

    active_complaints = Complaint.objects.filter(
        Q(assigned_to=request.user) | Q(assigned_to__isnull=True),
        status__in=[ComplaintStatus.PENDING, ComplaintStatus.IN_PROGRESS],
    ).select_related('guest', 'booking__room', 'assigned_to').order_by('created_at')
    
    context = {
        'today': today,
        'today_check_ins': today_check_ins,
        'today_check_outs': today_check_outs,
        'current_bookings': current_bookings,
        'upcoming_check_ins': upcoming_check_ins,
        'pending_onsite_payments': pending_onsite_payments,
        'todays_arrivals': todays_arrivals,
        'active_guests': active_guests,
        'housekeeping_tasks': housekeeping_tasks,
        'rooms': rooms,
        'room_status_choices': room_status_choices,
        'active_complaints': active_complaints,
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'available_rooms': available_rooms,
    }
    context.update(get_occupancy_chart_context(today))
    
    return render(request, 'staff/dashboard.html', context)


@login_required(login_url='auth:login')
@staff_manager_or_admin_required
@require_http_methods(["POST"])
def confirm_onsite_cash_payment(request, payment_id):
    """Confirm a pending onsite cash payment from the staff dashboard."""
    payment = get_object_or_404(
        Payment.objects.select_related('booking'),
        id=payment_id,
        status=PaymentStatus.PENDING_ONSITE,
    )
    booking = payment.booking

    payment.status = PaymentStatus.COMPLETED
    payment.completed_at = timezone.now()
    payment.notes = 'Cash payment confirmed by staff'
    payment.save()
    confirm_booking_after_completed_payment(payment)
    log_activity(
        request.user,
        f'Confirmed cash payment for Booking #{booking.id}',
        f'Payment #{payment.id}',
        request
    )

    messages.success(request, 'Cash payment confirmed successfully.')
    return redirect('staff:dashboard')


@login_required(login_url='auth:login')
@staff_manager_or_admin_required
@require_http_methods(["POST"])
def dashboard_check_in_booking(request, booking_id):
    """Route dashboard check-in attempts to the official verification workflow."""
    booking = get_object_or_404(Booking, id=booking_id, status=BookingStatus.CONFIRMED)
    messages.info(request, 'Use the check-in verification form before marking the guest as checked in.')
    return redirect(f"{reverse('staff:check_in_checkout')}?q={booking.id}")


@login_required(login_url='auth:login')
@staff_manager_or_admin_required
@require_http_methods(["POST"])
def dashboard_check_out_booking(request, booking_id):
    """Mark an active guest as checked out."""
    booking = get_object_or_404(Booking, id=booking_id, status=BookingStatus.CHECKED_IN)
    booking.status = BookingStatus.CHECKED_OUT
    booking.checked_out_at = timezone.now()
    booking.save()

    room = booking.room
    previous_status = room.status
    room.status = RoomStatus.DIRTY
    room.is_available = True
    room.save(update_fields=['status', 'is_available', 'updated_at'])
    RoomHousekeepingLog.objects.create(
        room=room,
        previous_status=previous_status,
        current_status=RoomStatus.DIRTY,
        updated_by=request.user,
        booking=booking,
        notes=f'Room {room.room_number} set to dirty after check-out.'
    )

    if not send_checkout_email(booking):
        messages.warning(request, 'Guest checked out, but the checkout receipt email could not be sent.')
    guest_name = booking.guest.get_full_name() or booking.guest.username
    log_activity(
        request.user,
        f'Checked out {guest_name} from Room {room.room_number}',
        f'Booking #{booking.id}',
        request
    )
    messages.success(request, 'Guest checked out successfully')
    return redirect('staff:dashboard')


@login_required(login_url='auth:login')
@staff_manager_or_admin_required
@require_http_methods(["POST"])
def mark_booking_no_show(request, booking_id):
    """Mark a confirmed arrival as no-show."""
    booking = get_object_or_404(Booking, id=booking_id, status=BookingStatus.CONFIRMED)
    booking.status = BookingStatus.NO_SHOW
    booking.save()

    messages.warning(request, f'Booking #{booking.id} marked as no-show.')
    return redirect('staff:dashboard')


@login_required(login_url='auth:login')
@staff_or_admin_required
def room_status(request):
    """View and manage room status"""
    rooms = Room.objects.all().order_by('room_number')
    today = timezone.now().date()
    
    # Get in-house or date-active bookings for each room.
    current_bookings = Booking.objects.filter(
        check_in__lte=today,
        check_out__gt=today,
        status__in=[BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]
    ).select_related('guest', 'room')
    
    # Add booking info to rooms
    for room in rooms:
        room.current_booking = current_bookings.filter(room=room).first()
    
    context = {
        'rooms': rooms,
    }
    
    return render(request, 'staff/room_status.html', context)


@login_required(login_url='auth:login')
@staff_or_admin_required
@require_http_methods(["GET", "POST"])
def room_detail_staff(request, room_id):
    """Staff view for room details and status updates"""
    room = get_object_or_404(Room, id=room_id)
    today = timezone.now().date()
    
    # Get current booking for this room.
    current_booking = Booking.objects.filter(
        room=room,
        check_in__lte=today,
        check_out__gt=today,
        status__in=[BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]
    ).first()
    
    # Get upcoming booking
    upcoming_booking = Booking.objects.filter(
        room=room,
        check_in__gt=today,
        status=BookingStatus.CONFIRMED
    ).order_by('check_in').first()
    
    context = {
        'room': room,
        'current_booking': current_booking,
        'upcoming_booking': upcoming_booking,
    }
    
    return render(request, 'staff/room_detail.html', context)


@login_required(login_url='auth:login')
@staff_or_admin_required
def check_in_checkout_list(request):
    """View upcoming check-ins and check-outs"""
    today = timezone.now().date()
    search_query = request.GET.get('q', '').strip()
    
    # Check-ins today
    check_ins = Booking.objects.filter(
        check_in=today,
        status=BookingStatus.CONFIRMED
    ).select_related('guest', 'room')
    
    # Check-outs today
    check_outs = Booking.objects.filter(
        check_out=today,
        status=BookingStatus.CHECKED_IN
    ).select_related('guest', 'room')
    
    # Tomorrow's check-ins
    tomorrow = today + timedelta(days=1)
    tomorrow_check_ins = Booking.objects.filter(
        check_in=tomorrow,
        status=BookingStatus.CONFIRMED
    ).select_related('guest', 'room')

    search_results = Booking.objects.none()
    if search_query:
        search_filters = (
            Q(booking_reference__iexact=search_query)
            | Q(guest__first_name__icontains=search_query)
            | Q(guest__last_name__icontains=search_query)
            | Q(guest__email__icontains=search_query)
            | Q(guest__phone_number__icontains=search_query)
        )
        booking_id_query = search_query.lstrip('#')
        if booking_id_query.isdigit():
            search_filters |= Q(id=int(booking_id_query))

        search_results = (
            Booking.objects
            .filter(search_filters)
            .select_related('guest', 'room')
            .order_by('-check_in', 'room__room_number')[:10]
        )
    
    context = {
        'today': today,
        'tomorrow': tomorrow,
        'check_ins': check_ins,
        'check_outs': check_outs,
        'tomorrow_check_ins': tomorrow_check_ins,
        'search_query': search_query,
        'search_results': search_results,
    }
    
    return render(request, 'staff/check_in_checkout.html', context)


@login_required(login_url='auth:login')
@staff_or_admin_required
@require_http_methods(["POST"])
def check_in_booking(request, booking_id):
    """Verify guest proof before marking a booking as checked in."""
    booking = get_object_or_404(Booking, id=booking_id)
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
        room = booking.room
        previous_status = room.status
        room.status = RoomStatus.OCCUPIED
        room.is_available = False
        room.save(update_fields=['status', 'is_available', 'updated_at'])
        RoomHousekeepingLog.objects.create(
            room=room,
            previous_status=previous_status,
            current_status=RoomStatus.OCCUPIED,
            updated_by=request.user,
            booking=booking,
            notes=f'Room {room.room_number} set to occupied by check-in verification.'
        )
        if not send_checkin_email(booking):
            messages.warning(request, 'Guest checked in, but the check-in email could not be sent.')
        guest_name = booking.guest.get_full_name() or booking.guest.username
        log_activity(
            request.user,
            f'Checked in {guest_name} to Room {room.room_number}',
            f'Booking #{booking.id}',
            request
        )
        messages.success(request, f'{booking.guest.get_full_name() or booking.guest.username} has been verified and checked in.')

    return redirect('staff:check_in_checkout')


@login_required(login_url='auth:login')
@staff_or_admin_required
@require_http_methods(["GET", "POST"])
def mark_room_clean(request, room_id):
    """Mark room as clean"""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        if room.status == RoomStatus.OCCUPIED:
            message = f'Room {room.room_number} is occupied and cannot be marked clean.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': message}, status=400)
            messages.error(request, message)
            return redirect('staff:room_detail', room_id=room.id)

        previous_status = room.status
        room.status = RoomStatus.CLEAN
        room.is_available = True
        room.save(update_fields=['status', 'is_available', 'updated_at'])
        RoomHousekeepingLog.objects.create(
            room=room,
            previous_status=previous_status,
            current_status=RoomStatus.CLEAN,
            updated_by=request.user,
            notes=f'Room {room.room_number} marked clean from staff room controls.'
        )
        messages.success(request, f'{room.room_number} marked as clean.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Room marked as clean'})
        
        return redirect('staff:room_detail', room_id=room.id)
    
    return redirect('staff:room_detail', room_id=room.id)


@login_required(login_url='auth:login')
@staff_manager_or_admin_required
@require_http_methods(["POST"])
def update_room_status(request):
    """Update a room status from the staff dashboard."""
    room = get_object_or_404(Room, id=request.POST.get('room_id'))
    new_status = request.POST.get('new_status')
    allowed_statuses = [status[0] for status in RoomStatus.choices if status[0] != RoomStatus.OCCUPIED]

    if new_status not in allowed_statuses:
        messages.error(request, 'Select a valid room status. Occupied is set automatically by check-in and check-out.')
        return redirect('staff:dashboard')

    previous_status = room.status
    room.status = new_status
    room.is_available = new_status == RoomStatus.CLEAN
    room.save(update_fields=['status', 'is_available', 'updated_at'])

    RoomHousekeepingLog.objects.create(
        room=room,
        previous_status=previous_status,
        current_status=new_status,
        updated_by=request.user,
        notes=f'Room {room.room_number} status changed to {new_status} by staff {request.user.get_username()}'
    )
    log_audit(
        request,
        request.user,
        'ROOM_STATUS_CHANGED',
        'Room',
        room.id,
        description=f'Room {room.room_number} status changed to {new_status} by staff {request.user.get_username()}',
        changes={'previous_status': previous_status, 'new_status': new_status}
    )
    log_activity(
        request.user,
        f'Updated Room {room.room_number} status to {room.get_status_display()}',
        f'Previous status: {previous_status}',
        request
    )

    messages.success(request, f'Room {room.room_number} status updated to {room.get_status_display()}.')
    return redirect('staff:dashboard')


@login_required(login_url='auth:login')
@staff_manager_or_admin_required
@require_http_methods(["POST"])
def mark_housekeeping_task_complete(request, task_id):
    """Mark an assigned housekeeping task complete and set the room clean."""
    task_queryset = HousekeepingTask.objects.select_related('room', 'assigned_to')
    if request.user.is_staff_member():
        task_queryset = task_queryset.filter(assigned_to=request.user)

    task = get_object_or_404(task_queryset, id=task_id)
    task.status = HousekeepingTaskStatus.COMPLETED
    task.completed_at = timezone.now()
    task.save(update_fields=['status', 'completed_at'])

    room = task.room
    previous_status = room.status
    room.status = RoomStatus.CLEAN
    room.is_available = True
    room.save(update_fields=['status', 'is_available', 'updated_at'])
    RoomHousekeepingLog.objects.create(
        room=room,
        previous_status=previous_status,
        current_status=RoomStatus.CLEAN,
        updated_by=request.user,
        notes=f'Housekeeping task #{task.id} completed by {request.user.get_username()}.'
    )
    log_activity(
        request.user,
        'Completed housekeeping task',
        f'Task #{task.id} for Room {room.room_number}',
        request
    )

    messages.success(request, f'Housekeeping task for room {room.room_number} marked complete.')
    return redirect('staff:dashboard')


@login_required(login_url='auth:login')
@staff_manager_or_admin_required
def guest_services(request):
    """View guest service requests and issues"""
    from .models import ContactMessage
    
    # Get all contact messages
    contact_messages = ContactMessage.objects.all().order_by('-created_at')
    
    # Calculate statistics
    total_messages = contact_messages.count()
    unread_count = contact_messages.filter(is_read=False).count()
    replied_count = contact_messages.filter(is_replied=True).count()
    pending_count = contact_messages.filter(is_read=True, is_replied=False).count()

    base_template = 'staff/staff_base.html'
    dashboard_url_name = 'staff:dashboard'
    dashboard_label = 'Staff Dashboard'
    if request.user.is_manager():
        base_template = 'manager/manager_base.html'
        dashboard_url_name = 'auth:manager_dashboard'
        dashboard_label = 'Manager Dashboard'
    elif request.user.is_admin():
        base_template = 'admin/admin_base.html'
        dashboard_url_name = 'admin_panel:dashboard'
        dashboard_label = 'Admin Dashboard'
    
    context = {
        'page_title': 'Guest Inquiries',
        'base_template': base_template,
        'dashboard_url_name': dashboard_url_name,
        'dashboard_label': dashboard_label,
        'contact_messages': contact_messages,
        'total_messages': total_messages,
        'unread_count': unread_count,
        'replied_count': replied_count,
        'pending_count': pending_count,
    }
    
    return render(request, 'staff/guest_services.html', context)


@login_required(login_url='auth:login')
@staff_manager_or_admin_required
@require_http_methods(["GET"])
def get_message_details(request, message_id):
    """Get message details and replies via AJAX"""
    from .models import ContactMessage, MessageReply
    import re
    from datetime import datetime
    
    try:
        message = ContactMessage.objects.get(id=message_id)
        
        # Mark as read
        if not message.is_read:
            message.is_read = True
            message.save()
        
        # Get all structured replies
        structured_replies = MessageReply.objects.filter(contact_message=message).order_by('created_at')
        
        # Format staff replies
        staff_replies_data = []
        for reply in structured_replies.filter(sender_type=MessageReply.SenderType.STAFF):
            staff_replies_data.append({
                'id': reply.id,
                'staff_name': reply.staff_member.get_full_name() if reply.staff_member else 'System',
                'staff_email': reply.staff_member.email if reply.staff_member else '',
                'reply_text': reply.reply_text,
                'created_at': reply.created_at.strftime('%b %d, %Y at %H:%M'),
                'created_at_iso': reply.created_at.isoformat(),  # For sorting
            })
        
        # Get structured guest replies, then parse legacy guest replies from staff_response.
        guest_replies_data = []
        for reply in structured_replies.filter(sender_type=MessageReply.SenderType.GUEST):
            guest_replies_data.append({
                'id': reply.id,
                'timestamp': reply.created_at.strftime('%b %d, %Y at %H:%M'),
                'timestamp_iso': reply.created_at.isoformat(),
                'text': reply.reply_text,
            })

        if message.staff_response:
            # Pattern: --- Guest Reply (timestamp): ---\n{reply_text}
            pattern = r'--- Guest Reply \((.*?)\): ---\n(.*?)(?=\n\n(?:---|$)|$)'
            matches = re.finditer(pattern, message.staff_response, re.DOTALL)
            for match in matches:
                timestamp_str = match.group(1)
                parsed_dt = None
                # Support both long and short month formats from historical records
                for fmt in ('%B %d, %Y at %I:%M %p', '%b %d, %Y at %I:%M %p', '%b %d, %Y at %H:%M'):
                    try:
                        parsed_dt = timezone.make_aware(datetime.strptime(timestamp_str, fmt))
                        break
                    except Exception:
                        continue

                guest_replies_data.append({
                    'timestamp': timestamp_str,
                    'timestamp_iso': parsed_dt.isoformat() if parsed_dt else '',
                    'text': match.group(2).strip(),
                })
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'name': message.name,
                'email': message.email,
                'phone': message.phone,
                'subject': message.subject,
                'message': message.message,
                'created_at': message.created_at.strftime('%b %d, %Y at %H:%M'),
                'created_at_iso': message.created_at.isoformat(),  # For sorting
                'is_read': message.is_read,
                'is_replied': message.is_replied,
            },
            'staff_replies': staff_replies_data,
            'guest_replies': guest_replies_data,
        })
    except ContactMessage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)


@login_required(login_url='auth:login')
@staff_manager_or_admin_required
@require_http_methods(["POST"])
def send_reply(request, message_id):
    """Send reply to a contact message"""
    from .models import ContactMessage, MessageReply
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        message = ContactMessage.objects.get(id=message_id)
        reply_text = request.POST.get('reply_text', '').strip()
        
        if not reply_text:
            return JsonResponse({'success': False, 'error': 'Reply cannot be empty'}, status=400)
        
        # Create reply
        reply = MessageReply.objects.create(
            contact_message=message,
            staff_member=request.user,
            sender_type=MessageReply.SenderType.STAFF,
            reply_text=reply_text
        )
        
        # Mark message as replied
        message.is_replied = True
        message.notification_sent = False
        message.save(update_fields=['is_replied', 'notification_sent', 'updated_at'])
        
        # Send email to guest
        try:
            email_body = f"""
Hello {message.name},

Thank you for contacting Cebu Luxury Hotel. We appreciate your inquiry.

Your Original Message:
Subject: {message.subject}
Message: {message.message}

---

Our Reply:

{reply_text}

---

If you have any further questions, please don't hesitate to contact us.

Best regards,
Cebu Luxury Hotel Staff
Contact: info@cebuhotel.com | Phone: +63 2 XXXX-XXXX
"""
            
            send_mail(
                subject=f'Re: {message.subject}',
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[message.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't fail the reply creation
            print(f"Error sending email: {str(e)}")
        
        staff_name = request.user.get_full_name() or request.user.username
        timestamp = reply.created_at.strftime('%b %d, %Y at %I:%M %p')
        return JsonResponse({
            'success': True,
            # Flat fields for immediate bubble injection
            'reply_text': reply_text,
            'timestamp': timestamp,
            'staff_name': staff_name,
            # Nested for backwards compatibility
            'reply': {
                'id': reply.id,
                'staff_name': staff_name,
                'staff_email': request.user.email,
                'reply_text': reply_text,
                'created_at': timestamp,
            },
            'message': 'Reply sent successfully and email notification sent to guest!'
        })
    except ContactMessage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='auth:login')
@staff_or_admin_required
def staff_reports(request):
    """Staff reports and statistics"""
    from .models import Payment, PaymentStatus, ContactMessage
    
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    # BOOKING STATISTICS
    total_bookings = Booking.objects.filter(check_in__gte=start_date).count()
    completed_bookings = Booking.objects.filter(
        check_out__lte=today,
        status=BookingStatus.CONFIRMED
    ).count()
    
    # Calculate completion rate percentage
    if total_bookings > 0:
        percentage = (completed_bookings / total_bookings) * 100
    else:
        percentage = 0
    
    # PENDING BOOKINGS
    pending_bookings = Booking.objects.filter(
        status=BookingStatus.PENDING,
        check_in__gte=today
    ).count()
    
    # CANCELLED BOOKINGS
    cancelled_bookings = Booking.objects.filter(
        status=BookingStatus.CANCELLED,
        cancelled_at__gte=start_date
    ).count()
    
    # AVERAGE BOOKING DURATION
    confirmed_bookings = Booking.objects.filter(
        check_out__gte=start_date,
        status=BookingStatus.CONFIRMED
    )
    
    # Better calculation for average duration
    total_nights = sum([b.get_duration() for b in confirmed_bookings])
    avg_duration = (total_nights / confirmed_bookings.count()) if confirmed_bookings.count() > 0 else 0
    
    # REVENUE GENERATED (Last 30 days from completed payments)
    revenue = Payment.objects.filter(
        status=PaymentStatus.COMPLETED,
        completed_at__gte=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # OCCUPANCY RATE
    total_rooms = Room.objects.count()
    rooms_occupied = Room.objects.filter(is_available=False).count()
    occupancy_rate = (rooms_occupied / total_rooms * 100) if total_rooms > 0 else 0
    
    # UNREAD CONTACT MESSAGES
    unread_messages = ContactMessage.objects.filter(is_read=False).count()
    unreplied_messages = ContactMessage.objects.filter(is_replied=False, is_read=True).count()
    
    context = {
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'percentage': round(percentage, 1),
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'avg_duration': round(avg_duration, 1),
        'revenue': revenue,
        'occupancy_rate': round(occupancy_rate, 1),
        'unread_messages': unread_messages,
        'unreplied_messages': unreplied_messages,
        'page_title': 'Staff Reports',
    }
    
    return render(request, 'staff/reports.html', context)


@login_required(login_url='auth:login')
@staff_or_admin_required
def manual_booking(request):
    """Create manual booking for walk-in customers with payment collection"""
    from django.contrib.auth import get_user_model
    from .models import Payment, PaymentMethod, PaymentStatus
    
    User = get_user_model()
    available_rooms = Room.objects.filter(is_available=True)
    payment_methods = PaymentMethod.choices
    
    if request.method == 'POST':
        # Get form data
        guest_first_name = request.POST.get('guest_first_name', '')
        guest_last_name = request.POST.get('guest_last_name', '')
        guest_email = request.POST.get('guest_email', '')
        guest_phone = request.POST.get('guest_phone', '')
        room_id = request.POST.get('room', '')
        check_in = request.POST.get('check_in', '')
        check_out = request.POST.get('check_out', '')
        payment_method = request.POST.get('payment_method', 'CASH')
        payment_amount = request.POST.get('payment_amount', '0')
        reference_number = request.POST.get('reference_number', '')
        
        # Validate reference number for external payment methods
        if payment_method in ['GCASH', 'BANK_TRANSFER']:
            if not reference_number or not reference_number.strip():
                messages.error(request, f'Reference number is required for {"GCash" if payment_method == "GCASH" else "Bank Transfer"} payments.')
                context = {
                    'available_rooms': available_rooms,
                    'payment_methods': payment_methods,
                    'page_title': 'Manual Booking - Walk-in',
                }
                return render(request, 'staff/manual_booking.html', context)
        
        try:
            room = Room.objects.get(id=room_id)
            
            # Check if guest email exists, if not create or reuse
            guest, created = User.objects.get_or_create(
                email=guest_email,
                defaults={
                    'username': guest_email,
                    'first_name': guest_first_name,
                    'last_name': guest_last_name,
                    'phone_number': guest_phone,
                    'role': UserRole.GUEST,
                }
            )
            
            if not created:
                # Update guest info if they already exist
                guest.first_name = guest_first_name
                guest.last_name = guest_last_name
                guest.phone_number = guest_phone
                guest.save()
            
            # Create booking
            from decimal import Decimal
            from datetime import datetime
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
            total_price = Decimal(str(room.price_per_night)) * (check_out_date - check_in_date).days
            
            booking = Booking.objects.create(
                guest=guest,
                room=room,
                check_in=check_in_date,
                check_out=check_out_date,
                total_price=total_price,
                status=BookingStatus.PENDING,
                special_requests=f'Walk-in booking created by {request.user.get_full_name()}'
            )
            
            # Create Payment Record
            payment_amount_decimal = Decimal(payment_amount) if payment_amount else total_price
            
            # Cash/walk-in bookings stay pending until staff explicitly confirms collection.
            if payment_method == 'CASH':
                payment_status = PaymentStatus.PENDING_ONSITE
            else:
                payment_status = PaymentStatus.COMPLETED if payment_amount_decimal >= total_price else PaymentStatus.PENDING
            
            # Handle reference number generation
            # For Cash/Card: auto-generate a reference number
            # For GCash/Bank Transfer: use the provided reference number
            if payment_method in ['CASH', 'STRIPE']:
                # Auto-generate reference for Cash and Card payments
                # Format: WALK-IN-YYYYMMDD-HHMM-BOOKING_ID
                from django.utils import timezone
                now = timezone.now()
                auto_reference = f"WALK-IN-{now.strftime('%Y%m%d%H%M')}-{booking.id}"
                final_reference = auto_reference
            else:
                # Use provided reference for GCash and Bank Transfer
                final_reference = reference_number.strip()
            
            payment = Payment.objects.create(
                booking=booking,
                amount=total_price,  # Store full booking amount
                payment_method=payment_method,
                status=payment_status,
                reference_number=final_reference,
                notes=f'Walk-in payment collected: ₱{payment_amount_decimal}. Created by {request.user.get_full_name()}'
            )
            
            if payment_status == PaymentStatus.COMPLETED:
                from django.utils import timezone
                payment.completed_at = timezone.now()
                payment.save()
                confirm_booking_after_completed_payment(payment)

            log_activity(
                request.user,
                f'Created walk-in booking #{booking.id}',
                f'Payment #{payment.id}',
                request
            )
            
            # Update room availability
            room.is_available = False
            room.save()
            
            # Prepare success message with receipt info
            if payment_status == PaymentStatus.PENDING_ONSITE:
                messages.warning(
                    request,
                    f'Walk-in cash booking created and awaiting staff cash confirmation.\n\nGuest: {guest_first_name} {guest_last_name}\n'
                    f'Room: {room.room_number}\nCheck-in: {check_in_date}\nCheck-out: {check_out_date}\n'
                    f'Amount Due: PHP {total_price}\nReference: {final_reference}'
                )
            elif payment_status == PaymentStatus.COMPLETED:
                messages.success(
                    request, 
                    f'✓ Walk-in booking created & PAID\n\nGuest: {guest_first_name} {guest_last_name}\n'
                    f'Room: {room.room_number}\nCheck-in: {check_in_date}\nCheck-out: {check_out_date}\n'
                    f'Amount: ₱{total_price}\nReceipt: {final_reference}'
                )
            else:
                balance_due = total_price - payment_amount_decimal
                messages.warning(
                    request,
                    f'⚠ Walk-in booking created (PARTIAL PAYMENT)\n\nGuest: {guest_first_name} {guest_last_name}\n'
                    f'Room: {room.room_number}\nPaid: ₱{payment_amount_decimal}\n'
                    f'Balance Due: ₱{balance_due}\nReference: {final_reference}'
                )
            
            return redirect('staff:dashboard')
        
        except Room.DoesNotExist:
            messages.error(request, 'Selected room not found')
        except Exception as e:
            messages.error(request, f'Error creating booking: {str(e)}')
    
    context = {
        'available_rooms': available_rooms,
        'payment_methods': payment_methods,
        'page_title': 'Manual Booking - Walk-in',
    }
    
    return render(request, 'staff/manual_booking.html', context)


@login_required(login_url='auth:login')
@staff_or_admin_required
def pending_balance_bookings(request):
    """View list of bookings with pending balance due"""
    from .models import Payment, PaymentStatus
    from decimal import Decimal
    
    # Get confirmed or checked-in bookings with a balance due.
    bookings_with_partial_payment = []
    
    confirmed_bookings = Booking.objects.filter(
        status__in=[BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]
    ).select_related('guest', 'room')
    
    for booking in confirmed_bookings:
        # Calculate total paid for this booking
        total_paid = Payment.objects.filter(
            booking=booking,
            status=PaymentStatus.COMPLETED
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        balance_due = booking.total_price - total_paid
        
        if balance_due > 0:
            booking.balance_due = balance_due
            booking.total_paid = total_paid
            bookings_with_partial_payment.append(booking)
    
    context = {
        'bookings': bookings_with_partial_payment,
        'page_title': 'Pending Balance Bookings',
    }
    
    return render(request, 'staff/pending_balance_bookings.html', context)


@login_required(login_url='auth:login')
@staff_or_admin_required
@require_http_methods(["GET", "POST"])
def process_remaining_payment(request, booking_id):
    """Process remaining/balance payment for a booking"""
    from .models import Payment, PaymentStatus, PaymentMethod
    from decimal import Decimal
    
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        status__in=[BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]
    )
    
    # Calculate total paid and balance due
    total_paid = Payment.objects.filter(
        booking=booking,
        status=PaymentStatus.COMPLETED
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    
    balance_due = booking.total_price - total_paid
    
    if balance_due <= 0:
        messages.info(request, f'✓ Booking #{booking.id} is fully paid. No additional payment needed.')
        return redirect('staff:dashboard')
    
    payment_methods = PaymentMethod.choices
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'CASH')
        payment_amount = request.POST.get('payment_amount', '0')
        reference_number = request.POST.get('reference_number', '')
        
        # Validate reference number for external payment methods
        if payment_method in ['GCASH', 'BANK_TRANSFER']:
            if not reference_number or not reference_number.strip():
                messages.error(request, f'Reference number is required for {"GCash" if payment_method == "GCASH" else "Bank Transfer"} payments.')
                context = {
                    'booking': booking,
                    'total_paid': total_paid,
                    'balance_due': balance_due,
                    'payment_methods': payment_methods,
                    'page_title': 'Process Remaining Payment',
                }
                return render(request, 'staff/process_remaining_payment.html', context)
        
        try:
            payment_amount_decimal = Decimal(payment_amount) if payment_amount else balance_due
            
            # Don't allow overpayment
            if payment_amount_decimal > balance_due:
                messages.error(request, f'Payment amount cannot exceed balance due (₱{balance_due})')
                context = {
                    'booking': booking,
                    'total_paid': total_paid,
                    'balance_due': balance_due,
                    'payment_methods': payment_methods,
                    'page_title': 'Process Remaining Payment',
                }
                return render(request, 'staff/process_remaining_payment.html', context)
            
            # Determine payment status
            new_balance = balance_due - payment_amount_decimal
            payment_status = PaymentStatus.COMPLETED if new_balance <= 0 else PaymentStatus.PENDING
            
            # Handle reference number generation
            if payment_method in ['CASH', 'STRIPE']:
                # Auto-generate reference for Cash and Card payments
                from django.utils import timezone
                now = timezone.now()
                auto_reference = f"BALANCE-{now.strftime('%Y%m%d%H%M')}-{booking.id}"
                final_reference = auto_reference
            else:
                # Use provided reference for GCash and Bank Transfer
                final_reference = reference_number.strip()
            
            # Create payment record for remaining balance
            payment = Payment.objects.create(
                booking=booking,
                amount=payment_amount_decimal,
                payment_method=payment_method,
                status=payment_status,
                reference_number=final_reference,
                notes=f'Balance payment collected: ₱{payment_amount_decimal}. Previous balance: ₱{balance_due}. Created by {request.user.get_full_name()}'
            )
            
            if payment_status == PaymentStatus.COMPLETED:
                from django.utils import timezone
                payment.completed_at = timezone.now()
                payment.save()

            log_activity(
                request.user,
                f'Confirmed cash payment for Booking #{booking.id}',
                f'Payment #{payment.id}',
                request
            )
            
            if new_balance <= 0:
                messages.success(
                    request,
                    f'✓ Balance Payment Complete!\n\nBooking #{booking.id}\nPrevious Balance: ₱{balance_due}\n'
                    f'Amount Paid: ₱{payment_amount_decimal}\nRemaining Balance: ₱{new_balance if new_balance > 0 else 0}\n'
                    f'Reference: {final_reference}'
                )
            else:
                messages.warning(
                    request,
                    f'⚠ Partial Balance Payment Recorded\n\nBooking #{booking.id}\n'
                    f'Amount Paid: ₱{payment_amount_decimal}\n'
                    f'Previous Balance: ₱{balance_due}\n'
                    f'Remaining Balance: ₱{new_balance}\nReference: {final_reference}'
                )
            
            return redirect('staff:pending_balance')
        
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
    
    context = {
        'booking': booking,
        'total_paid': total_paid,
        'balance_due': balance_due,
        'payment_methods': payment_methods,
        'page_title': 'Process Remaining Payment',
    }
    
    return render(request, 'staff/process_remaining_payment.html', context)


@login_required(login_url='auth:login')
@staff_required
def update_room_housekeeping_status(request, room_id):
    """Staff updates room housekeeping status (clean, dirty, maintenance)"""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status not in [status[0] for status in RoomStatus.choices if status[0] != RoomStatus.OCCUPIED]:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Create housekeeping log entry
        log_entry = RoomHousekeepingLog.objects.create(
            room=room,
            previous_status=room.status,
            current_status=new_status,
            updated_by=request.user,
            notes=notes
        )

        room.status = new_status
        room.is_available = new_status == RoomStatus.CLEAN
        room.save(update_fields=['status', 'is_available', 'updated_at'])
        
        # Log audit
        log_audit(
            request,
            request.user,
            'ROOM_STATUS_CHANGED',
            'Room',
            room.id,
            description=f'Staff updated room {room.room_number} housekeeping status to {new_status}',
            changes={'housekeeping_status': new_status, 'notes': notes}
        )
        log_activity(
            request.user,
            f'Updated Room {room.room_number} status to {room.get_status_display()}',
            f'Previous status: {log_entry.previous_status}',
            request
        )
        
        messages.success(request, f'Room {room.room_number} status updated to {new_status}.')
        return redirect('staff:dashboard')
    
    context = {
        'room': room,
        'statuses': [status for status in RoomStatus.choices if status[0] != RoomStatus.OCCUPIED],
    }
    
    return render(request, 'staff/update_room_status.html', context)


@login_required(login_url='auth:login')
@staff_required
def escalate_guest_complaint(request, booking_id):
    """Staff escalates unresolved guest complaint to manager"""
    from .utils import log_audit
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        complaint_description = request.POST.get('complaint_description')
        staff_notes = request.POST.get('staff_notes', '')
        manager = CustomUser.objects.filter(
            role=UserRole.MANAGER,
            is_active=True,
        ).order_by('id').first()
        
        if not complaint_description:
            messages.error(request, 'Complaint description is required.')
            return redirect('staff:dashboard')

        if not manager:
            messages.error(request, 'No active manager is available for escalation.')
            return redirect('staff:dashboard')
        
        complaint = Complaint.objects.create(
            guest=booking.guest,
            booking=booking,
            subject=f'Complaint for Booking #{booking.id}',
            description=complaint_description,
            assigned_to=request.user,
            escalated_to=manager,
            staff_notes=staff_notes,
            status=ComplaintStatus.ESCALATED,
        )

        if manager.email:
            guest_name = booking.guest.get_full_name() or booking.guest.username
            send_mail(
                f'Complaint escalated: {complaint.subject}',
                (
                    f'Complaint #{complaint.id} has been escalated by {request.user.get_full_name() or request.user.username}.\n\n'
                    f'Guest: {guest_name}\n'
                    f'Room {booking.room.room_number}\n'
                    f'Booking #{booking.id}\n\n'
                    f'{complaint.description}'
                ),
                settings.DEFAULT_FROM_EMAIL,
                [manager.email],
                fail_silently=True,
            )
        
        log_audit(
            request,
            request.user,
            'COMPLAINT_ESCALATED',
            'Complaint',
            complaint.id,
            affected_user=booking.guest,
            description=f'Staff escalated guest complaint for Booking {booking.id}',
            changes={'status': ComplaintStatus.ESCALATED, 'reported_by': request.user.email}
        )
        log_activity(
            request.user,
            'Escalated complaint',
            f'Complaint #{complaint.id} to {manager.get_full_name() or manager.username}',
            request
        )
        
        messages.success(request, 'Guest complaint escalated to manager.')
        return redirect('staff:dashboard')
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'staff/escalate_complaint.html', context)


@login_required(login_url='auth:login')
@staff_required
def request_refund(request, booking_id):
    """Staff can request a refund on behalf of guest or manual booking"""
    from decimal import Decimal
    from .models import RefundRequest, RefundRequestStatus, Payment
    from .utils import log_audit
    
    booking = get_object_or_404(Booking, id=booking_id)
    payment = get_object_or_404(Payment, booking=booking)
    
    if request.method == 'POST':
        refund_amount = request.POST.get('refund_amount')
        reason = request.POST.get('reason')
        
        if not refund_amount or not reason:
            messages.error(request, 'Refund amount and reason are required.')
            return redirect('staff:dashboard')
        
        try:
            refund_amount = Decimal(refund_amount)
            if refund_amount <= 0 or refund_amount > payment.amount:
                messages.error(request, 'Invalid refund amount.')
                return redirect('staff:dashboard')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid refund amount.')
            return redirect('staff:dashboard')
        
        # Create refund request
        refund_request = RefundRequest.objects.create(
            booking=booking,
            requested_by=request.user,
            status=RefundRequestStatus.REQUESTED,
            reason=reason,
            requested_amount=refund_amount
        )
        
        # Log audit
        log_audit(
            request,
            request.user,
            'REFUND_REQUESTED',
            'RefundRequest',
            refund_request.id,
            affected_user=booking.guest,
            description=f'Staff requested refund of ₱{refund_amount} for Booking {booking.id}',
            changes={'status': 'REQUESTED', 'requested_amount': str(refund_amount)}
        )
        
        messages.success(request, 'Refund request submitted for manager approval.')
        return redirect('staff:dashboard')
    
    context = {
        'booking': booking,
        'payment': payment,
    }
    
    return render(request, 'staff/request_refund.html', context)


@login_required(login_url='auth:login')
@staff_manager_or_admin_required
@require_http_methods(["GET"])
def staff_message_detail_view(request, message_id):
    """View detail of a specific guest message (STAFF POV)"""
    from .models import ContactMessage, MessageReply
    import re
    from datetime import datetime
    
    try:
        message = ContactMessage.objects.get(id=message_id)
        # Mark as read when staff views it
        if not message.is_read:
            message.is_read = True
            message.save()
        
        # Get structured replies from MessageReply model
        structured_replies = MessageReply.objects.filter(contact_message=message).order_by('created_at')

        # Parse guest replies from staff_response field
        guest_replies_raw = []
        if message.staff_response:
            # Match both formats:
            # 1. --- Guest Reply (May 15, 2024 at 10:30 AM): ---
            # 2. [Staff Reply - Name on May 15, 2024 at 10:30 AM]
            guest_pattern = r'--- Guest Reply \((.*?)\): ---\n(.*?)(?=\n\n(?:---|$)|$)'
            matches = re.finditer(guest_pattern, message.staff_response, re.DOTALL)
            for match in matches:
                guest_replies_raw.append({
                    'timestamp': match.group(1),
                    'text': match.group(2).strip()
                })
            
            # Legacy staff replies in staff_response field (if any still exist)
            staff_pattern = r'\[Staff Reply - (.*?) on (.*?)\]\n\n(.*?)(?=\n\n---|\Z)'
            staff_matches = re.finditer(staff_pattern, message.staff_response, re.DOTALL)
            for match in staff_matches:
                # To avoid duplication with MessageReply records, we could skip these
                # but for robustness we'll include them only if they aren't already represented
                # For now, we trust the MessageReply migration is complete or mostly complete.
                pass

        # --- Build chronologically-sorted combined reply list ---
        combined_replies = []

        # Start with the original message
        combined_replies.append({
            'type': 'guest',
            'sender': message.name,
            'text': message.message,
            'dt': message.created_at,
            'timestamp': message.created_at.strftime('%b %d, %Y %I:%M %p'),
        })

        for reply in structured_replies:
            sender_name = message.name
            if reply.sender_type == MessageReply.SenderType.STAFF:
                sender_name = 'Staff'
                if reply.staff_member:
                    sender_name = reply.staff_member.get_full_name() or reply.staff_member.username
            combined_replies.append({
                'type': reply.sender_type,
                'sender': sender_name,
                'text': reply.reply_text,
                'dt': reply.created_at,
                'timestamp': reply.created_at.strftime('%b %d, %Y %I:%M %p'),
            })

        for gr in guest_replies_raw:
            # Parse the human-readable timestamp back to datetime for sorting
            dt = None
            for fmt in ('%B %d, %Y at %I:%M %p', '%b %d, %Y at %I:%M %p', '%b %d, %Y at %H:%M'):
                try:
                    dt = timezone.make_aware(datetime.strptime(gr['timestamp'], fmt))
                    break
                except Exception:
                    continue

            if dt is None:
                # Keep unknown historical formats near the tail of thread, not at top
                dt = timezone.now()
            combined_replies.append({
                'type': 'guest',
                'sender': message.name,
                'text': gr['text'],
                'dt': dt,
                'timestamp': gr['timestamp'],
            })

        combined_replies.sort(key=lambda r: r['dt'])

        base_template = 'staff/staff_base.html'
        back_label = 'Back to Guest Inquiries'
        reply_heading = 'Send Reply to Guest'
        reply_button_label = 'Send Reply & Email Guest'
        reply_note = 'Your reply will be sent to the guest via email and displayed in the conversation.'

        if request.user.is_manager():
            base_template = 'manager/manager_base.html'
            reply_heading = 'Manager Reply to Guest'
            reply_button_label = 'Send Manager Reply'
            reply_note = 'Your manager response will be sent to the guest and recorded in the inquiry thread.'
        elif request.user.is_admin():
            base_template = 'admin/admin_base.html'
            reply_heading = 'Admin Reply to Guest'
            reply_button_label = 'Send Admin Reply'
            reply_note = 'Your admin response will be sent to the guest and recorded in the inquiry thread.'

        context = {
            'message': message,
            'combined_replies': combined_replies,
            'is_staff_view': True,
            'base_template': base_template,
            'back_label': back_label,
            'reply_heading': reply_heading,
            'reply_button_label': reply_button_label,
            'reply_note': reply_note,
        }
        return render(request, 'staff/message_detail.html', context)
    except ContactMessage.DoesNotExist:
        messages.error(request, 'Message not found.')
        return redirect('staff:guest_services')


# ==================== STAFF COMPLAINT & REFUND TRACKING ====================

@login_required(login_url='auth:login')
@staff_required
def staff_escalated_complaints_view(request):
    """View complaints escalated by this staff member"""
    complaints = Complaint.objects.filter(
        assigned_to=request.user,
        status__in=[ComplaintStatus.ESCALATED, ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED],
    ).select_related('booking__room', 'guest', 'escalated_to').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        complaints = complaints.filter(status=status_filter)
    
    context = {
        'complaints': complaints,
        'status_filter': status_filter,
        'statuses': ComplaintStatus.choices,
    }
    
    return render(request, 'staff/escalated_complaints.html', context)


@login_required(login_url='auth:login')
@staff_required
@require_http_methods(["POST"])
def escalate_complaint(request, complaint_id):
    """Escalate an active guest complaint to the first available manager."""
    complaint = get_object_or_404(
        Complaint.objects.select_related('guest', 'booking__room', 'assigned_to'),
        Q(assigned_to=request.user) | Q(assigned_to__isnull=True),
        id=complaint_id,
        status__in=[ComplaintStatus.PENDING, ComplaintStatus.IN_PROGRESS],
    )
    manager = CustomUser.objects.filter(
        role=UserRole.MANAGER,
        is_active=True,
    ).order_by('id').first()

    if not manager:
        messages.error(request, 'No active manager is available for escalation.')
        return redirect('staff:complaint_detail', complaint_id=complaint.id)

    if not complaint.assigned_to_id:
        complaint.assigned_to = request.user
    complaint.escalated_to = manager
    complaint.status = ComplaintStatus.ESCALATED
    complaint.staff_notes = request.POST.get('staff_notes', complaint.staff_notes).strip()
    complaint.save(update_fields=['assigned_to', 'escalated_to', 'status', 'staff_notes', 'updated_at'])

    if manager.email:
        guest_name = complaint.guest.get_full_name() or complaint.guest.username
        room_label = f"Room {complaint.booking.room.room_number}" if complaint.booking and complaint.booking.room else "No room linked"
        send_mail(
            f'Complaint escalated: {complaint.subject}',
            (
                f'Complaint #{complaint.id} has been escalated by {request.user.get_full_name() or request.user.username}.\n\n'
                f'Guest: {guest_name}\n'
                f'{room_label}\n'
                f'Subject: {complaint.subject}\n\n'
                f'{complaint.description}'
            ),
            settings.DEFAULT_FROM_EMAIL,
            [manager.email],
            fail_silently=True,
        )

    log_activity(
        request.user,
        'Escalated complaint',
        f'Complaint #{complaint.id} to {manager.get_full_name() or manager.username}',
        request
    )
    messages.success(request, 'Complaint escalated to manager.')
    return redirect('staff:complaint_detail', complaint_id=complaint.id)


@login_required(login_url='auth:login')
@staff_required
def staff_complaint_detail_view(request, complaint_id):
    """View detail of a complaint assigned to or available for this staff member."""
    complaint = get_object_or_404(
        Complaint.objects.select_related('guest', 'booking__room', 'assigned_to', 'escalated_to'),
        Q(assigned_to=request.user) | Q(assigned_to__isnull=True),
        id=complaint_id,
    )
    
    context = {
        'complaint': complaint,
        'booking': complaint.booking,
        'can_escalate': complaint.status in [ComplaintStatus.PENDING, ComplaintStatus.IN_PROGRESS],
    }
    
    return render(request, 'staff/complaint_detail.html', context)


@login_required(login_url='auth:login')
@staff_required
def staff_requested_refunds_view(request):
    """View refunds requested by this staff member"""
    from .models import RefundRequest
    
    refunds = RefundRequest.objects.filter(
        requested_by=request.user
    ).select_related('booking', 'approved_by').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter == RefundRequestStatus.APPROVED:
        status_filter = 'all'
    if status_filter != 'all':
        refunds = refunds.filter(status=status_filter)

    visible_statuses = [
        choice for choice in RefundRequestStatus.choices
        if choice[0] != RefundRequestStatus.APPROVED
    ]
    
    context = {
        'refunds': refunds,
        'status_filter': status_filter,
        'statuses': visible_statuses,
    }
    
    return render(request, 'staff/requested_refunds.html', context)


@login_required(login_url='auth:login')
@staff_required
def staff_refund_detail_view(request, refund_id):
    """View detail of a refund requested by this staff member"""
    from .models import RefundRequest
    
    refund = get_object_or_404(
        RefundRequest,
        id=refund_id,
        requested_by=request.user
    )
    
    context = {
        'refund': refund,
        'booking': refund.booking,
    }
    
    return render(request, 'staff/refund_detail.html', context)
