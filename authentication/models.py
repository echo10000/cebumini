from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import secrets
import string

class UserRole(models.TextChoices):
    GUEST = 'GUEST', 'Guest'
    STAFF = 'STAFF', 'Staff'
    MANAGER = 'MANAGER', 'Manager'
    ADMIN = 'ADMIN', 'Administrator'

class TermsAndConditions(models.Model):
    """Store Terms and Conditions versions"""
    version = models.CharField(max_length=20, default='1.0')
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'terms_and_conditions'
        verbose_name = 'Terms and Conditions'
        verbose_name_plural = 'Terms and Conditions'
        ordering = ['-created_at']

    def __str__(self):
        return f"T&C v{self.version}"


class CustomUser(AbstractUser):
    """Custom User Model with Role Support"""
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.GUEST
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    terms_accepted = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    terms_version = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_admin(self):
        """Check if user is admin"""
        return self.role == UserRole.ADMIN

    def is_manager(self):
        """Check if user is manager"""
        return self.role == UserRole.MANAGER

    def is_guest(self):
        """Check if user is guest"""
        return self.role == UserRole.GUEST

    def is_staff_member(self):
        """Check if user is staff"""
        return self.role == UserRole.STAFF

    def has_accepted_terms(self):
        """Check if user has accepted terms"""
        return self.terms_accepted

    def accept_terms(self, version='1.0'):
        """Record terms acceptance"""
        self.terms_accepted = True
        self.terms_accepted_at = timezone.now()
        self.terms_version = version
        self.save()


class RoomType(models.TextChoices):
    """Room type choices"""
    STANDARD = 'STANDARD', 'Standard Room'
    DELUXE = 'DELUXE', 'Deluxe Room'
    SUITE = 'SUITE', 'Suite Room'


