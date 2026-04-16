#!/usr/bin/env python
"""
Detailed diagnostics for user authentication and 2FA issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from authentication.models import TwoFactorAuth, UserRole

User = get_user_model()

print("\n" + "=" * 80)
print("USER AUTHENTICATION & 2FA DIAGNOSTICS".center(80))
print("=" * 80)

# ============================================================================
# 1. DIAGNOSE USER AUTHENTICATION ISSUES
# ============================================================================
print("\n[DIAGNOSIS 1] USER AUTHENTICATION ISSUES".center(80))
print("-" * 80)

# List all users
print("All Users in Database:")
for user in User.objects.all():
    print(f"  • {user.username} | {user.email} | {user.get_role_display()} | Active: {user.is_active}")

print("\n" + "-" * 80)
print("Testing Authentication for Each User:")
print("-" * 80)

# Test authentication for each user
test_cases = [
    ('admin_super', 'AdminPass123!', 'Admin'),
    ('guest_john', 'GuestPass123!', 'Guest'),
    ('staff_emily', 'StaffPass123!', 'Staff'),
    ('manager_alex', 'ManagerPass123!', 'Manager'),
]

for username, password, role in test_cases:
    user = User.objects.filter(username=username).first()
    if user:
        # Try authentication
        auth_result = authenticate(username=username, password=password)
        
        print(f"\n✓ User: {username} ({role})")
        print(f"  └─ Exists: Yes")
        print(f"  └─ Email: {user.email}")
        print(f"  └─ Is Active: {user.is_active}")
        print(f"  └─ Has Usable Password: {user.has_usable_password()}")
        
        if auth_result:
            print(f"  └─ Authentication: ✓ SUCCESS")
        else:
            print(f"  └─ Authentication: ✗ FAILED")
            
            # Try different password scenarios
            if user.check_password('GuestPass123!'):
                print(f"     └─ Actual password appears to be: GuestPass123!")
            elif user.check_password('StaffPass123!'):
                print(f"     └─ Actual password appears to be: StaffPass123!")
            elif user.check_password('ManagerPass123!'):
                print(f"     └─ Actual password appears to be: ManagerPass123!")
            elif user.check_password('AdminPass123!'):
                print(f"     └─ Actual password appears to be: AdminPass123!")
            else:
                print(f"     └─ Password does not match expected values")
    else:
        print(f"\n✗ User: {username} - NOT FOUND IN DATABASE")

# ============================================================================
# 2. SETUP 2FA FOR TEST USERS
# ============================================================================
print("\n\n[DIAGNOSIS 2] TWO FACTOR AUTHENTICATION SETUP".center(80))
print("-" * 80)

# Create 2FA records for some users
users_to_enable_2fa = [
    User.objects.filter(role=UserRole.GUEST).first(),
    User.objects.filter(role=UserRole.STAFF).first(),
    User.objects.filter(role=UserRole.ADMIN).first(),
]

for user in users_to_enable_2fa:
    if user:
        # Delete existing 2FA record if any
        TwoFactorAuth.objects.filter(user=user).delete()
        
        # Create new 2FA record
        twofa = TwoFactorAuth.objects.create(
            user=user,
            is_enabled=True,
            is_verified=True,
            method='TOTP',
            secret_key='JBSWY3DPEBLW64TMMQ======',  # Example TOTP secret
        )
        
        print(f"✓ Created 2FA for {user.username}:")
        print(f"  └─ Method: TOTP (Authenticator App)")
        print(f"  └─ Status: Enabled & Verified")
        print(f"  └─ Secret Key: {twofa.secret_key}")

# Verify 2FA records
print(f"\n✓ 2FA Setup Complete:")
twofa_count = TwoFactorAuth.objects.count()
enabled_count = TwoFactorAuth.objects.filter(is_enabled=True).count()
verified_count = TwoFactorAuth.objects.filter(is_verified=True).count()
print(f"  └─ Total 2FA Records: {twofa_count}")
print(f"  └─ Enabled: {enabled_count}")
print(f"  └─ Verified: {verified_count}")

print("\n" + "=" * 80)
print("DIAGNOSTICS COMPLETE".center(80))
print("=" * 80 + "\n")
