#!/usr/bin/env python
"""
Create a test user with first and last name for testing dashboard display
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Delete any existing test user
User.objects.filter(username='testdashboard').delete()

# Create test user with names
user = User.objects.create_user(
    username='testdashboard',
    email='testdashboard@example.com',
    password='TestPass123!',
    first_name='Test',
    last_name='User',
    role='GUEST',
    is_active=True
)

print(f"✓ Created test user")
print(f"  Username: {user.username}")
print(f"  Email: {user.email}")
print(f"  First Name: {user.first_name}")
print(f"  Last Name: {user.last_name}")
print(f"\nYou can now login with:")
print(f"  Username: testdashboard")
print(f"  Email: testdashboard@example.com")
print(f"  Password: TestPass123!")
