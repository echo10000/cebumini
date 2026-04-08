#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from authentication.models import Room

# Room descriptions to update
room_updates = {
    '101': 'Comfortable standard room with essential amenities. Features a cozy bed, modern bathroom, and convenient work desk. Perfect for solo travelers and couples.',
    '102': 'Comfortable standard room with essential amenities. Features a cozy bed, modern bathroom, and convenient work desk. Perfect for solo travelers and couples.',
    '201': 'Spacious deluxe room with premium furnishings and enhanced amenities. Features king-size bed, luxury bathroom, and premium toiletries. Perfect for business travelers and leisure guests.',
    '202': 'Spacious deluxe room with premium furnishings and enhanced amenities. Features king-size bed, luxury bathroom with rainfall shower, and premium toiletries. Perfect for business travelers and leisure guests.',
    '203': 'Spacious deluxe room with premium furnishings and enhanced amenities. Features king-size bed, city views, and premium bathroom. Perfect for business travelers and leisure guests.',
    '301': 'Luxurious suite with separate living area and bedroom. Features premium bathroom with jacuzzi, wine bar, and dedicated butler service for ultimate comfort.',
    '302': 'Executive suite with separate living area and bedroom. Features panoramic views, private balcony, luxury spa bath with jacuzzi, and dedicated butler service.',
    '303': 'Royal suite with master and guest bedrooms, separate living areas, and premium amenities. Includes jacuzzi, private chef access, and dedicated butler service.',
}

# Update descriptions
updated_count = 0
for room_number, new_description in room_updates.items():
    try:
        room = Room.objects.get(room_number=room_number)
        room.description = new_description
        room.save()
        updated_count += 1
        print(f"✓ Updated Room {room_number} description")
    except Room.DoesNotExist:
        print(f"✗ Room {room_number} not found")

print(f"\n✅ Successfully updated {updated_count} room descriptions!")
