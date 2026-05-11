import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import PaymentStatus

logger = logging.getLogger(__name__)


def _send_booking_email(booking, subject, template_name, context):
    recipient = booking.guest.email
    return _send_guest_email(recipient, subject, template_name, context, booking_id=booking.id)


def _send_guest_email(recipient, subject, template_name, context, booking_id=None):
    if not recipient:
        return False

    try:
        html_body = render_to_string(template_name, context)
        text_body = strip_tags(html_body)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=False)
        return True
    except Exception as exc:
        logger.warning('Guest email failed for booking %s: %s', booking_id or 'N/A', exc, exc_info=True)
        return False


def send_checkin_email(booking):
    guest_name = booking.guest.get_full_name() or booking.guest.username
    return _send_booking_email(
        booking,
        "You're Checked In! - Cebu Mini Hotel",
        'emails/checkin_confirmation.html',
        {
            'booking': booking,
            'guest_name': guest_name,
            'room': booking.room,
            'checked_in_at': booking.checked_in_at or booking.verified_at,
        },
    )


def send_checkout_email(booking):
    guest_name = booking.guest.get_full_name() or booking.guest.username
    payment = (
        booking.payments.filter(status=PaymentStatus.COMPLETED).order_by('-completed_at', '-created_at').first()
        or booking.payments.order_by('-created_at').first()
    )
    return _send_booking_email(
        booking,
        'Thank you for staying - Cebu Mini Hotel',
        'emails/checkout_receipt.html',
        {
            'booking': booking,
            'guest_name': guest_name,
            'room': booking.room,
            'payment': payment,
            'checked_in_at': booking.checked_in_at or booking.verified_at,
            'checked_out_at': booking.checked_out_at,
        },
    )


def send_cancellation_email(booking, payment=None):
    guest_name = booking.guest.get_full_name() or booking.guest.username
    return _send_booking_email(
        booking,
        'Booking Cancellation Confirmed - Cebu Mini Hotel',
        'emails/booking_cancellation.html',
        {
            'booking': booking,
            'guest_name': guest_name,
            'room': booking.room,
            'payment': payment,
        },
    )


def send_complaint_resolved_email(complaint):
    guest_name = complaint.guest.get_full_name() or complaint.guest.username
    return _send_guest_email(
        complaint.guest.email,
        'Your Complaint Has Been Resolved - Cebu Mini Hotel',
        'emails/complaint_resolved.html',
        {
            'complaint': complaint,
            'guest_name': guest_name,
            'booking': complaint.booking,
            'room': complaint.booking.room if complaint.booking else None,
        },
    )


def send_refund_confirmation_email(booking, payment, amount):
    guest_name = booking.guest.get_full_name() or booking.guest.username
    return _send_booking_email(
        booking,
        'Your Refund Has Been Processed - Cebu Mini Hotel',
        'emails/refund_confirmation.html',
        {
            'booking': booking,
            'guest_name': guest_name,
            'payment': payment,
            'amount': amount,
        },
    )
