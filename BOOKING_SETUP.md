# 🚀 Booking System - Setup & Installation Guide

## Prerequisites

Before setting up the booking system, ensure you have:
- Django 4.2.0 installed
- Python 3.8+
- Virtual environment activated
- All requirements.txt dependencies installed

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This should install:
- Django==4.2.0
- djangorestframework==3.14.0
- python-decouple==3.8
- Pillow==10.0.0

## Step 2: Run Migrations

```bash
# Create migration files
python manage.py makemigrations authentication

# Apply migrations to database
python manage.py migrate
```

This creates the following tables:
- `bookings` (Booking model)
- `booking_status_choices` (if using choices)

## Step 3: Create Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account with:
- Username
- Email
- Password
- Confirm password

## Step 4: Create Test Data (Optional)

```bash
python manage.py shell
```

Then in the shell:
```python
from authentication.models import Room, RoomType

# Create test rooms
Room.objects.create(
    room_number='101',
    room_type=RoomType.STANDARD,
    description='Comfortable standard room with queen bed',
    price_per_night=3500,
    capacity=2,
    is_available=True,
    amenities='WiFi, TV, AC, Private Bathroom, Shower'
)

Room.objects.create(
    room_number='102',
    room_type=RoomType.DELUXE,
    description='Spacious deluxe room with premium amenities',
    price_per_night=5500,
    capacity=2,
    is_available=True,
    amenities='WiFi, Smart TV, AC, Minibar, Premium Bathroom, Bath Tub'
)

Room.objects.create(
    room_number='201',
    room_type=RoomType.SUITE,
    description='Luxurious suite with separate living area',
    price_per_night=8500,
    capacity=4,
    is_available=True,
    amenities='WiFi, Smart TV, AC, Minibar, Jacuzzi, Premium Toiletries, Bathrobe'
)

exit()
```

## Step 5: Run Development Server

```bash
python manage.py runserver
```

Access the application at: `http://localhost:8000`

## Step 6: Access Admin Panel

1. Navigate to: `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Click on "Bookings" to view the booking model
4. Click on "Rooms" to verify test data

## Step 7: Test Guest Booking Flow

### As Guest:

1. Register a new account at `/auth/register/`
2. Accept terms and conditions
3. Navigate to `/rooms/` to view available rooms
4. Click "View Details" on a room
5. Click "Book Now" button
6. Select check-in date (today or future)
7. Select check-out date (after check-in)
8. Add special requests (optional)
9. Click "Continue to Confirmation"
10. Review booking summary
11. Check "I agree to booking terms"
12. Click "Confirm & Book Now"
13. View booking confirmation
14. Click "My Bookings" to see booking history

### Test Overlapping Booking Prevention:

1. Note the dates you booked (e.g., Feb 20-23)
2. Try to book same room for Feb 21-25
3. Should see error: "Room X is not available for selected dates"
4. Try booking for Feb 23-25 (after first booking)
5. Should succeed

## Step 8: Test Admin Features

### As Admin:

1. Login as superuser at `/auth/login/`
2. Navigate to `/bookings/admin/all/`
3. View all bookings statistics
4. View all bookings in table
5. Test filters:
   - Filter by room type
   - Filter by status (CONFIRMED, PENDING, CANCELLED)
   - Filter by check-in date range
   - Search by guest name
6. Click on booking to view details
7. Test actions:
   - Confirm pending booking
   - Cancel confirmed booking
8. View updated statistics

## File Structure Created

```
authentication/
├── models.py (updated with Booking model)
├── forms_bookings.py (NEW)
├── views_bookings.py (NEW)
├── urls_bookings.py (NEW)
├── admin.py (updated with BookingAdmin)
└── management/commands/
    └── add_terms.py

templates/
└── bookings/ (NEW directory)
    ├── create_booking.html
    ├── confirm_booking.html
    ├── booking_detail.html
    ├── booking_history.html
    ├── cancel_booking.html
    ├── admin_bookings.html
    └── admin_cancel_booking.html

