"""
Views for room recommendations
Provides recommendation endpoints and helper functions
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Room, Booking
from .recommendation_engine import (
    get_room_recommendations,
    analyze_booking_patterns,
    get_similar_rooms,
)


@login_required(login_url='login')
@require_http_methods(["GET"])
def get_user_recommendations(request):
    """
    Get personalized room recommendations for logged-in user
    Returns JSON response
    """
    user = request.user
    limit = int(request.GET.get('limit', 3))
    exclude_room_id = request.GET.get('exclude_room_id', None)
    
    recommendations = get_room_recommendations(
        user=user,
        exclude_room_id=exclude_room_id,
        limit=limit
    )
    
    # Format for JSON response
    data = {
        'recommendations': [],
        'user_profile': analyze_booking_patterns(user),
    }
    
    for rec in recommendations:
        room = rec['room']
        data['recommendations'].append({
            'id': room.id,
            'room_number': room.room_number,
            'room_type': room.get_room_type_display(),
            'price_per_night': float(room.price_per_night),
            'capacity': room.capacity,
            'score': rec['score'],
            'reason': rec['reason'],
            'popularity': rec.get('popularity', 'Popular'),
            'booking_count': rec.get('booking_count', 0),
        })
    
    return JsonResponse(data)


@login_required(login_url='login')
def user_booking_profile(request):
    """View user's booking profile and preferences"""
    user = request.user
    profile = analyze_booking_patterns(user)
    
    # Get user's booking history
    bookings = Booking.objects.filter(
        guest=user
    ).select_related('room').order_by('-created_at')[:5]
    
    context = {
        'profile': profile,
        'bookings': bookings,
        'has_history': profile['booking_count'] > 0,
    }
    
    return render(request, 'recommendations/user_profile.html', context)


@login_required(login_url='login')
def room_recommendations_page(request):
    """Dedicated page for viewing all recommendations"""
    user = request.user
    limit = int(request.GET.get('limit', 5))
    
    recommendations = get_room_recommendations(user=user, limit=limit)
    profile = analyze_booking_patterns(user)
    
    context = {
        'recommendations': recommendations,
        'profile': profile,
        'has_history': profile['booking_count'] > 0,
        'total_recommendations': len(recommendations),
    }
    
    return render(request, 'recommendations/recommendations.html', context)


def get_recommendations_context(request, exclude_room_id=None, limit=3):
    """
    Helper function to get recommendations context for templates
    Used in other views to include recommendations
    """
    if not request.user.is_authenticated:
        return {
            'recommendations': [],
            'has_recommendations': False,
        }
    
    raw_recommendations = get_room_recommendations(
        user=request.user,
        exclude_room_id=exclude_room_id,
        limit=limit
    )
    
    # Serialize recommendations to avoid template rendering issues
    # Convert Django ORM objects to simple dictionaries
    serialized_recommendations = []
    for rec in raw_recommendations:
        room = rec['room']
        serialized_recommendations.append({
            'room': {
                'id': room.id,
                'room_number': room.room_number,
                'room_type': room.room_type,
                'room_type_display': room.get_room_type_display(),
                'price_per_night': float(room.price_per_night),
                'capacity': room.capacity,
                'is_available': room.is_available,
                'description': room.description,
            },
            'score': round(rec['score'], 1),
            'reason': rec['reason'],
            'booking_count': rec.get('booking_count', 0),
            'popularity': rec.get('popularity', 'New'),
        })
    
    return {
        'recommendations': serialized_recommendations,
        'has_recommendations': len(serialized_recommendations) > 0,
    }
