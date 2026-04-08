#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.adapters import CustomAccountAdapter

User = get_user_model()

print("=" * 60)
print("TESTING ALLAUTH CUSTOM ADAPTER")
print("=" * 60)

# Check existing users
print("\n📋 Current Users in Database:")
print("-" * 60)
existing_users = User.objects.all()
if existing_users.exists():
    for user in existing_users:
        print(f"  ✓ Email: {user.email}")
        print(f"    Username: {user.username}")
        print(f"    Created: {user.created_at}")
        print()
else:
    print("  No users found")

# Test adapter username generation
print("\n🧪 Testing Username Generation:")
print("-" * 60)

test_cases = [
    ('echoghost@gmail.com', 'Test case 1: Gmail'),
    ('user.name+tag@example.com', 'Test case 2: Complex email'),
    ('jericho.blando@cebu.ph', 'Test case 3: Business email'),
]

for email, description in test_cases:
    email_prefix = email.split('@')[0]
    base_username = email_prefix[:20]
    
    # Check if would conflict
    exists = User.objects.filter(username=base_username).exists()
    status = "⚠️  CONFLICT" if exists else "✓ OK"
    
    print(f"{description}")
    print(f"  Email: {email}")
    print(f"  Generated Username: {base_username}")
    print(f"  Status: {status}")
    print()

# Test with echoecho26@gmail.com specifically
print("\n🎯 Testing Email from Error (echoecho26@gmail.com):")
print("-" * 60)
test_email = 'echoecho26@gmail.com'
prefix = test_email.split('@')[0]
print(f"Email: {test_email}")
print(f"Proposed Username: {prefix}")
print(f"Exists: {User.objects.filter(username=prefix).exists()}")
print(f"Exists with Full Email: {User.objects.filter(email=test_email).exists()}")

print("\n" + "=" * 60)
print("✓ Adapter test complete")
print("=" * 60)
