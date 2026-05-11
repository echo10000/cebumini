"""
Utility functions for authentication, audit logging, and role management
"""

from django.utils import timezone
from django.conf import settings
from .models import ActivityLog, AuditLog
from decimal import Decimal
import secrets


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Extract user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


def log_audit(request, actor, action, affected_entity_type, affected_entity_id=None,
              affected_user=None, description='', changes=None):
    """
    Create an audit log entry for an action.
    
    Args:
        request: HTTP request object (used to get IP and user agent)
        actor: The user performing the action
        action: Action type from AuditLog.ACTION_CHOICES
        affected_entity_type: Type of entity (e.g., 'Booking', 'Room', 'Payment')
        affected_entity_id: ID of the affected entity
        affected_user: User affected by the action (if different from actor)
        description: Additional description of the action
        changes: Dict of changes tracking (old values, new values)
    """
    ip_address = get_client_ip(request) if request else None
    user_agent = get_user_agent(request) if request else None
    
    return AuditLog.log_action(
        actor=actor,
        action=action,
        affected_entity_type=affected_entity_type,
        affected_entity_id=affected_entity_id,
        affected_user=affected_user,
        description=description,
        changes=changes or {},
        ip_address=ip_address,
        user_agent=user_agent
    )


def log_activity(user, action, target, request=None):
    """Create a manager-visible staff activity entry."""
    return ActivityLog.objects.create(
        user=user if getattr(user, 'is_authenticated', False) else None,
        action=action,
        target=target,
        ip_address=get_client_ip(request) if request else None,
    )


def user_requires_2fa(user):
    """Return True when this user's role must have verified 2FA."""
    dev_bypass_users = {'sample_manager', 'sample_admin'}
    if getattr(settings, 'DEBUG', False) and getattr(user, 'username', '') in dev_bypass_users:
        return False

    return (
        getattr(user, 'is_authenticated', False)
        and (user.is_admin() or user.is_manager())
    )


def get_two_fa_status(user):
    """Return the user's 2FA object if enabled and verified, otherwise None."""
    if not user_requires_2fa(user):
        return None

    try:
        two_fa = user.two_factor_auth
    except Exception:
        return None

    if two_fa.is_enabled and two_fa.is_verified:
        return two_fa
    return None


def is_two_fa_configured(user):
    """Check whether a privileged user has completed 2FA setup."""
    return get_two_fa_status(user) is not None


def confirm_booking_after_completed_payment(payment, send_email=True):
    """
    Confirm a booking only after its payment has been marked completed.
    Returns True when the booking moved to confirmed, False when already confirmed.
    """
    from .models import BookingStatus, PaymentStatus

    if payment.status != PaymentStatus.COMPLETED:
        raise ValueError('Payment must be completed before confirming the booking.')

    booking = payment.booking
    if booking.status == BookingStatus.CONFIRMED:
        return False

    booking.status = BookingStatus.CONFIRMED
    booking.save(update_fields=['status', 'updated_at'])

    if send_email:
        booking.send_confirmation_email()

    return True


def generate_refund_transaction_id(refund_request):
    """Create a unique internal reference for an issued refund."""
    from .models import Payment, RefundRequest

    date_part = timezone.now().strftime('%Y%m%d')
    while True:
        token = secrets.token_hex(3).upper()
        transaction_id = f'RFND-{date_part}-{refund_request.id:06d}-{token}'
        if (
            not Payment.objects.filter(refund_transaction_id=transaction_id).exists()
            and not RefundRequest.objects.filter(refund_transaction_id=transaction_id).exists()
        ):
            return transaction_id


