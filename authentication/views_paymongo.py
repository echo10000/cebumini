"""
PayMongo Payment Handler Views
Handles GCash, Cards, and Maya payments through PayMongo
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.db import models
from datetime import datetime
import json
import hashlib
import hmac
import requests
from decimal import Decimal

from .views_admin import admin_required
from .models import Booking, Payment, PaymentStatus, PaymentMethod, BookingStatus
from .utils import confirm_booking_after_completed_payment


def _complete_paymongo_payment(payment, transaction_id=None, reference_number=None, notes='PayMongo payment completed'):
    """Mark a PayMongo payment completed and confirm the booking through one guarded path."""
    payment.status = PaymentStatus.COMPLETED
    payment.payment_method = PaymentMethod.PAYMONGO
    if transaction_id:
        payment.transaction_id = transaction_id
    if reference_number:
        payment.reference_number = reference_number
    payment.notes = notes
    payment.completed_at = timezone.now()
    payment.save()
    confirm_booking_after_completed_payment(payment)


def _find_payment_from_paymongo_payload(event_data):
    """Find a local payment from PayMongo checkout/payment webhook payloads."""
    metadata = event_data.get('metadata') or {}
    attributes = event_data.get('attributes') or {}
    checkout_id = event_data.get('id') or attributes.get('checkout_session_id') or attributes.get('checkout_session')
    payment_id = attributes.get('payment_id') or attributes.get('id')

    payments = attributes.get('payments') or event_data.get('payments') or []
    if payments:
        first_payment = payments[0] or {}
        payment_id = payment_id or first_payment.get('id')

    booking_id = metadata.get('booking_id') or attributes.get('metadata', {}).get('booking_id')

    if checkout_id:
        payment = Payment.objects.filter(reference_number=checkout_id).first()
        if payment:
            return payment, payment_id, checkout_id

    if payment_id:
        payment = Payment.objects.filter(
            models.Q(transaction_id=payment_id) | models.Q(reference_number=payment_id)
        ).first()
        if payment:
            return payment, payment_id, checkout_id

    if booking_id:
        payment = Payment.objects.filter(
            booking_id=booking_id,
            payment_method=PaymentMethod.PAYMONGO,
        ).order_by('-created_at').first()
        if payment:
            return payment, payment_id, checkout_id

    return None, payment_id, checkout_id


class PayMongoHandler:
    """PayMongo payment handler"""
    
    def __init__(self):
        self.public_key = settings.PAYMONGO_PUBLIC_KEY
        self.secret_key = settings.PAYMONGO_SECRET_KEY
        self.webhook_secret = settings.PAYMONGO_WEBHOOK_SECRET
        self.test_mode = settings.PAYMONGO_TEST_MODE
        self.api_url = 'https://api.paymongo.com/v1'
        self.refund_api_url = 'https://api.paymongo.com'
        self.authorization = self._get_auth()
    
    def _get_auth(self):
        """Get authorization header for PayMongo API"""
        import base64
        credentials = base64.b64encode(f'{self.secret_key}:'.encode()).decode()
        return f'Basic {credentials}'
    
    def create_checkout_session(self, booking, return_url):
        """Create a PayMongo checkout session"""
        try:
            headers = {
                'Authorization': self.authorization,
                'Content-Type': 'application/json'
            }
            
            # Calculate line items based on nights
            nights = (booking.check_out - booking.check_in).days
            price_in_cents = int(booking.total_price * 100)  # Convert to centavos
            
            payload = {
                'data': {
                    'attributes': {
                        'line_items': [
                            {
                                'amount': price_in_cents,
                                'currency': 'PHP',
                                'description': f'{booking.room.room_number} ({nights}N)',
                                'name': f'Room {booking.room.room_number}',
                                'quantity': 1,
                            }
                        ],
                        'payment_method_types': ['card', 'gcash', 'paymaya', 'grab_pay'],
                        'success_url': return_url,
                        'cancel_url': return_url,
                        'description': f'Booking #{booking.id}',
                        'metadata': {
                            'booking_id': str(booking.id),
                            'guest_email': booking.guest.email,
                            'guest_name': booking.guest.get_full_name(),
                        }
                    }
                }
            }
            
            response = requests.post(
                f'{self.api_url}/checkout_sessions',
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                session_data = response.json().get('data', {})
                return {
                    'success': True,
                    'session_id': session_data.get('id'),
                    'checkout_url': session_data.get('attributes', {}).get('checkout_url'),
                    'session_data': session_data
                }
            else:
                return {
                    'success': False,
                    'error': f'PayMongo API error: {response.status_code}',
                    'response': response.text
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'PayMongo error: {str(e)}'
            }
    
    def retrieve_session(self, session_id):
        """Retrieve checkout session details"""
        try:
            headers = {
                'Authorization': self.authorization,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.api_url}/checkout_sessions/{session_id}',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get('data', {})
            return None
        
        except Exception as e:
            print(f'Error retrieving session: {str(e)}')
            return None

    def create_refund(self, payment):
        """Create a PayMongo refund for a completed payment."""
        return self.process_refund(
            payment.transaction_id,
            int(payment.amount * 100),
            reason='others'
        )

    def process_refund(self, payment_id, amount_in_centavos, reason="others"):
        """Create a PayMongo refund for a payment ID and amount in centavos."""
        try:
            if not payment_id:
                return {
                    'success': False,
                    'refund_id': None,
                    'error': 'Missing PayMongo payment ID.'
                }

            if str(payment_id).startswith(('ch_', 'cs_')):
                return {
                    'success': False,
                    'refund_id': None,
                    'error': 'Stored PayMongo ID is not a payment ID. Re-verify the payment before refunding.'
                }

            headers = {
                'Authorization': self.authorization,
                'Content-Type': 'application/json'
            }
            payload = {
                'data': {
                    'attributes': {
                        'amount': amount_in_centavos,
                        'payment_id': payment_id,
                        'reason': reason,
                    }
                }
            }

            response = requests.post(
                f'{self.refund_api_url}/refunds',
                headers=headers,
                json=payload
            )

            if response.status_code in [200, 201]:
                refund_data = response.json().get('data', {})
                return {
                    'success': True,
                    'refund_id': refund_data.get('id'),
                    'refund_data': refund_data,
                    'error': None,
                }
            return {
                'success': False,
                'refund_id': None,
                'error': f'PayMongo refund API error: {response.status_code}',
                'response': response.text
            }
        except Exception as e:
            return {
                'success': False,
                'refund_id': None,
                'error': f'PayMongo refund error: {str(e)}'
            }
    
    def verify_webhook(self, payload, signature):
        """Verify PayMongo webhook signature"""
        try:
            if not self.webhook_secret or not signature:
                return False

            signature_parts = {}
            for part in signature.split(','):
                key, _, value = part.strip().partition('=')
                if key and value:
                    signature_parts[key] = value

            timestamp = signature_parts.get('t')
            expected_signature = signature_parts.get('te' if self.test_mode else 'li')
            if not timestamp or not expected_signature:
                return False

            signed_payload = timestamp.encode() + b'.' + payload
            computed_signature = hmac.new(
                self.webhook_secret.encode(),
                signed_payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(computed_signature, expected_signature)
        except Exception:
            return False


@login_required
@admin_required
@require_http_methods(["POST"])
def refund_paymongo_payment(request):
    """Refund a completed PayMongo payment from the admin booking detail page."""
    booking_id = request.POST.get('booking_id')
    booking = get_object_or_404(Booking, id=booking_id)
    payment = Payment.objects.filter(
        booking=booking,
        status=PaymentStatus.COMPLETED,
    ).first()

    if not payment:
        messages.error(request, 'No completed payment found for this booking.')
        return redirect('admin_panel:booking_detail', booking_id=booking.id)

    if not payment.transaction_id:
        messages.error(request, 'This payment cannot be refunded because it has no PayMongo payment ID.')
        return redirect('admin_panel:booking_detail', booking_id=booking.id)

    paymongo = PayMongoHandler()
    result = paymongo.create_refund(payment)

    if result['success']:
        payment.status = PaymentStatus.REFUNDED
        payment.notes = 'PayMongo refund processed by admin'
        payment.save()

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = booking.cancellation_reason or 'Refunded by admin'
        booking.save()

        messages.success(request, f'Refund processed for booking #{booking.id}.')
    else:
        error_detail = result.get('response') or result.get('error') or 'Unknown PayMongo refund error'
        messages.error(request, f'Refund failed: {error_detail}')

    return redirect('admin_panel:booking_detail', booking_id=booking.id)


@login_required
@require_http_methods(["GET", "POST"])
def paymongo_payment_view(request, booking_id):
    """PayMongo payment page - GCash, Cards, Maya - ONLY payment method"""
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    
    # Ensure payment record exists
    payment, created = Payment.objects.get_or_create(
        booking=booking,
        payment_method=PaymentMethod.PAYMONGO,
        defaults={
            'amount': booking.total_price,
            'status': PaymentStatus.PENDING
        }
    )
    
    # Initialize PayMongo handler
    paymongo = PayMongoHandler()
    
    if request.method == 'POST':
        # Create checkout session
        return_url = request.build_absolute_uri(
            f'/bookings/paymongo-callback/?booking_id={booking.id}'
        )
        
        result = paymongo.create_checkout_session(booking, return_url)
        
        if result['success']:
            payment.reference_number = result['session_id']
            payment.notes = 'PayMongo checkout session created'
            payment.save()
            # Redirect to PayMongo checkout
            return redirect(result['checkout_url'])
        else:
            messages.error(request, f"Payment processing failed: {result.get('error')}")
            return redirect('bookings:payment_failed', booking_id=booking.id)
    
    context = {
        'booking': booking,
        'payment': payment,
        'paymongo_public_key': paymongo.public_key,
        'test_mode': paymongo.test_mode,
        'payment_methods': ['GCash', 'Cards (Visa/Mastercard)', 'Maya'],
    }
    
    return render(request, 'payments/paymongo_payment.html', context)


@login_required
@require_http_methods(["GET"])
def paymongo_callback(request):
    """Handle PayMongo payment callback"""
    import logging
    logger = logging.getLogger(__name__)
    
    booking_id = request.GET.get('booking_id')
    session_id = request.GET.get('checkout_session_id') or request.GET.get('session_id')
    
    # Log all parameters for debugging
    logger.info(f"PayMongo Callback: booking_id={booking_id}, session_id={session_id}, GET params={request.GET.dict()}")
    
    if not booking_id:
        logger.error("PayMongo callback: missing booking_id")
        messages.error(request, 'Invalid payment callback - missing booking information')
        return redirect('auth:dashboard')
    
    try:
        booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
        payment = get_object_or_404(
            Payment.objects.order_by('-created_at'),
            booking=booking,
            payment_method=PaymentMethod.PAYMONGO,
        )
        
        logger.info(f"PayMongo callback: found booking {booking_id}, payment status={payment.status}")
        
        if not session_id:
            session_id = payment.reference_number or payment.transaction_id
            logger.info(f"No session_id in GET; falling back to stored session token {session_id}")
        
        # Check payment status - webhook should have updated this
        if payment.status == PaymentStatus.COMPLETED:
            logger.info(f"Payment {payment.id} already marked COMPLETED by webhook")
            confirm_booking_after_completed_payment(payment)
            
            messages.success(request, 'Payment successful! Your booking is confirmed.')
            return redirect('bookings:payment_success', booking_id=booking.id)
        
        # If we have session_id, try to verify with PayMongo
        elif session_id:
            logger.info(f"Attempting to verify session {session_id} with PayMongo")
            paymongo = PayMongoHandler()
            session_data = paymongo.retrieve_session(session_id)
            
            if session_data:
                attributes = session_data.get('attributes', {})
                status = attributes.get('status')
                logger.info(f"Session {session_id} status from PayMongo: {status}")
                
                logger.info(f"PayMongo session payload: {session_data}")
                if status in ['success', 'paid', 'completed', 'succeeded']:
                    payment_data = attributes.get('payments', [{}])[0]
                    _complete_paymongo_payment(
                        payment,
                        transaction_id=payment_data.get('id', session_id),
                        reference_number=session_id,
                        notes=f'PayMongo {payment_data.get("type", "card")} payment',
                    )
                    logger.info(f"Payment {payment.id} marked COMPLETED after PayMongo verification")
                    
                    messages.success(request, 'Payment successful! Your booking is confirmed.')
                    return redirect('bookings:payment_success', booking_id=booking.id)
                
                elif status in ['failed', 'cancelled', 'declined']:
                    payment.status = PaymentStatus.FAILED
                    payment.notes = 'PayMongo payment failed'
                    payment.save()
                    logger.warning(f"Payment {payment.id} marked FAILED")
                    
                    messages.error(request, 'Payment failed. Please try again.')
                    return redirect('bookings:payment_failed', booking_id=booking.id)
        
        # If payment is pending, show pending status
        if payment.status == PaymentStatus.PENDING:
            logger.info(f"Payment {payment.id} still PENDING, check back later")
            return redirect('bookings:payment_pending', booking_id=booking.id)
        
        # Default: payment still pending
        logger.warning(f"PayMongo callback: unclear payment status for {payment.id}")
        messages.info(request, 'Payment is being processed. Please check your bookings.')
        return redirect('bookings:booking_detail', booking_id=booking.id)
    
    except Exception as e:
        messages.error(request, f'Payment processing error: {str(e)}')
        return redirect('auth:dashboard')


@csrf_exempt
@require_http_methods(["POST"])
def paymongo_webhook(request):
    """Handle PayMongo webhook events"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        signature = (
            request.headers.get('Paymongo-Signature')
            or request.headers.get('X-Paymongo-Signature')
            or ''
        )
        payload = request.body

        paymongo = PayMongoHandler()

        if not paymongo.verify_webhook(payload, signature):
            logger.warning('Invalid PayMongo webhook signature')
            return JsonResponse({'error': 'Invalid signature'}, status=401)

        data = json.loads(payload)
        data_node = data.get('data', {})
        event_attributes = data_node.get('attributes', {})
        event_type = event_attributes.get('type') or data_node.get('type')
        event_data = event_attributes.get('data') or event_attributes

        logger.info(f'PayMongo webhook received: {event_type}')

        if event_type == 'checkout_session.payment.paid':
            payment, payment_id, checkout_id = _find_payment_from_paymongo_payload(event_data)

            if not payment:
                logger.warning(
                    f'PayMongo webhook could not find payment for checkout_id={checkout_id}, payment_id={payment_id}'
                )
            else:
                _complete_paymongo_payment(
                    payment,
                    transaction_id=payment_id,
                    reference_number=checkout_id or payment.reference_number,
                    notes='PayMongo checkout session payment paid webhook',
                )
                logger.info(f'Payment {payment.id} completed from checkout_session.payment.paid')

        elif event_type == 'charge.updated':
            charge_id = event_data.get('id') or data_node.get('id')
            status = event_data.get('status')
            logger.info(f'PayMongo charge.updated: id={charge_id}, status={status}')

            payment = Payment.objects.filter(
                models.Q(transaction_id=charge_id) | models.Q(reference_number=charge_id)
            ).first()

            if not payment:
                payment, _, _ = _find_payment_from_paymongo_payload(event_data)

            if not payment:
                logger.warning(f'PayMongo webhook could not find payment for charge_id={charge_id}')
            else:
                if status in ['paid', 'succeeded']:
                    _complete_paymongo_payment(
                        payment,
                        transaction_id=charge_id,
                        reference_number=payment.reference_number,
                        notes='PayMongo charge paid webhook',
                    )

                elif status == 'failed':
                    payment.status = PaymentStatus.FAILED
                    payment.save()

        return JsonResponse({'success': True})

    except Exception as e:
        logger.error(f'Webhook error: {str(e)}', exc_info=True)
        return JsonResponse({'error': str(e)}, status=400)
