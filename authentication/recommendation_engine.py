"""
Smart Room Recommendation Engine
Analyzes user booking history and suggests personalized room recommendations
"""

import pandas as pd
import numpy as np
from django.db.models import Avg, Count, Q
from datetime import timedelta
from .models import Booking, Room, BookingStatus, RoomType, CustomUser


class RoomRecommendationEngine:
    """Recommendation engine for personalized room suggestions"""
    
    def __init__(self, user):
        """Initialize with user"""
        self.user = user
        self.user_bookings = None
        self.all_bookings = None
        
    def get_user_profile(self):
        """Extract user's booking preferences from history"""
        # Get user's confirmed bookings
        user_bookings = Booking.objects.filter(
            guest=self.user,
            status=BookingStatus.CONFIRMED
        ).select_related('room')
        
        if not user_bookings.exists():
            return None
        
        profile = {
            'favorite_room_type': None,
            'average_price': 0,
            'average_stay_duration': 0,
            'price_range': {'min': float('inf'), 'max': 0},
            'booking_count': 0,
            'room_types_booked': set(),
            'total_spent': 0,
        }
        
        stay_durations = []
        prices = []
        
        for booking in user_bookings:
            # Calculate stay duration
            duration = (booking.check_out - booking.check_in).days
            stay_durations.append(duration)
            
            # Get room price
            price = float(booking.room.price_per_night)
            prices.append(price)
            
            # Track room type
            profile['room_types_booked'].add(booking.room.room_type)
            
            # Track spending
            profile['total_spent'] += float(booking.total_price)
            
            profile['booking_count'] += 1
        
        # Calculate averages
        if prices:
            profile['average_price'] = np.mean(prices)
            profile['price_range']['min'] = np.min(prices)
            profile['price_range']['max'] = np.max(prices)
        
        if stay_durations:
            profile['average_stay_duration'] = np.mean(stay_durations)
        
        # Find favorite room type (most booked)
        if profile['room_types_booked']:
            type_counts = {}
            for booking in user_bookings:
                rt = booking.room.room_type
                type_counts[rt] = type_counts.get(rt, 0) + 1
            profile['favorite_room_type'] = max(type_counts, key=type_counts.get)
        
        return profile
    
    def calculate_similarity_score(self, room, user_profile):
        """Calculate how similar a room is to user's preferences"""
        if not user_profile:
            return 0
        
        score = 0.0
        max_score = 0.0
        
        # 1. Room Type Match (40% weight)
        if room.room_type in user_profile['room_types_booked']:
            score += 40
            max_score += 40
            
            # Bonus if it's the favorite type
            if room.room_type == user_profile['favorite_room_type']:
                score += 10
            max_score += 10
        else:
            max_score += 50
        
        # 2. Price Similarity (40% weight)
        avg_price = user_profile['average_price']
        room_price = float(room.price_per_night)
        
        if avg_price > 0:
            price_diff = abs(room_price - avg_price)
            # Allow 30% variance
            if price_diff <= avg_price * 0.3:
                score += 40
            elif price_diff <= avg_price * 0.6:
                score += 20
            else:
                score += 0
        
        max_score += 40
        
        # 3. Availability & Quality (20% weight)
        if room.is_available:
            score += 10
        
        # Higher capacity rooms slightly preferred (more value)
        if room.capacity >= 3:
            score += 10
        
        max_score += 20
        
        # Normalize to 0-100
        if max_score > 0:
            return (score / max_score) * 100
        return 0
    
    def get_recommendations(self, exclude_room_id=None, limit=3):
        """Get personalized room recommendations for user"""
        # Get user profile
        user_profile = self.get_user_profile()
        
        if not user_profile:
            # No booking history, return random popular rooms
            return self._get_popular_rooms(limit=limit, exclude_room_id=exclude_room_id)
        
        # Get all available rooms
        rooms = Room.objects.filter(is_available=True)
        
        if exclude_room_id:
            rooms = rooms.exclude(id=exclude_room_id)
        
        # Calculate similarity scores
        recommendations = []
        
        for room in rooms:
            score = self.calculate_similarity_score(room, user_profile)
            
            recommendations.append({
                'room': room,
                'score': score,
                'reason': self._get_recommendation_reason(room, user_profile),
            })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N
        return recommendations[:limit]
    
    def get_recommendations_with_details(self, exclude_room_id=None, limit=3):
        """Get recommendations with additional details"""
        recommendations = self.get_recommendations(
            exclude_room_id=exclude_room_id,
            limit=limit
        )
        
        detailed_recommendations = []
        
        for rec in recommendations:
            room = rec['room']
            
            # Get booking statistics for this room
            room_bookings = Booking.objects.filter(
                room=room,
                status=BookingStatus.CONFIRMED
            )
            
            booking_count = room_bookings.count()
            
            detailed_recommendations.append({
                'room': room,
                'score': round(rec['score'], 1),
                'reason': rec['reason'],
                'booking_count': booking_count,
                'popularity': self._get_popularity_label(booking_count),
            })
        
        return detailed_recommendations
    
    def _get_recommendation_reason(self, room, user_profile):
        """Generate human-readable reason for recommendation"""
        reasons = []
        
        # Room type match
        if room.room_type in user_profile['room_types_booked']:
            if room.room_type == user_profile['favorite_room_type']:
                reasons.append("Your favorite room type")
            else:
                reasons.append("Similar to rooms you've booked")
        
        # Price match
        avg_price = user_profile['average_price']
        room_price = float(room.price_per_night)
        
        if avg_price > 0:
            price_diff_pct = abs(room_price - avg_price) / avg_price * 100
            if price_diff_pct <= 15:
                reasons.append("Your typical price range")
            elif price_diff_pct <= 30:
                reasons.append("Similar to prices you've paid")
        
        # Availability
        if len(reasons) == 0:
            reasons.append("Available for your dates")
        
        return " • ".join(reasons)
    
    def _get_popularity_label(self, booking_count):
        """Get popularity label based on booking count"""
        if booking_count >= 10:
            return "Very Popular"
        elif booking_count >= 5:
            return "Popular"
        elif booking_count >= 2:
            return "Somewhat Popular"
        else:
            return "New"
    
    def _get_popular_rooms(self, limit=3, exclude_room_id=None):
        """Get most popular rooms when user has no booking history"""
        rooms = Room.objects.filter(is_available=True)
        
        if exclude_room_id:
            rooms = rooms.exclude(id=exclude_room_id)
        
        # Annotate with booking count
        rooms_with_count = rooms.annotate(
            booking_count=Count('bookings', filter=Q(
                bookings__status=BookingStatus.CONFIRMED
            ))
        ).order_by('-booking_count', '-id')[:limit]
        
        recommendations = []
        
        for room in rooms_with_count:
            recommendations.append({
                'room': room,
                'score': 50.0,  # Default score for new users
                'reason': "Most popular with our guests",
            })
        
        return recommendations


