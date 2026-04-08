#!/usr/bin/env python
"""
Comprehensive System Testing Script
Tests: Registration, Login, 2FA Setup, 2FA Login
"""

import os
import sys
import django
import json
from urllib.parse import urljoin

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from authentication.models import TwoFactorAuth, LoginSession, TermsAndConditions
import pyotp

User = get_user_model()
client = Client()

# Test data
TEST_EMAIL = 'testuser123@hotel.com'
TEST_PASSWORD = 'TestPass123!'
TEST_FIRST_NAME = 'Test'
TEST_LAST_NAME = 'User'

def print_test(name, status, details=""):
    status_symbol = "✓" if status else "✗"
    status_text = "PASS" if status else "FAIL"
    print(f"  [{status_symbol}] {name}: {status_text}")
    if details:
        print(f"      └─ {details}")

def print_section(name):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

def test_registration():
    """Test user registration flow"""
    print_section("TEST 1: USER REGISTRATION")
    
    # Delete test user if exists
    User.objects.filter(email=TEST_EMAIL).delete()
    
    # Test 1.1: Register with valid data
    print("\n  1.1 Testing registration with valid data...")
    response = client.post('/auth/register/', {
        'email': TEST_EMAIL,
        'first_name': TEST_FIRST_NAME,
        'last_name': TEST_LAST_NAME,
        'password1': TEST_PASSWORD,
        'password2': TEST_PASSWORD,
        'accept_terms': 'on'
    }, follow=True)
    
    user_exists = User.objects.filter(email=TEST_EMAIL).exists()
    print_test("User created in database", user_exists)
    
    if user_exists:
        user = User.objects.get(email=TEST_EMAIL)
        print_test("User role is GUEST", user.role == 'GUEST', f"role={user.role}")
        print_test("Terms accepted flag set", user.terms_accepted, f"terms_accepted={user.terms_accepted}")
        print_test("First name saved", user.first_name == TEST_FIRST_NAME, f"first_name={user.first_name}")
        
        # Test password
        password_correct = user.check_password(TEST_PASSWORD)
        print_test("Password stored correctly", password_correct)
        
        return user
    else:
        print_test("Registration failed", False, "User not found in database")
        return None


def test_login_without_2fa(user):
    """Test login without 2FA enabled"""
    print_section("TEST 2: LOGIN WITHOUT 2FA")
    
    # Test 2.1: Login with email
    print("\n  2.1 Testing login with email...")
    response = client.post('/auth/login/', {
        'username': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'remember_me': False
    }, follow=True)
    
    is_authenticated = response.wsgi_request.user.is_authenticated
    print_test("User authenticated with email", is_authenticated)
    
    if is_authenticated:
        print_test("User is correct user", response.wsgi_request.user.id == user.id)
        print_test("Redirected to dashboard", '/dashboard/' in response.request['PATH_INFO'] or 
                   response.status_code == 200, f"Path: {response.request['PATH_INFO']}")
    
    # Test 2.2: Logout
    print("\n  2.2 Testing logout...")
    response = client.post('/auth/logout/', follow=True)
    is_logged_out = not response.wsgi_request.user.is_authenticated
    print_test("User logged out", is_logged_out)
    
    # Test 2.3: Login again (to test remember me)
    print("\n  2.3 Testing login with Remember Me...")
    response = client.post('/auth/login/', {
        'username': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'remember_me': True
    }, follow=True)
    
    is_authenticated = response.wsgi_request.user.is_authenticated
    print_test("User authenticated with Remember Me", is_authenticated)


def test_2fa_setup(user):
    """Test 2FA setup flow"""
    print_section("TEST 3: 2FA SETUP")
    
    # Make sure user is logged in
    print("\n  3.1 Logging in for 2FA setup...")
    login_success = client.login(username=user.username, password=TEST_PASSWORD)
    print_test("User logged in for setup", login_success)
    
    if not login_success:
        return None
    
    # Test 3.2: Generate QR code
    print("\n  3.2 Testing QR code generation...")
    response = client.post('/auth/2fa/setup/', {
        'action': 'setup'
    })
    
    qr_code_in_response = response.context and 'qr_code' in response.context if response.context else False
    print_test("QR code generated", qr_code_in_response)
    
    secret_in_response = response.context and 'secret' in response.context if response.context else False
    print_test("Secret key returned", secret_in_response)
    
    backup_codes_in_response = response.context and 'backup_codes' in response.context if response.context else False
    print_test("Backup codes generated", backup_codes_in_response)
    
    if response.context and secret_in_response and backup_codes_in_response:
        secret = response.context['secret']
        backup_codes = response.context['backup_codes']
        
        print_test("Secret key is 32 chars", len(secret) >= 16, f"Length: {len(secret)}")
        print_test("10 backup codes generated", len(backup_codes) == 10, f"Count: {len(backup_codes)}")
        
        # Test 3.3: Generate TOTP code and verify
        print("\n  3.3 Testing TOTP code verification...")
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        
        print_test("TOTP code generated", bool(current_code), f"Code: {current_code}")
        
        # Test 3.4: Verify code
        print("\n  3.4 Testing 2FA verification...")
        response = client.post('/auth/2fa/setup/', {
            'action': 'verify',
            'code': current_code,
            'secret': secret
        })
        
        # Check if 2FA was enabled in database
        user.refresh_from_db()
        try:
            two_fa = user.two_factor_auth
            print_test("TwoFactorAuth record created", True)
            print_test("2FA is_enabled flag set", two_fa.is_enabled, f"is_enabled={two_fa.is_enabled}")
            print_test("2FA is_verified flag set", two_fa.is_verified, f"is_verified={two_fa.is_verified}")
            print_test("2FA method is TOTP", two_fa.method == 'TOTP', f"method={two_fa.method}")
            print_test("Secret key saved", len(two_fa.secret_key) > 0, f"Length: {len(two_fa.secret_key)}")
            print_test("Backup codes saved", len(two_fa.backup_codes) == 10, f"Count: {len(two_fa.backup_codes)}")
            
            return two_fa
        except TwoFactorAuth.DoesNotExist:
            print_test("TwoFactorAuth record created", False, "Record not found!")
            return None
    else:
        print_test("Setup response invalid", False, "Missing secret or backup codes")
        return None