class Room(models.Model):
    """Room Model"""
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(
        max_length=20,
        choices=RoomType.choices,
        default=RoomType.STANDARD
    )
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    capacity = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1)]
    )
    is_available = models.BooleanField(default=True)
    amenities = models.TextField(
        blank=True,
        help_text="Comma-separated list of amenities"
    )
    image = models.ImageField(
        upload_to='rooms/%Y/%m/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rooms'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        ordering = ['room_number']

    def __str__(self):
        return f"Room {self.room_number} ({self.get_room_type_display()})"

    def get_amenities_list(self):
        """Return amenities as list"""
        if self.amenities:
            return [a.strip() for a in self.amenities.split(',')]
        return []

    def get_status(self):
        """Get room status"""
        return "Available" if self.is_available else "Occupied"


class RoomImage(models.Model):
    """Additional room images"""
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='rooms/%Y/%m/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'room_images'
        verbose_name = 'Room Image'
        verbose_name_plural = 'Room Images'
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Image of {self.room.room_number}"


class BookingStatus(models.TextChoices):
    """Booking status choices"""
    PENDING = 'PENDING', 'Pending Confirmation'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    CHECKED_IN = 'CHECKED_IN', 'Checked In'
    CHECKED_OUT = 'CHECKED_OUT', 'Checked Out'
    CANCELLED = 'CANCELLED', 'Cancelled'


class CancellationPolicy(models.TextChoices):
    """Cancellation policies"""
    FREE = 'FREE', 'Free (100% refund)'
    STANDARD = 'STANDARD', 'Standard (50% refund)'
    NON_REFUNDABLE = 'NON_REFUNDABLE', 'Non-Refundable (0% refund)'


class Booking(models.Model):
    """Booking Model"""
    REFERENCE_PREFIX = 'CEBU'
    REFERENCE_ALPHABET = string.ascii_uppercase + string.digits

    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    guest = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    check_in = models.DateField()
    check_out = models.DateField()
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    cancellation_policy = models.CharField(
        max_length=20,
        choices=CancellationPolicy.choices,
        default=CancellationPolicy.FREE,
        help_text="Policy for this booking"
    )
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason provided for cancellation"
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When booking was cancelled"
    )
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    booking_reference = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
        help_text="Random guest-facing reference code used during check-in verification"
    )
    reference_verified = models.BooleanField(default=False)
    id_verified = models.BooleanField(default=False)
    contact_verified = models.BooleanField(default=False)
    payment_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_bookings',
        help_text="Staff member who completed check-in verification"
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    special_requests = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room', 'check_in', 'check_out']),
            models.Index(fields=['guest', 'status']),
        ]

    def __str__(self):
        return f"Booking {self.id} - Room {self.room.room_number} ({self.check_in} to {self.check_out})"

    @classmethod
    def generate_booking_reference(cls):
        """Generate a random, guest-facing booking reference."""
        return f"{cls.REFERENCE_PREFIX}-{''.join(secrets.choice(cls.REFERENCE_ALPHABET) for _ in range(6))}"

    @classmethod
    def create_unique_booking_reference(cls):
        """Generate a booking reference that is not already in use."""
        reference = cls.generate_booking_reference()
        while cls.objects.filter(booking_reference=reference).exists():
            reference = cls.generate_booking_reference()
        return reference

    def get_duration(self):
        """Calculate booking duration in days"""
        return (self.check_out - self.check_in).days

    @property
    def number_of_nights(self):
        """Property to get number of nights (alias for get_duration)"""
        return self.get_duration()

    def calculate_total_price(self):
        """Calculate total price based on duration and room price"""
        duration = self.get_duration()
        return duration * self.room.price_per_night

    def is_active(self):
        """Check if booking is currently active"""
        today = timezone.now().date()
        return self.check_in <= today <= self.check_out and self.status == BookingStatus.CONFIRMED

    def can_be_cancelled(self):
        """Check if booking can be cancelled"""
        today = timezone.now().date()
        return self.status != BookingStatus.CANCELLED and self.check_in > today

    def complete_check_in_verification(self, staff_user, submitted_reference, checklist, notes=''):
        """
        Validate front-desk proof and check the guest in.
        Returns a list of error messages; an empty list means success.
        """
        errors = []
        submitted_reference = (submitted_reference or '').strip().upper()

        if self.status != BookingStatus.CONFIRMED:
            errors.append('Only confirmed bookings can be checked in.')

        if submitted_reference != (self.booking_reference or '').upper():
            errors.append('Booking reference does not match this reservation.')

        required_checks = {
            'reference_verified': 'booking confirmation/reference',
            'id_verified': 'valid ID matching the guest name',
            'contact_verified': 'email or phone number matching the account',
            'payment_verified': 'payment status or collection requirement',
        }
        for field, label in required_checks.items():
            if not checklist.get(field):
                errors.append(f'Please verify the {label}.')

        if errors:
            return errors

        self.reference_verified = True
        self.id_verified = True
        self.contact_verified = True
        self.payment_verified = True
        self.verified_by = staff_user
        self.verified_at = timezone.now()
        self.verification_notes = notes or ''
        self.status = BookingStatus.CHECKED_IN
        self.save()
        return []

    def get_refund_amount(self):
        """
        Calculate refund amount based on cancellation policy and timing.
        Returns tuple: (refund_amount, refund_percentage, policy_details)
        """
        today = timezone.now().date()
        days_until_checkin = (self.check_in - today).days
        
        if self.cancellation_policy == CancellationPolicy.NON_REFUNDABLE:
            return (0, 0, 'Non-refundable booking - no refund available')
        
        elif self.cancellation_policy == CancellationPolicy.STANDARD:
            # 50% refund if 3+ days before check-in, 0% otherwise
            if days_until_checkin >= 3:
                refund_amount = self.total_price * Decimal('0.50')
                return (refund_amount, 50, f'50% refund (cancelled {days_until_checkin} days before check-in)')
            else:
                return (Decimal('0'), 0, f'Late cancellation - no refund ({days_until_checkin} days before check-in)')
        
        else:  # FREE policy
            # 100% refund if 7+ days before check-in, 50% if 3-7 days, 0% if less than 3 days
            if days_until_checkin >= 7:
                refund_amount = self.total_price
                return (refund_amount, 100, f'100% refund (cancelled {days_until_checkin} days before check-in)')
            elif days_until_checkin >= 3:
                refund_amount = self.total_price * Decimal('0.50')
                return (refund_amount, 50, f'50% refund (cancelled {days_until_checkin} days before check-in)')
            else:
                return (Decimal('0'), 0, f'Late cancellation - no refund ({days_until_checkin} days before check-in)')

    def save(self, *args, **kwargs):
        """Override save to calculate total price and assign a reference code."""
        if not self.total_price or self.total_price == 0:
            self.total_price = self.calculate_total_price()
        if not self.booking_reference:
            self.booking_reference = self.create_unique_booking_reference()
        super().save(*args, **kwargs)

    def send_confirmation_email(self):
        """Send booking confirmation email to the guest."""
        import logging
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string

        logger = logging.getLogger(__name__)
        subject = f'Booking Confirmation #{self.id} - {self.room.room_number}'
        host = settings.ALLOWED_HOSTS[0] if getattr(settings, 'ALLOWED_HOSTS', None) else 'localhost:8000'
        context = {
            'booking': self,
            'guest': self.guest,
            'room': self.room,
            'booking_url': f'https://{host}/bookings/{self.id}/',
        }

        text_content = render_to_string('account/email/booking_confirmation_email.txt', context)
        html_content = render_to_string('account/email/booking_confirmation_email.html', context)

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Cebu Hotel <support@cebuhotel.com>')
        recipient_list = [self.guest.email]

        try:
            email = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            email.attach_alternative(html_content, 'text/html')
            email.send(fail_silently=False)
            logger.info(f"Booking confirmation sent for booking {self.id} to {self.guest.email}")
            return True
        except Exception as e:
            logger.error(f"Error sending booking confirmation email for booking {self.id}: {e}")
            return False

    @staticmethod
    def check_availability(room_id, check_in, check_out, exclude_booking_id=None):
        """
        Check if room is available for given dates
        Returns True if available, False if overlapping booking exists
        """
        from django.db.models import Q
        
        # Exclude cancelled bookings
        query = Booking.objects.filter(
            room_id=room_id,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
        )
        
        # Exclude current booking if editing
        if exclude_booking_id:
            query = query.exclude(id=exclude_booking_id)
        
        # Check for overlapping bookings
        overlapping = query.filter(
            Q(check_in__lt=check_out) & Q(check_out__gt=check_in)
        ).exists()
        
        return not overlapping


