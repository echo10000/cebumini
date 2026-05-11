"""
Context processors for authentication app
"""

def guest_notifications(request):
    """
    Add guest notification context to all templates
    Shows unread/unreplied messages for logged-in users
    """
    context = {
        'guest_unread_replies': 0,
        'guest_has_notifications': False,
    }
    
    if request.user.is_authenticated:
        from .models import ContactMessage
        
        # Count messages with unread replies (is_replied=True, notification_sent=False)
        unread_replies = ContactMessage.objects.filter(
            guest=request.user,
            is_replied=True,
            notification_sent=False
        ).count()
        
        context['guest_unread_replies'] = unread_replies
        context['guest_has_notifications'] = unread_replies > 0
    
    return context


def echo_chatbot_context(request):
    """Add small guest booking hints for Echo's client-side quick replies."""
    context = {
        'echo_booking_status_text': '',
        'echo_booking_detail_url': '',
        'echo_cancel_help_url': '',
        'echo_receipt_url': '',
    }

    if not request.user.is_authenticated:
        return context

    if request.user.is_manager() or request.user.is_staff_member() or request.user.is_admin():
        return context

    from django.urls import reverse
    from .models import Booking, BookingStatus

    booking = (
        Booking.objects
        .filter(
            guest=request.user,
            status__in=[
                BookingStatus.PENDING,
                BookingStatus.CONFIRMED,
                BookingStatus.CHECKED_IN,
            ]
        )
        .select_related('room')
        .order_by('-created_at')
        .first()
    )

    if not booking:
        booking = (
            Booking.objects
            .filter(guest=request.user)
            .select_related('room')
            .order_by('-created_at')
            .first()
        )

    if booking:
        context['echo_booking_status_text'] = (
            f"Your latest booking is #{booking.id} for Room {booking.room.room_number}. "
            f"Status: {booking.get_status_display()}. "
            f"Stay dates: {booking.check_in:%b %d, %Y} to {booking.check_out:%b %d, %Y}."
        )
        detail_url = reverse('bookings:booking_detail', args=[booking.id])
        context['echo_booking_detail_url'] = detail_url
        context['echo_cancel_help_url'] = detail_url if booking.can_be_cancelled() else reverse('bookings:booking_history')
        context['echo_receipt_url'] = reverse('bookings:booking_pdf', args=[booking.id])
    else:
        context['echo_booking_status_text'] = 'You do not have any bookings yet. Browse rooms to start a reservation.'
        context['echo_cancel_help_url'] = reverse('rooms:list')

    return context
