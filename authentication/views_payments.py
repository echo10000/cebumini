"""
Payment Status Views - PayMongo Only
Only handles success, failed, and pending payment status displays.
All payment processing is handled by PayMongo gateway.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .models import Booking, BookingStatus, Payment, PaymentStatus


@login_required
@require_http_methods(["GET"])
def payment_success_view(request, booking_id):
    """
    Payment success confirmation page.
    Displayed after successful PayMongo payment.
    """
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    payment = get_object_or_404(Payment, booking=booking)

    if payment.status == PaymentStatus.COMPLETED and booking.status != BookingStatus.CONFIRMED:
        booking.status = BookingStatus.CONFIRMED
        booking.save()
        messages.info(request, 'Booking has been confirmed after payment verification.')

    if booking.status == BookingStatus.CONFIRMED:
        email_sent_key = f'booking_{booking.id}_confirmation_sent'
        if not request.session.get(email_sent_key, False):
            sent = booking.send_confirmation_email()
            if sent:
                request.session[email_sent_key] = True
                messages.success(request, f'Booking confirmation email sent to {booking.guest.email}.')
            else:
                messages.warning(request, 'Booking confirmation email was not sent. Please contact support.')
        else:
            messages.info(request, 'A booking confirmation email has already been sent for this booking.')

    context = {
        'booking': booking,
        'payment': payment,
    }
    return render(request, 'payments/payment_success.html', context)


@login_required
@require_http_methods(["GET"])
def payment_failed_view(request, booking_id):
    """
    Payment failed page with retry option.
    Displayed when PayMongo payment fails.
    """
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    payment = get_object_or_404(Payment, booking=booking)

    context = {
        'booking': booking,
        'payment': payment,
    }
    return render(request, 'payments/payment_failed.html', context)


@login_required
@require_http_methods(["GET"])
def payment_pending_view(request, booking_id):
    """
    Payment pending verification page.
    Displayed when payment is pending manual verification.
    """
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    payment = get_object_or_404(Payment, booking=booking)

    context = {
        'booking': booking,
        'payment': payment,
    }
    return render(request, 'payments/payment_pending.html', context)
