"""
Manager Views
Manager-specific dashboard, staff management, refund approvals, and escalations
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, F, Case, When, IntegerField, Avg
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from .models import (
    Booking, Room, BookingStatus, CustomUser, UserRole, Payment, PaymentStatus,
    RefundRequest, RefundRequestStatus, RoomHousekeepingLog, RoomStatus,
    GuestComplaintEscalation, AuditLog
)
from .decorators import manager_required, manager_or_admin_required
from .utils import log_audit


@login_required(login_url='auth:login')
@manager_or_admin_required
def manager_dashboard_view(request):
    """Manager Dashboard with staff, bookings, and escalations overview"""
    today = timezone.now().date()
    
    # Get stats relevant to manager
    context = {
        # Booking stats
        'pending_bookings': Booking.objects.filter(status=BookingStatus.PENDING).count(),
        'confirmed_bookings': Booking.objects.filter(status=BookingStatus.CONFIRMED).count(),
        'active_bookings': Booking.objects.filter(
            check_in__lte=today,
            check_out__gte=today,
            status=BookingStatus.CONFIRMED
        ).count(),
        
        # Refund requests awaiting approval
        'pending_refunds': RefundRequest.objects.filter(
            status=RefundRequestStatus.REQUESTED
        ).count(),
        'pending_refunds_total': RefundRequest.objects.filter(
            status=RefundRequestStatus.REQUESTED
        ).aggregate(Sum('requested_amount'))['requested_amount__sum'] or 0,
        
        # Guest complaints escalations
        'open_complaints': GuestComplaintEscalation.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS']
        ).count(),
        'recent_open_complaints': GuestComplaintEscalation.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS']
        ).select_related('booking', 'guest', 'reported_by_staff').order_by('-created_at')[:5],
        
        # Recent bookings requiring approval
        'recent_bookings': Booking.objects.filter(
            status=BookingStatus.PENDING
        ).select_related('guest', 'room').order_by('-created_at')[:5],
        
        # Pending refund requests
        'pending_refund_requests': RefundRequest.objects.filter(
            status=RefundRequestStatus.REQUESTED
        ).select_related('booking', 'requested_by').order_by('-created_at')[:5],
        
        # Staff performance summary
        'staff_members': CustomUser.objects.filter(role=UserRole.STAFF),
    }
    
    return render(request, 'dashboard/manager_dashboard.html', context)


@login_required(login_url='auth:login')
@manager_or_admin_required
def manager_refund_requests_view(request):
    """View all refund requests for manager approval"""
    # Get all refund requests for this manager
    refund_requests = RefundRequest.objects.select_related(
        'booking', 'requested_by', 'approved_by'
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        refund_requests = refund_requests.filter(status=status_filter)
    
    context = {
        'refund_requests': refund_requests,
        'status_filter': status_filter,
        'statuses': RefundRequestStatus.choices,
    }
    
    return render(request, 'manager/refund_requests.html', context)


@login_required(login_url='auth:login')
@manager_or_admin_required
def approve_refund_request_view(request, refund_request_id):
    """Manager approves or rejects a refund request"""
    refund_request = get_object_or_404(RefundRequest, id=refund_request_id)
    
    if refund_request.status != RefundRequestStatus.REQUESTED:
        messages.error(request, 'This refund request has already been processed.')
        return redirect('auth:manager_refunds')
    
    if request.method == 'POST':
        action = request.POST.get('action')  # 'approve' or 'reject'
        manager_notes = request.POST.get('manager_notes', '')
        approved_amount = request.POST.get('approved_amount')
        
        if action == 'approve':
            # Validate approved amount
            try:
                approved_amount = Decimal(approved_amount)
                if approved_amount <= 0 or approved_amount > refund_request.requested_amount:
                    messages.error(request, 'Approved amount must be between 0 and requested amount.')
                    return redirect('auth:manager_refunds')
            except (ValueError, TypeError):
                messages.error(request, 'Invalid approved amount.')
                return redirect('auth:manager_refunds')
            
            # Approve refund
            refund_request.status = RefundRequestStatus.APPROVED
            refund_request.approved_by = request.user
            refund_request.approved_amount = approved_amount
            refund_request.manager_notes = manager_notes
            refund_request.approved_at = timezone.now()
            refund_request.save()
            
            # Log audit
            log_audit(
                request,
                request.user,
                'REFUND_APPROVED',
                'RefundRequest',
                refund_request.id,
                affected_user=refund_request.requested_by,
                description=f'Manager approved refund of ₱{approved_amount}',
                changes={'status': 'APPROVED', 'approved_amount': str(approved_amount)}
            )
            
            messages.success(request, 'Refund request approved. Admin will now issue the refund.')
        
        elif action == 'reject':
            # Reject refund
            refund_request.status = RefundRequestStatus.REJECTED
            refund_request.approved_by = request.user
            refund_request.manager_notes = manager_notes
            refund_request.approved_at = timezone.now()
            refund_request.save()
            
            # Log audit
            log_audit(
                request,
                request.user,
                'REFUND_REJECTED',
                'RefundRequest',
                refund_request.id,
                affected_user=refund_request.requested_by,
                description=f'Manager rejected refund request',
                changes={'status': 'REJECTED'}
            )
            
            messages.info(request, 'Refund request rejected.')
        
        return redirect('auth:manager_refunds')
    
    context = {
        'refund_request': refund_request,
        'booking': refund_request.booking,
    }
    
    return render(request, 'manager/refund_detail.html', context)


@login_required(login_url='auth:login')
@manager_or_admin_required
def complaints_escalations_view(request):
    """View all escalated guest complaints"""
    complaints = GuestComplaintEscalation.objects.select_related(
        'booking', 'guest', 'reported_by_staff', 'escalated_to'
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        complaints = complaints.filter(status=status_filter)
    
    context = {
        'complaints': complaints,
        'status_filter': status_filter,
        'statuses': dict(GuestComplaintEscalation._meta.get_field('status').choices),
    }
    
    return render(request, 'manager/complaints_escalations.html', context)


@login_required(login_url='auth:login')
@manager_or_admin_required
def resolve_complaint_escalation_view(request, escalation_id):
    """Manager resolves an escalated complaint"""
    escalation = get_object_or_404(GuestComplaintEscalation, id=escalation_id)
    
    if escalation.status == 'CLOSED':
        messages.error(request, 'This complaint is already closed.')
        return redirect('auth:manager_complaints')
    
    if request.method == 'POST':
        action = request.POST.get('action')  # 'in_progress', 'resolve', 'close'
        manager_notes = request.POST.get('manager_notes', '')
        
        if action == 'in_progress':
            escalation.status = 'IN_PROGRESS'
            escalation.escalated_to = request.user
            escalation.manager_notes = manager_notes
            message_text = 'Complaint marked as in progress.'
        
        elif action == 'resolve':
            escalation.status = 'RESOLVED'
            escalation.escalated_to = request.user
            escalation.manager_notes = manager_notes
            escalation.resolved_at = timezone.now()
            message_text = 'Complaint marked as resolved.'
        
        elif action == 'close':
            escalation.status = 'CLOSED'
            escalation.escalated_to = request.user
            escalation.manager_notes = manager_notes
            escalation.resolved_at = timezone.now()
            message_text = 'Complaint closed.'
        
        escalation.updated_at = timezone.now()
        escalation.save()
        
        # Log audit
        log_audit(
            request,
            request.user,
            'COMPLAINT_RESOLVED',
            'GuestComplaintEscalation',
            escalation.id,
            affected_user=escalation.guest,
            description=f'Manager {action} complaint: {manager_notes}',
            changes={'status': escalation.status}
        )
        
        messages.success(request, message_text)
        return redirect('auth:manager_complaints')
    
    context = {
        'escalation': escalation,
        'booking': escalation.booking,
    }
    
    return render(request, 'manager/complaint_detail.html', context)


@login_required(login_url='auth:login')
@manager_or_admin_required
def staff_members_view(request):
    """Manage staff members under this manager"""
    staff_members = CustomUser.objects.filter(role=UserRole.STAFF).order_by('-created_at')
    
    # Manager can only see staff they've registered (future implementation)
    # For now, show all staff
    
    context = {
        'staff_members': staff_members,
    }
    
    return render(request, 'manager/staff_members.html', context)


@login_required(login_url='auth:login')
@manager_or_admin_required
def register_staff_view(request):
    """Manager registers new staff members"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password1') or request.POST.get('password')  # Support both field names
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_number = request.POST.get('phone_number', '')
        
        # Validate required fields
        if not all([username, email, password]):
            messages.error(request, 'Username, email, and password are required.')
            return render(request, 'manager/register_staff.html')
        
        # Validate passwords match
        if password2 and password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'manager/register_staff.html')
        
        # Validate username uniqueness
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'manager/register_staff.html')
        
        # Validate email uniqueness
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'manager/register_staff.html')
        
        # Validate password length
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'manager/register_staff.html')
        
        # Create staff user
        staff_user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=UserRole.STAFF,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            is_active=True
        )
        
        # Log audit
        log_audit(
            request,
            request.user,
            'STAFF_REGISTERED',
            'CustomUser',
            staff_user.id,
            affected_user=staff_user,
            description=f'Manager registered new staff member: {staff_user.email}',
            changes={'role': 'STAFF', 'email': email}
        )
        
        messages.success(request, f'Staff member {username} created successfully.')
        return redirect('auth:manager_staff')
    
    return render(request, 'manager/register_staff.html')


