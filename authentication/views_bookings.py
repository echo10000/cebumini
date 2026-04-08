from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime
from decimal import Decimal

from .models import Booking, Room, BookingStatus, Payment, PaymentStatus
from .forms_bookings import (
    BookingForm, BookingFilterForm, BookingConfirmationForm, CancelBookingForm
)
from .views_recommendations import get_recommendations_context
from .decorators import guest_required, admin_required


# ==================== GUEST VIEWS ====================

@login_required(login_url='login')
@guest_required
def create_booking_view(request, room_id):
    """Create a new booking for a room"""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        # First step: submit dates
        form = BookingForm(request.POST, room=room)
        
        if form.is_valid():
            # Store in session for confirmation step
            request.session['booking_data'] = {
                'room_id': room_id,
                'check_in': form.cleaned_data['check_in'].isoformat(),
                'check_out': form.cleaned_data['check_out'].isoformat(),
                'special_requests': form.cleaned_data['special_requests'],
            }
            
            # Calculate total price for display
            duration = (form.cleaned_data['check_out'] - form.cleaned_data['check_in']).days
            total_price = duration * room.price_per_night
            request.session['booking_price'] = str(total_price)
            
            return redirect('bookings:confirm_booking')
    else:
        form = BookingForm(room=room)
    
    # Get available dates (occupied dates for calendar display)
    occupied_dates = []
    bookings = Booking.objects.filter(
        room=room,
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
    )
    for booking in bookings:
        current_date = booking.check_in
        while current_date < booking.check_out:
            occupied_dates.append(current_date.isoformat())
            current_date = current_date + timezone.timedelta(days=1)

    context = {
        'form': form,
        'room': room,
        'occupied_dates': occupied_dates,
    }
    return render(request, 'bookings/create_booking.html', context)


@login_required(login_url='login')
def confirm_booking_view(request):
    """Confirm booking before finalizing"""
    booking_data = request.session.get('booking_data')
    
    if not booking_data:
        messages.error(request, 'Invalid booking session. Please start over.')
        return redirect('rooms:list')
    
    room = get_object_or_404(Room, id=booking_data['room_id'])
    check_in = datetime.fromisoformat(booking_data['check_in']).date()
    check_out = datetime.fromisoformat(booking_data['check_out']).date()
    duration = (check_out - check_in).days
    total_price = duration * room.price_per_night
    
    if request.method == 'POST':
        confirmation_form = BookingConfirmationForm(request.POST)
        
        if confirmation_form.is_valid():
            # Create booking with PENDING status (payment required before confirmation)
            booking = Booking.objects.create(
                room=room,
                guest=request.user,
                check_in=check_in,
                check_out=check_out,
                total_price=total_price,
                special_requests=booking_data.get('special_requests', ''),
                status=BookingStatus.PENDING  # Changed from CONFIRMED to PENDING
            )
            
            # Clear session
            del request.session['booking_data']
            if 'booking_price' in request.session:
                del request.session['booking_price']
            
            messages.info(
                request, 
                'Booking created! Please proceed to payment to confirm your reservation.'
            )
            # Redirect to payment page instead of booking detail
            return redirect('bookings:payment_page', booking_id=booking.id)
    else:
        confirmation_form = BookingConfirmationForm()
    
    # Get recommendations for other rooms
    recommendations_context = get_recommendations_context(
        request, 
        exclude_room_id=room.id,
        limit=3
    )
    
    context = {
        'room': room,
        'check_in': check_in,
        'check_out': check_out,
        'duration': duration,
        'total_price': total_price,
        'special_requests': booking_data.get('special_requests', ''),
        'confirmation_form': confirmation_form,
        'recommendations': recommendations_context['recommendations'],
        'has_recommendations': recommendations_context['has_recommendations'],
    }
    return render(request, 'bookings/confirm_booking.html', context)


@login_required(login_url='login')
def booking_detail_view(request, booking_id):
    """View booking details"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check authorization: guest can only view their own bookings
    if request.user != booking.guest and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('rooms:list')
    
    can_cancel = booking.can_be_cancelled()
    
    # Get recommendations for this booking
    recommendations_context = get_recommendations_context(
        request,
        exclude_room_id=booking.room.id,
        limit=3
    )
    
    context = {
        'booking': booking,
        'can_cancel': can_cancel,
        'recommendations': recommendations_context['recommendations'],
        'has_recommendations': recommendations_context['has_recommendations'],
    }
    return render(request, 'bookings/booking_detail.html', context)


@login_required(login_url='login')
def booking_history_view(request):
    """View guest's booking history"""
    bookings = Booking.objects.filter(guest=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'bookings': page_obj.object_list,
        'status_filter': status_filter,
        'total_bookings': bookings.count(),
    }
    return render(request, 'bookings/booking_history.html', context)


