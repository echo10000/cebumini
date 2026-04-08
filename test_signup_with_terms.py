#!/usr/bin/env python
"""
Test AllAuth signup flow with T&C acceptance
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from allauth.account.forms import SignupForm
from authentication.models import TermsAndConditions

User = get_user_model()

print("=" * 80)
print("TESTING ALLAUTH SIGNUP WITH T&C ACCEPTANCE")
print("=" * 80)

# Check T&C exists
terms = TermsAndConditions.objects.filter(version='1.0', is_active=True).first()
print(f"\n✓ T&C Available: {terms is not None}")
if terms:
    print(f"  Version: {terms.version}")
    print(f"  Content Length: {len(terms.content):,} characters")

# Create a test request with T&C acceptance
factory = RequestFactory()
request = factory.post('/accounts/signup/')

# Add session and auth middleware
middleware = SessionMiddleware(lambda x: None)
middleware.process_request(request)
auth_middleware = AuthenticationMiddleware(lambda x: None)
auth_middleware.process_request(request)
request.session.save()

# Add T&C to POST data
request.POST = request.POST.copy()
request.POST['accept_terms'] = 'on'

# Test signup form data
test_email = 'testhotel@example.com'
signup_data = {
    'email': test_email,
    'password1': 'SecurePassword123!',
    'password2': 'SecurePassword123!',
    'accept_terms': 'on',
}

print(f"\n📧 Test Signup Data:")
print(f"  Email: {signup_data['email']}")
print(f"  Password: ****** (strong password)")
print(f"  Accept Terms: {signup_data['accept_terms']}")

# Clean up if exists
if User.objects.filter(email=test_email).exists():
    User.objects.filter(email=test_email).delete()
    print(f"\n🧹 Cleaned up existing user")

# Test form validation
print(f"\n🧪 Testing SignupForm Validation:")
print("-" * 80)

form = SignupForm(data=signup_data)
if form.is_valid():
    print("  ✓ Form is VALID")
    print(f"    Email: {form.cleaned_data['email']}")
else:
    print("  ❌ Form ERRORS:")
    for field, errors in form.errors.items():
        for error in errors:
            print(f"    - {field}: {error}")

# Try to save the user
print(f"\n💾 Testing User Creation with T&C:")
print("-" * 80)

try:
    if form.is_valid():
        user, resp = form.try_save(request)
        print(f"  ✓ User created successfully!")
        print(f"    Email: {user.email}")
        print(f"    Username: {user.username}")
        print(f"    Terms Accepted: {user.terms_accepted}")
        print(f"    Terms Version: {user.terms_version}")
        print(f"    Accepted At: {user.terms_accepted_at}")
        
        # Verify T&C was accepted
        if user.terms_accepted and user.terms_version == '1.0':
            print(f"\n  ✅ T&C ACCEPTANCE CONFIRMED!")
        else:
            print(f"\n  ⚠️  T&C ACCEPTANCE NOT RECORDED")
        
        # Clean up
        user.delete()
        print(f"\n  ✓ Test user cleaned up")
    else:
        print("  ⚠️  Form validation failed")
        
except Exception as e:
    print(f"  ❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ SIGNUP FLOW TEST COMPLETE")
print("=" * 80)
print("\nNext step: Test in browser at http://localhost:8000/accounts/signup/")
print("=" * 80)
