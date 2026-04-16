#!/usr/bin/env python
"""
Test script to verify first_name and last_name are saved during registration.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.forms import RegisterForm

User = get_user_model()

# Test 1: Create a user manually and verify it displays
print("=" * 60)
print("TEST 1: Manual user creation")
print("=" * 60)

# Delete any existing test user
User.objects.filter(email='testuser@example.com').delete()

user = User.objects.create_user(
    email='testuser@example.com',
    username='testuser',
    password='TestPass123!',
    first_name='John',
    last_name='Doe',
    role='GUEST'
)
print(f"✓ Created user: {user.email}")
print(f"  First Name: |{user.first_name}|")
print(f"  Last Name: |{user.last_name}|")

# Test 2: Test the form with POST data
print("\n" + "=" * 60)
print("TEST 2: Form binding and save")
print("=" * 60)

# Delete previous test user
User.objects.filter(email='formtest@example.com').delete()

form_data = {
    'email': 'formtest@example.com',
    'first_name': 'Jane',
    'last_name': 'Smith',
    'password1': 'TestPass123!',
    'password2': 'TestPass123!',
    'accept_terms': True
}

form = RegisterForm(data=form_data)
print(f"Form valid: {form.is_valid()}")

if not form.is_valid():
    print("Form errors:")
    for field, errors in form.errors.items():
        print(f"  {field}: {errors}")
else:
    user = form.save(commit=False)
    user.first_name = form.cleaned_data.get('first_name', '')
    user.last_name = form.cleaned_data.get('last_name', '')
    user.role = 'GUEST'
    user.save()
    
    # Verify saved
    saved_user = User.objects.get(email='formtest@example.com')
    print(f"✓ Saved user: {saved_user.email}")
    print(f"  First Name: |{saved_user.first_name}|")
    print(f"  Last Name: |{saved_user.last_name}|")

print("\n" + "=" * 60)
print("SUMMARY: Both tests should show names with content, not empty pipes")
print("=" * 60)
