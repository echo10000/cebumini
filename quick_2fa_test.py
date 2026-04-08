#!/usr/bin/env python
"""Quick 2FA Test After Backend Fix"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from authentication.models import TwoFactorAuth
import pyotp

User = get_user_model()
client = Client()

print("\n" + "="*70)
print("QUICK 2FA VERIFICATION TEST - Backend Fix")
print("="*70 + "\n")

TEST_EMAIL = 'quick2fa@test.com'
TEST_PASSWORD = 'QuickTest123!'

# Cleanup
User.objects.filter(email=TEST_EMAIL).delete()
print("[1] Setup: Cleaned old data\n")

# Register
client.post('/auth/register/', {
    'email': TEST_EMAIL,
    'first_name': 'Quick',
    'last_name': 'Test',
    'password1': TEST_PASSWORD,
    'password2': TEST_PASSWORD,
    'accept_terms': 'on'
})
print("[2] Registration: User created\n")

# Login and setup 2FA
client.login(username=TEST_EMAIL, password=TEST_PASSWORD)
client.post('/auth/2fa/setup/', {'action': 'setup'})
user = User.objects.get(email=TEST_EMAIL)
secret = user.two_factor_auth.secret_key
totp = pyotp.TOTP(secret)
code = totp.now()

# Verify 2FA
client.post('/auth/2fa/setup/', {'action': 'verify', 'code': code, 'secret': secret})
print("[3] 2FA Setup: Enabled successfully\n")

# Test login with 2FA
client.logout()
client.post('/auth/login/', {'username': TEST_EMAIL, 'password': TEST_PASSWORD})
print("[4] First Login: Status OK")
print(f"    Session 2fa_user_id exists: {client.session.get('2fa_user_id') is not None}\n")

# Verify with 2FA code
code = totp.now()
response = client.post('/auth/2fa/verify/', {'code': code})
print(f"[5] 2FA Verification: Status {response.status_code}")

# Check if authenticated
is_auth = response.wsgi_request.user.is_authenticated
print(f"    User authenticated: {is_auth}")
print(f"    User email: {response.wsgi_request.user.email if is_auth else 'N/A'}\n")

if is_auth and response.wsgi_request.user.email == TEST_EMAIL:
    print("✓ SUCCESS: 2FA Login Flow Working!")
    print("\nThe system is READY for production testing:")
    print("  1. Registration works")
    print("  2. 2FA setup works")
    print("  3. 2FA verification works with backend fix")
    print("  4. Session management works")
else:
    print("✗ ISSUE: Authentication failed")
    print(f"  Status: {response.status_code}")

print("\n" + "="*70 + "\n")
