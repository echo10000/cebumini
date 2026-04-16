"""
Utility functions for authentication, audit logging, and role management
"""

from django.utils import timezone
from .models import AuditLog


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
    APPROVED = 'APPROVED'    # Manager approved
    REJECTED = 'REJECTED'    # Manager rejected
    ISSUED = 'ISSUED'        # Admin issued the refund
    
    CHOICES = [
        (REQUESTED, 'Requested by Staff'),
        (APPROVED, 'Approved by Manager'),
        (REJECTED, 'Rejected by Manager'),
        (ISSUED, 'Refund Issued by Admin'),
    ]
