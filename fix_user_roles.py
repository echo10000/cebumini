"""
Script to verify and fix user roles
Run: python fix_user_roles.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import UserRole

User = get_user_model()

def fix_user_roles():
    """Fix roles for existing users"""
    print("\n" + "="*60)
    print("Fixing User Roles")
    print("="*60)
    
    # Fix admin user
    try:
        admin_user = User.objects.get(username='admin')
        admin_user.role = UserRole.ADMIN
        admin_user.is_staff = True
        admin_user.save()
        print(f"\n✓ Updated admin user:")
        print(f"  Username: {admin_user.username}")
        print(f"  Role: {admin_user.get_role_display()}")
        print(f"  Is Superuser: {admin_user.is_superuser}")
        print(f"  Is Staff: {admin_user.is_staff}")
        print(f"  is_admin() method returns: {admin_user.is_admin()}")
    except User.DoesNotExist:
        print("✗ Admin user not found")
    
    # Fix staff user
    try:
        staff_user = User.objects.get(username='staff')
        staff_user.role = UserRole.STAFF
        staff_user.is_staff = True
        staff_user.save()
        print(f"\n✓ Updated staff user:")
        print(f"  Username: {staff_user.username}")
        print(f"  Role: {staff_user.get_role_display()}")
        print(f"  Is Staff: {staff_user.is_staff}")
        print(f"  is_staff_member() method returns: {staff_user.is_staff_member()}")
    except User.DoesNotExist:
        print("✗ Staff user not found")
    
    print("\n" + "="*60)
    print("Role Verification Complete!")
    print("="*60 + "\n")

if __name__ == '__main__':
    fix_user_roles()