class PaymentMethod(models.TextChoices):
    """Payment method choices"""
    CASH = 'CASH', 'Cash'
    STRIPE = 'STRIPE', 'Stripe'
    PAYMONGO = 'PAYMONGO', 'PayMongo (GCash/Cards)'
    MAYA = 'MAYA', 'Maya'
    GCASH = 'GCASH', 'GCash'
    BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'


class PaymentStatus(models.TextChoices):
    """Payment status choices"""
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'
    REFUND_PENDING = 'REFUND_PENDING', 'Refund Pending'
    REFUNDED = 'REFUNDED', 'Refunded'
    PARTIALLY_REFUNDED = 'PARTIALLY_REFUNDED', 'Partially Refunded'


class Payment(models.Model):
    """Payment Model for booking transactions"""
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.STRIPE
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Stripe/GCash transaction ID"
    )
    reference_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Reference number for manual transfers"
    )
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Amount refunded (if any)"
    )
    refund_transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Refund transaction ID from payment provider"
    )
    refund_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Why the refund was issued"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', 'status']),
            models.Index(fields=['transaction_id']),
        ]

    def __str__(self):
        return f"Payment for Booking #{self.booking.id} - ₱{self.amount} ({self.get_status_display()})"

    def is_paid(self):
        """Check if payment is completed"""
        return self.status == PaymentStatus.COMPLETED


class Testimonial(models.Model):
    """Customer Testimonials/Reviews"""
    RATING_CHOICES = [
        (5, '⭐⭐⭐⭐⭐ Excellent'),
        (4, '⭐⭐⭐⭐ Very Good'),
        (3, '⭐⭐⭐ Good'),
        (2, '⭐⭐ Fair'),
        (1, '⭐ Poor'),
    ]
    
    guest = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='testimonials',
        null=True,
        blank=True
    )
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    rating = models.IntegerField(choices=RATING_CHOICES, default=5)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'testimonials'
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.guest_name} - {self.get_rating_display()}"

    def get_rating_stars(self):
        """Return rating as stars"""
        return '⭐' * self.rating