@login_required(login_url='auth:login')
@manager_or_admin_required
def deactivate_staff_view(request, staff_id):
    """Manager deactivates a staff member"""
    staff_user = get_object_or_404(CustomUser, id=staff_id, role=UserRole.STAFF)
    
    staff_user.is_active = False
    staff_user.save()
    
    # Log audit
    log_audit(
        request,
        request.user,
        'STAFF_DEACTIVATED',
        'CustomUser',
        staff_user.id,
        affected_user=staff_user,
        description=f'Manager deactivated staff member: {staff_user.email}',
        changes={'is_active': False}
    )
    
    messages.success(request, f'Staff member {staff_user.username} deactivated.')
    return redirect('auth:manager_staff')


@login_required(login_url='auth:login')
@manager_or_admin_required
def reactivate_staff_view(request, staff_id):
    """Manager reactivates a staff member"""
    staff_user = get_object_or_404(CustomUser, id=staff_id, role=UserRole.STAFF)

    staff_user.is_active = True
    staff_user.save(update_fields=['is_active'])

    log_audit(
        request,
        request.user,
        'STAFF_REACTIVATED',
        'CustomUser',
        staff_user.id,
        affected_user=staff_user,
        description=f'Manager reactivated staff member: {staff_user.email}',
        changes={'is_active': True}
    )

    messages.success(request, f'Staff member {staff_user.username} reactivated.')
    return redirect('auth:manager_staff')


@login_required(login_url='auth:login')
@manager_required
def staff_dashboard_view(request, staff_id):
    """Manager can view individual staff member dashboards"""
    if not staff_id:
        messages.error(request, 'Staff member not specified.')
        return redirect('auth:manager_staff')
    
    staff_member = get_object_or_404(CustomUser, id=staff_id, role=UserRole.STAFF)
    
    today = timezone.now().date()
    
    context = {
        'staff_member': staff_member,
        'created_bookings': Booking.objects.filter(
            created_at__startswith=today
        ).count(),
        'room_status_updates': RoomHousekeepingLog.objects.filter(
            updated_by=staff_member
        ).order_by('-created_at')[:10],
        'escalated_complaints': GuestComplaintEscalation.objects.filter(
            reported_by_staff=staff_member
        ),
    }
    
    return render(request, 'manager/staff_dashboard.html', context)
