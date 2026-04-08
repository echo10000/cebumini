# Login Instructions - Admin & Staff Access

## Quick Start: Create Admin & Staff Users

Run this command from your project directory:

```bash
python create_admin_staff.py
```

This will create:
- **Admin User**: username=`admin`, password=`admin@12345`
- **Staff User**: username=`staff`, password=`staff@12345`

---

## Login as Admin

### Method 1: Django Admin Dashboard
1. Go to: `http://127.0.0.1:8000/admin/`
2. Enter credentials:
   - Username: `admin`
   - Password: `admin@12345`
3. You'll see the Django admin panel with full database management

### Features Available:
- Manage users, rooms, bookings
- View system logs and statistics
- Complete database access

---

## Login as Staff

### Method 1: Website Login
1. Go to: `http://127.0.0.1:8000/auth/login/`
2. Enter credentials:
   - Username: `staff`
   - Password: `staff@12345`
3. Click "Sign In"

### Method 2: Using Email
1. Go to: `http://127.0.0.1:8000/auth/login/`
2. Use email: `staff@example.com`
3. Password: `staff@12345`

### Features Available:
- View dashboard
- Manage rooms (if permissions set)
- View bookings
- Access staff-only features

---

## Verification

### Check User Roles in Admin Panel
1. Login to admin: `http://127.0.0.1:8000/admin/`
2. Go to "Users" section
3. Look for:
   - **Admin user**: Has "Staff status" and "Superuser status" checked
   - **Staff user**: Has "Staff status" checked

### Check Logged-in User
On any page after logging in, you'll see:
- Your username in the navigation bar
- Staff users: May see "Staff Dashboard" link
- Admin users: Can access admin panel from menu

---

## Troubleshooting

### Can't Create Users
If the script fails, run manually in Django shell:

```bash
python manage.py shell
```

Then paste:
```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Create admin
User.objects.create_superuser('admin', 'admin@example.com', 'admin@12345')

# Create staff
user = User.objects.create_user('staff', 'staff@example.com', 'staff@12345')
user.is_staff = True
user.save()

print("Users created!")
```

### Forgot Password
Reset in Django shell:

```python
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='admin')
user.set_password('newpassword')
user.save()
print("Password reset to: newpassword")
```

---

## User Permission Levels

### Anonymous User
- View public rooms
- Browse hotel information
- Cannot book or access admin features

### Regular User (Logged In)
- Book rooms
- View booking history
- Get personalized recommendations
- Cannot manage rooms

### Staff User
- Login with username/password
- Access staff features
- Manage room availability (if configured)
- View all bookings

### Admin User (Superuser)
- Full Django admin access
- `http://127.0.0.1:8000/admin/`
- Create/Edit/Delete any objects
- Manage permissions
- System configuration

---

## Check Permissions

To verify user permissions:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# Check admin
admin = User.objects.get(username='admin')
print(f"Admin is superuser: {admin.is_superuser}")
print(f"Admin is staff: {admin.is_staff}")

# Check staff
staff = User.objects.get(username='staff')
print(f"Staff is superuser: {staff.is_superuser}")
print(f"Staff is staff: {staff.is_staff}")
```

---

## Note on RecursionError

The previous RecursionError at `/rooms/` has been fixed by:
1. Improving template variable resolution
2. Adding null checks in the recommendations widget
3. Removing circular context dependencies

If you still see the error, cleared your browser cache and restart the Django server:

```bash
python manage.py runserver
```

---

**Need help?** Check the documentation files:
- `USERS_GUIDE.md` - User management
- `GETTING_STARTED.md` - General setup
- `README.md` - Project overview