def get_room_recommendations(user, exclude_room_id=None, limit=3):
    """
    Convenience function to get recommendations for a user
    
    Args:
        user: CustomUser instance
        exclude_room_id: Room ID to exclude from recommendations
        limit: Number of recommendations to return
    
    Returns:
        List of recommendation dicts with room, score, reason
    """
    engine = RoomRecommendationEngine(user)
    return engine.get_recommendations_with_details(
        exclude_room_id=exclude_room_id,
        limit=limit
    )


def analyze_booking_patterns(user):
    """
    Analyze booking patterns for a specific user
    
    Returns:
        Dictionary with user's booking preferences
    """
    engine = RoomRecommendationEngine(user)
    profile = engine.get_user_profile()
    
    if not profile:
        return {
            'booking_count': 0,
            'total_spent': 0,
            'average_price': 0,
            'average_stay_duration': 0,
            'favorite_room_type': None,
        }
    
    return {
        'booking_count': profile['booking_count'],
        'total_spent': profile['total_spent'],
        'average_price': round(profile['average_price'], 2),
        'average_stay_duration': round(profile['average_stay_duration'], 1),
        'favorite_room_type': profile['favorite_room_type'],
        'room_types_booked': list(profile['room_types_booked']),
        'price_range': profile['price_range'],
    }


def get_similar_rooms(room, user=None, limit=3):
    """
    Get rooms similar to a given room
    
    Args:
        room: Room instance
        user: Optional CustomUser for personalization
        limit: Number of similar rooms to return
    
    Returns:
        List of similar rooms
    """
    if not user:
        # Return rooms of same type with similar price
        similar_rooms = Room.objects.filter(
            room_type=room.room_type,
            is_available=True
        ).exclude(id=room.id).annotate(
            price_diff=Abs(
                F('price_per_night') - room.price_per_night
            )
        ).order_by('price_diff')[:limit]
        
        return list(similar_rooms)
    
    # Use recommendation engine for personalized similar rooms
    engine = RoomRecommendationEngine(user)
    recommendations = engine.get_recommendations(
        exclude_room_id=room.id,
        limit=limit
    )
    
    return recommendations
