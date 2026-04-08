#!/usr/bin/env python
import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("FIXING USERS WITH EMPTY USERNAMES")
print("=" * 60)

# Find users with empty usernames
empty_username_users = User.objects.filter(username='') | User.objects.filter(username__isnull=True)

print(f"\nFound {empty_username_users.count()} users with empty/null usernames")

for user in empty_username_users:
    print(f"\n📝 Fixing user:")
    print(f"  Email: {user.email}")
    print(f"  Current Username: '{user.username}'")
    
    # Generate username from email
    email_prefix = user.email.split('@')[0][:20]
    base_username = email_prefix
    
    # Make it unique
    counter = 1
    new_username = base_username
    while User.objects.filter(username=new_username).exclude(id=user.id).exists():
        suffix = str(uuid.uuid4())[:8]
        new_username = f"{base_username}_{suffix}"[:30]
        counter += 1
    
    user.username = new_username
    user.save()
    print(f"  ✓ New Username: {new_username}")

print("\n" + "=" * 60)
print("✓ Users fixed successfully!")
print("=" * 60)

# Verify all users now have usernames
print("\n📋 All Users (Verification):")
print("-" * 60)
for user in User.objects.all():
    status = "✓" if user.username else "❌"
    print(f"{status} {user.email:35} → {user.username}")

print("\n" + "=" * 60)
