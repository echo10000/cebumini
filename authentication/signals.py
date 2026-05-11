"""
Signal handlers for OAuth and authentication events
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib import messages as message_api
from django.contrib.messages import get_messages
from django.db.models.signals import pre_save, post_save, post_delete
from allauth.socialaccount.signals import social_account_updated, pre_social_login
from allauth.account.signals import user_signed_up

from .middleware import get_current_request
from .models import (
    AuditLog,
    Booking,
    BookingStatus,
    CustomUser,
    Payment,
    PaymentStatus,
    RefundRequest,
    RefundRequestStatus,
    Room,
    Testimonial,
    TwoFactorAuth,
)
from .utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

try:
    from allauth.account.signals import password_changed
except ImportError:  # pragma: no cover - depends on installed allauth version
    password_changed = None

User = get_user_model()


def _request_actor(default=None):
    request = get_current_request()
    if request and getattr(request, 'user', None) and request.user.is_authenticated:
        return request.user
    return default


def _request_metadata():
    request = get_current_request()
    if not request:
        return None, ''
    return get_client_ip(request), get_user_agent(request)


def _log(actor, action, model_name, object_id=None, affected_user=None, description='', changes=None):
    ip_address, user_agent = _request_metadata()
    try:
        return AuditLog.log_action(
            actor=actor,
            action=action,
            affected_entity_type=model_name,
            affected_entity_id=object_id,
            affected_user=affected_user,
            description=description,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception:
        return None


def _send_login_notification(request, user):
    if not getattr(settings, 'SEND_LOGIN_NOTIFICATION_EMAILS', True) or not user.email:
        return

    ip_address, user_agent = _request_metadata()
    subject = 'New sign-in to your Cebu Luxury account'
    message = (
        f"Hello {user.get_full_name() or user.email},\n\n"
        "Your Cebu Luxury account was just signed in successfully.\n\n"
        f"Email: {user.email}\n"
        f"IP address: {ip_address or 'Unknown'}\n"
        f"Browser: {user_agent or 'Unknown'}\n\n"
        "If this was you, no action is needed. If you did not sign in, please contact the hotel administrator.\n\n"
        "- Cebu Luxury Hotel"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.warning('Could not send login notification email to %s: %s', user.email, exc)
        if request:
            message_api.warning(
                request,
                'Signed in successfully, but the login notification email could not be sent. Please check SMTP settings.',
            )


@receiver(user_logged_in)
def clear_allauth_messages(request, user, **kwargs):
    """
    Clear allauth's built-in success messages after login.
    We don't want to show "Successfully signed in as <user>" messages.
    """
    try:
        storage = get_messages(request)
        preserved_messages = []
        for message in storage:
            text = str(message)
            if text.startswith('Successfully signed in as ') or text.startswith('Successfully signed up as '):
                continue
            preserved_messages.append(message)

        if hasattr(storage, 'used'):
            storage.used = True

        for message in preserved_messages:
            message_api.add_message(
                request,
                message.level,
                message.message,
                extra_tags=message.extra_tags,
            )
    except Exception:
        pass

    _log(
        user,
        'LOGIN_SUCCESSFUL',
        'CustomUser',
        user.id,
        affected_user=user,
        description=f'{user.email or user.username} logged in successfully',
    )
    _send_login_notification(request, user)


@receiver(user_login_failed)
def audit_user_login_failed(sender, credentials, request, **kwargs):
    login_value = credentials.get('username') or credentials.get('email') or credentials.get('login') or ''
    ip_address = get_client_ip(request) if request else None
    user_agent = get_user_agent(request) if request else ''
    AuditLog.log_action(
        actor=None,
        action='LOGIN_FAILED',
        affected_entity_type='CustomUser',
        description=f'Failed login attempt for {login_value}',
        changes={'login': login_value},
        ip_address=ip_address,
        user_agent=user_agent,
    )


@receiver(user_logged_out)
def audit_user_logged_out(sender, request, user, **kwargs):
    if user:
        _log(
            user,
            'LOGOUT',
            'CustomUser',
            user.id,
            affected_user=user,
            description=f'{user.email or user.username} logged out',
        )


if password_changed:
    @receiver(password_changed)
    def audit_password_changed(request, user, **kwargs):
        _log(
            user,
            'PASSWORD_CHANGED',
            'CustomUser',
            user.id,
            affected_user=user,
            description=f'{user.email or user.username} changed their password',
        )


@receiver(user_signed_up)
def handle_user_signed_up(request, user, sociallogin=None, **kwargs):
    """
    Handle user sign-up event (both traditional and social auth).
    Ensure new users get the GUEST role.
    """
    if sociallogin:
        # OAuth user
        user.role = 'GUEST'
        user.is_email_verified = sociallogin.account.extra_data.get('email_verified', True) is not False
        user.save()
        if request:
            message_api.success(request, 'Registration successful! Your Google account is now ready to use.')


@receiver(pre_social_login)
def handle_pre_social_login(request, sociallogin, **kwargs):
    """
    Handle pre-social login event.
    This is called before the social auth login is processed.
    """
    # Get the email from the social account
    email = sociallogin.account.extra_data.get('email')
    email_verified = sociallogin.account.extra_data.get('email_verified', True)
    
    if email and email_verified is not False and not sociallogin.is_existing:
        try:
            user = User.objects.get(email=email)
            # If user exists, connect the social account
            if not user.is_admin() and not user.is_manager() and not user.is_staff_member():
                sociallogin.connect(request, user)
        except (User.DoesNotExist, Exception):
            # New user will be created by allauth
            pass


@receiver(social_account_updated)
def handle_social_account_updated(request, sociallogin, **kwargs):
    """
    Handle social account updates.
    Keep user profile in sync with social provider.
    """
    user = sociallogin.user
    
    # Update user info from social provider
    extra_data = sociallogin.account.extra_data
    
    # Update first and last name if available
    if 'given_name' in extra_data and extra_data['given_name']:
        user.first_name = extra_data['given_name']
    
    if 'family_name' in extra_data and extra_data['family_name']:
        user.last_name = extra_data['family_name']
    
    # Ensure GUEST role for OAuth users
    if not user.role:
        user.role = 'GUEST'
    
    user.save()


@receiver(pre_save)
def cache_previous_audit_state(sender, instance, **kwargs):
    tracked_models = (Booking, Payment, RefundRequest, Room, CustomUser, TwoFactorAuth, Testimonial)
    if sender not in tracked_models or not getattr(instance, 'pk', None):
        return

    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if isinstance(instance, Booking):
        instance._audit_previous_status = previous.status
    elif isinstance(instance, Payment):
        instance._audit_previous_status = previous.status
    elif isinstance(instance, RefundRequest):
        instance._audit_previous_status = previous.status
    elif isinstance(instance, Room):
        instance._audit_previous_values = {
            'room_number': previous.room_number,
            'room_type': previous.room_type,
            'price_per_night': str(previous.price_per_night),
            'status': previous.status,
            'is_available': previous.is_available,
        }
    elif isinstance(instance, CustomUser):
        instance._audit_previous_values = {
            'email': previous.email,
            'role': previous.role,
            'is_active': previous.is_active,
            'first_name': previous.first_name,
            'last_name': previous.last_name,
        }
    elif isinstance(instance, TwoFactorAuth):
        instance._audit_previous_enabled = previous.is_enabled
    elif isinstance(instance, Testimonial):
        instance._audit_previous_values = {
            'status': getattr(previous, 'status', None),
            'is_approved': getattr(previous, 'is_approved', None),
        }


@receiver(post_save, sender=Booking)
def audit_booking_saved(sender, instance, created, **kwargs):
    actor = _request_actor(instance.guest)
    if created:
        _log(
            actor,
            'BOOKING_CREATED',
            'Booking',
            instance.id,
            affected_user=instance.guest,
            description=f'Booking #{instance.id} created',
            changes={'status': instance.status},
        )
        return

    previous_status = getattr(instance, '_audit_previous_status', None)
    if previous_status == instance.status:
        return

    action_map = {
        BookingStatus.CONFIRMED: 'BOOKING_CONFIRMED',
        BookingStatus.CANCELLED: 'BOOKING_CANCELLED',
        BookingStatus.CHECKED_IN: 'BOOKING_CHECKED_IN',
        BookingStatus.CHECKED_OUT: 'BOOKING_CHECKED_OUT',
    }
    action = action_map.get(instance.status)
    if action:
        _log(
            actor,
            action,
            'Booking',
            instance.id,
            affected_user=instance.guest,
            description=f'Booking #{instance.id} changed from {previous_status} to {instance.status}',
            changes={'status': {'old': previous_status, 'new': instance.status}},
        )


@receiver(post_save, sender=Payment)
def audit_payment_saved(sender, instance, created, **kwargs):
    previous_status = getattr(instance, '_audit_previous_status', None)
    if created or previous_status == instance.status:
        return

    action = None
    if instance.status == PaymentStatus.COMPLETED:
        action = 'PAYMENT_COMPLETED'
    elif instance.status == PaymentStatus.FAILED:
        action = 'PAYMENT_REJECTED'

    if action:
        booking = instance.booking
        _log(
            _request_actor(getattr(booking, 'guest', None)),
            action,
            'Payment',
            instance.id,
            affected_user=getattr(booking, 'guest', None),
            description=f'Payment #{instance.id} changed from {previous_status} to {instance.status}',
            changes={'status': {'old': previous_status, 'new': instance.status}},
        )


@receiver(post_save, sender=RefundRequest)
def audit_refund_request_saved(sender, instance, created, **kwargs):
    actor = _request_actor(instance.requested_by)
    if created:
        _log(
            actor,
            'REFUND_REQUESTED',
            'RefundRequest',
            instance.id,
            affected_user=instance.requested_by,
            description=f'Refund request #{instance.id} created',
            changes={'status': instance.status},
        )
        return

    previous_status = getattr(instance, '_audit_previous_status', None)
    if previous_status == instance.status:
        return

    action_map = {
        RefundRequestStatus.APPROVED: 'REFUND_APPROVED',
        RefundRequestStatus.REJECTED: 'REFUND_REJECTED',
        RefundRequestStatus.ISSUED: 'REFUND_ISSUED',
    }
    action = action_map.get(instance.status)
    if action:
        _log(
            actor,
            action,
            'RefundRequest',
            instance.id,
            affected_user=instance.requested_by,
            description=f'Refund request #{instance.id} changed from {previous_status} to {instance.status}',
            changes={'status': {'old': previous_status, 'new': instance.status}},
        )


@receiver(post_save, sender=Room)
def audit_room_saved(sender, instance, created, **kwargs):
    actor = _request_actor()
    if created:
        _log(actor, 'ROOM_CREATED', 'Room', instance.id, description=f'Room {instance.room_number} created')
        return

    previous = getattr(instance, '_audit_previous_values', {})
    current = {
        'room_number': instance.room_number,
        'room_type': instance.room_type,
        'price_per_night': str(instance.price_per_night),
        'status': instance.status,
        'is_available': instance.is_available,
    }
    changes = {
        field: {'old': previous.get(field), 'new': value}
        for field, value in current.items()
        if previous.get(field) != value
    }
    if changes:
        _log(actor, 'ROOM_UPDATED', 'Room', instance.id, description=f'Room {instance.room_number} updated', changes=changes)


@receiver(post_delete, sender=Room)
def audit_room_deleted(sender, instance, **kwargs):
    _log(_request_actor(), 'ROOM_DELETED', 'Room', instance.id, description=f'Room {instance.room_number} deleted')


@receiver(post_save, sender=CustomUser)
def audit_user_saved(sender, instance, created, **kwargs):
    actor = _request_actor(instance)
    if created:
        _log(actor, 'USER_CREATED', 'CustomUser', instance.id, affected_user=instance, description=f'User {instance.email} created')
        return

    previous = getattr(instance, '_audit_previous_values', {})
    if previous.get('is_active') is True and instance.is_active is False:
        action = 'USER_DEACTIVATED'
    else:
        action = 'USER_UPDATED'

    current = {
        'email': instance.email,
        'role': instance.role,
        'is_active': instance.is_active,
        'first_name': instance.first_name,
        'last_name': instance.last_name,
    }
    changes = {
        field: {'old': previous.get(field), 'new': value}
        for field, value in current.items()
        if previous.get(field) != value
    }
    if changes:
        _log(actor, action, 'CustomUser', instance.id, affected_user=instance, description=f'User {instance.email} updated', changes=changes)


@receiver(post_save, sender=TwoFactorAuth)
def audit_two_factor_saved(sender, instance, created, **kwargs):
    previous_enabled = getattr(instance, '_audit_previous_enabled', None)
    if created and not instance.is_enabled:
        return
    if previous_enabled == instance.is_enabled:
        return

    action = 'TWO_FACTOR_ENABLED' if instance.is_enabled else 'TWO_FACTOR_DISABLED'
    _log(
        _request_actor(instance.user),
        action,
        'TwoFactorAuth',
        instance.id,
        affected_user=instance.user,
        description=f'2FA {"enabled" if instance.is_enabled else "disabled"} for {instance.user.email}',
        changes={'is_enabled': {'old': previous_enabled, 'new': instance.is_enabled}},
    )


@receiver(post_save, sender=Testimonial)
def audit_testimonial_saved(sender, instance, created, **kwargs):
    if created:
        return

    previous = getattr(instance, '_audit_previous_values', {})
    old_status = previous.get('status')
    new_status = getattr(instance, 'status', None)
    if old_status != new_status and new_status in {'approved', 'rejected', 'APPROVED', 'REJECTED'}:
        action = 'TESTIMONIAL_APPROVED' if str(new_status).lower() == 'approved' else 'TESTIMONIAL_REJECTED'
    elif previous.get('is_approved') is False and getattr(instance, 'is_approved', False):
        action = 'TESTIMONIAL_APPROVED'
    else:
        return

    guest = getattr(instance, 'guest', None)
    _log(
        _request_actor(getattr(instance, 'reviewed_by', None)),
        action,
        'Testimonial',
        instance.id,
        affected_user=guest,
        description=f'Testimonial #{instance.id} reviewed',
        changes={'status': {'old': old_status, 'new': new_status}},
    )
