"""
Manager Views
Manager-specific dashboard, staff management, refund approvals, and escalations
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.apps import apps
from django.db import connection, transaction
from django.db.utils import DatabaseError, IntegrityError
from django.db.models import Count, Sum, Q, F, Case, When, IntegerField, Avg
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.dateparse import parse_date
from decimal import Decimal
from datetime import timedelta, datetime, time

from .models import (
    Booking, Room, BookingStatus, CustomUser, UserRole, Payment, PaymentStatus,
    RefundRequest, RefundRequestStatus, RoomHousekeepingLog, RoomStatus,
    ActivityLog, Complaint, ComplaintStatus
)
from .decorators import manager_required, manager_or_admin_required
from .utils import get_two_fa_status, issue_approved_refund, log_activity, log_audit
from .emails import send_complaint_resolved_email


def _staff_registration_context(form_data=None, errors=None):
    """Keep submitted values and inline errors when staff registration fails."""
    return {
        'form_data': form_data or {},
        'form_errors': errors or {},
    }


def _get_housekeeping_task_model():
    """Return the optional housekeeping assignment model when another branch adds it."""
    try:
        return apps.get_model('authentication', 'HousekeepingTask')
    except LookupError:
        return None


def _housekeeping_storage_ready(task_model):
    if task_model is None:
        return False

    try:
        return task_model._meta.db_table in connection.introspection.table_names()
    except DatabaseError:
        return False


def _field_names(model):
    return {field.name for field in model._meta.get_fields()}


def _task_type_choices(model):
    default_choices = [
        ('CLEANING', 'Cleaning'),
        ('INSPECTION', 'Inspection'),
        ('MAINTENANCE', 'Maintenance'),
    ]

    field_names = _field_names(model)
    task_type_field = None
    if 'task_type' in field_names:
        task_type_field = model._meta.get_field('task_type')
    elif 'type' in field_names:
        task_type_field = model._meta.get_field('type')

    choices = list(getattr(task_type_field, 'choices', []) or [])
    return choices or default_choices


def _choice_value(model, field_name, preferred_values):
    if field_name not in _field_names(model):
        return None

    field = model._meta.get_field(field_name)
    choice_values = [choice[0] for choice in getattr(field, 'choices', []) or []]
    if not choice_values:
        return preferred_values[0] if preferred_values else None

    normalized = {str(value).upper(): value for value in choice_values}
    for preferred in preferred_values:
        value = normalized.get(str(preferred).upper())
        if value is not None:
            return value
    return None


def _due_value_for_field(model, field_name, due_date):
    field = model._meta.get_field(field_name)
    if field.get_internal_type() == 'DateTimeField':
        return timezone.make_aware(datetime.combine(due_date, time.min))
    return due_date


def _build_housekeeping_task_kwargs(task_model, room, staff_user, task_type, due_date, manager_user):
    field_names = _field_names(task_model)
    kwargs = {}

    for field_name in ('room', 'assigned_room'):
        if field_name in field_names:
            kwargs[field_name] = room
            break

    for field_name in ('assigned_to', 'staff', 'staff_member', 'assigned_staff'):
        if field_name in field_names:
            kwargs[field_name] = staff_user
            break

    for field_name in ('task_type', 'type'):
        if field_name in field_names:
            kwargs[field_name] = task_type
            break

    for field_name in ('due_date', 'due', 'target_date', 'scheduled_date'):
        if field_name in field_names:
            kwargs[field_name] = _due_value_for_field(task_model, field_name, due_date)
            break

    status_value = _choice_value(task_model, 'status', ['PENDING', 'OPEN', 'ASSIGNED', 'NEW'])
    if status_value is not None:
        kwargs['status'] = status_value

    for field_name in ('assigned_by', 'created_by', 'manager'):
        if field_name in field_names:
            kwargs[field_name] = manager_user
            break

    return kwargs


def _set_optional_task_manager(task, manager_user):
    field_names = _field_names(task.__class__)
    for field_name in ('assigned_by', 'created_by', 'manager'):
        if field_name in field_names:
            setattr(task, field_name, manager_user)
            task.save(update_fields=[field_name])
            break


def _mark_room_for_maintenance(room):
    previous_status = getattr(room, 'status', RoomStatus.CLEAN)
    update_fields = []

    if hasattr(room, 'housekeeping_status'):
        room.housekeeping_status = RoomStatus.MAINTENANCE
        update_fields.append('housekeeping_status')

    if hasattr(room, 'status'):
        status_field = room._meta.get_field('status')
        choices = [choice[0] for choice in getattr(status_field, 'choices', []) or []]
        maintenance_value = RoomStatus.MAINTENANCE
        if choices:
            normalized = {str(value).upper(): value for value in choices}
            maintenance_value = normalized.get('MAINTENANCE', maintenance_value)
        room.status = maintenance_value
        update_fields.append('status')

    if hasattr(room, 'is_available'):
        room.is_available = False
        update_fields.append('is_available')

    if update_fields:
        room.save(update_fields=update_fields)

    RoomHousekeepingLog.objects.create(
        room=room,
        previous_status=previous_status,
        current_status=RoomStatus.MAINTENANCE,
        updated_by=None,
        notes='Marked for maintenance from manager housekeeping assignment.'
    )


def _recent_housekeeping_tasks(task_model):
    if not task_model:
        return []

    try:
        queryset = task_model.objects.all().order_by('-id')[:5]
        task_rows = list(queryset)
    except DatabaseError:
        return []

    tasks = []
    for task in task_rows:
        room = getattr(task, 'room', None) or getattr(task, 'assigned_room', None)
        staff_user = (
            getattr(task, 'assigned_to', None) or
            getattr(task, 'staff', None) or
            getattr(task, 'staff_member', None) or
            getattr(task, 'assigned_staff', None)
        )
        task_type = getattr(task, 'task_type', None) or getattr(task, 'type', '')
        due_date = (
            getattr(task, 'due_date', None) or
            getattr(task, 'due', None) or
            getattr(task, 'target_date', None) or
            getattr(task, 'scheduled_date', None)
        )
        tasks.append({
            'id': task.id,
            'room': room,
            'staff': staff_user,
            'task_type': task_type,
            'due_date': due_date,
            'status': getattr(task, 'status', ''),
        })
    return tasks


def _month_delta(month_start, offset):
    """Return the first day of the month offset from a timezone-aware month start."""
    month_index = month_start.month - 1 + offset
    year = month_start.year + month_index // 12
    month = month_index % 12 + 1
    return month_start.replace(year=year, month=month, day=1)


@login_required(login_url='auth:login')
@manager_or_admin_required
def manager_dashboard_view(request):
    """Manager Dashboard with staff, bookings, and escalations overview"""
    today = timezone.now().date()
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    task_model = _get_housekeeping_task_model()
    housekeeping_storage_ready = _housekeeping_storage_ready(task_model)
    staff_members = CustomUser.objects.filter(role=UserRole.STAFF).order_by('first_name', 'last_name', 'username')

    if request.method == 'POST' and request.POST.get('action') == 'assign_housekeeping':
        if not housekeeping_storage_ready:
            messages.error(request, 'Housekeeping assignment storage is not available yet. Apply the model migration first.')
            return redirect('auth:manager_dashboard')

        room = get_object_or_404(Room, id=request.POST.get('room_id'))
        staff_user = get_object_or_404(CustomUser, id=request.POST.get('staff_id'), role=UserRole.STAFF)
        task_type = request.POST.get('task_type', '').strip()
        due_date = parse_date(request.POST.get('due_date', '').strip())
        valid_task_types = [choice[0] for choice in _task_type_choices(task_model)]

        if task_type not in valid_task_types:
            messages.error(request, 'Select a valid task type.')
            return redirect('auth:manager_dashboard')

        if due_date is None:
            messages.error(request, 'Select a valid due date.')
            return redirect('auth:manager_dashboard')

        try:
            with transaction.atomic():
                task_kwargs = _build_housekeeping_task_kwargs(task_model, room, staff_user, task_type, due_date, request.user)
                task = task_model.objects.create(**task_kwargs)
                _set_optional_task_manager(task, request.user)

                if str(task_type).upper() == 'MAINTENANCE':
                    _mark_room_for_maintenance(room)

                log_audit(
                    request,
                    request.user,
                    'ROOM_STATUS_CHANGED',
                    'HousekeepingTask',
                    task.id,
                    affected_user=staff_user,
                    description=f'Manager assigned {task_type} task for room {room.room_number}',
                    changes={'room_id': room.id, 'staff_id': staff_user.id, 'task_type': task_type, 'due_date': str(due_date)}
                )
        except (TypeError, DatabaseError) as exc:
            messages.error(request, f'Housekeeping assignment storage is not ready yet: {exc}')
            return redirect('auth:manager_dashboard')

        messages.success(request, f'Housekeeping task assigned to {staff_user.get_full_name() or staff_user.username}.')
        return redirect('auth:manager_dashboard')

    completed_payments = Payment.objects.filter(status=PaymentStatus.COMPLETED)
    total_revenue = completed_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_revenue = completed_payments.filter(
        completed_at__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    average_payment_value = completed_payments.aggregate(average=Avg('amount'))['average'] or Decimal('0.00')

    monthly_revenue_rows = completed_payments.filter(
        completed_at__isnull=False,
        completed_at__gte=_month_delta(month_start, -5),
    ).annotate(
        month=TruncMonth('completed_at')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    monthly_revenue_by_month = {
        row['month'].date().replace(day=1): row['total'] or Decimal('0.00')
        for row in monthly_revenue_rows
        if row['month']
    }
    revenue_chart_months = [_month_delta(month_start, offset).date().replace(day=1) for offset in range(-5, 1)]
    revenue_chart_data = {
        'labels': [month.strftime('%b %Y') for month in revenue_chart_months],
        'values': [float(monthly_revenue_by_month.get(month, Decimal('0.00'))) for month in revenue_chart_months],
    }

    booking_statuses = [
        (BookingStatus.PENDING, 'Pending'),
        (BookingStatus.CONFIRMED, 'Confirmed'),
        (BookingStatus.CHECKED_IN, 'Checked In'),
        (BookingStatus.CHECKED_OUT, 'Checked Out'),
        (BookingStatus.CANCELLED, 'Cancelled'),
    ]
    booking_status_counts = {
        row['status']: row['count']
        for row in Booking.objects.values('status').annotate(count=Count('id'))
    }
    total_status_bookings = Booking.objects.count()
    booking_status_breakdown = []
    for status, label in booking_statuses:
        count = booking_status_counts.get(status, 0)
        percentage = (count / total_status_bookings * 100) if total_status_bookings else 0
        booking_status_breakdown.append({
            'status': status,
            'label': label,
            'count': count,
            'percentage': round(percentage, 1),
        })
    
    # Get stats relevant to manager
    context = {
        # Revenue stats
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'average_payment_value': average_payment_value,
        'average_booking_value': average_payment_value,
        'revenue_chart_data': revenue_chart_data,
        'booking_status_breakdown': booking_status_breakdown,
        'recent_activity_logs': ActivityLog.objects.select_related('user').order_by('-timestamp')[:20],

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
        'open_complaints': Complaint.objects.filter(
            status__in=[ComplaintStatus.ESCALATED, ComplaintStatus.IN_PROGRESS]
        ).count(),
        'recent_open_complaints': Complaint.objects.filter(
            status__in=[ComplaintStatus.ESCALATED, ComplaintStatus.IN_PROGRESS]
        ).select_related('booking', 'guest', 'assigned_to', 'escalated_to').order_by('-created_at')[:5],
        
        # Recent bookings requiring approval
        'recent_bookings': Booking.objects.filter(
            status=BookingStatus.PENDING
        ).select_related('guest', 'room').order_by('-created_at')[:5],
        
        # Pending refund requests
        'pending_refund_requests': RefundRequest.objects.filter(
            status=RefundRequestStatus.REQUESTED
        ).select_related('booking', 'requested_by').order_by('-created_at')[:5],
        
        # Staff performance summary
        'staff_members': staff_members,
        'housekeeping_task_model_available': housekeeping_storage_ready,
        'housekeeping_rooms': Room.objects.all().order_by('room_number'),
        'housekeeping_task_type_choices': _task_type_choices(task_model) if task_model else [
            ('CLEANING', 'Cleaning'),
            ('INSPECTION', 'Inspection'),
            ('MAINTENANCE', 'Maintenance'),
        ],
        'recent_housekeeping_tasks': _recent_housekeeping_tasks(task_model),
        'today': today,
        'two_fa': get_two_fa_status(request.user),
    }
    
    return render(request, 'manager/manager_dashboard.html', context)


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
    visible_statuses = [
        choice for choice in RefundRequestStatus.choices
        if choice[0] != RefundRequestStatus.APPROVED
    ]
    if status_filter == RefundRequestStatus.APPROVED:
        status_filter = 'all'
    if status_filter != 'all':
        refund_requests = refund_requests.filter(status=status_filter)
    
    context = {
        'refund_requests': refund_requests,
        'status_filter': status_filter,
        'statuses': visible_statuses,
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
        action = request.POST.get('action')  # 'issue' or 'reject'
        manager_notes = request.POST.get('manager_notes', '')
        approved_amount = request.POST.get('approved_amount')
        
        if action == 'issue':
            try:
                approved_amount = Decimal(approved_amount)
                if approved_amount <= 0 or approved_amount > refund_request.requested_amount:
                    messages.error(request, 'Refund amount must be between 0 and requested amount.')
                    return redirect('auth:manager_refunds')
            except (ValueError, TypeError):
                messages.error(request, 'Invalid refund amount.')
                return redirect('auth:manager_refunds')

            refund_request.approved_by = request.user
            refund_request.approved_amount = approved_amount
            refund_request.manager_notes = manager_notes
            refund_request.approved_at = timezone.now()
            refund_request.save(update_fields=[
                'approved_by',
                'approved_amount',
                'manager_notes',
                'approved_at',
                'updated_at',
            ])

            try:
                payment, transaction_id, issued_amount = issue_approved_refund(
                    refund_request,
                    request.user,
                    manager_notes or 'Refund issued by manager',
                )
            except ValueError as error:
                messages.error(request, str(error))
                return redirect('auth:manager_refunds')

            log_audit(
                request,
                request.user,
                'REFUND_ISSUED',
                'RefundRequest',
                refund_request.id,
                affected_user=refund_request.booking.guest,
                description=f'Manager issued refund of PHP {issued_amount}',
                changes={
                    'status': 'ISSUED',
                    'amount': str(issued_amount),
                    'refund_transaction_id': transaction_id,
                }
            )
            messages.success(request, f'Refund issued with transaction ID {transaction_id}.')
        
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
    complaints = Complaint.objects.filter(
        status__in=[ComplaintStatus.ESCALATED, ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED]
    ).select_related(
        'booking__room', 'guest', 'assigned_to', 'escalated_to'
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', ComplaintStatus.ESCALATED)
    if status_filter != 'all':
        complaints = complaints.filter(status=status_filter)
    
    context = {
        'complaints': complaints,
        'status_filter': status_filter,
        'statuses': ComplaintStatus.choices,
    }
    
    return render(request, 'manager/complaints_escalations.html', context)


@login_required(login_url='auth:login')
@manager_or_admin_required
def resolve_complaint_escalation_view(request, escalation_id):
    """Manager resolves an escalated complaint"""
    complaint = get_object_or_404(
        Complaint.objects.select_related('booking__room', 'guest', 'assigned_to', 'escalated_to'),
        id=escalation_id,
        status__in=[ComplaintStatus.ESCALATED, ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED],
    )
    
    if request.method == 'POST':
        if complaint.status == ComplaintStatus.RESOLVED:
            messages.info(request, 'This complaint is already resolved.')
            return redirect('auth:manager_resolve_complaint', escalation_id=complaint.id)

        action = request.POST.get('action')  # 'in_progress' or 'resolve'
        manager_notes = request.POST.get('manager_notes', '').strip()
        
        if action == 'in_progress':
            complaint.status = ComplaintStatus.IN_PROGRESS
            complaint.escalated_to = request.user
            if manager_notes:
                complaint.resolution_notes = manager_notes
            message_text = 'Complaint marked as in progress.'
        
        elif action == 'resolve':
            if not manager_notes:
                messages.error(request, 'Resolution notes are required before marking a complaint resolved.')
                return redirect('auth:manager_resolve_complaint', escalation_id=complaint.id)

            complaint.status = ComplaintStatus.RESOLVED
            complaint.escalated_to = request.user
            complaint.resolution_notes = manager_notes
            complaint.resolved_at = timezone.now()
            message_text = 'Complaint marked as resolved.'

        else:
            messages.error(request, 'Select a valid complaint action.')
            return redirect('auth:manager_resolve_complaint', escalation_id=complaint.id)

        complaint.save()

        if action == 'resolve':
            if not send_complaint_resolved_email(complaint):
                messages.warning(request, 'Complaint resolved, but the guest resolution email could not be sent.')
            log_activity(
                request.user,
                f'Resolved complaint #{complaint.id}',
                f'Complaint #{complaint.id}',
                request
            )
        
        # Log audit
        log_audit(
            request,
            request.user,
            'COMPLAINT_RESOLVED',
            'Complaint',
            complaint.id,
            affected_user=complaint.guest,
            description=f'Manager {action} complaint: {manager_notes}',
            changes={'status': complaint.status}
        )
        
        messages.success(request, message_text)
        return redirect('auth:manager_complaints')
    
    context = {
        'complaint': complaint,
        'booking': complaint.booking,
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
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password1') or request.POST.get('password')  # Support both field names
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_number = request.POST.get('phone_number', '')
        form_data = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': phone_number,
        }
        
        # Validate required fields
        if not all([username, email, password]):
            messages.error(request, 'Username, email, and password are required.')
            return render(
                request,
                'manager/register_staff.html',
                _staff_registration_context(
                    form_data,
                    {'non_field_errors': ['Username, email, and password are required.']},
                ),
            )
        
        # Validate passwords match
        if not password2:
            messages.error(request, 'Please confirm the staff password.')
            return render(
                request,
                'manager/register_staff.html',
                _staff_registration_context(form_data, {'password2': ['Please confirm the staff password.']}),
            )

        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(
                request,
                'manager/register_staff.html',
                _staff_registration_context(form_data, {'password2': ['Passwords do not match.']}),
            )
        
        # Validate username uniqueness
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(
                request,
                'manager/register_staff.html',
                _staff_registration_context(form_data, {'username': ['Username already exists.']}),
            )
        
        # Validate email uniqueness
        if CustomUser.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email already registered.')
            return render(
                request,
                'manager/register_staff.html',
                _staff_registration_context(form_data, {'email': ['Email already registered.']}),
            )
        
        # Validate password length
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(
                request,
                'manager/register_staff.html',
                _staff_registration_context(form_data, {'password': ['Password must be at least 8 characters.']}),
            )

        try:
            validate_password(password)
        except ValidationError as exc:
            messages.error(request, 'Please choose a stronger password.')
            return render(
                request,
                'manager/register_staff.html',
                _staff_registration_context(form_data, {'password': list(exc.messages)}),
            )
        
        try:
            with transaction.atomic():
                staff_user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=UserRole.STAFF,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                    is_active=True,
                    is_staff=True,
                )
        except IntegrityError:
            messages.error(request, 'Could not create staff member because the username or email is already in use.')
            return render(
                request,
                'manager/register_staff.html',
                _staff_registration_context(form_data, {'non_field_errors': ['Username or email is already in use.']}),
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
    
    return render(request, 'manager/register_staff.html', _staff_registration_context())


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
        'escalated_complaints': Complaint.objects.filter(
            assigned_to=staff_member,
            status__in=[ComplaintStatus.ESCALATED, ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED],
        ).select_related('booking', 'guest', 'escalated_to'),
    }
    
    return render(request, 'manager/staff_dashboard.html', context)
