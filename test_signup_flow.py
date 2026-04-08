#!/usr/bin/env python
"""
Test AllAuth signup flow with the custom adapter
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

User = get_user_model()

print("=" * 70)
print("TESTING ALLAUTH SIGNUP WITH CUSTOM ADAPTER")
print("=" * 70)

# Create a test request
factory = RequestFactory()
request = factory.post('/accounts/signup/')

# Add session and auth middleware
middleware = SessionMiddleware(lambda x: None)
middleware.process_request(request)

auth_middleware = AuthenticationMiddleware(lambda x: None)
auth_middleware.process_request(request)

request.session.save()

# Test signup form data
test_email = 'echoecho26@gmail.com'
signup_data = {
    'email': test_email,
    'password1': 'kindaawful',
    'password2': 'kindaawful',
}

print(f"\n📧 Test Signup Data:")
print(f"  Email: {signup_data['email']}")
print(f"  Password: ****** (length: {len(signup_data['password1'])})")

# Check if email already exists
existing = User.objects.filter(email=test_email).exists()
print(f"\n✓ Email already exists in DB: {existing}")

if existing:
    print("  Cleaning up existing user for test...")
    User.objects.filter(email=test_email).delete()
    print("  ✓ Existing user deleted")

# Test form validation
print(f"\n🧪 Testing SignupForm Validation:")
print("-" * 70)

form = SignupForm(data=signup_data)
if form.is_valid():
    print("  ✓ Form is VALID")
    print(f"  Fields: email, password1, password2")
else:
    print("  ❌ Form has ERRORS:")
    for field, errors in form.errors.items():
        for error in errors:
            print(f"    - {field}: {error}")

# Try to save the user (simulate what AllAuth does)
print(f"\n💾 Testing User Creation with Adapter:")
print("-" * 70)

try:
    if form.is_valid():
        # This simulates what AllAuth does internally
        user, resp = form.try_save(request)
        print(f"  ✓ User created successfully!")
        print(f"    Email: {user.email}")
        print(f"    Username: {user.username}")
        print(f"    First Name: {user.first_name or '(not set)'}")
        print(f"    Last Name: {user.last_name or '(not set)'}")
        print(f"    ID: {user.id}")
        
        # Clean up
        user.delete()
        print(f"\n  ✓ Test user cleaned up (deleted from DB)")
    else:
        print("  ⚠️  Form validation failed, skipping user creation")
        
except Exception as e:
    print(f"  ❌ ERROR during user creation:")
    print(f"    {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("✓ Test complete! Ready for browser testing.")
print("=" * 70)
print("\nNext steps:")
print("1. Go to http://localhost:8000/accounts/signup/")
print("2. Enter email: echoecho26@gmail.com")
print("3. Enter password: kindaawful")
print("4. Confirm password: kindaawful")
print("5. Click Signup")
print("=" * 70)