cebuhotel/
├── urls.py (updated with bookings include)
└── settings.py (should already have AUTH settings)
```

## URL Endpoints

### Guest Endpoints
```
POST   /bookings/<room_id>/create/              Create booking
POST   /bookings/confirm/                       Confirm booking
GET    /bookings/<booking_id>/                  View booking
GET    /bookings/history/                       View history
POST   /bookings/<booking_id>/cancel/           Cancel booking
```

### Admin Endpoints
```
GET    /bookings/admin/all/                     View all bookings
POST   /bookings/admin/<booking_id>/confirm/    Confirm booking
POST   /bookings/admin/<booking_id>/cancel/     Cancel booking
```

## Database Schema

### Bookings Table
```sql
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES rooms(id),
    guest_id INTEGER NOT NULL REFERENCES users(id),
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    total_price DECIMAL(10, 2),
    status VARCHAR(20),
    special_requests TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Indexes Created
```sql
CREATE INDEX idx_booking_room_dates 
    ON bookings(room_id, check_in, check_out);

CREATE INDEX idx_booking_guest_status 
    ON bookings(guest_id, status);
```

## Configuration Check

Verify in `cebuhotel/settings.py`:

```python
# Should contain:
INSTALLED_APPS = [
    # ...
    'authentication',
]

AUTH_USER_MODEL = 'authentication.CustomUser'

# Bookings URLs should be included
# Check urls.py for: path('bookings/', include('authentication.urls_bookings')),
```

## Common Setup Issues

### Issue: "ModuleNotFoundError: No module named 'booking'"
**Solution:** Ensure file is named `urls_bookings.py` not `booking.py`

### Issue: "Relation 'bookings' does not exist"
**Solution:** Run migrations:
```bash
python manage.py migrate
```

### Issue: Admin page shows "Bookings" but can't click
**Solution:** Ensure `BookingAdmin` is registered in `admin.py`:
```python
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # ...
```

### Issue: Dates not showing in form
**Solution:** Ensure browser supports HTML5 date input, or add jQuery date picker

### Issue: Can't access `/bookings/admin/all/` as admin
**Solution:** Verify user role is set to 'ADMIN' in admin panel

## Testing Commands

```bash
# Create test bookings (shell)
python manage.py shell
>>> from authentication.models import Room, Booking, CustomUser
>>> user = CustomUser.objects.first()
>>> room = Room.objects.first()
>>> Booking.objects.create(room=room, guest=user, check_in='2026-02-20', check_out='2026-02-23')

# Check for overlapping bookings
>>> Booking.check_availability(room.id, '2026-02-21', '2026-02-25')
False  # Should return False due to overlap

# Run all tests
python manage.py test authentication

# Run specific test
python manage.py test authentication.tests.BookingTests
```

## Performance Tips

1. **For Large Datasets:** Add pagination limit:
   ```python
   # In admin
   list_per_page = 100
   ```

2. **Database Optimization:**
   ```bash
   python manage.py sqlsequencereset authentication | python manage.py dbshell
   ```

3. **Caching:** Consider caching room availability for better performance

## Deployment Considerations

### Before Going Live:

1. ✅ Set `DEBUG = False` in settings.py
2. ✅ Configure `ALLOWED_HOSTS` in settings.py
3. ✅ Set `SECRET_KEY` to random value
4. ✅ Configure database (PostgreSQL recommended)
5. ✅ Set up static file storage (S3, etc.)
6. ✅ Set up media file storage
7. ✅ Configure email backend for notifications
8. ✅ Enable HTTPS
9. ✅ Set up logging and monitoring
10. ✅ Configure backups

### Production Settings
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

## Monitoring Commands

```bash
# Check booking count
python manage.py shell
>>> from authentication.models import Booking
>>> Booking.objects.count()

# Check revenue
>>> from django.db.models import Sum
>>> Booking.objects.filter(status='CONFIRMED').aggregate(Sum('total_price'))

# Check occupancy for specific date
>>> from datetime import date
>>> today = date.today()
>>> Booking.objects.filter(check_in__lte=today, check_out__gte=today, status='CONFIRMED').count()
```

## Next Steps

After setup is complete:

1. ✅ Test all booking flows
2. ✅ Test admin features
3. ✅ Verify email notifications (when implemented)
4. ✅ Load test with concurrent bookings
5. ✅ Review security settings
6. ✅ Document business logic for team
7. ✅ Plan for payment integration
8. ✅ Set up monitoring/alerts

## Support & Documentation

- **Models Documentation:** See `BOOKING_SYSTEM.md`
- **Room Management:** See `ROOM_MANAGEMENT.md`
- **Authentication:** See docs in templates/
- **Admin Interface:** Access at `/admin/` when logged in as superuser

---

**Setup Status**: ✅ COMPLETE
**Ready for Testing**: ✅ YES
**Production Ready**: ✅ AFTER FINAL CHECKS