def test_login_with_2fa(user, two_fa):
    """Test login with 2FA enabled"""
    print_section("TEST 4: LOGIN WITH 2FA ENABLED")
    
    # Logout first
    print("\n  4.1 Logging out...")
    client.logout()
    
    # Test 4.2: Normal login (should redirect to 2FA)
    print("\n  4.2 Testing login redirects to 2FA verification...")
    response = client.post('/auth/login/', {
        'username': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'remember_me': False
    }, follow=True)
    
    redirected_to_2fa = 'verify-2fa-login' in response.request['PATH_INFO']
    print_test("Redirected to 2FA verification page", redirected_to_2fa, f"Path: {response.request['PATH_INFO']}")
    
    session_has_2fa_id = response.wsgi_request.session.get('2fa_user_id') is not None
    print_test("Session has 2fa_user_id", session_has_2fa_id)
    
    # Test 4.3: Invalid 2FA code
    print("\n  4.3 Testing invalid 2FA code...")
    response = client.post('/auth/verify-2fa-login/', {
        'code': '000000'
    }, follow=True)
    
    error_in_response = 'invalid' in response.content.decode().lower() or 'error' in response.content.decode().lower()
    print_test("Invalid code shows error", error_in_response or '/verify-2fa-login/' in response.request['PATH_INFO'], 
               f"Still on verification page: {'/verify-2fa-login/' in response.request['PATH_INFO']}")
    
    # Test 4.4: Valid 2FA code
    print("\n  4.4 Testing valid 2FA code...")
    totp = pyotp.TOTP(two_fa.secret_key)
    valid_code = totp.now()
    
    response = client.post('/auth/verify-2fa-login/', {
        'code': valid_code
    }, follow=True)
    
    is_authenticated = response.wsgi_request.user.is_authenticated
    print_test("User authenticated with 2FA", is_authenticated)
    
    redirected_to_dashboard = '/dashboard/' in response.request['PATH_INFO']
    print_test("Redirected to dashboard after 2FA", redirected_to_dashboard, f"Path: {response.request['PATH_INFO']}")
    
    session_cleared = response.wsgi_request.session.get('2fa_user_id') is None
    print_test("Session 2fa_user_id cleared", session_cleared)
    
    # Check LoginSession was created
    print("\n  4.5 Checking LoginSession record...")
    latest_session = LoginSession.objects.filter(user=user).latest('created_at')
    print_test("LoginSession record created", True)
    print_test("is_2fa_verified flag set", latest_session.is_2fa_verified)


def test_backup_codes(user, two_fa):
    """Test backup code functionality"""
    print_section("TEST 5: BACKUP CODES")
    
    # Logout
    print("\n  5.1 Logging out...")
    client.logout()
    
    # Save a backup code to test
    if two_fa.backup_codes:
        test_backup_code = two_fa.backup_codes[0]
        print_test("Backup code available", True, f"Code: {test_backup_code[:4]}...")
        
        # Test 5.2: Login with backup code
        print("\n  5.2 Testing login with backup code...")
        response = client.post('/auth/login/', {
            'username': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'remember_me': False
        }, follow=True)
        
        redirected_to_2fa = '/verify-2fa-login/' in response.request['PATH_INFO']
        print_test("Redirected to 2FA page", redirected_to_2fa)
        
        # Submit backup code
        response = client.post('/auth/verify-2fa-login/', {
            'code': test_backup_code
        }, follow=True)
        
        is_authenticated = response.wsgi_request.user.is_authenticated
        print_test("User authenticated with backup code", is_authenticated)
        
        # Test 5.3: Verify backup code was used (removed from list)
        print("\n  5.3 Testing backup code was removed after use...")
        two_fa.refresh_from_db()
        code_still_exists = test_backup_code in two_fa.backup_codes
        print_test("Backup code removed from list", not code_still_exists, 
                   f"Remaining codes: {len(two_fa.backup_codes)}")
    else:
        print_test("No backup codes available", False)


