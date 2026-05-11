import random
import smtplib
import string
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailOTP


class EmailOTPDeliveryError(Exception):
    """Raised when an email OTP cannot be delivered."""

    def __init__(self, message, otp_code=None):
        super().__init__(message)
        self.otp_code = otp_code


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(user):
    """Generate a fresh email OTP and send it to the user's email."""
    # Invalidate previous unused OTPs for this user
    EmailOTP.objects.filter(user=user, is_used=False).update(is_used=True)

    otp = generate_otp()
    expires_at = timezone.now() + timedelta(seconds=getattr(settings, 'OTP_EMAIL_TOKEN_VALIDITY', 300))

    email_otp = EmailOTP.objects.create(
        user=user,
        otp_code=otp,
        expires_at=expires_at,
    )

    subject = getattr(settings, 'OTP_EMAIL_SUBJECT', 'Your Cebu Luxury Verification Code')
    sender = getattr(settings, 'OTP_EMAIL_SENDER', settings.DEFAULT_FROM_EMAIL)

    message = (
        f"Your verification code is: {otp}\n\n"
        "This code expires in 5 minutes.\n\n"
        "If you did not request this, please ignore this email.\n\n"
        "- Cebu Luxury Hotel"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=sender,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except (smtplib.SMTPException, OSError) as exc:
        if getattr(settings, 'DEBUG', False):
            raise EmailOTPDeliveryError(
                'Unable to send the verification code. Please check email settings.',
                otp_code=otp,
            ) from exc

        email_otp.is_used = True
        email_otp.save(update_fields=['is_used'])
        raise EmailOTPDeliveryError('Unable to send the verification code. Please check email settings.') from exc

    return otp


def verify_otp(user, otp_code):
    """Return True if the provided code matches a valid unused OTP."""
    try:
        otp = EmailOTP.objects.filter(
            user=user,
            otp_code=otp_code,
            is_used=False,
        ).latest('created_at')
    except EmailOTP.DoesNotExist:
        return False

    if otp.is_valid():
        otp.is_used = True
        otp.save()
        return True

    return False
