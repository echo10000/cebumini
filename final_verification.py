#!/usr/bin/env python
"""
Final verification: Simulate signup and verify names are saved
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Simulate signup with same email
post_data = {
    'email': 'echogoodkid@gmail.com',
    'first_name': 'Cebu',
    'last_name': 'Guest',
    'password1': 'StrongPass123!',
    'password2': 'StrongPass123!',
    'accept_terms': 'on',
}

print("=" * 60)
print("FINAL VERIFICATION: Testing Registration Form Fix")
print("=" * 60)
print(f"\nSimulating signup with data:")
for k, v in post_data.items():
    if 'password' not in k:
        print(f"  {k}: {v}")

client = Client()
response = client.post('/auth/register/', data=post_data)

print(f"\nResponse status: {response.status_code}")

if response.status_code == 302:
    print("✓ Registration accepted")
    
    user = User.objects.filter(email='echogoodkid@gmail.com').first()
    if user:
        print(f"\n✓ User created: {user.username}")
        print(f"  First Name: {user.first_name}")
        print(f"  Last Name: {user.last_name}")
        print(f"  Email: {user.email}")
        
        if user.first_name == 'Cebu' and user.last_name == 'Guest':
            print("\n" + "=" * 60)
            print("✓✓✓ FIX VERIFIED - NAMES ARE BEING SAVED!")
            print("=" * 60)
        else:
            print("\n✗ Names don't match input")
    else:
        print("✗ User not found")
else:
    print(f"✗ Registration failed")
