from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, F, Case, When, IntegerField, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Booking, Room, BookingStatus, CustomUser, RoomType
from .decorators import admin_required
import json


def get_booking_statistics():
    """Get all booking statistics"""
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    stats = {
        # Booking counts
        'total_bookings': Booking.objects.count(),
        'confirmed_bookings': Booking.objects.filter(status=BookingStatus.CONFIRMED).count(),
        'pending_bookings': Booking.objects.filter(status=BookingStatus.PENDING).count(),
        'cancelled_bookings': Booking.objects.filter(status=BookingStatus.CANCELLED).count(),
        
        # Revenue
        'total_revenue': Booking.objects.filter(
            status=BookingStatus.CONFIRMED
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0,
        
        # Room statistics
        'total_rooms': Room.objects.count(),
        'available_rooms': Room.objects.filter(is_available=True).count(),
        'booked_rooms': Room.objects.filter(is_available=False).count(),
        
        # Occupancy
        'occupancy_rate': calculate_occupancy_rate(),
        
        # Most booked room
        'most_booked_room': get_most_booked_room(),
        
        # Active bookings (currently checked in)
        'active_bookings': Booking.objects.filter(
            check_in__lte=today,
            check_out__gte=today,
            status=BookingStatus.CONFIRMED
        ).count(),
        
        # Today's check-ins and check-outs
        'todays_checkins': Booking.objects.filter(
            check_in=today,
            status=BookingStatus.CONFIRMED
        ).count(),
        
        'todays_checkouts': Booking.objects.filter(
            check_out=today,
            status=BookingStatus.CONFIRMED
        ).count(),
        
        # This week
        'bookings_this_week': Booking.objects.filter(
            created_at__date__gte=start_of_week,
            status=BookingStatus.CONFIRMED
        ).count(),
        
        'revenue_this_week': Booking.objects.filter(
            created_at__date__gte=start_of_week,
            status=BookingStatus.CONFIRMED
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0,
        
        # This month
        'bookings_this_month': Booking.objects.filter(
            created_at__date__gte=start_of_month,
            status=BookingStatus.CONFIRMED
        ).count(),
        
        'revenue_this_month': Booking.objects.filter(
            created_at__date__gte=start_of_month,
            status=BookingStatus.CONFIRMED
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0,
    }
    
    return stats


def calculate_occupancy_rate():
    """Calculate current occupancy rate"""
    today = timezone.now().date()
    
    total_rooms = Room.objects.count()
    if total_rooms == 0:
        return 0
    
    occupied_rooms = Booking.objects.filter(
        check_in__lte=today,
        check_out__gte=today,
        status=BookingStatus.CONFIRMED
    ).values('room').distinct().count()
    
    rate = (occupied_rooms / total_rooms) * 100
    return round(rate, 1)


def get_most_booked_room():
    """Get the most booked room"""
    most_booked = Room.objects.annotate(
        booking_count=Count('bookings', filter=Q(
            bookings__status=BookingStatus.CONFIRMED
        ))
    ).order_by('-booking_count').first()
    
    return most_booked


def get_booking_trends(days=30):
    """Get booking trends for the last N days"""
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    bookings_by_date = []
    revenue_by_date = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        daily_bookings = Booking.objects.filter(
            created_at__date=current_date,
            status=BookingStatus.CONFIRMED
        ).count()
        
        daily_revenue = Booking.objects.filter(
            created_at__date=current_date,
            status=BookingStatus.CONFIRMED
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        bookings_by_date.append({
            'date': current_date.strftime('%b %d'),
            'count': daily_bookings,
        })
        
        revenue_by_date.append({
            'date': current_date.strftime('%b %d'),
            'amount': float(daily_revenue),
        })
    
    return {
        'bookings': bookings_by_date,
        'revenue': revenue_by_date,
    }


def get_room_statistics():
    """Get statistics per room"""
    rooms = Room.objects.annotate(
        booking_count=Count('bookings', filter=Q(
            bookings__status=BookingStatus.CONFIRMED
        )),
        total_revenue=Sum('bookings__total_price', filter=Q(
            bookings__status=BookingStatus.CONFIRMED
        )),
        occupancy_days=Sum(
            Case(
                When(
                    bookings__status=BookingStatus.CONFIRMED,
                    then=F('bookings__check_out') - F('bookings__check_in')
                ),
                default=0,
                output_field=IntegerField()
            )
        )
    ).order_by('-booking_count')
    
    room_stats = []
    for room in rooms:
        room_stats.append({
            'room': room,
            'booking_count': room.booking_count or 0,
            'total_revenue': room.total_revenue or 0,
            'occupancy_days': room.occupancy_days or 0,
        })
    
    return room_stats[:10]  # Top 10 rooms


def get_guest_statistics():
    """Get guest/user statistics"""
    total_guests = CustomUser.objects.filter(role='GUEST').count()
    admin_users = CustomUser.objects.filter(role='ADMIN').count()
    
    guests_with_bookings = CustomUser.objects.filter(
        bookings__status=BookingStatus.CONFIRMED
    ).distinct().count()
    
    return {
        'total_guests': total_guests,
        'admin_users': admin_users,
        'guests_with_bookings': guests_with_bookings,
        'guests_without_bookings': total_guests - guests_with_bookings,
    }


@login_required(login_url='login')
@admin_required
def dashboard_view(request):
    """Admin dashboard with statistics"""
    
    # Get all statistics
    booking_stats = get_booking_statistics()
    room_stats = get_room_statistics()
    guest_stats = get_guest_statistics()
    
    # Get recent bookings
    recent_bookings = Booking.objects.select_related(
        'room', 'guest'
    ).order_by('-created_at')[:10]
    
    context = {
        'booking_stats': booking_stats,
        'room_stats': room_stats,
        'guest_stats': guest_stats,
        'recent_bookings': recent_bookings,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required(login_url='login')
def revenue_analytics_view(request):
    """Detailed revenue analytics"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        return redirect('home')
    
    today = timezone.now().date()
    
    # Time period for analysis
    time_period = request.GET.get('period', '30')
    try:
        days = int(time_period)
    except (ValueError, TypeError):
        days = 30
    
    start_date = today - timedelta(days=days)
    
    # Calculate weekly/monthly averages
    start_of_week = today - timedelta(days=today.weekday())
    last_start_of_week = start_of_week - timedelta(days=7)
    start_of_month = today.replace(day=1)
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    
    this_week_revenue = Booking.objects.filter(
        created_at__date__gte=start_of_week,
        status=BookingStatus.CONFIRMED
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    last_week_revenue = Booking.objects.filter(
        created_at__date__gte=last_start_of_week,
        created_at__date__lt=start_of_week,
        status=BookingStatus.CONFIRMED
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    this_month_revenue = Booking.objects.filter(
        created_at__date__gte=start_of_month,
        status=BookingStatus.CONFIRMED
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    last_month_revenue = Booking.objects.filter(
        created_at__date__gte=last_month_start,
        created_at__date__lt=start_of_month,
        status=BookingStatus.CONFIRMED
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Revenue by room type
    revenue_by_room_type = []
    total_revenue = Booking.objects.filter(
        status=BookingStatus.CONFIRMED
    ).aggregate(Sum('total_price'))['total_price__sum'] or 1  # Prevent division by zero
    
    for room_type_code, room_type_name in RoomType.choices:
        room_type_revenue = Booking.objects.filter(
            room__room_type=room_type_code,
            status=BookingStatus.CONFIRMED
        ).aggregate(
            total=Sum('total_price'),
            count=Count('id')
        )
        
        if room_type_revenue['count'] and room_type_revenue['count'] > 0:
            revenue_by_room_type.append({
                'room_type': room_type_name,
                'booking_count': room_type_revenue['count'],
                'total_revenue': room_type_revenue['total'] or 0,
                'average_price': (room_type_revenue['total'] or 0) / room_type_revenue['count'],
                'percentage': round(((room_type_revenue['total'] or 0) / total_revenue) * 100, 1),
            })
    
    # Daily revenue chart data
    daily_revenue_data = []
    daily_labels = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        day_revenue = Booking.objects.filter(
            created_at__date=current_date,
            status=BookingStatus.CONFIRMED
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        daily_labels.append(current_date.strftime('%m/%d'))
        daily_revenue_data.append(float(day_revenue))
    
    revenue_chart_data = {
        'labels': daily_labels,
        'values': daily_revenue_data,
    }
    
    # Total revenue and average
    total_revenue_amount = Booking.objects.filter(
        status=BookingStatus.CONFIRMED
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    confirmed_count = Booking.objects.filter(
        status=BookingStatus.CONFIRMED
    ).count()
    
    avg_booking = total_revenue_amount / confirmed_count if confirmed_count > 0 else 0
    
    # Week trend calculation
    week_trend = ((this_week_revenue - last_week_revenue) / (last_week_revenue or 1)) * 100 if last_week_revenue > 0 else 0
    month_trend = ((this_month_revenue - last_month_revenue) / (last_month_revenue or 1)) * 100 if last_month_revenue > 0 else 0
    
    revenue_analytics = {
        'total_revenue': total_revenue_amount,
        'daily_revenue': Booking.objects.filter(
            created_at__date=today,
            status=BookingStatus.CONFIRMED
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'average_booking_value': avg_booking,
        'revenue_by_status': {
            'confirmed': Booking.objects.filter(
                status=BookingStatus.CONFIRMED
            ).aggregate(Sum('total_price'))['total_price__sum'] or 0,
            'pending': Booking.objects.filter(
                status=BookingStatus.PENDING
            ).aggregate(Sum('total_price'))['total_price__sum'] or 0,
        },
        'revenue_by_room_type': revenue_by_room_type,
        'this_week_revenue': this_week_revenue,
        'last_week_revenue': last_week_revenue,
        'this_month_revenue': this_month_revenue,
        'last_month_revenue': last_month_revenue,
        'weekly_average': (this_week_revenue + last_week_revenue) / 2 if (this_week_revenue + last_week_revenue) > 0 else 0,
        'monthly_average': (this_month_revenue + last_month_revenue) / 2 if (this_month_revenue + last_month_revenue) > 0 else 0,
        'week_trend': week_trend,
        'month_trend': month_trend,
    }
    
    context = {
        'revenue_analytics': revenue_analytics,
        'revenue_chart_data': json.dumps(revenue_chart_data),
    }
    
    return render(request, 'dashboard/revenue_analytics.html', context)


@login_required(login_url='login')
def occupancy_analytics_view(request):
    """Occupancy analysis and room status"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        return redirect('home')
    
    today = timezone.now().date()
    
    # Time period
    time_period = request.GET.get('period', '30')
    try:
        days = int(time_period)
    except (ValueError, TypeError):
        days = 30
    
    start_date = today - timedelta(days=days)
    start_of_week = today - timedelta(days=today.weekday())
    last_start_of_week = start_of_week - timedelta(days=7)
    start_of_month = today.replace(day=1)
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    
    # Daily occupancy rate
    occupancy_chart_labels = []
    occupancy_chart_values = []
    total_rooms = Room.objects.count()
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        occupied_rooms = Booking.objects.filter(
            check_in__lte=current_date,
            check_out__gte=current_date,
            status=BookingStatus.CONFIRMED
        ).values('room').distinct().count()
        
        if total_rooms > 0:
            occupancy_rate = (occupied_rooms / total_rooms) * 100
        else:
            occupancy_rate = 0
        
        occupancy_chart_labels.append(current_date.strftime('%m/%d'))
        occupancy_chart_values.append(round(occupancy_rate, 1))
    
    occupancy_chart_data = {
        'labels': occupancy_chart_labels,
        'values': occupancy_chart_values,
    }
    
    # Occupancy by room type
    occupancy_by_type = []
    for room_type_code, room_type_name in RoomType.choices:
        total_type = Room.objects.filter(room_type=room_type_code).count()
        
        occupied_type = Booking.objects.filter(
            room__room_type=room_type_code,
            check_in__lte=today,
            check_out__gte=today,
            status=BookingStatus.CONFIRMED
        ).values('room').distinct().count()
        
        if total_type > 0:
            occupancy_rate = (occupied_type / total_type) * 100
        else:
            occupancy_rate = 0
        
        occupancy_by_type.append({
            'room_type': room_type_name,
            'total': total_type,
            'occupied': occupied_type,
            'available': total_type - occupied_type,
            'occupancy_rate': round(occupancy_rate, 1),
        })
    
    # Room status
    room_status = []
    for room in Room.objects.all():
        is_occupied = Booking.objects.filter(
            room=room,
            check_in__lte=today,
            check_out__gte=today,
            status=BookingStatus.CONFIRMED
        ).exists()
        
        room_status.append({
            'room': room,
            'is_occupied': is_occupied,
        })
    
    # Weekly and monthly trends
    this_week_occupied_days = 0
    this_week_total_days = 0
    
    for i in range((today - start_of_week).days + 1):
        current_date = start_of_week + timedelta(days=i)
        occupied = Booking.objects.filter(
            check_in__lte=current_date,
            check_out__gte=current_date,
            status=BookingStatus.CONFIRMED
        ).values('room').distinct().count()
        this_week_occupied_days += occupied
        this_week_total_days += total_rooms
    
    this_week_occupancy = (this_week_occupied_days / this_week_total_days * 100) if this_week_total_days > 0 else 0
    
    last_week_occupied_days = 0
    last_week_total_days = 0
    
    for i in range(7):
        current_date = last_start_of_week + timedelta(days=i)
        occupied = Booking.objects.filter(
            check_in__lte=current_date,
            check_out__gte=current_date,
            status=BookingStatus.CONFIRMED
        ).values('room').distinct().count()
        last_week_occupied_days += occupied
        last_week_total_days += total_rooms
    
    last_week_occupancy = (last_week_occupied_days / last_week_total_days * 100) if last_week_total_days > 0 else 0
    
    weekly_trend = ((this_week_occupancy - last_week_occupancy) / (last_week_occupancy or 1)) * 100 if last_week_occupancy > 0 else 0
    
    # Monthly occupancy
    this_month_days = (today - start_of_month).days + 1
    this_month_occupied_days = 0
    
    for i in range(this_month_days):
        current_date = start_of_month + timedelta(days=i)
        occupied = Booking.objects.filter(
            check_in__lte=current_date,
            check_out__gte=current_date,
            status=BookingStatus.CONFIRMED
        ).values('room').distinct().count()
        this_month_occupied_days += occupied
    
    this_month_occupancy = (this_month_occupied_days / (this_month_days * total_rooms) * 100) if total_rooms > 0 else 0
    
    occupancy_analytics = {
        'occupancy_rate': calculate_occupancy_rate(),
        'occupied_rooms': Booking.objects.filter(
            check_in__lte=today,
            check_out__gte=today,
            status=BookingStatus.CONFIRMED
        ).values('room').distinct().count(),
        'available_rooms': total_rooms - Booking.objects.filter(
            check_in__lte=today,
            check_out__gte=today,
            status=BookingStatus.CONFIRMED
        ).values('room').distinct().count(),
        'total_rooms': total_rooms,
        'occupancy_by_type': occupancy_by_type,
        'room_status': room_status,
        'average_occupancy_30d': round(sum(occupancy_chart_values) / len(occupancy_chart_values), 1) if occupancy_chart_values else 0,
        'this_week_occupancy': round(this_week_occupancy, 1),
        'last_week_occupancy': round(last_week_occupancy, 1),
        'this_month_occupancy': round(this_month_occupancy, 1),
        'weekly_trend': round(weekly_trend, 1),
        'monthly_trend': 0,  # Need more data for this
    }
    
    context = {
        'occupancy_analytics': occupancy_analytics,
        'occupancy_chart_data': json.dumps(occupancy_chart_data),
    }
    
    return render(request, 'dashboard/occupancy_analytics.html', context)


@login_required(login_url='login')
def booking_analytics_view(request):
    """Detailed booking analytics"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        return redirect('home')
    
    today = timezone.now().date()
    
    # Time period
    time_period = request.GET.get('period', '30')
    try:
        days = int(time_period)
    except (ValueError, TypeError):
        days = 30
    
    start_date = today - timedelta(days=days)
    
    # Daily bookings chart data
    daily_bookings_data = []
    daily_labels = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        created = Booking.objects.filter(
            created_at__date=current_date,
            status=BookingStatus.CONFIRMED
        ).count()
        
        daily_labels.append(current_date.strftime('%m/%d'))
        daily_bookings_data.append(created)
    
    trend_chart_data = {
        'labels': daily_labels,
        'values': daily_bookings_data,
    }
    
    # Status breakdown
    confirmed = Booking.objects.filter(status=BookingStatus.CONFIRMED).count()
    pending = Booking.objects.filter(status=BookingStatus.PENDING).count()
    cancelled = Booking.objects.filter(status=BookingStatus.CANCELLED).count()
    
    total = confirmed + pending + cancelled or 1
    
    # Average stay duration
    confirmed_bookings = Booking.objects.filter(
        status=BookingStatus.CONFIRMED
    ).annotate(
        stay_duration=F('check_out') - F('check_in')
    )
    
    if confirmed_bookings.exists():
        avg_stay = confirmed_bookings.aggregate(
            avg=Avg('stay_duration')
        )['avg']
        avg_stay_days = avg_stay.days if avg_stay else 0
    else:
        avg_stay_days = 0
    
    # Bookings by day of week
    bookings_by_day = {}
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day in days_of_week:
        bookings_by_day[day] = 0
    
    bookings = Booking.objects.filter(status=BookingStatus.CONFIRMED)
    for booking in bookings:
        day_name = booking.created_at.strftime('%A')
        bookings_by_day[day_name] = bookings_by_day.get(day_name, 0) + 1
    
    # This month and last month stats
    start_of_month = today.replace(day=1)
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    
    this_month_bookings = Booking.objects.filter(
        created_at__date__gte=start_of_month
    ).count()
    
    this_month_confirmed = Booking.objects.filter(
        created_at__date__gte=start_of_month,
        status=BookingStatus.CONFIRMED
    ).count()
    
    this_month_pending = Booking.objects.filter(
        created_at__date__gte=start_of_month,
        status=BookingStatus.PENDING
    ).count()
    
    this_month_cancelled = Booking.objects.filter(
        created_at__date__gte=start_of_month,
        status=BookingStatus.CANCELLED
    ).count()
    
    last_month_bookings = Booking.objects.filter(
        created_at__date__gte=last_month_start,
        created_at__date__lt=start_of_month
    ).count()
    
    last_month_confirmed = Booking.objects.filter(
        created_at__date__gte=last_month_start,
        created_at__date__lt=start_of_month,
        status=BookingStatus.CONFIRMED
    ).count()
    
    last_month_pending = Booking.objects.filter(
        created_at__date__gte=last_month_start,
        created_at__date__lt=start_of_month,
        status=BookingStatus.PENDING
    ).count()
    
    last_month_cancelled = Booking.objects.filter(
        created_at__date__gte=last_month_start,
        created_at__date__lt=start_of_month,
        status=BookingStatus.CANCELLED
    ).count()
    
    booking_analytics = {
        'total_bookings': total,
        'confirmed_bookings': confirmed,
        'pending_bookings': pending,
        'cancelled_bookings': cancelled,
        'confirmed_percentage': round((confirmed / total) * 100, 1) if total > 0 else 0,
        'pending_percentage': round((pending / total) * 100, 1) if total > 0 else 0,
        'cancelled_percentage': round((cancelled / total) * 100, 1) if total > 0 else 0,
        'average_stay_days': avg_stay_days,
        'bookings_by_day': bookings_by_day,
        'this_month_bookings': this_month_bookings,
        'this_month_confirmed': this_month_confirmed,
        'this_month_pending': this_month_pending,
        'this_month_cancelled': this_month_cancelled,
        'last_month_bookings': last_month_bookings,
        'last_month_confirmed': last_month_confirmed,
        'last_month_pending': last_month_pending,
        'last_month_cancelled': last_month_cancelled,
    }
    
    context = {
        'booking_analytics': booking_analytics,
        'trend_chart_data': json.dumps(trend_chart_data),
    }
    
    return render(request, 'dashboard/booking_analytics.html', context)


def calculate_occupancy_rate():
    """Calculate current occupancy rate"""
    total_rooms = Room.objects.count()
    if total_rooms == 0:
        return 0
    
    today = timezone.now().date()
    occupied_rooms = Booking.objects.filter(
        check_in__lte=today,
        check_out__gte=today,
        status=BookingStatus.CONFIRMED
    ).values('room').distinct().count()
    
    occupancy_rate = (occupied_rooms / total_rooms) * 100
    return round(occupancy_rate, 2)


def get_most_booked_room():
    """Get the most booked room"""
    most_booked = Room.objects.annotate(
        booking_count=Count('bookings', filter=Q(
            bookings__status__in=[BookingStatus.CONFIRMED, BookingStatus.PENDING]
        ))
    ).order_by('-booking_count').first()
    
    return most_booked


def get_booking_trends(days=30):
    """Get booking trends for the last N days"""
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    bookings_by_date = []
    revenue_by_date = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        daily_bookings = Booking.objects.filter(
            created_at__date=current_date,
            status=BookingStatus.CONFIRMED
        ).count()
        
        daily_revenue = Booking.objects.filter(
            created_at__date=current_date,
            status=BookingStatus.CONFIRMED
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        bookings_by_date.append({
            'date': current_date.strftime('%b %d'),
            'count': daily_bookings,
        })
        
        revenue_by_date.append({
            'date': current_date.strftime('%b %d'),
            'amount': float(daily_revenue),
        })
    
    return {
        'bookings': bookings_by_date,
        'revenue': revenue_by_date,
    }


def get_room_statistics():
    """Get statistics per room"""
    rooms = Room.objects.annotate(
        booking_count=Count('bookings', filter=Q(
            bookings__status=BookingStatus.CONFIRMED
        )),
        total_revenue=Sum('bookings__total_price', filter=Q(
            bookings__status=BookingStatus.CONFIRMED
        )),
        occupancy_days=Sum(
            Case(
                When(
                    bookings__status=BookingStatus.CONFIRMED,
                    then=F('bookings__check_out') - F('bookings__check_in')
                ),
                default=0,
                output_field=IntegerField()
            )
        )
    ).order_by('-booking_count')
    
    room_stats = []
    for room in rooms:
        room_stats.append({
            'room': room,
            'booking_count': room.booking_count or 0,
            'total_revenue': room.total_revenue or 0,
            'occupancy_days': room.occupancy_days or 0,
        })
    
    return room_stats


def get_guest_statistics():
    """Get guest/user statistics"""
    total_guests = CustomUser.objects.filter(role='GUEST').count()
    admin_users = CustomUser.objects.filter(role='ADMIN').count()
    
    guests_with_bookings = CustomUser.objects.filter(
        bookings__status=BookingStatus.CONFIRMED
    ).distinct().count()
    
    return {
        'total_guests': total_guests,
        'admin_users': admin_users,
        'guests_with_bookings': guests_with_bookings,
        'guests_without_bookings': total_guests - guests_with_bookings,
    }


@login_required(login_url='login')
def dashboard_view(request):
    """Admin/User dashboard with statistics"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        from django.shortcuts import redirect
        return redirect('home')
    
    # Get all statistics
    booking_stats = get_booking_statistics()
    room_stats = get_room_statistics()
    guest_stats = get_guest_statistics()
    trends = get_booking_trends(days=30)
    
    # Get recent bookings
    recent_bookings = Booking.objects.select_related(
        'room', 'guest'
    ).order_by('-created_at')[:10]
    
    context = {
        'booking_stats': booking_stats,
        'room_stats': room_stats,
        'guest_stats': guest_stats,
        'trends': trends,
        'recent_bookings': recent_bookings,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required(login_url='login')
def revenue_analytics_view(request):
    """Detailed revenue analytics"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        from django.shortcuts import redirect
        return redirect('home')
    
    today = timezone.now().date()
    
    # Time period for analysis
    time_period = request.GET.get('period', '30')
    try:
        days = int(time_period)
    except (ValueError, TypeError):
        days = 30
    
    start_date = today - timedelta(days=days)
    
    # Revenue by day
    daily_revenue = []
    cumulative_revenue = 0
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        day_revenue = Booking.objects.filter(
            created_at__date=current_date,
            status=BookingStatus.CONFIRMED
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        cumulative_revenue += day_revenue
        
        daily_revenue.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'date_display': current_date.strftime('%b %d'),
            'revenue': float(day_revenue),
            'cumulative': float(cumulative_revenue),
        })
    
    # Revenue by room type
    revenue_by_type = Room.objects.annotate(
        total_revenue=Sum('bookings__total_price', filter=Q(
            bookings__created_at__date__gte=start_date,
            bookings__status=BookingStatus.CONFIRMED
        )),
        booking_count=Count('bookings', filter=Q(
            bookings__created_at__date__gte=start_date,
            bookings__status=BookingStatus.CONFIRMED
        ))
    ).values('room_type').annotate(
        total=Sum('total_revenue'),
        count=Sum('booking_count')
    ).order_by('-total')
    
    # Average booking value
    avg_booking = Booking.objects.filter(
        created_at__date__gte=start_date,
        status=BookingStatus.CONFIRMED
    ).aggregate(avg=Sum('total_price') / Count('id') if Count('id') > 0 else 0)['avg'] or 0
    
    context = {
        'daily_revenue': daily_revenue,
        'revenue_by_type': revenue_by_type,
        'avg_booking': float(avg_booking),
        'total_revenue': sum(d['revenue'] for d in daily_revenue),
        'time_period': time_period,
        'start_date': start_date,
        'end_date': today,
    }
    
    return render(request, 'dashboard/revenue_analytics.html', context)


@login_required(login_url='login')
def occupancy_analytics_view(request):
    """Occupancy analysis and room status"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        from django.shortcuts import redirect
        return redirect('home')
    
    today = timezone.now().date()
    
    # Time period
    time_period = request.GET.get('period', '30')
    try:
        days = int(time_period)
    except (ValueError, TypeError):
        days = 30
    
    start_date = today - timedelta(days=days)
    
    # Daily occupancy rate
    daily_occupancy = []
    total_rooms = Room.objects.count()
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        occupied_rooms = Booking.objects.filter(
            check_in__lte=current_date,
            check_out__gte=current_date,
            status=BookingStatus.CONFIRMED
        ).values('room').distinct().count()
        
        if total_rooms > 0:
            occupancy_rate = (occupied_rooms / total_rooms) * 100
        else:
            occupancy_rate = 0
        
        daily_occupancy.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'date_display': current_date.strftime('%b %d'),
            'occupied': occupied_rooms,
            'total': total_rooms,
            'available': total_rooms - occupied_rooms,
            'rate': round(occupancy_rate, 2),
        })
    
    # Room occupancy status
    room_occupancy = []
    for room in Room.objects.all():
        # Current occupancy
        is_occupied = Booking.objects.filter(
            room=room,
            check_in__lte=today,
            check_out__gte=today,
            status=BookingStatus.CONFIRMED
        ).exists()
        
        # Upcoming booking
        next_booking = Booking.objects.filter(
            room=room,
            check_in__gte=today,
            status=BookingStatus.CONFIRMED
        ).order_by('check_in').first()
        
        # Booking history (last 7 days)
        recent_bookings = Booking.objects.filter(
            room=room,
            check_out__gte=today - timedelta(days=7),
            check_in__lte=today,
            status=BookingStatus.CONFIRMED
        ).count()
        
        room_occupancy.append({
            'room': room,
            'is_occupied': is_occupied,
            'next_booking': next_booking,
            'recent_bookings': recent_bookings,
        })
    
    context = {
        'daily_occupancy': daily_occupancy,
        'room_occupancy': room_occupancy,
        'total_rooms': total_rooms,
        'current_occupancy_rate': calculate_occupancy_rate(),
        'time_period': time_period,
    }
    
    return render(request, 'dashboard/occupancy_analytics.html', context)


@login_required(login_url='login')
def booking_analytics_view(request):
    """Detailed booking analytics"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        from django.shortcuts import redirect
        return redirect('home')
    
    today = timezone.now().date()
    
    # Time period
    time_period = request.GET.get('period', '30')
    try:
        days = int(time_period)
    except (ValueError, TypeError):
        days = 30
    
    start_date = today - timedelta(days=days)
    
    # Daily bookings
    daily_bookings = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        created = Booking.objects.filter(
            created_at__date=current_date,
            status=BookingStatus.CONFIRMED
        ).count()
        
        checkins = Booking.objects.filter(
            check_in=current_date,
            status=BookingStatus.CONFIRMED
        ).count()
        
        checkouts = Booking.objects.filter(
            check_out=current_date,
            status=BookingStatus.CONFIRMED
        ).count()
        
        daily_bookings.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'date_display': current_date.strftime('%b %d'),
            'created': created,
            'checkins': checkins,
            'checkouts': checkouts,
        })
    
    # Booking status breakdown
    status_breakdown = Booking.objects.filter(
        created_at__date__gte=start_date
    ).values('status').annotate(count=Count('id')).order_by('-count')
    
    # Average stay duration
    avg_stay = Booking.objects.filter(
        created_at__date__gte=start_date,
        status=BookingStatus.CONFIRMED
    ).aggregate(
        avg_nights=Sum(F('check_out') - F('check_in'), output_field=IntegerField()) / 
                   Count('id') if Count('id') > 0 else 0
    )['avg_nights'] or 0
    
    context = {
        'daily_bookings': daily_bookings,
        'status_breakdown': status_breakdown,
        'avg_stay': round(float(avg_stay.total_seconds() / 86400), 2) if avg_stay else 0,
        'time_period': time_period,
    }
    
    return render(request, 'dashboard/booking_analytics.html', context)