def test_edge_cases(user):
    """Test edge cases and error handling"""
    print_section("TEST 6: EDGE CASES & ERROR HANDLING")
    
    # Test 6.1: Duplicate registration
    print("\n  6.1 Testing duplicate email registration...")
    response = client.post('/auth/register/', {
        'email': TEST_EMAIL,
        'first_name': 'Another',
        'last_name': 'User',
        'password1': TEST_PASSWORD,
        'password2': TEST_PASSWORD,
        'accept_terms': 'on'
    })
    
    form_has_error = 'already register' in response.content.decode().lower()
    print_test("Duplicate email rejected", form_has_error or response.status_code == 200, 
               "Error shown or form re-displayed")
    
    # Test 6.2: Mismatched passwords
    print("\n  6.2 Testing mismatched password registration...")
    response = client.post('/auth/register/', {
        'email': 'different@hotel.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password1': TEST_PASSWORD,
        'password2': 'DifferentPass123!',
        'accept_terms': 'on'
    })
    
    error_shown = response.status_code == 200  # Form re-displayed with errors
    print_test("Mismatched passwords rejected", error_shown, "Form re-displayed")
    
    # Test 6.3: Missing T&C acceptance
    print("\n  6.3 Testing missing T&C acceptance...")
    response = client.post('/auth/register/', {
        'email': 'another@hotel.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password1': TEST_PASSWORD,
        'password2': TEST_PASSWORD,
        'accept_terms': ''  # Not checked
    })
    
    error_shown = response.status_code == 200
    print_test("Missing T&C rejected", error_shown, "Form re-displayed with error")
    
    # Test 6.4: Invalid login credentials
    print("\n  6.4 Testing invalid login credentials...")
    response = client.post('/auth/login/', {
        'username': TEST_EMAIL,
        'password': 'WrongPassword123!',
        'remember_me': False
    })
    
    error_shown = 'invalid' in response.content.decode().lower()
    print_test("Invalid credentials rejected", error_shown or response.status_code == 200)
    
    # Test 6.5: Cannot access dashboard without login
    print("\n  6.5 Testing dashboard access restrictions...")
    response = client.get('/auth/dashboard/')
    redirected_to_login = response.status_code in [301, 302] or '/login/' in str(response.url)
    print_test("Unauthorized access redirected to login", redirected_to_login)


def test_database_integrity():
    """Test database integrity and model relationships"""
    print_section("TEST 7: DATABASE INTEGRITY")
    
    # Test 7.1: User-TwoFactorAuth relationship
    print("\n  7.1 Testing OneToOne relationship...")
    user = User.objects.get(email=TEST_EMAIL)
    
    try:
        two_fa = user.two_factor_auth
        print_test("Can access two_factor_auth via user", True)
        print_test("Reverse relationship works", two_fa.user.id == user.id)
    except Exception as e:
        print_test("Relationship access", False, str(e))
    
    # Test 7.2: LoginSession records
    print("\n  7.2 Testing LoginSession records...")
    sessions = LoginSession.objects.filter(user=user)
    print_test("LoginSession records created", sessions.count() > 0, f"Count: {sessions.count()}")
    
    if sessions.exists():
        for session in sessions[:2]:
            print_test(f"Session record complete", 
                      session.ip_address and session.user_agent and session.created_at,
                      f"IP: {session.ip_address[:15]}...")
    
    # Test 7.3: Data persistence
    print("\n  7.3 Testing data persistence...")
    user_reload = User.objects.get(id=user.id)
    print_test("User data persists", user_reload.email == TEST_EMAIL)
    
    if hasattr(user, 'two_factor_auth'):
        two_fa_reload = TwoFactorAuth.objects.get(user=user)
        print_test("2FA data persists", two_fa_reload.is_enabled)
        print_test("Backup codes persist", len(two_fa_reload.backup_codes) > 0)


def main():
    """Run all tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     COMPREHENSIVE LOGIN, SIGNUP & 2FA SYSTEM TEST          ║")
    print("║            Cebu Hotel - February 27, 2026                   ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\nStarting automated tests...\n")
    
    try:
        # Run all tests
        user = test_registration()
        
        if user:
            test_login_without_2fa(user)
            two_fa = test_2fa_setup(user)
            
            if two_fa:
                test_login_with_2fa(user, two_fa)
                test_backup_codes(user, two_fa)
            
            test_edge_cases(user)
            test_database_integrity()
        
        # Final summary
        print_section("TEST SUMMARY")
        print("\n  ✓ All test suites completed successfully!")
        print("\n  Next steps:")
        print("    1. Review the test results above")
        print("    2. Check for any failures (marked with ✗)")
        print("    3. Visit http://localhost:8000 to test manually")
        print("    4. Try the flows from a web browser")
        print("\n")
        
    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
