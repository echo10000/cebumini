#!/usr/bin/env python
"""
Simulate exactly what the view does
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from authentication.forms import RegisterForm
from django.contrib.auth import get_user_model

User = get_user_model()

# Clean up
User.objects.filter(email='viewtest@example.com').delete()

# Simulate view POST
post_data = {
    'email': 'viewtest@example.com',
    'first_name': 'View',
    'last_name': 'Test',
    'password1': 'TestPass123!',
    'password2': 'TestPass123!',
    'accept_terms': 'on',
}

form = RegisterForm(data=post_data)

print("=" * 60)
print("SIMULATING EXACT VIEW FLOW")
print("=" * 60)

if form.is_valid():
    print("✓ Form is valid")
    
    # This is what the view does
    user = form.save(commit=False)
    print(f"After form.save(commit=False):")
    print(f"  first_name: |{user.first_name}|")
    print(f"  last_name: |{user.last_name}|")
    
    # Set names
    first_name_value = form.cleaned_data.get('first_name', '')
    last_name_value = form.cleaned_data.get('last_name', '')
    
    print(f"\nFrom form.cleaned_data:")
    print(f"  first_name: {first_name_value}")
    print(f"  last_name: {last_name_value}")
    
    user.first_name = first_name_value
    user.last_name = last_name_value
    
    print(f"\nAfter setting on user object:")
    print(f"  first_name: |{user.first_name}|")
    print(f"  last_name: |{user.last_name}|")
    
    user.role = 'GUEST'
    user.save()
    
    # Fetch from DB
    saved_user = User.objects.get(email='viewtest@example.com')
    print(f"\nAfter saving to DB:")
    print(f"  first_name: |{saved_user.first_name}|")
    print(f"  last_name: |{saved_user.last_name}|")
    
    if saved_user.first_name and saved_user.last_name:
        print("\n✓✓✓ NAMES SAVED SUCCESSFULLY!")
    else:
        print("\n✗ NAMES NOT SAVED!")
else:
    print("✗ Form is NOT valid")
    print(f"Errors: {form.errors}")
