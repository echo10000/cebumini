#!/usr/bin/env python
"""
Create a sample booking for TODAY so it appears on the staff dashboard
"""
import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import (
    Room, Booking, BookingStatus, CancellationPolicy, UserRole
)

User = get_user_model()

print("=" * 70)
print("CREATING TODAY'S BOOKING FOR STAFF DASHBOARD".center(70))
print("=" * 70)

today = timezone.now().date()
tomorrow = today + timedelta(days=1)

# Get or create a guest
guest_username = 'guest_john'
guest = User.objects.filter(username=guest_username).first()

if not guest:
    print(f"\n❌ Guest '{guest_username}' not found!")
    print("   Please run: python create_sample_accounts.py first")
    exit(1)

print(f"\n✓ Found guest: {guest.get_full_name()} ({guest.email})")

# Get a room
room = Room.objects.filter(is_available=True).first()

if not room:
    print("\n❌ No available rooms found!")
    print("   Please run: python create_sample_rooms.py first")
    exit(1)

print(f"✓ Found room: {room.room_number} - {room.room_type}")

# Delete any existing booking for this guest today
Booking.objects.filter(guest=guest, check_in=today).delete()

# Create booking for today
booking = Booking.objects.create(
    room=room,
    guest=guest,
    check_in=today,
    check_out=tomorrow,
    status=BookingStatus.CONFIRMED,
    cancellation_policy=CancellationPolicy.FREE,
    special_requests="Sample booking for testing staff dashboard",
)

# Calculate and save total price
booking.total_price = booking.calculate_total_price()
booking.save()

print(f"\n{'=' * 70}")
print("✅ BOOKING CREATED SUCCESSFULLY!".center(70))
print("=" * 70)
print(f"\nBooking Details:")
print(f"  • Booking ID: {booking.id}")
print(f"  • Guest: {guest.get_full_name()}")
print(f"  • Room: {room.room_number} ({room.room_type})")
print(f"  • Check-in: {today}")
print(f"  • Check-out: {tomorrow}")
print(f"  • Status: {booking.get_status_display()}")
print(f"  • Total Price: ₱{booking.total_price:.2f}")

print(f"\n📋 You should now see this booking in:")
print(f"   1. Staff Dashboard → Today's Check-ins")
print(f"   2. http://localhost:8000/staff/")
print(f"   3. Login with staff account (staff_emily / StaffPass123!)")
print("\n" + "=" * 70)
