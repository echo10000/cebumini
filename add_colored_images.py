"""
Script to add colorful placeholder images to all rooms
"""
import os
import sys
import django
from PIL import Image, ImageDraw, ImageFont

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.core.files.base import ContentFile
from authentication.models import Room, RoomImage
from io import BytesIO

# Different colors for different room types
COLORS = {
    'STANDARD': [(100, 140, 170), (120, 160, 190), (80, 120, 150), (110, 150, 180)],
    'DELUXE': [(180, 100, 140), (200, 120, 160), (160, 80, 120), (190, 110, 150)],
    'SUITE': [(100, 150, 100), (120, 170, 120), (80, 130, 80), (110, 160, 110)]
}

CAPTIONS = {
    'STANDARD': [
        'Comfortable Bedroom',
        'Modern Bathroom',
        'City View',
        'Room Amenities'
    ],
    'DELUXE': [
        'Premium Bedroom',
        'Luxury Bathroom',
        'Sitting Area',
        'Entertainment Center'
    ],
    'SUITE': [
        'Spacious Living Area',
        'Master Bedroom',
        'Executive Suite',
        'Premium Bathroom'
    ]
}

def create_image(caption, color, width=400, height=300):
    """Create a colored image with text"""
    # Create image with solid color
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font
    try:
        font = ImageFont.truetype("arial.ttf", 36)
        small_font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
        small_font = font
    
    # Draw main caption
    text_color = (255, 255, 255)
    bbox = draw.textbbox((0, 0), caption, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    text_y = height // 2 - 40
    
    draw.text((text_x, text_y), caption, fill=text_color, font=font)
    
    # Draw hotel name at bottom
    draw.text((20, height - 40), "Cebu Hotel", fill=text_color, font=small_font)
    
    return img

def add_images():
    """Add images to all rooms"""
    rooms = Room.objects.all()
    
    if not rooms.exists():
        print("❌ No rooms found")
        return
    
    print(f"Adding images to {rooms.count()} rooms...\n")
    
    for room in rooms:
        print(f"Room {room.room_number}...")
        
        # Clear existing images
        room.images.all().delete()
        if room.image:
            room.image.delete()
        
        # Get colors and captions for this room type
        colors = COLORS.get(room.room_type, COLORS['STANDARD'])
        captions = CAPTIONS.get(room.room_type, CAPTIONS['STANDARD'])
        
        # Add main image
        img = create_image(captions[0], colors[0])
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        room.image.save(
            f'room_{room.room_number}_main.png',
            ContentFile(img_io.getvalue()),
            save=True
        )
        print(f"  ✓ Main: {captions[0]}")
        
        # Add gallery images
        for idx, (caption, color) in enumerate(zip(captions[1:], colors[1:]), 1):
            img = create_image(caption, color)
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
            print(f"  ✓ Gallery: {caption}")
    
    print(f"\n✅ Done! All rooms now have images.")

if __name__ == '__main__':
    try:
        add_images()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
