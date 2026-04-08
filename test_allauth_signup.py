#!/usr/bin/env python
"""Test allauth signup flow with console email backend"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
client = Client()

print("\n" + "="*70)
print("ALLAUTH SIGNUP TEST - Console Email Backend")
print("="*70 + "\n")

# Test email
TEST_EMAIL = 'allauth_test@hotel.com'
User.objects.filter(email=TEST_EMAIL).delete()

print("[TEST] Attempting signup via allauth...")
print(f"Email: {TEST_EMAIL}\n")

# Try signup
response = client.post('/accounts/signup/', {
    'email': TEST_EMAIL,
    'password1': 'AllAuthTest123!',
    'password2': 'AllAuthTest123!',
})

print(f"[RESULT] Status Code: {response.status_code}")

if response.status_code == 302:
    print("[✓] Signup successful - redirect (302)")
    
    # Check if user was created
    user = User.objects.filter(email=TEST_EMAIL).first()
    if user:
        print(f"[✓] User created: {user.email}")
        print(f"[✓] Username: {user.username}")
        print(f"[✓] Email verified: {user.emailaddress_set.filter(primary=True, verified=True).exists()}")
    else:
        print("[✗] User not found in database")
        
elif response.status_code == 200:
    print("[⚠] Got 200 OK - form may have errors")
    # Check for error messages
    content = response.content.decode()
    if 'error' in content.lower():
        print("[✗] Form errors present")
    else:
        print("[?] Check page for any issues")
else:
    print(f"[✗] Unexpected status: {response.status_code}")

print("\n" + "="*70)
print("If an email was sent, check the console above for the email output")
print("="*70 + "\n")
