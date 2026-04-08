from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class RoomType(models.TextChoices):
    """Room type choices"""
    STANDARD = 'STANDARD', 'Standard Room'
    DELUXE = 'DELUXE', 'Deluxe Room'
    SUITE = 'SUITE', 'Suite Room'


class Room(models.Model):
    """Room Model"""
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(
        max_length=20,
        choices=RoomType.choices,
        default=RoomType.STANDARD
    )
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    capacity = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1)]
    )
    is_available = models.BooleanField(default=True)
    amenities = models.TextField(
        blank=True,
        help_text="Comma-separated list of amenities"
    )
    image = models.ImageField(
        upload_to='rooms/%Y/%m/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rooms'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        ordering = ['room_number']

    def __str__(self):
        return f"Room {self.room_number} ({self.get_room_type_display()})"

    def get_amenities_list(self):
        """Return amenities as list"""
        if self.amenities:
            return [a.strip() for a in self.amenities.split(',')]
        return []

    def get_status(self):
        """Get room status"""
        return "Available" if self.is_available else "Occupied"


class RoomImage(models.Model):
    """Additional room images"""
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='rooms/%Y/%m/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'room_images'
        verbose_name = 'Room Image'
        verbose_name_plural = 'Room Images'
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Image of {self.room.room_number}"
