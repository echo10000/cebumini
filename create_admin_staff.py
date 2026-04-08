"""
Script to create admin and staff user accounts for testing
Run: python create_admin_staff.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import UserRole

User = get_user_model()

def create_admin_user():
    """Create admin user"""
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin@12345'
    
    # Check if admin already exists
    if User.objects.filter(username=username).exists():
        print(f"✓ Admin user '{username}' already exists")
        return
    
    admin_user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    admin_user.role = UserRole.ADMIN
    admin_user.save()
    print(f"✓ Created admin user:")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print(f"  Role: Administrator")
    return admin_user


def create_staff_user():
    """Create staff user"""
    username = 'staff'
    email = 'staff@example.com'
    password = 'staff@12345'
    
    # Check if staff already exists
    if User.objects.filter(username=username).exists():
        print(f"✓ Staff user '{username}' already exists")
        return
    
    staff_user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    staff_user.role = UserRole.STAFF
    staff_user.is_staff = True
    staff_user.save()
    print(f"✓ Created staff user:")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print(f"  Role: Staff (Housekeeping/Front Desk)")
    return staff_user


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Creating Admin & Staff Users")
    print("="*60)
    
    create_admin_user()
    create_staff_user()
    
    print("\n" + "="*60)
    print("User Creation Complete!")
    print("="*60)
    print("\nYou can now login with:")
    print("\n" + "-"*60)
    print("ADMIN ACCOUNT:")
    print("-"*60)
    print("  • URL: http://127.0.0.1:8000/auth/login/")
    print("  • Username: admin")
    print("  • Password: admin@12345")
    print("  • Access Admin Panel: http://127.0.0.1:8000/admin-panel/")
    
    print("\n" + "-"*60)
    print("STAFF ACCOUNT (Housekeeping/Front Desk):")
    print("-"*60)
    print("  • URL: http://127.0.0.1:8000/auth/login/")
    print("  • Username: staff")
    print("  • Password: staff@12345")
    print("  • Access Staff Dashboard: http://127.0.0.1:8000/staff/")
    
    print("\n" + "="*60 + "\n")
