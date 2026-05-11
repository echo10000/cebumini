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
from .utils import confirm_booking_after_completed_payment


@login_required
@require_http_methods(["GET"])
def payment_success_view(request, booking_id):
    """
    Payment success confirmation page.
    Displayed after successful PayMongo payment.
    """
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    payment = get_object_or_404(Payment.objects.order_by('-created_at'), booking=booking)

    if payment.status == PaymentStatus.COMPLETED and booking.status != BookingStatus.CONFIRMED:
        confirm_booking_after_completed_payment(payment)
        messages.info(request, 'Booking has been confirmed after payment verification.')

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
    payment = get_object_or_404(Payment.objects.order_by('-created_at'), booking=booking)

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
    payment = get_object_or_404(Payment.objects.order_by('-created_at'), booking=booking)

    context = {
        'booking': booking,
        'payment': payment,
    }
    return render(request, 'payments/payment_pending.html', context)
