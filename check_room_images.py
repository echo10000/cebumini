import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from authentication.models import Room, RoomImage

rooms = Room.objects.all()
print(f"Total rooms: {rooms.count()}\n")

for room in rooms[:2]:  # Check first 2 rooms
    print(f"Room {room.room_number}:")
    print(f"  Main image: {room.image}")
    print(f"  Image file exists: {room.image.name if room.image else 'None'}")
    print(f"  Gallery images: {room.images.count()}")
    for img in room.images.all()[:2]:
        print(f"    - {img.image.name}")
    print()
