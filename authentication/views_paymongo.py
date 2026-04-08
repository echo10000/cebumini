"""
PayMongo Payment Handler Views
Handles GCash, Cards, and Maya payments through PayMongo
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import json
import hashlib
import hmac
import requests
from decimal import Decimal

from .models import Booking, Payment, PaymentStatus, PaymentMethod, BookingStatus


class PayMongoHandler:
    """PayMongo payment handler"""
    
    def __init__(self):
        self.public_key = settings.PAYMONGO_PUBLIC_KEY
        self.secret_key = settings.PAYMONGO_SECRET_KEY
        self.test_mode = settings.PAYMONGO_TEST_MODE
        self.api_url = 'https://api.paymongo.com/v1'
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
                        'payment_method_types': ['card', 'gcash', 'maya'],
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
                    'error': f'PayMongo API error: {response.status_code}'
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
    
    def verify_webhook(self, payload, signature):
        """Verify PayMongo webhook signature"""
        try:
            computed_signature = hmac.new(
                self.secret_key.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return computed_signature == signature
        except:
            return False


@login_required
@require_http_methods(["GET", "POST"])
def paymongo_payment_view(request, booking_id):
    """PayMongo payment page - GCash, Cards, Maya"""
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    payment = get_object_or_404(Payment, booking=booking)
    
    # Initialize PayMongo handler
    paymongo = PayMongoHandler()
    
    if request.method == 'POST':
        # Create checkout session
        return_url = request.build_absolute_uri(
            f'/bookings/paymongo-callback/?booking_id={booking.id}'
        )
        
        result = paymongo.create_checkout_session(booking, return_url)
        
        if result['success']:
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
    booking_id = request.GET.get('booking_id')
    session_id = request.GET.get('checkout_session_id')
    
    if not booking_id or not session_id:
        messages.error(request, 'Invalid payment callback')
        return redirect('auth:dashboard')
    
    try:
        booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
        payment = get_object_or_404(Payment, booking=booking)
        
        # Verify session with PayMongo
        paymongo = PayMongoHandler()
        session_data = paymongo.retrieve_session(session_id)
        
        if session_data:
            attributes = session_data.get('attributes', {})
            
            # Check if payment was successful
            if attributes.get('status') == 'success':
                # Get payment details
                payment_data = attributes.get('payments', [{}])[0]
                
                # Update payment record
                payment.status = PaymentStatus.COMPLETED
                payment.transaction_id = payment_data.get('id', session_id)
                payment.reference_number = session_id
                payment.payment_method = PaymentMethod.PAYMONGO
                payment.notes = f'PayMongo {payment_data.get("type", "card")} payment - {session_id}'
                payment.completed_at = timezone.now()
                payment.save()
                
                # Confirm booking
                booking.status = BookingStatus.CONFIRMED
                booking.save()
                
                messages.success(request, f'Payment successful! Booking confirmed.')
                return redirect('bookings:payment_success', booking_id=booking.id)
            
            elif attributes.get('status') == 'failed':
                payment.status = PaymentStatus.FAILED
                payment.notes = 'PayMongo payment failed'
                payment.save()
                
                messages.error(request, 'Payment failed. Please try again.')
                return redirect('bookings:payment_failed', booking_id=booking.id)
            
            else:
                # Pending or processing
                messages.info(request, 'Payment is being processed. Please check back soon.')
                return redirect('bookings:payment_pending', booking_id=booking.id)
        
        else:
            messages.error(request, 'Could not verify payment session.')
            return redirect('bookings:payment_failed', booking_id=booking.id)
    
    except Exception as e:
        messages.error(request, f'Payment processing error: {str(e)}')
        return redirect('auth:dashboard')


@require_http_methods(["POST"])
def paymongo_webhook(request):
    """Handle PayMongo webhook events"""
    try:
        signature = request.headers.get('X-Paymongo-Signature', '')
        payload = request.body
        
        paymongo = PayMongoHandler()
        
        # Verify signature
        if not paymongo.verify_webhook(payload, signature):
            return JsonResponse({'error': 'Invalid signature'}, status=401)
        
        data = json.loads(payload)
        event_type = data.get('data', {}).get('type')
        event_data = data.get('data', {}).get('attributes', {})
        
        # Handle charge.updated event (payment completed)
        if event_type == 'charge.updated':
            charge_id = data.get('data', {}).get('id')
            status = event_data.get('status')
            
            # Find payment by transaction ID
            try:
                payment = Payment.objects.get(transaction_id=charge_id)
                
                if status == 'paid':
                    payment.status = PaymentStatus.COMPLETED
                    payment.completed_at = timezone.now()
                    payment.save()
                    
                    # Confirm booking
                    booking = payment.booking
                    booking.status = BookingStatus.CONFIRMED
                    booking.save()
                
                elif status == 'failed':
                    payment.status = PaymentStatus.FAILED
                    payment.save()
            
            except Payment.DoesNotExist:
                pass
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        print(f'Webhook error: {str(e)}')
        return JsonResponse({'error': str(e)}, status=400)