class ContactMessage(models.Model):
    """Contact Form Messages"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    guest = models.ForeignKey('CustomUser', on_delete=models.CASCADE, null=True, blank=True, related_name='contact_messages')
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    staff_response = models.TextField(blank=True, help_text="Staff's response message")
    notification_sent = models.BooleanField(default=False, help_text="Has guest been notified of reply?")
    last_notified_at = models.DateTimeField(null=True, blank=True, help_text="When was guest last notified?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contact_messages'
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    def send_confirmation_email(self):
        """Send confirmation email to guest when message is submitted"""
        from django.core.mail import send_mail
        
        subject = f"We received your message: {self.subject}"
        message = f"""Dear {self.name},

Thank you for contacting Cebu Hotel!

We have received your message regarding "{self.subject}" and our team will review it shortly.

You can expect a response from us within 24 hours.

If you need immediate assistance, please call us at +63 (32) 412-3456.

Best regards,
Cebu Hotel Team
---
Message Reference ID: {self.id}
Date Submitted: {self.created_at.strftime('%B %d, %Y at %I:%M %p')}
"""
        
        try:
            send_mail(
                subject,
                message,
                'support@cebuhotel.com',
                [self.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending email to {self.email}: {str(e)}")
            return False
    
    def send_reply_notification(self):
        """Send email to guest when staff marks message as replied"""
        from django.core.mail import send_mail
        from django.utils import timezone
        
        if self.is_replied and not self.notification_sent:
            subject = f"Response to your message: {self.subject}"
            message = f"""Dear {self.name},

Thank you for your inquiry regarding "{self.subject}".

Our team has reviewed your message and will be in touch with you shortly.

"""
            
            if self.staff_response:
                message += f"Here's a response from our team:\n\n{self.staff_response}\n\n"
            
            message += """If you have any additional questions or concerns, please don't hesitate to contact us.

You can reach us by:
- Phone: +63 (32) 412-3456 (Mon-Fri 9AM-6PM, Sat-Sun 10AM-5PM)
- Email: support@cebuhotel.com
- Live Chat: Available on our website

Best regards,
Cebu Hotel Team
---
Message Reference ID: {self.id}
"""
            
            try:
                send_mail(
                    subject,
                    message,
                    'support@cebuhotel.com',
                    [self.email],
                    fail_silently=False,
                )
                self.notification_sent = True
                self.last_notified_at = timezone.now()
                self.save()
                return True
            except Exception as e:
                print(f"Error sending notification to {self.email}: {str(e)}")
                return False
        
        return False


class MessageReply(models.Model):
    """Replies to Contact Messages"""
    class SenderType(models.TextChoices):
        GUEST = 'guest', 'Guest'
        STAFF = 'staff', 'Staff'
        SYSTEM = 'system', 'System'

    contact_message = models.ForeignKey(
        ContactMessage,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    staff_member = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_replies'
    )
    sender_type = models.CharField(
        max_length=10,
        choices=SenderType.choices,
        default=SenderType.STAFF,
        db_index=True,
    )
    reply_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'message_replies'
        verbose_name = 'Message Reply'
        verbose_name_plural = 'Message Replies'
        ordering = ['created_at']

    def __str__(self):
        return f"Reply to {self.contact_message.name} on {self.created_at.date()}"


class TwoFactorAuth(models.Model):
    """Two Factor Authentication Settings"""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='two_factor_auth'
    )
    is_enabled = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    method = models.CharField(
        max_length=20,
        choices=[
            ('TOTP', 'Time-based One-Time Password (Authenticator App)'),
            ('SMS', 'SMS Code'),
            ('EMAIL', 'Email Code'),
        ],
        default='TOTP'
    )
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_verified = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'two_factor_auth'
        verbose_name = '2FA Setting'
        verbose_name_plural = '2FA Settings'

    def __str__(self):
        return f"2FA for {self.user.email} - {'Enabled' if self.is_enabled else 'Disabled'}"

    def generate_backup_codes(self, count=10):
        """Generate backup codes for 2FA"""
        import secrets
        codes = [secrets.token_hex(4) for _ in range(count)]
        self.backup_codes = codes
        self.save()
        return codes

    def use_backup_code(self, code):
        """Use and remove a backup code"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save()
            return True
        return False


