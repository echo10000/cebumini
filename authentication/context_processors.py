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
