#!/usr/bin/env python
"""
Script to manage and delete users from the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import LoginSession, TwoFactorAuth

User = get_user_model()

print("=" * 80)
print("USER MANAGEMENT TOOL")
print("=" * 80)

# Show all users
print("\n📋 CURRENT USERS IN DATABASE:")
print("-" * 80)

users = User.objects.all().order_by('-created_at')

if not users.exists():
    print("No users found in database")
else:
    for i, user in enumerate(users, 1):
        print(f"\n{i}. Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Name: {user.first_name} {user.last_name}")
        print(f"   Created: {user.created_at}")
        print(f"   2FA Enabled: {hasattr(user, 'twofactorauth') and user.twofactorauth.is_enabled}")

# Option to delete users
print("\n" + "=" * 80)
print("DELETE OPTIONS:")
print("=" * 80)

choice = input("\nWhat would you like to do?\n"
               "1. Delete a specific user by email\n"
               "2. Delete all users except admin\n"
               "3. Delete all users\n"
               "4. Just view users (do nothing)\n"
               "\nEnter choice (1-4): ").strip()

if choice == '1':
    email = input("\nEnter email address to delete: ").strip()
    user = User.objects.filter(email=email).first()
    
    if user:
        print(f"\n⚠️  About to delete: {user.email}")
        confirm = input("Are you sure? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            username = user.username
            user.delete()
            print(f"✓ User {email} deleted successfully!")
        else:
            print("✗ Deletion cancelled")
    else:
        print(f"✗ User with email '{email}' not found")

elif choice == '2':
    print("\n⚠️  This will delete all users except superusers (admins)")
    confirm = input("Continue? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        deleted_count = 0
        for user in User.objects.filter(is_superuser=False):
            email = user.email
            user.delete()
            deleted_count += 1
            print(f"  ✓ Deleted: {email}")
        
        print(f"\n✓ Total deleted: {deleted_count} users")
    else:
        print("✗ Deletion cancelled")

elif choice == '3':
    print("\n⚠️  WARNING: This will delete ALL users including admins!")
    confirm = input("Are you absolutely sure? (type 'DELETE ALL' to confirm): ").strip()
    
    if confirm == 'DELETE ALL':
        deleted_count = User.objects.count()
        User.objects.all().delete()
        print(f"\n✓ ALL {deleted_count} users have been deleted!")
    else:
        print("✗ Deletion cancelled")

elif choice == '4':
    print("\n✓ No changes made")

else:
    print("\n✗ Invalid choice")

# Show remaining users
print("\n" + "=" * 80)
print("USERS AFTER OPERATION:")
print("=" * 80)

users = User.objects.all().order_by('-created_at')
if users.exists():
    for i, user in enumerate(users, 1):
        admin_badge = " [ADMIN]" if user.is_superuser else ""
        print(f"{i}. {user.email}{admin_badge}")
else:
    print("No users in database")

print("\n" + "=" * 80)