class EmailOTP(models.Model):
    """One-time passcodes sent by email."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='email_otps'
    )
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'email_otps'
        verbose_name = 'Email OTP'
        verbose_name_plural = 'Email OTPs'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.email} ({self.otp_code})"

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()


class LoginSession(models.Model):
    """Track login sessions for security"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='login_sessions'
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_2fa_verified = models.BooleanField(default=False)
    is_oauth = models.BooleanField(default=False)
    oauth_provider = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'login_sessions'
        verbose_name = 'Login Session'
        verbose_name_plural = 'Login Sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
class RefundRequestStatus(models.TextChoices):
    """Refund request workflow statuses"""
    REQUESTED = 'REQUESTED', 'Requested by Staff'
    APPROVED = 'APPROVED', 'Approved by Manager'
    REJECTED = 'REJECTED', 'Rejected by Manager'
    ISSUED = 'ISSUED', 'Refund Issued by Admin'


class RefundRequest(models.Model):
    """Refund Request - workflow: Staff request → Manager approve → Admin issue"""
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='refund_request'
    )
    requested_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='refund_requests_created',
        limit_choices_to={'role__in': ['STAFF', 'GUEST']},
        help_text="Staff or Guest who requested the refund"
    )
    status = models.CharField(
        max_length=20,
        choices=RefundRequestStatus.choices,
        default=RefundRequestStatus.REQUESTED,
        help_text="Current status of refund request"
    )
    reason = models.TextField(
        help_text="Reason for refund request"
    )
    requested_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Amount initially requested for refund"
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund_requests_approved',
        limit_choices_to={'role': 'MANAGER'},
        help_text="Manager who approved/rejected the request"
    )
    approved_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Amount approved by manager"
    )
    manager_notes = models.TextField(
        blank=True,
        help_text="Manager's notes on approval/rejection"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When manager approved/rejected"
    )
    issued_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund_requests_issued',
        limit_choices_to={'role': 'ADMIN'},
        help_text="Admin who issued the refund"
    )
    issued_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When admin issued the refund"
    )
    refund_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Transaction ID from payment provider for the refund"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'refund_requests'
        verbose_name = 'Refund Request'
        verbose_name_plural = 'Refund Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Refund Request for Booking #{self.booking.id} - {self.get_status_display()}"

    def can_staff_request(self):
        """Check if this refund can still be requested by staff"""
        return self.status == RefundRequestStatus.REQUESTED and not self.approved_by

    def can_manager_approve(self):
        """Check if manager can approve/reject this request"""
        return self.status == RefundRequestStatus.REQUESTED and not self.approved_by

    def can_admin_issue(self):
        """Check if admin can issue this refund"""
        return self.status == RefundRequestStatus.APPROVED and not self.issued_by


class RoomStatus(models.TextChoices):
    """Housekeeping room status choices"""
    CLEAN = 'CLEAN', 'Clean'
    DIRTY = 'DIRTY', 'Dirty'
    MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'


