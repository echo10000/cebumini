"""
Staff Views - Handle housekeeping and front desk operations
Staff members can manage room status, check-ins, check-outs, and maintenance
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.db import models
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta

from .decorators import staff_required, staff_or_admin_required
from .models import Booking, BookingStatus, Room, CustomUser, UserRole
from .forms_bookings import ContactForm


@login_required(login_url='auth:login')
@staff_or_admin_required
def staff_dashboard(request):
    """Staff Dashboard with daily tasks and room status"""
    today = timezone.now().date()
    
    # Get today's bookings
    today_check_ins = Booking.objects.filter(
        check_in=today,
        status=BookingStatus.CONFIRMED
    ).select_related('guest', 'room')
    
    today_check_outs = Booking.objects.filter(
        check_out=today,
        status=BookingStatus.CONFIRMED
    ).select_related('guest', 'room')
    
    # Get current bookings (checked in but not checked out yet)
    current_bookings = Booking.objects.filter(
        check_in__lte=today,
        check_out__gt=today,
        status=BookingStatus.CONFIRMED
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
    
    context = {
        'today': today,
        'today_check_ins': today_check_ins,
        'today_check_outs': today_check_outs,
        'current_bookings': current_bookings,
        'upcoming_check_ins': upcoming_check_ins,
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'available_rooms': available_rooms,
    }
    
    return render(request, 'staff/dashboard.html', context)


@login_required(login_url='auth:login')
@staff_or_admin_required
def room_status(request):
    """View and manage room status"""
    rooms = Room.objects.all().order_by('room_number')
    today = timezone.now().date()
    
    # Get current bookings for each room
    current_bookings = Booking.objects.filter(
        check_in__lte=today,
        check_out__gt=today,
        status=BookingStatus.CONFIRMED
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
    
    # Get current booking for this room
    current_booking = Booking.objects.filter(
        room=room,
        check_in__lte=today,
        check_out__gt=today,
        status=BookingStatus.CONFIRMED
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
    
    # Check-ins today
    check_ins = Booking.objects.filter(
        check_in=today,
        status=BookingStatus.CONFIRMED
    ).select_related('guest', 'room')
    
    # Check-outs today
    check_outs = Booking.objects.filter(
        check_out=today,
        status=BookingStatus.CONFIRMED
    ).select_related('guest', 'room')
    
    # Tomorrow's check-ins
    tomorrow = today + timedelta(days=1)
    tomorrow_check_ins = Booking.objects.filter(
        check_in=tomorrow,
        status=BookingStatus.CONFIRMED
    ).select_related('guest', 'room')
    
    context = {
        'today': today,
        'tomorrow': tomorrow,
        'check_ins': check_ins,
        'check_outs': check_outs,
        'tomorrow_check_ins': tomorrow_check_ins,
    }
    
    return render(request, 'staff/check_in_checkout.html', context)


@login_required(login_url='auth:login')
@staff_or_admin_required
@require_http_methods(["GET", "POST"])
def mark_room_clean(request, room_id):
    """Mark room as clean"""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        # Update room status (if you have a status field)
        # For now, we'll just show a success message
        messages.success(request, f'{room.room_number} marked as clean.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Room marked as clean'})
        
        return redirect('staff:dashboard')
    
    return redirect('staff:dashboard')


@login_required(login_url='auth:login')
@staff_or_admin_required
def guest_services(request):
    """View guest service requests and issues"""
    # Get contact messages (you might want to add a support ticket model)
    context = {
        'page_title': 'Guest Services',
    }
    
    return render(request, 'staff/guest_services.html', context)


@login_required(login_url='auth:login')
@staff_or_admin_required
def staff_reports(request):
    """Staff reports and statistics"""
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    
    # Occupancy stats
    total_bookings = Booking.objects.filter(check_in__gte=start_date).count()
    completed_bookings = Booking.objects.filter(
        check_out__lte=today,
        status=BookingStatus.CONFIRMED
    ).count()
    
    context = {
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
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
                status=BookingStatus.CONFIRMED,
                special_requests=f'Walk-in booking created by {request.user.get_full_name()}'
            )
            
            # Create Payment Record
            payment_amount_decimal = Decimal(payment_amount) if payment_amount else total_price
            
            # Determine payment status based on amount collected
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
            
            # Update room availability
            room.is_available = False
            room.save()
            
            # Prepare success message with receipt info
            if payment_status == PaymentStatus.COMPLETED:
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
            
            return redirect('auth:dashboard')
        
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
    
    # Get all bookings with CONFIRMED status (checked in or staying)
    bookings_with_partial_payment = []
    
    confirmed_bookings = Booking.objects.filter(
        status=BookingStatus.CONFIRMED
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
    
    booking = get_object_or_404(Booking, id=booking_id, status=BookingStatus.CONFIRMED)
    
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
            
            # Update booking status if fully paid
            if new_balance <= 0:
                booking.status = BookingStatus.CONFIRMED  # Already confirmed, just updating the payment
                booking.save()
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
            
            return redirect('staff:dashboard')
        
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
    from .models import RoomStatus, RoomHousekeepingLog
    from .utils import log_audit
    
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status not in [status[0] for status in RoomStatus.choices]:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Create housekeeping log entry
        log_entry = RoomHousekeepingLog.objects.create(
            room=room,
            previous_status=getattr(room, 'housekeeping_status', RoomStatus.CLEAN),
            current_status=new_status,
            updated_by=request.user,
            notes=notes
        )
        
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
        
        messages.success(request, f'Room {room.room_number} status updated to {new_status}.')
        return redirect('staff:dashboard')
    
    context = {
        'room': room,
        'statuses': RoomStatus.choices,
    }
    
    return render(request, 'staff/update_room_status.html', context)


@login_required(login_url='auth:login')
@staff_required
def escalate_guest_complaint(request, booking_id):
    """Staff escalates unresolved guest complaint to manager"""
    from .models import GuestComplaintEscalation
    from .utils import log_audit
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        complaint_description = request.POST.get('complaint_description')
        staff_notes = request.POST.get('staff_notes', '')
        
        if not complaint_description:
            messages.error(request, 'Complaint description is required.')
            return redirect('staff:dashboard')
        
        # Create escalation record
        escalation = GuestComplaintEscalation.objects.create(
            booking=booking,
            guest=booking.guest,
            complaint_description=complaint_description,
            reported_by_staff=request.user,
            staff_notes=staff_notes,
            status='OPEN'
        )
        
        # Log audit
        log_audit(
            request,
            request.user,
            'COMPLAINT_ESCALATED',
            'GuestComplaintEscalation',
            escalation.id,
            affected_user=booking.guest,
            description=f'Staff escalated guest complaint for Booking {booking.id}',
            changes={'status': 'OPEN', 'reported_by': request.user.email}
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


