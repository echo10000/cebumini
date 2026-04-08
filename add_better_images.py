"""
Script to add realistic sample images to rooms using placeholder service
"""
import os
import sys
import django
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.core.files.base import ContentFile
from authentication.models import Room, RoomImage

# Room image descriptions and placeholder URLs
ROOM_IMAGES = {
    'STANDARD': [
        ('Standard Room with Queen Bed', 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=400&h=300&fit=crop'),
        ('Modern Bathroom', 'https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=300&fit=crop'),
        ('City View from Window', 'https://images.unsplash.com/photo-1516455590570-61b3b8b8b9b4?w=400&h=300&fit=crop'),
        ('Room Amenities Setup', 'https://images.unsplash.com/photo-1618883182384-a83a8e7b9b47?w=400&h=300&fit=crop'),
    ],
    'DELUXE': [
        ('Deluxe Room with Premium Furnishings', 'https://images.unsplash.com/photo-1578926314433-8471404f186f?w=400&h=300&fit=crop'),
        ('Luxury Bathroom with Jacuzzi', 'https://images.unsplash.com/photo-1552856521-b06e0bc86e8d?w=400&h=300&fit=crop'),
        ('Deluxe Room Seating Area', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400&h=300&fit=crop'),
        ('Premium In-Room Entertainment', 'https://images.unsplash.com/photo-1598928506323-37ba7dda89e6?w=400&h=300&fit=crop'),
    ],
    'SUITE': [
        ('Spacious Suite Living Area', 'https://images.unsplash.com/photo-1614162692292-7ac56d7f7f1e?w=400&h=300&fit=crop'),
        ('Suite Bedroom with King Bed', 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=400&h=300&fit=crop'),
        ('Executive Suite Sitting Area', 'https://images.unsplash.com/photo-1579634874568-bc348c19f250?w=400&h=300&fit=crop'),
        ('Suite Luxury Bathroom', 'https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=300&fit=crop'),
    ]
}

def create_simple_image(caption, width=400, height=300):
    """Create a simple placeholder image with text when URL fails"""
    img = Image.new('RGB', (width, height), color=(73, 109, 137))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 28)
        small_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw text
    text_color = (255, 255, 255)
    bbox = draw.textbbox((0, 0), caption, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    
    draw.text((text_x, height // 2 - 30), caption, fill=text_color, font=font)
    draw.text((20, height - 50), "Cebu Hotel", fill=text_color, font=small_font)
    
    return img

def download_image(url):
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"    ⚠️ Could not download from URL, using placeholder: {str(e)[:50]}")
        return None

def add_sample_images():
    """Add sample images to all rooms"""
    rooms = Room.objects.all()
    
    if not rooms.exists():
        print("❌ No rooms found in the database.")
        return
    
    print(f"Found {rooms.count()} rooms. Adding realistic sample images...\n")
    
    for room in rooms:
        print(f"Processing Room {room.room_number} ({room.get_room_type_display()})...")
        
        # Delete existing images
        room.images.all().delete()
        if room.image:
            room.image.delete()
        
        # Get room type images
        captions_and_urls = ROOM_IMAGES.get(room.room_type, ROOM_IMAGES['STANDARD'])
        
        # Add first image as main image
        if len(captions_and_urls) > 0:
            caption, url = captions_and_urls[0]
            img = download_image(url)
            if img is None:
                img = create_simple_image(caption)
            
            # Save as main image
            img_io = BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            
            room.image.save(
                f'room_{room.room_number}_main.png',
                ContentFile(img_io.getvalue()),
                save=True
            )
            print(f"  ✓ Added main image: {caption}")
        
        # Add gallery images
        for idx, (caption, url) in enumerate(captions_and_urls[1:], 1):
            try:
                img = download_image(url)
                if img is None:
                    img = create_simple_image(caption)
                
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
                print(f"  ❌ Error adding gallery image: {str(e)[:50]}")
    
    print(f"\n✅ Sample images added successfully!")

if __name__ == '__main__':
    try:
        add_sample_images()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
