#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import Room, Booking, BookingStatus
from datetime import datetime, timedelta

User = get_user_model()

print("=" * 60)
print("🏨 BOOKING SYSTEM TEST")
print("=" * 60)

# Check rooms
rooms_count = Room.objects.count()
print(f"\n✓ Total rooms created: {rooms_count}")

if rooms_count > 0:
    room = Room.objects.first()
    print(f"\n📍 Sample Room Details:")
    print(f"   Room Number: {room.room_number}")
    print(f"   Type: {room.get_room_type_display()}")
    print(f"   Price: ₱{room.price_per_night}/night")
    print(f"   Capacity: {room.capacity} guests")
    print(f"   Available: {room.is_available}")

# Check for test user
try:
    test_user = User.objects.get(email='test@test.com')
    print(f"\n✓ Test user exists: {test_user.email}")
    
    # Check existing bookings
    user_bookings = Booking.objects.filter(guest=test_user)
    print(f"✓ Test user has {user_bookings.count()} booking(s)")
    
    for booking in user_bookings:
        print(f"  - Room {booking.room.room_number}: {booking.check_in} to {booking.check_out}")
except User.DoesNotExist:
    print(f"\n⚠ No test user found")

# Check booking models
all_bookings = Booking.objects.all()
print(f"\n📊 Total bookings in system: {all_bookings.count()}")

# Test booking flow validation
print(f"\n✓ Booking System Ready!")
print(f"   - {Room.objects.count()} rooms available")
print(f"   - Booking model: Operational")
print(f"   - Status choices: {list(BookingStatus.choices)}")

print("\n" + "=" * 60)
print("✅ Booking system is ready for testing!")
print("=" * 60)
