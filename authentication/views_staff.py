"""
Staff Views - Handle housekeeping and front desk operations
Staff members can manage room status, check-ins, check-outs, and maintenance
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
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
        
        return redirect('staff:room_status')
    
    return redirect('staff:room_status')


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
            
            payment = Payment.objects.create(
                booking=booking,
                amount=total_price,  # Store full booking amount
                payment_method=payment_method,
                status=payment_status,
                reference_number=reference_number if reference_number else f"WALK-IN-{booking.id}",
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
                    f'Amount: ₱{total_price}\nReceipt: {reference_number if reference_number else f"WALK-IN-{booking.id}"}'
                )
            else:
                balance_due = total_price - payment_amount_decimal
                messages.warning(
                    request,
                    f'⚠ Walk-in booking created (PARTIAL PAYMENT)\n\nGuest: {guest_first_name} {guest_last_name}\n'
                    f'Room: {room.room_number}\nPaid: ₱{payment_amount_decimal}\n'
                    f'Balance Due: ₱{balance_due}'
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