def issue_approved_refund(refund_request, issued_by, notes=''):
    """
    Mark a refund request as issued and update its related payment.
    Returns (payment, transaction_id, amount).
    Raises ValueError when the refund cannot be issued.
    """
    from .models import PaymentStatus, RefundRequestStatus

    if refund_request.status not in {RefundRequestStatus.REQUESTED, RefundRequestStatus.APPROVED} or refund_request.issued_by_id:
        raise ValueError('This refund cannot be issued.')

    amount = refund_request.approved_amount or refund_request.requested_amount
    if amount <= Decimal('0'):
        raise ValueError('Refund amount must be greater than zero.')

    payment = (
        refund_request.booking.payments
        .filter(status__in=[
            PaymentStatus.COMPLETED,
            PaymentStatus.REFUND_PENDING,
            PaymentStatus.PARTIALLY_REFUNDED,
        ])
        .order_by('-completed_at', '-created_at')
        .first()
    )
    if not payment:
        raise ValueError('No refundable payment was found for this booking.')

    transaction_id = generate_refund_transaction_id(refund_request)
    existing_refund_amount = payment.refund_amount or Decimal('0')
    payment.refund_amount = existing_refund_amount + amount
    payment.refund_transaction_id = transaction_id
    payment.refund_reason = refund_request.reason
    payment.refunded_at = timezone.now()
    payment.status = PaymentStatus.REFUNDED if payment.refund_amount >= payment.amount else PaymentStatus.PARTIALLY_REFUNDED
    if notes:
        payment.notes = notes
    elif not payment.notes:
        payment.notes = 'Refund issued'
    payment.save(update_fields=[
        'refund_amount',
        'refund_transaction_id',
        'refund_reason',
        'refunded_at',
        'status',
        'notes',
        'updated_at',
    ])

    refund_request.status = RefundRequestStatus.ISSUED
    refund_request.issued_by = issued_by
    refund_request.issued_at = timezone.now()
    refund_request.refund_transaction_id = transaction_id
    refund_request.save(update_fields=[
        'status',
        'issued_by',
        'issued_at',
        'refund_transaction_id',
        'updated_at',
    ])

    return payment, transaction_id, amount


def get_occupancy_chart_context(today=None):
    """Build shared room occupancy data for staff/admin dashboards."""
    from datetime import timedelta
    import json

    from .models import (
        Booking,
        BookingStatus,
        PaymentStatus,
        Room,
        RoomHousekeepingLog,
        RoomStatus,
    )

    today = today or timezone.now().date()
    rooms = list(Room.objects.order_by('room_number'))
    total_rooms = len(rooms)

    checked_in_bookings = (
        Booking.objects
        .filter(
            status=BookingStatus.CHECKED_IN,
            check_in__lte=today,
            check_out__gte=today,
        )
        .select_related('guest', 'room')
        .order_by('-checked_in_at', '-created_at')
    )
    checked_in_by_room = {booking.room_id: booking for booking in checked_in_bookings}

    checked_out_today = (
        Booking.objects
        .filter(status=BookingStatus.CHECKED_OUT, check_out=today)
        .select_related('guest', 'room')
        .order_by('-checked_out_at', '-updated_at')
    )
    checked_out_by_room = {booking.room_id: booking for booking in checked_out_today}

    confirmed_paid_bookings = (
        Booking.objects
        .filter(
            status=BookingStatus.CONFIRMED,
            check_in=today,
            payments__status=PaymentStatus.COMPLETED,
        )
        .select_related('guest', 'room')
        .order_by('check_in', 'created_at')
        .distinct()
    )
    confirmed_by_room = {booking.room_id: booking for booking in confirmed_paid_bookings}

    room_cards = []
    for room in rooms:
        booking = None
        if room.id in checked_in_by_room:
            booking = checked_in_by_room[room.id]
            status_key = 'checked-in'
            status_label = 'Checked In'
        elif room.id in checked_out_by_room:
            booking = checked_out_by_room[room.id]
            status_key = 'checked-out'
            status_label = 'Checked Out Today'
        elif room.id in confirmed_by_room:
            booking = confirmed_by_room[room.id]
            status_key = 'confirmed'
            status_label = 'Confirmed'
        elif getattr(room, 'status', RoomStatus.CLEAN) == RoomStatus.MAINTENANCE:
            status_key = 'maintenance'
            status_label = 'Under Maintenance'
        elif getattr(room, 'status', RoomStatus.CLEAN) == RoomStatus.DIRTY:
            status_key = 'checked-out'
            status_label = 'Dirty'
        else:
            status_key = 'available'
            status_label = 'Available'

        room_cards.append({
            'room': room,
            'status_key': status_key,
            'status_label': status_label,
            'guest_name': (
                booking.guest.get_full_name()
                or booking.guest.username
                if booking else ''
            ),
        })

    occupied_today_count = len(checked_in_by_room)
    occupancy_rate = (occupied_today_count / total_rooms * 100) if total_rooms else 0

    weekly_labels = []
    weekly_values = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        occupied_count = (
            Booking.objects
            .filter(
                status__in=[BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT],
                check_in__lte=day,
                check_out__gt=day,
            )
            .values('room')
            .distinct()
            .count()
        )
        weekly_labels.append(day.strftime('%b %d'))
        weekly_values.append(occupied_count)

    return {
        'occupancy_room_cards': room_cards,
        'occupancy_total_rooms': total_rooms,
        'occupancy_occupied_today': occupied_today_count,
        'occupancy_rate_percent': occupancy_rate,
        'weekly_occupancy_labels_json': json.dumps(weekly_labels),
        'weekly_occupancy_values_json': json.dumps(weekly_values),
    }


