#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from authentication.models import Room

# Clear existing rooms
Room.objects.all().delete()

# Sample rooms data
rooms_data = [
    {
        'room_number': '101',
        'room_type': 'STANDARD',
        'description': 'Comfortable standard room with essential amenities. Features a cozy bed, modern bathroom, and convenient work desk. Perfect for solo travelers and couples.',
        'price_per_night': 150.00,
        'capacity': 2,
        'is_available': True,
        'amenities': 'WiFi, Air Conditioning, TV, Mini Bar, Safe, Work Desk'
    },
    {
        'room_number': '102',
        'room_type': 'STANDARD',
        'description': 'Comfortable standard room with essential amenities. Features a cozy bed, modern bathroom, and convenient work desk. Perfect for solo travelers and couples.',
        'price_per_night': 150.00,
        'capacity': 2,
        'is_available': True,
        'amenities': 'WiFi, Air Conditioning, TV, Mini Bar, Safe, Work Desk'
    },
    {
        'room_number': '201',
        'room_type': 'DELUXE',
        'description': 'Spacious deluxe room with premium furnishings and enhanced amenities. Features king-size bed, luxury bathroom, and premium toiletries. Perfect for business travelers and leisure guests.',
        'price_per_night': 250.00,
        'capacity': 2,
        'is_available': True,
        'amenities': 'WiFi, Air Conditioning, Smart TV, Mini Bar, Safe, Work Desk, Bathrobe, Premium Toiletries, Espresso Machine'
    },
    {
        'room_number': '202',
        'room_type': 'DELUXE',
        'description': 'Spacious deluxe room with premium furnishings and enhanced amenities. Features king-size bed, luxury bathroom with rainfall shower, and premium toiletries. Perfect for business travelers and leisure guests.',
        'price_per_night': 250.00,
        'capacity': 2,
        'is_available': True,
        'amenities': 'WiFi, Air Conditioning, Smart TV, Mini Bar, Safe, Work Desk, Bathrobe, Premium Toiletries, Espresso Machine'
    },
    {
        'room_number': '203',
        'room_type': 'DELUXE',
        'description': 'Spacious deluxe room with premium furnishings and enhanced amenities. Features king-size bed, city views, and premium bathroom. Perfect for business travelers and leisure guests.',
        'price_per_night': 250.00,
        'capacity': 3,
        'is_available': True,
        'amenities': 'WiFi, Air Conditioning, Smart TV, Mini Bar, Safe, Work Desk, Bathrobe, Premium Toiletries, Espresso Machine'
    },
    {
        'room_number': '301',
        'room_type': 'SUITE',
        'description': 'Luxurious suite with separate living area and bedroom. Features premium bathroom with jacuzzi, wine bar, and dedicated butler service for ultimate comfort.',
        'price_per_night': 450.00,
        'capacity': 4,
        'is_available': True,
        'amenities': 'WiFi, Air Conditioning, Smart TV, Wine Bar, Safe, Work Desk, Bathrobe, Premium Toiletries, Espresso Machine, Jacuzzi, Separate Living Area, Butler Service'
    },
    {
        'room_number': '302',
        'room_type': 'SUITE',
        'description': 'Executive suite with separate living area and bedroom. Features panoramic views, private balcony, luxury spa bath with jacuzzi, and dedicated butler service.',
        'price_per_night': 450.00,
        'capacity': 4,
        'is_available': True,
        'amenities': 'WiFi, Air Conditioning, Smart TV, Wine Bar, Safe, Work Desk, Bathrobe, Premium Toiletries, Espresso Machine, Jacuzzi, Separate Living Area, Butler Service'
    },
    {
        'room_number': '303',
        'room_type': 'SUITE',
        'description': 'Royal suite with master and guest bedrooms, separate living areas, and premium amenities. Includes jacuzzi, private chef access, and dedicated butler service.',
        'price_per_night': 550.00,
        'capacity': 6,
        'is_available': True,
        'amenities': 'WiFi, Air Conditioning, Smart TV, Wine Bar, Safe, Work Desk, Bathrobe, Premium Toiletries, Espresso Machine, Jacuzzi, Separate Living Areas, Butler Service, Private Chef Access'
    },
]

# Create rooms
created_count = 0
for room_data in rooms_data:
    room, created = Room.objects.get_or_create(
        room_number=room_data['room_number'],
        defaults=room_data
    )
    if created:
        created_count += 1
        print(f"✓ Created {room.get_room_type_display()} - Room {room.room_number} (${room.price_per_night}/night)")
    else:
        print(f"→ Room {room.room_number} already exists")

print(f"\n✅ Successfully created {created_count} sample rooms!")
print(f"📊 Total rooms in database: {Room.objects.count()}")
