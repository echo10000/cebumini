#!/usr/bin/env python
"""
Script to create 5 sample guest accounts with bookings checking in today
Run with: python manage.py shell < create_sample_guests.py
"""

import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.utils import timezone
from authentication.models import CustomUser, UserRole, Booking, BookingStatus, Room, CancellationPolicy

# Sample guest data
guests_data = [
    {
        'username': 'john_smith',
        'email': 'john.smith@email.com',
        'first_name': 'John',
        'last_name': 'Smith',
        'phone_number': '+63-9123456789',
    },
    {
        'username': 'maria_garcia',
        'email': 'maria.garcia@email.com',
        'first_name': 'Maria',
        'last_name': 'Garcia',
        'phone_number': '+63-9198765432',
    },
    {
        'username': 'alex_johnson',
        'email': 'alex.johnson@email.com',
        'first_name': 'Alex',
        'last_name': 'Johnson',
        'phone_number': '+63-9112345678',
    },
    {
        'username': 'sophia_williams',
        'email': 'sophia.williams@email.com',
        'first_name': 'Sophia',
        'last_name': 'Williams',
        'phone_number': '+63-9187654321',
    },
    {
        'username': 'david_brown',
        'email': 'david.brown@email.com',
        'first_name': 'David',
        'last_name': 'Brown',
        'phone_number': '+63-9143219876',
    },
]

# Get available rooms (pick first 5 or create rooms if needed)
rooms = Room.objects.all()[:5]
if rooms.count() < 5:
    print(f"⚠️  Warning: Only {rooms.count()} rooms available. Need at least 5 rooms.")
    print("Creating sample rooms...")
    for i in range(5 - rooms.count()):
        room = Room.objects.create(
            room_number=f"SAMPLE{i+1:03d}",
            room_type='STANDARD',
            price_per_night=3000.00,
            capacity=2,
            is_available=True,
        )
        rooms = rooms | Room.objects.filter(id=room.id)

# Create guests and bookings
today = timezone.now().date()
tomorrow = today + timedelta(days=1)
checkout_date = today + timedelta(days=3)

created_count = 0
existing_count = 0

for idx, guest_data in enumerate(guests_data):
    # Check if user already exists
    if CustomUser.objects.filter(username=guest_data['username']).exists():
        user = CustomUser.objects.get(username=guest_data['username'])
        existing_count += 1
        print(f"✓ Guest {idx+1}: {user.first_name} {user.last_name} (already exists)")
    else:
        # Create guest user
        user = CustomUser.objects.create_user(
            username=guest_data['username'],
            email=guest_data['email'],
            first_name=guest_data['first_name'],
            last_name=guest_data['last_name'],
            phone_number=guest_data['phone_number'],
            password='TempPassword123!',
            role=UserRole.GUEST,
            is_email_verified=True,
            is_active=True,
        )
        user.accept_terms('1.0')
        created_count += 1
        print(f"✓ Guest {idx+1}: {user.first_name} {user.last_name} created")

    # Create booking for today
    room = list(rooms)[idx]
    
    # Check if booking already exists for this guest today
    existing_booking = Booking.objects.filter(
        guest=user,
        check_in=today,
        room=room
    ).exists()
    
    if not existing_booking:
        booking = Booking.objects.create(
            room=room,
            guest=user,
            check_in=today,
            check_out=checkout_date,
            total_price=(checkout_date - today).days * room.price_per_night,
            status=BookingStatus.CONFIRMED,
            cancellation_policy=CancellationPolicy.FREE,
            booking_reference=Booking.create_unique_booking_reference(),
            special_requests='Sample booking for testing',
        )
        print(f"  📅 Booking created: Room {room.room_number} | Ref: {booking.booking_reference}")
    else:
        print(f"  📅 Booking already exists for today")

print(f"\n✅ Sample Data Created Successfully!")
print(f"   Created: {created_count} new guests")
print(f"   Existing: {existing_count} guests")
print(f"   Total bookings for today: 5")
print(f"\n📝 Check-in Details:")
print(f"   Check-in Date: {today}")
print(f"   Check-out Date: {checkout_date}")
print(f"   Default Password: TempPassword123!")
