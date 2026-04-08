"""
Test Script for Smart Room Recommendation System
Run this in Django shell: python manage.py shell < test_recommendations.py
"""

from authentication.models import User, Room, Booking, BookingStatus
from authentication.recommendation_engine import RoomRecommendationEngine
from authentication.views_recommendations import get_recommendations_context
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

def test_recommendation_engine():
    """Test the core recommendation engine"""
    print("\n" + "="*60)
    print("TEST 1: Core Recommendation Engine")
    print("="*60)
    
    # Find or create test user
    user, created = User.objects.get_or_create(
        username='test_recommendations',
        defaults={'email': 'test@recommendations.com'}
    )
    print(f"✓ Test user: {user.username} {'(created)' if created else '(existing)'}")
    
    # Check if user has bookings
    booking_count = Booking.objects.filter(guest=user).count()
    print(f"✓ User has {booking_count} bookings")
    
    if booking_count == 0:
        print("⚠ No bookings found - creating test bookings...")
        # Create test bookings
        confirmed_status = BookingStatus.objects.get_or_create(
            status='CONFIRMED',
            defaults={'description': 'Booking confirmed'}
        )[0]
        
        rooms = Room.objects.all()[:3]
        for i, room in enumerate(rooms):
            booking = Booking.objects.create(
                guest=user,
                room=room,
                check_in=datetime.now() + timedelta(days=i*10),
                check_out=datetime.now() + timedelta(days=i*10+3),
                total_price=room.price_per_night * 3,
                status='CONFIRMED'
            )
            print(f"  ✓ Created booking: {booking.room.room_number}")
    
    # Test engine
    print("\nTesting RoomRecommendationEngine...")
    engine = RoomRecommendationEngine(user)
    
    # Get user profile
    profile = engine.get_user_profile()
    print(f"\n✓ User Profile:")
    print(f"  - Total bookings: {profile['total_bookings']}")
    print(f"  - Total spent: ₱{profile['total_spent']}")
    print(f"  - Average price: ₱{profile['average_price']:.2f}")
    print(f"  - Average duration: {profile['average_duration']} nights")
    print(f"  - Favorite room type: {profile.get('favorite_room_type', 'N/A')}")
    
    # Get recommendations
    recommendations = engine.get_recommendations_with_details(limit=3)
    print(f"\n✓ Recommendations generated: {len(recommendations)}")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n  Recommendation {i}:")
        print(f"    - Room: {rec['room_number']}")
        print(f"    - Type: {rec['room_type']}")
        print(f"    - Price: ₱{rec['price_per_night']}")
        print(f"    - Match Score: {rec['match_score']}%")
        print(f"    - Reason: {rec['reason']}")
    
    return True


def test_new_user_fallback():
    """Test fallback for users with no booking history"""
    print("\n" + "="*60)
    print("TEST 2: New User Fallback (Popular Rooms)")
    print("="*60)
    
    # Create new user with no bookings
    user, created = User.objects.get_or_create(
        username='new_user_test',
        defaults={'email': 'newuser@test.com'}
    )
    print(f"✓ New user: {user.username} {'(created)' if created else '(existing)'}")
    
    # Delete any existing bookings
    Booking.objects.filter(guest=user).delete()
    print("✓ Cleared all bookings for new user")
    
    # Test engine
    engine = RoomRecommendationEngine(user)
    profile = engine.get_user_profile()
    print(f"\n✓ User Profile (empty):")
    print(f"  - Total bookings: {profile['total_bookings']}")
    
    # Get recommendations (should be popular rooms)
    recommendations = engine.get_recommendations(limit=3)
    print(f"\n✓ Fallback recommendations (popular rooms): {len(recommendations)}")
    for i, room in enumerate(recommendations, 1):
        print(f"  {i}. {room.room_number} - {room.get_room_type_display()} (₱{room.price_per_night})")
    
    return True


def test_scoring_algorithm():
    """Test the similarity scoring algorithm"""
    print("\n" + "="*60)
    print("TEST 3: Similarity Scoring Algorithm")
    print("="*60)
    
    user, _ = User.objects.get_or_create(
        username='score_test_user',
        defaults={'email': 'scoretest@test.com'}
    )
    
    engine = RoomRecommendationEngine(user)
    profile = engine.get_user_profile()
    
    # Get a sample room
    room = Room.objects.first()
    if room:
        score = engine.calculate_similarity_score(room, profile)
        print(f"✓ Sample room: {room.room_number}")
        print(f"  - Type: {room.get_room_type_display()}")
        print(f"  - Price: ₱{room.price_per_night}")
        print(f"  - Capacity: {room.capacity}")
        print(f"  - Similarity Score: {score:.1f}%")
    else:
        print("⚠ No rooms available for scoring test")
    
    return True


def test_multiple_room_types():
    """Test recommendations with varied room types"""
    print("\n" + "="*60)
    print("TEST 4: Multiple Room Types")
    print("="*60)
    
    user, created = User.objects.get_or_create(
        username='multiroom_test',
        defaults={'email': 'multiroom@test.com'}
    )
    print(f"✓ Test user: {user.username}")
    
    # Clear existing bookings
    Booking.objects.filter(guest=user).delete()
    
    # Create bookings with different room types
    rooms_by_type = Room.objects.values('room_type').distinct()
    confirmed_status = BookingStatus.objects.get_or_create(
        status='CONFIRMED',
        defaults={'description': 'Booking confirmed'}
    )[0]
    
    print(f"\n✓ Creating bookings for different room types...")
    rooms = Room.objects.order_by('room_type').distinct('room_type')[:3]
    for i, room in enumerate(rooms):
        Booking.objects.create(
            guest=user,
            room=room,
            check_in=datetime.now() + timedelta(days=i*5),
            check_out=datetime.now() + timedelta(days=i*5+2),
            total_price=room.price_per_night * 2,
            status='CONFIRMED'
        )
        print(f"  ✓ {room.get_room_type_display()} booked")
    
    # Get recommendations
    engine = RoomRecommendationEngine(user)
    profile = engine.get_user_profile()
    print(f"\n✓ User preferences:")
    print(f"  - Favorite type: {profile.get('favorite_room_type', 'N/A')}")
    print(f"  - Room types booked: {profile['room_types']}")
    
    recommendations = engine.get_recommendations_with_details(limit=3)
    print(f"\n✓ Recommendations based on diverse history:")
    for rec in recommendations:
        print(f"  - {rec['room_type']}: {rec['match_score']}%")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# SMART ROOM RECOMMENDATION SYSTEM - TEST SUITE")
    print("#"*60)
    
    tests = [
        ("Core Engine", test_recommendation_engine),
        ("New User Fallback", test_new_user_fallback),
        ("Scoring Algorithm", test_scoring_algorithm),
        ("Multiple Room Types", test_multiple_room_types),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"\n✗ TEST FAILED: {test_name}")
            print(f"  Error: {str(e)}")
            results.append((test_name, "ERROR"))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, status in results:
        symbol = "✓" if status == "PASS" else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print("\n" + "#"*60)
    print("# TEST SUITE COMPLETE")
    print("#"*60 + "\n")


if __name__ == '__main__':
    run_all_tests()
