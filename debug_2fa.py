#!/usr/bin/env python
"""
Debug 2FA Setup Issue
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
client = Client()

# Create test user
TEST_EMAIL = 'debug@hotel.com'
TEST_PASSWORD = 'TestPass123!'

User.objects.filter(email=TEST_EMAIL).delete()

# Register
client.post('/auth/register/', {
    'email': TEST_EMAIL,
    'first_name': 'Debug',
    'last_name': 'User',
    'password1': TEST_PASSWORD,
    'password2': TEST_PASSWORD,
    'accept_terms': 'on'
})

# Login
client.login(username=TEST_EMAIL, password=TEST_PASSWORD)

# Try 2FA setup
print("Attempting 2FA setup...")
response = client.post('/auth/2fa/setup/', {
    'action': 'setup'
})

print(f"Status Code: {response.status_code}")
print(f"Content type: {response.get('Content-Type', 'N/A')}")
print(f"Has context: {response.context is not None}")

if response.context:
    print(f"Context keys: {list(response.context.keys())}")
    if 'qr_code' in response.context:
        print(f"QR Code present: YES")
        print(f"QR Code length: {len(response.context['qr_code'])}")
    if 'secret' in response.context:
        print(f"Secret present: YES")
        print(f"Secret: {response.context['secret']}")
    if 'backup_codes' in response.context:
        print(f"Backup codes present: YES")
        print(f"Backup codes count: {len(response.context['backup_codes'])}")
else:
    print("\nNo context returned!")
    print(f"Response content (first 500 chars):\n{response.content.decode()[:500]}")

# Check if TwoFactorAuth was created
user = User.objects.get(email=TEST_EMAIL)
try:
    two_fa = user.two_factor_auth
    print(f"\nTwoFactorAuth record exists: YES")
    print(f"Is enabled: {two_fa.is_enabled}")
    print(f"Is verified: {two_fa.is_verified}")
    print(f"Secret key: {two_fa.secret_key}")
except:
    print(f"\nTwoFactorAuth record exists: NO")
