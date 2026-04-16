#!/usr/bin/env python
"""
Create sample rooms for testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from authentication.models import Room, RoomType

# Delete existing rooms
Room.objects.all().delete()

# Create sample rooms
rooms_data = [
    {
        'room_number': '101',
        'description': 'Spacious room with stunning ocean views, perfect for a romantic getaway.',
        'room_type': RoomType.DELUXE,
        'capacity': 2,
        'price_per_night': 3500.00,
        'amenities': 'WiFi, Air Conditioning, TV, Mini Bar, Safe, Ocean View',
        'is_available': True,
    },
    {
        'room_number': '102',
        'description': 'Comfortable and affordable room with all essential amenities.',
        'room_type': RoomType.STANDARD,
        'capacity': 2,
        'price_per_night': 1500.00,
        'amenities': 'WiFi, Air Conditioning, TV, Safe',
        'is_available': True,
    },
    {
        'room_number': '201',
        'description': 'Luxurious suite with separate living area and premium amenities.',
        'room_type': RoomType.SUITE,
        'capacity': 4,
        'price_per_night': 5500.00,
        'amenities': 'WiFi, Air Conditioning, TV, Mini Bar, Safe, Living Area',
        'is_available': True,
    },
    {
        'room_number': '103',
        'description': 'Cozy and economical room with basic amenities.',
        'room_type': RoomType.STANDARD,
        'capacity': 1,
        'price_per_night': 1200.00,
        'amenities': 'WiFi, Air Conditioning',
        'is_available': True,
    },
    {
        'room_number': '202',
        'description': 'Spacious deluxe suite with multiple beds and premium amenities.',
        'room_type': RoomType.DELUXE,
        'capacity': 3,
        'price_per_night': 4500.00,
        'amenities': 'WiFi, Air Conditioning, TV, Mini Bar, Safe, Balcony',
        'is_available': True,
    },
    {
        'room_number': '203',
        'description': 'Executive room with business amenities and premium services.',
        'room_type': RoomType.SUITE,
        'capacity': 2,
        'price_per_night': 5000.00,
        'amenities': 'WiFi, Air Conditioning, TV, Mini Bar, Safe, Work Desk',
        'is_available': True,
    },
]

created_count = 0
for room_data in rooms_data:
    room = Room.objects.create(**room_data)
    created_count += 1
    print(f"✓ Created: Room {room.room_number} ({room.get_room_type_display()}) - ₱{room.price_per_night}")

print(f"\n✓ Successfully created {created_count} rooms!")
