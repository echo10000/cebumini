"""
Script to create more realistic-looking room images with gradients, patterns, and details
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

# Room image definitions with more detail
ROOM_IMAGES = {
    'STANDARD': [
        {
            'caption': 'Comfortable Bedroom',
            'main_color': (70, 110, 150),
            'accent': (200, 180, 160),
            'icon': '🛏️'
        },
        {
            'caption': 'Modern Bathroom',
            'main_color': (100, 140, 180),
            'accent': (220, 220, 220),
            'icon': '🚿'
        },
        {
            'caption': 'City View',
            'main_color': (150, 180, 200),
            'accent': (255, 200, 100),
            'icon': '🌆'
        },
        {
            'caption': 'Room Amenities',
            'main_color': (100, 140, 170),
            'accent': (200, 150, 100),
            'icon': '⭐'
        }
    ],
    'DELUXE': [
        {
            'caption': 'Premium Bedroom',
            'main_color': (160, 80, 120),
            'accent': (220, 180, 200),
            'icon': '👑'
        },
        {
            'caption': 'Luxury Bathroom',
            'main_color': (180, 100, 140),
            'accent': (240, 220, 230),
            'icon': '✨'
        },
        {
            'caption': 'Sitting Area',
            'main_color': (150, 70, 110),
            'accent': (200, 150, 180),
            'icon': '🛋️'
        },
        {
            'caption': 'Entertainment Center',
            'main_color': (170, 90, 130),
            'accent': (220, 180, 210),
            'icon': '📺'
        }
    ],
    'SUITE': [
        {
            'caption': 'Spacious Living Area',
            'main_color': (80, 130, 80),
            'accent': (180, 220, 180),
            'icon': '🏡'
        },
        {
            'caption': 'Master Bedroom',
            'main_color': (100, 150, 100),
            'accent': (200, 240, 200),
            'icon': '🛏️'
        },
        {
            'caption': 'Executive Suite',
            'main_color': (70, 120, 70),
            'accent': (170, 210, 170),
            'icon': '💼'
        },
        {
            'caption': 'Premium Bathroom',
            'main_color': (90, 140, 90),
            'accent': (190, 230, 190),
            'icon': '🚿'
        }
    ]
}

def create_realistic_image(data, width=400, height=300):
    """Create a more realistic-looking room image"""
    img = Image.new('RGB', (width, height), color=data['main_color'])
    draw = ImageDraw.Draw(img)
    
    # Add gradient-like effect with rectangles
    steps = 15
    for i in range(steps):
        alpha = i / steps
        r = int(data['main_color'][0] * (1 - alpha) + data['accent'][0] * alpha)
        g = int(data['main_color'][1] * (1 - alpha) + data['accent'][1] * alpha)
        b = int(data['main_color'][2] * (1 - alpha) + data['accent'][2] * alpha)
        
        y = int((height * i) / steps)
        y_next = int((height * (i + 1)) / steps)
        draw.rectangle([(0, y), (width, y_next)], fill=(r, g, b))
    
    # Try to load fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 48)
        caption_font = ImageFont.truetype("arial.ttf", 20)
        detail_font = ImageFont.truetype("arial.ttf", 60)
    except:
        title_font = ImageFont.load_default()
        caption_font = ImageFont.load_default()
        detail_font = ImageFont.load_default()
    
    text_color = (255, 255, 255)
    shadow_color = (0, 0, 0, 128)
    
    # Draw decorative elements
    # Top left corner decoration
    draw.ellipse([(10, 10), (80, 80)], fill=(255, 255, 255, 50), outline=(255, 255, 255))
    
    # Bottom right corner decoration
    draw.ellipse([(width-80, height-80), (width-10, height-10)], fill=(255, 255, 255, 50), outline=(255, 255, 255))
    
    # Draw icon/emoji area (simulated with rectangle)
    icon_x = width // 2 - 40
    icon_y = height // 2 - 60
    draw.rectangle([(icon_x, icon_y), (icon_x + 80, icon_y + 80)], 
                   fill=(255, 255, 255), outline=text_color)
    
    # Draw caption
    bbox = draw.textbbox((0, 0), data['caption'], font=title_font)
    text_width = bbox[2] - bbox[0]
    caption_x = (width - text_width) // 2
    caption_y = height // 2 + 30
    
    # Shadow effect
    draw.text((caption_x + 2, caption_y + 2), data['caption'], 
             fill=(0, 0, 0), font=title_font)
    # Main text
    draw.text((caption_x, caption_y), data['caption'], 
             fill=text_color, font=title_font)
    
    # Draw hotel name at bottom
    hotel_text = "🏨 Cebu Hotel"
    bbox = draw.textbbox((0, 0), hotel_text, font=caption_font)
    hotel_width = bbox[2] - bbox[0]
    hotel_x = (width - hotel_width) // 2
    draw.text((hotel_x, height - 40), hotel_text, fill=text_color, font=caption_font)
    
    # Draw decorative line
    draw.line([(30, height - 65), (width - 30, height - 65)], fill=text_color, width=2)
    
    return img

def add_images():
    """Add enhanced images to all rooms"""
    rooms = Room.objects.all()
    
    if not rooms.exists():
        print("❌ No rooms found")
        return
    
    print(f"Creating enhanced images for {rooms.count()} rooms...\n")
    
    for room in rooms:
        print(f"Room {room.room_number}...")
        
        # Clear existing images
        room.images.all().delete()
        if room.image:
            room.image.delete()
        
        # Get image data for this room type
        images_data = ROOM_IMAGES.get(room.room_type, ROOM_IMAGES['STANDARD'])
        
        # Add main image
        img = create_realistic_image(images_data[0])
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        room.image.save(
            f'room_{room.room_number}_main.png',
            ContentFile(img_io.getvalue()),
            save=True
        )
        print(f"  ✓ Main: {images_data[0]['caption']}")
        
        # Add gallery images
        for idx, img_data in enumerate(images_data[1:], 1):
            img = create_realistic_image(img_data)
            img_io = BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            
            room_image = RoomImage(
                room=room,
                caption=img_data['caption']
            )
            room_image.image.save(
                f'room_{room.room_number}_gallery_{idx}.png',
                ContentFile(img_io.getvalue()),
                save=True
            )
            print(f"  ✓ Gallery: {img_data['caption']}")
    
    print(f"\n✅ Done! All rooms now have enhanced images.")

if __name__ == '__main__':
    try:
        add_images()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
