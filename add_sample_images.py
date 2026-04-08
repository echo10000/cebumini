"""
Script to add sample images to rooms using placeholder images
"""
import os
import sys
import django
from pathlib import Path
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.core.files.base import ContentFile
from authentication.models import Room, RoomImage
from django.core.files.storage import default_storage

# Sample image descriptions for different room types
ROOM_IMAGES = {
    'STANDARD': [
        'Standard room with comfortable bed and modern furniture',
        'Spacious bathroom with shower and amenities',
        'Window view of the city',
        'Bedroom lighting and room layout',
    ],
    'DELUXE': [
        'Deluxe room with premium bedding and elegant decor',
        'Luxurious bathroom with bathtub and shower',
        'Room seating area and entertainment',
        'Deluxe bathroom vanity and fixtures',
    ],
    'SUITE': [
        'Spacious suite with living area and bedroom',
        'Suite bathroom with jacuzzi bathtub',
        'Suite living room with comfortable seating',
        'Premium amenities and room service setup',
    ]
}

def create_placeholder_image(title, color=(73, 109, 137), size=(400, 300)):
    """Create a simple placeholder image with text"""
    # Create image
    img = Image.new('RGB', size, color=color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 32)
        small_font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw text
    text_color = (255, 255, 255)
    text_y = size[1] // 2 - 40
    
    # Check text size and adjust
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (size[0] - text_width) // 2
    
    draw.text((text_x, text_y), title, fill=text_color, font=font)
    draw.text((50, size[1] - 60), "Cebu Hotel", fill=text_color, font=small_font)
    
    return img

def add_sample_images():
    """Add sample images to all rooms"""
    rooms = Room.objects.all()
    
    if not rooms.exists():
        print("❌ No rooms found in the database.")
        print("Please create some rooms first using the admin interface or a management command.")
        return
    
    print(f"Found {rooms.count()} rooms. Adding sample images...\n")
    
    for room in rooms:
        print(f"Processing Room {room.room_number} ({room.get_room_type_display()})...")
        
        # Delete existing images if any
        room.images.all().delete()
        
        # Add main image
        if not room.image:
            color = {
                'STANDARD': (100, 140, 170),  # Blue-ish
                'DELUXE': (180, 100, 140),    # Purple-ish
                'SUITE': (100, 150, 100),     # Green-ish
            }.get(room.room_type, (100, 100, 100))
            
            img = create_placeholder_image(f"Room {room.room_number}", color=color)
            img_io = BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            
            room.image.save(f'room_{room.room_number}_main.png', ContentFile(img_io.getvalue()), save=True)
            print(f"  ✓ Added main image")
        
        # Add gallery images
        captions = ROOM_IMAGES.get(room.room_type, ROOM_IMAGES['STANDARD'])
        color = {
            'STANDARD': (100, 140, 170),
            'DELUXE': (180, 100, 140),
            'SUITE': (100, 150, 100),
        }.get(room.room_type, (100, 100, 100))
        
        for idx, caption in enumerate(captions):
            try:
                img = create_placeholder_image(f"View {idx + 1}", color=color, size=(400, 300))
                img_io = BytesIO()
                img.save(img_io, format='PNG')
                img_io.seek(0)
                
                room_image = RoomImage(
                    room=room,
                    caption=caption
                )
                room_image.image.save(
                    f'room_{room.room_number}_gallery_{idx}.png',
                    ContentFile(img_io.getvalue()),
                    save=True
                )
                print(f"  ✓ Added gallery image: {caption}")
            except Exception as e:
                print(f"  ❌ Error adding gallery image: {e}")
    
    print(f"\n✅ Sample images added successfully!")
    print(f"Total rooms processed: {rooms.count()}")

if __name__ == '__main__':
    try:
        add_sample_images()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