def can_manager_register_staff(manager_user):
    """
    Check if a manager can register staff accounts.
    Managers can only register staff-level accounts (not other Managers or Admins).
    """
    return manager_user.is_manager() and manager_user.has_accepted_terms()


def can_manager_view_staff_dashboard(manager_user, staff_user):
    """
    Check if a manager can view a staff member's dashboard.
    Manager can view staff dashboards for performance monitoring.
    """
    return manager_user.is_manager() and manager_user.has_accepted_terms()


def can_staff_request_refund(staff_user):
    """Check if staff can request refunds (but not issue them)"""
    return staff_user.is_staff_member() and staff_user.has_accepted_terms()


def can_manager_approve_refund(manager_user):
    """Check if manager can approve refunds"""
    return manager_user.is_manager() and manager_user.has_accepted_terms()


def can_admin_issue_refund(admin_user):
    """Check if admin can issue refunds"""
    return admin_user.is_admin() and admin_user.has_accepted_terms()


def get_staff_visible_guest_fields():
    """
    Return list of guest profile fields that staff can see.
    Based on clarification: Full guest profile (all fields)
    """
    return [
        'id', 'email', 'first_name', 'last_name', 'phone_number',
        'username', 'created_at', 'updated_at'
    ]


def can_staff_see_guest_profile(staff_user):
    """Check if staff can view guest profiles"""
    return staff_user.is_staff_member() and staff_user.has_accepted_terms()


def can_staff_create_booking_on_behalf(staff_user):
    """Check if staff can create bookings on behalf of guests (walk-in, phone)"""
    return staff_user.is_staff_member() and staff_user.has_accepted_terms()


def can_staff_update_room_status(staff_user):
    """Check if staff can update room housekeeping status"""
    return staff_user.is_staff_member() and staff_user.has_accepted_terms()


def can_staff_escalate_complaint(staff_user):
    """Check if staff can escalate guest complaints to manager"""
    return staff_user.is_staff_member() and staff_user.has_accepted_terms()


class RoomStatusChoices:
    """Room status choices for housekeeping"""
    CLEAN = 'CLEAN'
    DIRTY = 'DIRTY'
    MAINTENANCE = 'MAINTENANCE'
    
    CHOICES = [
        (CLEAN, 'Clean'),
        (DIRTY, 'Dirty'),
        (MAINTENANCE, 'Under Maintenance'),
    ]


class RefundRequestStatus:
    """Refund request workflow statuses"""
    REQUESTED = 'REQUESTED'  # Staff requested
    APPROVED = 'APPROVED'    # Legacy pending issue state
    REJECTED = 'REJECTED'    # Manager rejected
    ISSUED = 'ISSUED'        # Refund issued
    
    CHOICES = [
        (REQUESTED, 'Requested by Staff'),
        (APPROVED, 'Pending Issue'),
        (REJECTED, 'Rejected by Manager'),
        (ISSUED, 'Refund Issued'),
    ]