class RoomHousekeepingLog(models.Model):
    """Track room status changes for housekeeping management"""
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='housekeeping_logs'
    )
    previous_status = models.CharField(
        max_length=20,
        choices=RoomStatus.choices
    )
    current_status = models.CharField(
        max_length=20,
        choices=RoomStatus.choices
    )
    updated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'STAFF'},
        related_name='room_status_updates'
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about room condition or maintenance needs"
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Related booking if status change is due to booking"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'room_housekeeping_logs'
        verbose_name = 'Room Housekeeping Log'
        verbose_name_plural = 'Room Housekeeping Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
        ]

    def __str__(self):
        return f"{self.room.room_number} - {self.current_status} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class GuestComplaintEscalation(models.Model):
    """Track guest complaint escalations from Staff to Manager"""
    
    COMPLAINT_STATUS = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='complaint_escalations'
    )
    guest = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='complaint_escalations',
        limit_choices_to={'role': 'GUEST'}
    )
    complaint_description = models.TextField(
        help_text="Description of the guest's complaint"
    )
    reported_by_staff = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='escalated_complaints',
        limit_choices_to={'role': 'STAFF'},
        help_text="Staff member who escalated the complaint"
    )
    escalated_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_escalations',
        limit_choices_to={'role': 'MANAGER'},
        help_text="Manager assigned to handle escalation"
    )
    staff_notes = models.TextField(
        blank=True,
        help_text="Staff's notes about the complaint"
    )
    manager_notes = models.TextField(
        blank=True,
        help_text="Manager's resolution notes"
    )
    status = models.CharField(
        max_length=20,
        choices=COMPLAINT_STATUS,
        default='OPEN'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'guest_complaint_escalations'
        verbose_name = 'Guest Complaint Escalation'
        verbose_name_plural = 'Guest Complaint Escalations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['escalated_to', 'status']),
        ]

    def __str__(self):
        return f"Complaint for Booking #{self.booking.id} - {self.get_status_display()}"



class AuditLog(models.Model):
    """Audit Log for tracking all system actions"""
    
    ACTION_CHOICES = [
        ('BOOKING_CREATED', 'Booking Created'),
        ('BOOKING_APPROVED', 'Booking Approved'),
        ('BOOKING_CANCELLED', 'Booking Cancelled'),
        ('PAYMENT_APPROVED', 'Payment Approved'),
        ('PAYMENT_REJECTED', 'Payment Rejected'),
        ('REFUND_REQUESTED', 'Refund Requested'),
        ('REFUND_APPROVED', 'Refund Approved'),
        ('REFUND_ISSUED', 'Refund Issued'),
        ('ROOM_CREATED', 'Room Created'),
        ('ROOM_UPDATED', 'Room Updated'),
        ('ROOM_DELETED', 'Room Deleted'),
        ('PRICING_CHANGED', 'Pricing Changed'),
        ('ROOM_STATUS_CHANGED', 'Room Status Changed'),
        ('STAFF_REGISTERED', 'Staff Member Registered'),
        ('STAFF_DEACTIVATED', 'Staff Member Deactivated'),
        ('USER_ROLE_CHANGED', 'User Role Changed'),
        ('COMPLAINT_ESCALATED', 'Guest Complaint Escalated'),
        ('COMPLAINT_RESOLVED', 'Guest Complaint Resolved'),
        ('GUEST_PROFILE_VIEWED', 'Guest Profile Viewed'),
        ('LOGIN_SUCCESSFUL', 'Login Successful'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('PASSWORD_CHANGED', 'Password Changed'),
    ]
    
    actor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs_created',
        help_text="User who performed the action"
    )
    actor_role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        help_text="Role of the user at time of action"
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    affected_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs_affected',
        help_text="User affected by this action (if any)"
    )
    affected_entity_type = models.CharField(
        max_length=50,
        help_text="Type of entity affected (Booking, Room, Payment, etc.)"
    )
    affected_entity_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of the affected entity"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the action"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the request"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string from request"
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON object tracking what changed (old values, new values)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['affected_entity_type', 'affected_entity_id']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} by {self.actor.email if self.actor else 'Unknown'} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    @staticmethod
    def log_action(actor, action, affected_entity_type, affected_entity_id=None, 
                   affected_user=None, description='', changes=None, ip_address=None, user_agent=None):
        """
        Create an audit log entry.
        
        Args:
            actor: The user performing the action
            action: Action type from ACTION_CHOICES
            affected_entity_type: Type of entity (e.g., 'Booking', 'Room', 'Payment')
            affected_entity_id: ID of the affected entity
            affected_user: User affected by the action (if different from actor)
            description: Additional description
            changes: Dict of changes (old, new values)
            ip_address: IP address of the request
            user_agent: User agent string
        """
        return AuditLog.objects.create(
            actor=actor,
            actor_role=actor.role if actor else UserRole.GUEST,
            action=action,
            affected_user=affected_user,
            affected_entity_type=affected_entity_type,
            affected_entity_id=affected_entity_id,
            description=description,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