@login_required(login_url='login')
def cancel_booking_view(request, booking_id):
    """Cancel a booking with refund processing"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check authorization
    if request.user != booking.guest and not request.user.is_admin():
        messages.error(request, 'You do not have permission to cancel this booking.')
        return redirect('rooms:list')
    
    # Check if booking can be cancelled
    if not booking.can_be_cancelled():
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('bookings:booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        cancel_form = CancelBookingForm(request.POST)
        
        if cancel_form.is_valid():
            # Calculate refund amount
            refund_amount, refund_percent, refund_policy = booking.get_refund_amount()
            
            # Get or create payment record
            try:
                payment = booking.payment
            except:
                payment = None
            
            # Update booking
            booking.status = BookingStatus.CANCELLED
            booking.cancellation_reason = cancel_form.cleaned_data.get('reason', '')
            booking.cancelled_at = timezone.now()
            booking.save()
            
            # Update payment if exists
            if payment and payment.status == PaymentStatus.COMPLETED:
                if refund_amount > 0:
                    payment.refund_amount = refund_amount
                    payment.refund_reason = f'{refund_policy} - Booking cancelled by {request.user.email}'
                    if refund_amount >= payment.amount:
                        payment.status = PaymentStatus.REFUNDED
                    else:
                        payment.status = PaymentStatus.PARTIALLY_REFUNDED
                    payment.refunded_at = timezone.now()
                    payment.save()
                    
                    messages.success(
                        request,
                        f'Booking #{booking.id} cancelled. Refund: PHP {refund_amount:.2f} ({refund_percent}%) - {refund_policy}'
                    )
                else:
                    messages.warning(
                        request,
                        f'Booking #{booking.id} cancelled. No refund available - {refund_policy}'
                    )
            else:
                messages.success(
                    request,
                    f'Booking #{booking.id} has been cancelled successfully.'
                )
            
            return redirect('bookings:booking_history')
    else:
        cancel_form = CancelBookingForm()
    
    # Calculate refund info for display
    refund_amount, refund_percent, refund_policy = booking.get_refund_amount()
    
    context = {
        'booking': booking,
        'cancel_form': cancel_form,
        'refund_amount': refund_amount,
        'refund_percent': refund_percent,
        'refund_policy': refund_policy,
        'cancellation_policy': booking.get_cancellation_policy_display(),
    }
    return render(request, 'bookings/cancel_booking.html', context)


# ==================== ADMIN VIEWS ====================

@login_required(login_url='login')
def admin_bookings_view(request):
    """Admin view: list all bookings with filtering"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        return redirect('rooms:list')
    
    bookings = Booking.objects.select_related('room', 'guest').order_by('-created_at')
    
    # Apply filters
    filter_form = BookingFilterForm(request.GET)
    
    if filter_form.is_valid():
        # Room type filter
        room_type = filter_form.cleaned_data.get('room_type')
        if room_type:
            bookings = bookings.filter(room__room_type=room_type)
        
        # Status filter
        status = filter_form.cleaned_data.get('status')
        if status:
            bookings = bookings.filter(status=status)
        
        # Date range filters
        check_in_from = filter_form.cleaned_data.get('check_in_from')
        if check_in_from:
            bookings = bookings.filter(check_in__gte=check_in_from)
        
        check_in_to = filter_form.cleaned_data.get('check_in_to')
        if check_in_to:
            bookings = bookings.filter(check_in__lte=check_in_to)
        
        # Guest search
        guest_search = filter_form.cleaned_data.get('guest_search')
        if guest_search:
            bookings = bookings.filter(
                Q(guest__username__icontains=guest_search) |
                Q(guest__email__icontains=guest_search) |
                Q(guest__first_name__icontains=guest_search) |
                Q(guest__last_name__icontains=guest_search)
            )
    
    # Pagination
    paginator = Paginator(bookings, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(status=BookingStatus.CONFIRMED).count()
    pending_bookings = Booking.objects.filter(status=BookingStatus.PENDING).count()
    cancelled_bookings = Booking.objects.filter(status=BookingStatus.CANCELLED).count()
    
    # Revenue calculation
    revenue = sum(
        booking.total_price 
        for booking in Booking.objects.filter(status=BookingStatus.CONFIRMED)
    )
    
    context = {
        'page_obj': page_obj,
        'bookings': page_obj.object_list,
        'filter_form': filter_form,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'revenue': revenue,
    }
    return render(request, 'bookings/admin_bookings.html', context)


@login_required(login_url='login')
def admin_cancel_booking_view(request, booking_id):
    """Admin: cancel a booking"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        return redirect('rooms:list')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        booking.status = BookingStatus.CANCELLED
        booking.save()
        
        messages.success(
            request,
            f'Booking #{booking.id} for {booking.guest.username} has been cancelled.'
        )
        return redirect('bookings:admin_bookings')
    
    context = {
        'booking': booking,
    }
    return render(request, 'bookings/admin_cancel_booking.html', context)


@login_required(login_url='login')
def admin_confirm_booking_view(request, booking_id):
    """Admin: confirm a pending booking"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        return redirect('rooms:list')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.status != BookingStatus.PENDING:
        messages.warning(request, 'This booking is already confirmed or cancelled.')
        return redirect('bookings:admin_bookings')
    
    booking.status = BookingStatus.CONFIRMED
    booking.save()
    
    messages.success(
        request,
        f'Booking #{booking.id} for {booking.guest.username} has been confirmed.'
    )
    return redirect('bookings:admin_bookings')
