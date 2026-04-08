from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime
import json
import stripe

from .models import Booking, Payment, PaymentStatus, PaymentMethod
from .forms_payments import (
    PaymentMethodForm, StripePaymentForm, GCashPaymentForm, BankTransferForm
)

# Initialize Stripe with test key
stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
@require_http_methods(["GET", "POST"])
def payment_page_view(request, booking_id):
    """
    Main payment page - displays payment method selection.
    """
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    
    # Check if booking already has a completed payment
    try:
        payment = Payment.objects.get(booking=booking)
        if payment.status == PaymentStatus.COMPLETED:
            messages.info(request, 'This booking already has a completed payment.')
            return redirect('bookings:booking_detail', booking_id=booking.id)
    except Payment.DoesNotExist:
        # Create pending payment record
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            payment_method=PaymentMethod.STRIPE,  # Default
            status=PaymentStatus.PENDING
        )

    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            method = form.cleaned_data['payment_method']
            # Update payment method
            payment.payment_method = method
            payment.save()
            
            # Redirect to specific payment form
            if method == PaymentMethod.PAYMONGO:
                return redirect('bookings:paymongo_payment', booking_id=booking.id)
            elif method == PaymentMethod.STRIPE:
                return redirect('bookings:stripe_payment', booking_id=booking.id)
            elif method == PaymentMethod.GCASH:
                return redirect('bookings:gcash_payment', booking_id=booking.id)
            elif method == 'BANK_TRANSFER':
                return redirect('bookings:bank_transfer_payment', booking_id=booking.id)
    else:
        form = PaymentMethodForm(initial={'payment_method': payment.payment_method})

    context = {
        'booking': booking,
        'form': form,
        'payment': payment,
        'test_mode': settings.PAYMENT_TEST_MODE,
    }
    return render(request, 'payments/payment.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def stripe_payment_view(request, booking_id):
    """
    Stripe payment form and processing (test mode).
    """
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    payment = get_object_or_404(Payment, booking=booking)

    if request.method == 'POST':
        form = StripePaymentForm(request.POST)
        if form.is_valid():
            # In test mode, simulate payment processing
            if settings.PAYMENT_TEST_MODE:
                card_number = form.cleaned_data['card_number']
                
                # Simulate test card responses
                if card_number == '4242424242424242':
                    # Success
                    payment.status = PaymentStatus.COMPLETED
                    payment.transaction_id = f'stripe_test_{booking.id}_{int(datetime.now().timestamp())}'
                    payment.reference_number = form.cleaned_data.get('cardholder_name', 'Test Payment')
                    payment.notes = f"Test mode payment via Stripe - {form.cleaned_data['cardholder_name']}"
                    payment.completed_at = datetime.now()
                    payment.save()

                    # Mark booking as confirmed
                    booking.status = 'CONFIRMED'
                    booking.save()

                    messages.success(request, 'Payment successful! Your booking is confirmed.')
                    return redirect('bookings:payment_success', booking_id=booking.id)
                
                elif card_number == '4000000000000002':
                    # Failure
                    payment.status = PaymentStatus.FAILED
                    payment.notes = 'Test mode payment failed - card decline simulation'
                    payment.save()
                    messages.error(request, 'Payment failed. Please try again or use a different card.')
                    return redirect('bookings:payment_failed', booking_id=booking.id)
                else:
                    # Generic test card that succeeds
                    payment.status = PaymentStatus.COMPLETED
                    payment.transaction_id = f'stripe_test_{booking.id}_{int(datetime.now().timestamp())}'
                    payment.reference_number = form.cleaned_data.get('cardholder_name', 'Test Payment')
                    payment.notes = f"Test mode payment via Stripe - {form.cleaned_data['cardholder_name']}"
                    payment.completed_at = datetime.now()
                    payment.save()

                    # Mark booking as confirmed
                    booking.status = 'CONFIRMED'
                    booking.save()

                    messages.success(request, 'Payment successful! Your booking is confirmed.')
                    return redirect('bookings:payment_success', booking_id=booking.id)
            else:
                # Production mode - integrate with real Stripe API
                try:
                    # This would be actual Stripe integration
                    token = stripe.Token.create(
                        card={
                            'number': form.cleaned_data['card_number'],
                            'exp_month': int(form.cleaned_data['card_expiry'].split('/')[0]),
                            'exp_year': int(form.cleaned_data['card_expiry'].split('/')[1]),
                            'cvc': form.cleaned_data['card_cvc'],
                        }
                    )
                    
                    charge = stripe.Charge.create(
                        amount=int(booking.total_price * 100),  # Convert to cents
                        currency=settings.PAYMENT_CURRENCY.lower(),
                        source=token.id,
                        description=f'Booking #{booking.id} - Cebu Hotel'
                    )
                    
                    payment.status = PaymentStatus.COMPLETED
                    payment.transaction_id = charge.id
                    payment.completed_at = datetime.now()
                    payment.save()

                    booking.status = 'CONFIRMED'
                    booking.save()

                    messages.success(request, 'Payment successful! Your booking is confirmed.')
                    return redirect('bookings:payment_success', booking_id=booking.id)
                except stripe.error.CardError as e:
                    payment.status = PaymentStatus.FAILED
                    payment.notes = str(e)
                    payment.save()
                    messages.error(request, f'Payment failed: {e.message}')
                    return redirect('bookings:payment_failed', booking_id=booking.id)
    else:
        form = StripePaymentForm()

    context = {
        'booking': booking,
        'form': form,
        'payment': payment,
        'test_mode': settings.PAYMENT_TEST_MODE,
        'test_card_success': '4242 4242 4242 4242',
        'test_card_failure': '4000 0000 0000 0002',
    }
    return render(request, 'payments/stripe_payment.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def gcash_payment_view(request, booking_id):
    """
    GCash payment form and processing (Philippine mobile wallet).
    Two-step process: User sends payment via GCash, then enters reference here.
    """
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    payment = get_object_or_404(Payment, booking=booking)

    if request.method == 'POST':
        form = GCashPaymentForm(request.POST)
        if form.is_valid():
            reference = form.cleaned_data['gcash_reference'].strip()
            
            # Mark payment as completed with the reference provided
            payment.status = PaymentStatus.COMPLETED
            payment.transaction_id = f"GCASH_{reference}_{int(datetime.now().timestamp())}"
            payment.reference_number = reference
            payment.notes = f"GCash payment - Reference: {reference}"
            payment.completed_at = datetime.now()
            payment.save()

            # Mark booking as confirmed
            booking.status = 'CONFIRMED'
            booking.save()

            messages.success(request, 'GCash payment verified! Your booking is confirmed.')
            return redirect('bookings:payment_success', booking_id=booking.id)
    else:
        form = GCashPaymentForm()

    context = {
        'booking': booking,
        'form': form,
        'payment': payment,
    }
    return render(request, 'payments/gcash_payment.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def bank_transfer_payment_view(request, booking_id):
    """
    Bank transfer payment form and processing.
    """
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    payment = get_object_or_404(Payment, booking=booking)

    if request.method == 'POST':
        form = BankTransferForm(request.POST)
        if form.is_valid():
            # Save bank transfer details
            payment.status = PaymentStatus.PENDING  # Pending manual verification
            payment.transaction_id = f"BANK_{booking.id}_{int(datetime.now().timestamp())}"
            payment.reference_number = form.cleaned_data['reference_number']
            payment.notes = f"Bank: {form.cleaned_data['bank_name']} | {form.cleaned_data.get('notes', '')}"
            payment.save()

            messages.success(
                request,
                'Bank transfer details saved. Your payment is pending verification by our admin team.'
            )
            return redirect('bookings:payment_pending', booking_id=booking.id)

    else:
        form = BankTransferForm()

    context = {
        'booking': booking,
        'form': form,
        'payment': payment,
        'bank_accounts': {
            'BDO': 'BDO Unibank - 123-456-789',
            'BPI': 'BPI Family Savings Bank - 456-789-123',
            'Metrobank': 'Metropolitan Bank - 789-123-456',
        }
    }
    return render(request, 'payments/bank_transfer_payment.html', context)


@login_required
@require_http_methods(["GET"])
def payment_success_view(request, booking_id):
    """
    Payment success confirmation page.
    """
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    payment = get_object_or_404(Payment, booking=booking)

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
    Payment pending verification page (for bank transfers).
    """
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    payment = get_object_or_404(Payment, booking=booking)

    context = {
        'booking': booking,
        'payment': payment,
    }
    return render(request, 'payments/payment_pending.html', context)


@require_http_methods(["POST"])
def stripe_webhook_view(request):
    """
    Webhook endpoint for Stripe events (confirmation, failure, etc).
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        if settings.PAYMENT_TEST_MODE:
            # Skip webhook verification in test mode
            event = json.loads(payload)
        else:
            # Verify signature in production
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )

        if event['type'] == 'charge.succeeded':
            charge = event['data']['object']
            # Handle successful charge
            # Find and update payment record if needed
            pass

        elif event['type'] == 'charge.failed':
            charge = event['data']['object']
            # Handle failed charge
            pass

        return JsonResponse({'status': 'success'})

    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
