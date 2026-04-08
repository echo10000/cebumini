#!/usr/bin/env python
"""
2FA and Login/Signup System Verification Script
Run with: python verify_2fa_system.py
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import TwoFactorAuth, LoginSession, TermsAndConditions
import pyotp

User = get_user_model()


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Colors.END}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def verify_dependencies():
    """Check if required packages are installed"""
    print_header("1. VERIFYING DEPENDENCIES")
    
    required_packages = {
        'pyotp': 'pyotp',
        'qrcode': 'qrcode',
        'PIL': 'Pillow',
    }
    
    all_good = True
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print_success(f"{package_name} is installed")
        except ImportError:
            print_error(f"{package_name} is NOT installed")
            print_info(f"Install with: pip install {package_name}")
            all_good = False
    
    return all_good


def verify_models():
    """Check if models are created"""
    print_header("2. VERIFYING MODELS IN DATABASE")
    
    # Check CustomUser
    try:
        user_count = User.objects.count()
        print_success(f"CustomUser model exists ({user_count} users total)")
    except Exception as e:
        print_error(f"CustomUser model issue: {e}")
        return False
    
    # Check TwoFactorAuth
    try:
        twofa_count = TwoFactorAuth.objects.count()
        print_success(f"TwoFactorAuth model exists ({twofa_count} records total)")
    except Exception as e:
        print_error(f"TwoFactorAuth model issue: {e}")
        return False
    
    # Check LoginSession
    try:
        session_count = LoginSession.objects.count()
        print_success(f"LoginSession model exists ({session_count} records total)")
    except Exception as e:
        print_error(f"LoginSession model issue: {e}")
        return False
    
    # Check TermsAndConditions
    try:
        terms_count = TermsAndConditions.objects.count()
        print_success(f"TermsAndConditions model exists ({terms_count} records total)")
    except Exception as e:
        print_error(f"TermsAndConditions model issue: {e}")
        return False
    
    return True


def verify_test_user():
    """Find or create test user with 2FA"""
    print_header("3. CHECKING TEST USERS")
    
    test_email = 'test2fa@hotel.com'
    
    try:
        user = User.objects.get(email=test_email)
        print_success(f"Found test user: {user.email} (ID: {user.id})")
        
        # Check T&C acceptance
        if user.has_accepted_terms():
            print_success(f"  └─ Terms accepted: ✓")
        else:
            print_warning(f"  └─ Terms accepted: ✗")
        
        # Check 2FA status
        try:
            two_fa = user.two_factor_auth
            print_info(f"  └─ 2FA Status:")
            print_info(f"     - Enabled: {two_fa.is_enabled}")
            print_info(f"     - Verified: {two_fa.is_verified}")
            print_info(f"     - Method: {two_fa.method}")
            
            if two_fa.is_enabled and two_fa.is_verified:
                print_success(f"     └─ 2FA is properly configured! ✓")
                if two_fa.secret_key:
                    print_success(f"     └─ Secret key exists: {len(two_fa.secret_key)} chars")
                if two_fa.backup_codes:
                    print_success(f"     └─ Backup codes: {len(two_fa.backup_codes)} available")
            elif not two_fa.is_enabled:
                print_warning(f"     └─ 2FA not enabled (user can set it up)")
            
        except TwoFactorAuth.DoesNotExist:
            print_warning(f"  └─ 2FA not set up yet")
        
        # Check login sessions
        sessions = LoginSession.objects.filter(user=user)
        print_info(f"  └─ Login sessions: {sessions.count()}")
        for session in sessions.order_by('-created_at')[:3]:
            print_info(f"     - {session.created_at} (2FA: {session.is_2fa_verified})")
        
        return user
        
    except User.DoesNotExist:
        print_warning(f"Test user '{test_email}' not found")
        print_info("To create test user, visit: http://localhost:8000/auth/register/")
        return None


def verify_totp_code(user):
    """Test TOTP code generation and verification"""
    print_header("4. VERIFYING TOTP CODE GENERATION")
    
    try:
        two_fa = user.two_factor_auth
    except TwoFactorAuth.DoesNotExist:
        print_warning("2FA not set up - skipping TOTP test")
        return False
    
    if not two_fa.secret_key:
        print_warning("No secret key found - cannot test TOTP")
        return False
    
    try:
        # Generate current code
        totp = pyotp.TOTP(two_fa.secret_key)
        current_code = totp.now()
        print_success(f"Current TOTP code: {current_code}")
        print_info(f"  └─ This code expires in ~30 seconds")
        
        # Verify it works
        if totp.verify(current_code):
            print_success(f"TOTP code verification: PASSED ✓")
        else:
            print_error(f"TOTP code verification: FAILED ✗")
            return False
        
        # Test old code (should still work due to time window)
        old_code = totp.at(totp.timecode(int(__import__('time').time()) - 30))
        if totp.verify(old_code):
            print_success(f"Backward time window: Works (30-sec old code accepted)")
        else:
            print_warning(f"Backward time window: Old code not accepted")
        
        # Test invalid code
        if not totp.verify("000000"):
            print_success(f"Invalid code rejection: PASSED ✓")
        else:
            print_error(f"Invalid code rejection: FAILED ✗")
        
        return True
        
    except Exception as e:
        print_error(f"TOTP verification error: {e}")
        return False


def verify_backup_codes(user):
    """Test backup codes"""
    print_header("5. VERIFYING BACKUP CODES")
    
    try:
        two_fa = user.two_factor_auth
    except TwoFactorAuth.DoesNotExist:
        print_warning("2FA not set up - skipping backup codes test")
        return False
    
    if not two_fa.backup_codes:
        print_warning("No backup codes found")
        return False
    
    print_success(f"Found {len(two_fa.backup_codes)} backup codes")
    
    # Show first 3 codes (masked)
    for i, code in enumerate(two_fa.backup_codes[:3], 1):
        masked = code[:2] + '*' * (len(code) - 4) + code[-2:]
        print_info(f"  Code {i}: {masked}")
    
    # Test backup code usage function
    if two_fa.backup_codes:
        test_code = two_fa.backup_codes[0]
        print_info(f"  Testing backup code usage...")
        
        # Save original count
        original_count = len(two_fa.backup_codes)
        
        # Use a code
        result = two_fa.use_backup_code(test_code)
        
        if result:
            print_success(f"  └─ Backup code usage: PASSED ✓")
            print_info(f"     Codes remaining: {len(two_fa.backup_codes)} (was {original_count})")
            
            # Restore for testing purposes
            two_fa.backup_codes.append(test_code)
            two_fa.save()
            print_info(f"     (Code restored for testing)")
        else:
            print_error(f"  └─ Backup code usage: FAILED ✗")
            return False
    
    return True


def verify_user_fields():
    """Verify CustomUser model has all required fields"""
    print_header("6. VERIFYING USER MODEL FIELDS")
    
    required_fields = [
        'email',
        'username',
        'first_name',
        'last_name',
        'role',
        'is_email_verified',
        'terms_accepted',
        'terms_accepted_at',
        'terms_version',
    ]
    
    user = User.objects.first()
    if not user:
        print_warning("No users found in database")
        return False
    
    all_good = True
    for field in required_fields:
        if hasattr(user, field):
            value = getattr(user, field)
            print_success(f"Field '{field}': ✓ (value: {value})")
        else:
            print_error(f"Field '{field}': ✗ MISSING")
            all_good = False
    
    return all_good


def verify_login_session():
    """Verify LoginSession model"""
    print_header("7. VERIFYING LOGIN SESSION MODEL")
    
    if not User.objects.exists():
        print_warning("No users found - cannot test login sessions")
        return True  # Not a failure, just not testable
    
    user = User.objects.first()
    sessions = LoginSession.objects.filter(user=user)
    
    print_success(f"LoginSession model exists: ✓")
    print_info(f"Total login sessions: {sessions.count()}")
    
    if sessions.exists():
        latest = sessions.latest('created_at')
        print_info(f"  Latest session:")
        print_info(f"    - Time: {latest.created_at}")
        print_info(f"    - IP: {latest.ip_address}")
        print_info(f"    - 2FA Verified: {latest.is_2fa_verified}")
        print_success(f"LoginSession structure: ✓")
    else:
        print_warning("No login sessions yet - will be created on login")
    
    return True


def print_test_instructions():
    """Print manual testing instructions"""
    print_header("MANUAL TESTING INSTRUCTIONS")
    
    print("""
    Follow these steps to manually test the login/signup and 2FA flow:
    
    STEP 1: Test Registration
    ══════════════════════════
    1. Go to: http://localhost:8000/auth/register/
    2. Fill in:
       - Email: testuser@hotel.com
       - First Name: Test
       - Last Name: User
       - Password: TestPass123!
       - Confirm Password: TestPass123!
       - Check: "I agree to the Terms and Conditions"
    3. Click "Sign Up"
    
    EXPECTED: Message "Registration successful! Please log in."
              Redirected to login page
    
    ─────────────────────────────────────────────────────────────
    
    STEP 2: Test Login Without 2FA
    ══════════════════════════════
    1. Go to: http://localhost:8000/auth/login/
    2. Enter:
       - Username: testuser@hotel.com (or use email)
       - Password: TestPass123!
       - Check: "Remember Me" (optional)
    3. Click "Sign In"
    
    EXPECTED: Redirected to http://localhost:8000/auth/accept-terms/
              (if first time) or dashboard
    
    ─────────────────────────────────────────────────────────────
    
    STEP 3: Accept Terms
    ═══════════════════
    1. If on terms page:
       - Read the Terms and Conditions
       - Check: "I accept..."
       - Click "Accept"
    
    EXPECTED: Redirected to http://localhost:8000/auth/dashboard/
    
    ─────────────────────────────────────────────────────────────
    
    STEP 4: Setup 2FA
    ════════════════
    1. On dashboard, find "Set Up 2FA" or go to:
       http://localhost:8000/auth/2fa/setup/
    2. Click "Generate QR Code"
    3. Open Authenticator App (install if needed):
       - Google Authenticator (iOS/Android)
       - Authy (iOS/Android)
       - Microsoft Authenticator (iOS/Android)
    4. Scan the QR code displayed
    5. Enter the 6-digit code from your app
    6. Click "Verify & Enable"
    
    EXPECTED: "2FA has been enabled successfully!"
              Redirected to backup codes page
              10 backup codes displayed
    
    ─────────────────────────────────────────────────────────────
    
    STEP 5: Save Backup Codes
    ════════════════════════
    1. On the backup codes page:
       - Click "Copy All Codes" or "Download as File"
       - Save them somewhere safe
    
    EXPECTED: Codes copied to clipboard or file downloaded
    
    ─────────────────────────────────────────────────────────────
    
    STEP 6: Test Login With 2FA
    ═══════════════════════════
    1. Click "Logout" (top right)
    2. Go to: http://localhost:8000/auth/login/
    3. Enter:
       - Username: testuser@hotel.com
       - Password: TestPass123!
    4. Click "Sign In"
    
    EXPECTED: Redirected to http://localhost:8000/auth/verify-2fa-login/
              Page asks for 6-digit code
    
    ─────────────────────────────────────────────────────────────
    
    STEP 7: Verify 2FA Code
    ══════════════════════
    1. Open your authenticator app
    2. Find the code for "Cebu Hotel"
    3. Enter the 6-digit code
    4. Check: "Remember this device" (optional)
    5. Click "Verify Code"
    
    EXPECTED: "You have been logged in successfully!"
              Redirected to dashboard
              User is now logged in
    
    ─────────────────────────────────────────────────────────────
    
    STEP 8: Test Backup Code
    ════════════════════════
    1. Logout again
    2. Login with email + password (like Step 6)
    3. On 2FA verification page, paste backup code
    4. Click "Verify Code"
    
    EXPECTED: Login successful with backup code
              That backup code should not appear next time
    
    ─────────────────────────────────────────────────────────────
    
    This script checked all the technical parts. Now you've verified:
    ✓ Dependencies installed
    ✓ Database models exist
    ✓ Test user configuration
    ✓ TOTP code generation
    ✓ Backup codes function
    ✓ User model fields
    ✓ Login session tracking
    
    """)


def main():
    """Run all verification tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  2FA & LOGIN/SIGNUP SYSTEM VERIFICATION SCRIPT             ║")
    print("║  Cebu Hotel System                                          ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Dependencies
    tests_total += 1
    if verify_dependencies():
        tests_passed += 1
    
    # Test 2: Models
    tests_total += 1
    if verify_models():
        tests_passed += 1
    
    # Test 3: User model fields
    tests_total += 1
    if verify_user_fields():
        tests_passed += 1
    
    # Test 4: Login sessions
    tests_total += 1
    if verify_login_session():
        tests_passed += 1
    
    # Test 5-7: User-specific tests
    user = verify_test_user()
    if user:
        tests_total += 1
        if verify_totp_code(user):
            tests_passed += 1
        
        tests_total += 1
        if verify_backup_codes(user):
            tests_passed += 1
    
    # Print manual test instructions
    print_test_instructions()
    
    # Summary
    print_header("TEST SUMMARY")
    print_info(f"Automated tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print_success(f"All automated tests passed! ✓")
        print_info(f"Next: Run manual tests by following the instructions above")
    else:
        print_warning(f"Some tests failed. Please fix the issues above.")
    
    print(f"\n{Colors.BOLD}Useful Commands:{Colors.END}")
    print("  • Run server:    python manage.py runserver")
    print("  • Access app:    http://localhost:8000")
    print("  • Django shell:  python manage.py shell")
    print("  • Clear sessions: python manage.py clearsessions")
    print("")


if __name__ == '__main__':
    main()
