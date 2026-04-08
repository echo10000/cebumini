# System Flow Diagrams - Visual Reference

## 1. Registration Flow
```
START
  │
  ├─→ User visits /auth/register/
  │
  ├─→ Form displayed with fields:
  │   • Email (required, unique)
  │   • First Name (required)
  │   • Last Name (required)
  │   • Password (required, confirmed)
  │   • Accept T&C checkbox (required)
  │
  ├─→ User fills form and clicks "Sign Up"
  │
  ├─→ Backend validation:
  │   ├─ Email unique? 
  │   │  ├─ NO → Show error "Email already registered"
  │   │  └─ YES ✓
  │   │
  │   ├─ Passwords match?
  │   │  ├─ NO → Show error "Passwords don't match"
  │   │  └─ YES ✓
  │   │
  │   └─ T&C accepted?
  │      ├─ NO → Show error "Accept T&C"
  │      └─ YES ✓
  │
  ├─→ All validations pass:
  │   ├─ Create CustomUser
  │   ├─ Set role = 'GUEST'
  │   ├─ Set terms_accepted = True
  │   ├─ Set terms_accepted_at = now
  │
  ├─→ Show success message:
  │   "Registration successful! Please log in."
  │
  ├─→ Redirect to /auth/login/
  │
  END
```

## 2. Login Flow (Decision Tree)

```
START (/auth/login/)
  │
  ├─→ User enters:
  │   ├─ Email or Username
  │   ├─ Password
  │   └─ (Optional) Check "Remember Me"
  │
  ├─→ POST to login_view()
  │
  ├─→ STEP 1: Authenticate
  │   ├─ Try: authenticate(username=input, password=pwd)
  │   └─ If fails, try: User.objects.get(email=input) then authenticate
  │
  ├─→ DECISION: Credentials valid?
  │   │
  │   ├─ NO ✗
  │   │  ├─ Show error: "Invalid username or password"
  │   │  ├─ Stay on /auth/login/ page
  │   │  └─ User can retry
  │   │
  │   └─ YES ✓
  │      └─ Continue to STEP 2
  │
  ├─→ STEP 2: Check 2FA Status
  │   ├─ Get user.two_factor_auth
  │   │
  │   └─ DECISION: two_fa.is_enabled AND two_fa.is_verified?
  │      │
  │      ├─ YES (2FA Enabled)
  │      │  ├─ Set session['2fa_user_id'] = user.id
  │      │  ├─ Set session['2fa_remember_me'] = remember_me
  │      │  ├─ Redirect to /auth/verify-2fa-login/
  │      │  └─ STOP (Go to 2FA Verification Flow)
  │      │
  │      └─ NO (2FA Disabled)
  │         └─ Continue to STEP 3
  │
  ├─→ STEP 3: Check T&C Acceptance
  │   ├─ DECISION: user.terms_accepted?
  │   │
  │   ├─ NO ✗
  │   │  ├─ Redirect to /auth/accept-terms/
  │   │  └─ Message: "Please accept Terms"
  │   │
  │   └─ YES ✓
  │      └─ Continue to STEP 4
  │
  ├─→ STEP 4: Perform Login
  │   ├─ login(request, user)
  │   │
  │   ├─ DECISION: Remember Me checked?
  │   │  ├─ YES: Set session expiry to 30 days
  │   │  └─ NO: Session expires at browser close
  │   │
  │   ├─ Show message: "Welcome back, [First Name]!"
  │   │
  │   ├─ Redirect to /auth/dashboard/
  │   │
  │   └─ SUCCESS ✓
  │
  END
```

## 3. 2FA Setup Flow (Detailed)

```
User logged in → Clicks "Setup 2FA"
  │
  ├─→ GET /auth/2fa/setup/
  │   └─ Display setup page with "Generate QR Code" button
  │
  ├─→ User clicks "Generate QR Code"
  │
  ├─→ Backend (POST action='setup'):
  │   │
  │   ├─ STEP 1: Generate Secret
  │   │  ├─ secret = pyotp.random_base32()
  │   │  ├─ Example: "JBSWY3DPEBLW64TMMQ..."
  │   │  └─ Save to TwoFactorAuth.secret_key
  │   │
  │   ├─ STEP 2: Generate QR Code Image
  │   │  ├─ totp = pyotp.TOTP(secret)
  │   │  ├─ uri = totp.provisioning_uri(
  │   │  │       name=user.email,
  │   │  │       issuer_name='Cebu Hotel'
  │   │  │   )
  │   │  ├─ qrcode.QRCode() → image
  │   │  └─ Convert to base64 PNG for HTML
  │   │
  │   ├─ STEP 3: Generate Backup Codes
  │   │  ├─ Generate 10 random hex codes
  │   │  ├─ Example: "a1b2c3d4", "e5f6g7h8", etc.
  │   │  └─ Save to TwoFactorAuth.backup_codes (JSON)
  │   │
  │   └─ Return setup page with:
  │      ├─ QR code image
  │      ├─ Secret key (hidden field)
  │      └─ 10 backup codes (SHOWN but not saved yet)
  │
  ├─→ User's Action:
  │   ├─ Opens Authenticator App (Google Authenticator, Authy, etc.)
  │   ├─ Scans QR code
  │   ├─ App displays "Cebu Hotel" with 6-digit code
  │   ├─ Code changes every 30 seconds
  │   └─ Notes the current 6-digit code
  │
  ├─→ User enters 6-digit code on page
  │
  ├─→ Backend (POST action='verify'):
  │   │
  │   ├─ Get code from form (spaces removed)
  │   ├─ Get secret from hidden field
  │   │
  │   ├─ Verification: totp.verify(code)
  │   │
  │   └─ DECISION: Code valid?
  │      │
  │      ├─ NO ✗
  │      │  ├─ Error: "Invalid code. Please try again."
  │      │  └─ Stay on setup page, user can retry
  │      │
  │      └─ YES ✓
  │         └─ Continue
  │
  ├─→ Finalize 2FA Setup:
  │   ├─ TwoFactorAuth.is_enabled = True
  │   ├─ TwoFactorAuth.is_verified = True
  │   ├─ TwoFactorAuth.method = 'TOTP'
  │   ├─ TwoFactorAuth.secret_key = secret (save)
  │   ├─ TwoFactorAuth.backup_codes = [10 codes] (save)
  │   └─ TwoFactorAuth.save()
  │
  ├─→ Success message:
  │   "2FA has been enabled successfully!"
  │
  ├─→ Redirect to /auth/2fa/backup-codes/
  │
  ├─→ Display Page:
  │   ├─ ALL 10 backup codes displayed
  │   ├─ WARNING: "Save these codes! Not shown again"
  │   ├─ Button: "Download as File"
  │   ├─ Button: "Copy All"
  │   └─ Message in red: "These codes won't be shown again"
  │
  ├─→ User MUST save codes (critical!)
  │   ├─ Download, screenshot, or print
  │   ├─ Store in secure location
  │   └─ These are recovery if phone lost
  │
  └─→ Setup Complete!
```

## 4. Login with 2FA - Step by Step

```
STEP 1: Normal Login (Same as before)
─────────────────────────────────────
User enters email + password
  │
  └─→ Backend verifies credentials ✓
      ├─ Check 2FA status
      ├─ 2FA enabled? YES
      │
      └─→ Set session['2fa_user_id'] = user_id
          └─→ Redirect to /auth/verify-2fa-login/


STEP 2: 2FA Verification Page
─────────────────────────────
Display page:
  ├─ Title: "Enter your authentication code"
  ├─ Instructions: "Enter the 6-digit code from your authenticator"
  ├─ Input field: "Enter code"
  ├─ Button: "Verify Code"
  └─ Help text: "Or use one of your backup codes"

User's action:
  ├─ Open authenticator app on phone
  ├─ Find "Cebu Hotel" entry
  ├─ See 6-digit code (e.g., 123456)
  ├─ Enter code in form
  └─ Click "Verify Code"


STEP 3: Verification Process
────────────────────────────
Backend receives code:

Option A: TOTP Code (6-digit)
────────────────────────────
  ├─ Get user from session['2fa_user_id']
  ├─ Get user.two_factor_auth
  ├─ totp = pyotp.TOTP(secret_key)
  ├─ totp.verify(code)
  │
  └─ DECISION: Valid?
     │
     ├─ NO ✗
     │  ├─ Error: "Invalid code or backup code."
     │  └─ Stay on verification page for retry
     │
     └─ YES ✓
        └─ Continue to "CREATE SESSION"

Option B: Backup Code
────────────────────
  ├─ Check: if code in two_fa.backup_codes
  │
  └─ DECISION: Code found?
     │
     ├─ NO ✗
     │  ├─ Error: "Invalid code or backup code."
     │  └─ Stay on verification page
     │
     └─ YES ✓
        ├─ two_fa.use_backup_code(code)
        │  └─ Removes code from list
        │
        └─ Continue to "CREATE SESSION"


STEP 4: Create Session (Successful Verification)
─────────────────────────────────────────────────
  ├─ Create LoginSession:
  │  ├─ user = authenticated_user
  │  ├─ ip_address = get_client_ip(request)
  │  ├─ user_agent = HTTP_USER_AGENT
  │  ├─ is_2fa_verified = True ← IMPORTANT
  │  ├─ created_at = now
  │  └─ Save to database
  │
  ├─ login(request, user)
  │  └─ Sets session cookie
  │
  ├─ Clean up:
  │  ├─ del session['2fa_user_id']
  │  └─ del session['2fa_remember_me']
  │
  ├─ Message: "You have been logged in successfully!"
  │
  ├─ Redirect to /auth/dashboard/
  │
  └─ SUCCESS ✓
```

## 5. Complete User Journey Timeline

```
T=0min   User visits website
         ├─→ Not logged in
         └─→ Cannot access /dashboard/

T=1min   Click "Sign Up"
         ├─→ Fill form
         ├─→ Email: user@test.com
         ├─→ Password: SecurePass123!
         ├─→ ✓ Accept T&C
         └─→ Click "Sign Up"

T=2min   Registration successful
         ├─→ CustomUser created
         ├─→ terms_accepted = True
         ├─→ Redirected to /auth/login/

T=3min   Click "Sign In"
         ├─→ Enter email + password
         ├─→ Remember Me: Not checked
         └─→ Click "Sign In"

T=4min   Login successful (2FA not enabled yet)
         ├─→ Redirected to /auth/dashboard/
         ├─→ Message: "Welcome back!"
         └─→ See "Set Up 2FA" button

T=5min   Click "Set Up 2FA"
         ├─→ Redirected to /auth/2fa/setup/
         └─→ Click "Generate QR Code"

T=6min   QR Code displayed
         ├─→ Open phone
         ├─→ Open Authenticator app
         ├─→ Tap "Scan Code"
         └─→ Point at QR code

T=7min   Scan successful
         ├─→ App shows "Cebu Hotel"
         ├─→ Shows 6-digit code
         ├─→ Code changes in 20 seconds...
         └─→ Copy code: 123456

T=8min   Enter code on page
         ├─→ Type code: 123456
         ├─→ Click "Verify & Enable"
         └─→ Backend verifies ✓

T=9min   2FA Enabled
         ├─→ Message: "2FA enabled successfully!"
         ├─→ Redirected to backup codes page
         └─→ Display all 10 backup codes

T=10min  Save backup codes
         ├─→ Download file
         ├─→ Or screenshot codes
         ├─→ Store safely (VERY IMPORTANT!)
         └─→ Setup complete

T=11min  Click Logout
         ├─→ User logged out
         ├─→ Session cleared
         └─→ Redirected to login page

T=12min  Click "Sign In" again
         ├─→ Enter email + password
         └─→ Click "Sign In"

T=13min  2FA Verification Required (NEW!)
         ├─→ Redirected to /auth/verify-2fa-login/
         ├─→ Page asks for 6-digit code
         ├─→ (Not dashboard yet!)
         └─→ This is the security check

T=14min  Enter 2FA code
         ├─→ Open authenticator app
         ├─→ See code: 654321 (different from before)
         ├─→ Type: 654321
         └─→ Click "Verify Code"

T=15min  Login successful with 2FA
         ├─→ LoginSession created with is_2fa_verified=True
         ├─→ Redirected to /auth/dashboard/
         ├─→ Message: "Logged in successfully!"
         └─→ Session active!

T=20min  Browser closed (no Remember Me)
         └─→ Session ends

T=21min  User returns next day
         ├─→ Visits website
         ├─→ Not logged in
         └─→ Must login again

                NEXT LOGIN CYCLE
         ├─→ /auth/login/
         ├─→ /auth/verify-2fa-login/
         ├─→ /auth/dashboard/
         └─→ (Always requires 2FA)
```

## 6. Database State Changes

```
INITIAL STATE
═════════════
CustomUser (id=1)
├─ email: user@test.com
├─ username: user
├─ terms_accepted: False
└─ created_at: 2026-02-27

TwoFactorAuth: (doesn't exist yet)
LoginSession: (empty)


AFTER REGISTRATION
═════════════════
CustomUser (id=1)
├─ email: user@test.com
├─ username: user
├─ terms_accepted: True ← CHANGED
├─ terms_accepted_at: 2026-02-27 10:00:00 ← SET
└─ terms_version: "1.0" ← SET

TwoFactorAuth: (still doesn't exist)
LoginSession: (empty)


AFTER FIRST LOGIN
══════════════════
CustomUser: (no change)

TwoFactorAuth: (still doesn't exist)

LoginSession (id=1) ← NEW
├─ user: user@test.com
├─ ip_address: 127.0.0.1
├─ is_2fa_verified: False
├─ created_at: 2026-02-27 10:05:00


AFTER 2FA SETUP
═══════════════
CustomUser: (no change)

TwoFactorAuth (id=1) ← NEW
├─ user: user@test.com
├─ is_enabled: True ← SET
├─ is_verified: True ← SET
├─ secret_key: "JBSWY3DPEBLW64TMM..." ← SET
├─ backup_codes: ["a1b2c3d4", "e5f6g7h8", ...] ← SET (10 codes)
├─ method: "TOTP"
└─ created_at: 2026-02-27 10:10:00

LoginSession: (no change)


AFTER LOGIN WITH 2FA
═════════════════════
CustomUser: (no change)

TwoFactorAuth: (no change)

LoginSession (id=2) ← NEW
├─ user: user@test.com
├─ ip_address: 127.0.0.1
├─ is_2fa_verified: True ← CHANGED (was False)
├─ created_at: 2026-02-27 10:15:00


AFTER USING BACKUP CODE
════════════════════════
CustomUser: (no change)

TwoFactorAuth (id=1)
├─ backup_codes: ["e5f6g7h8", ...] ← ONE CODE REMOVED
│  (Now only 9 codes instead of 10)
└─ (rest same)

LoginSession (id=3) ← NEW
├─ is_2fa_verified: True
└─ created_at: 2026-02-27 10:20:00
```

## 7. Error Flow Diagram

```
LOGIN PAGE
  │
  ├─→ Submit credentials
  │
  ├─→ Credentials check
  │   │
  │   ├─ Invalid?
  │   │  ├─ Error: "Invalid username or password"
  │   │  └─ Retry on same page
  │   │
  │   └─ Valid? Continue...
  │
  ├─→ Check 2FA enabled
  │   │
  │   │ (2FA Enabled?) YES
  │   │  ├─ Go to 2FA verification page
  │   │  │
  │   │  └─→ 2FA VERIFICATION PAGE
  │   │      ├─ Enter 6-digit code (invalid)
  │   │      │  ├─ Error: "Invalid code"
  │   │      │  └─ Retry on same page
  │   │      │
  │   │      ├─ Enter code (valid)
  │   │      │  └─ Login successful ✓
  │   │      │
  │   │      └─ Enter backup code (invalid)
  │   │         ├─ Error: "Invalid backup code"
  │   │         └─ Retry on same page
  │   │
  │   ~/.
  │
  ├─→ Check T&C accepted
  │   │
  │   ├─ Not accepted?
  │   │  ├─ Go to /auth/accept-terms/
  │   │  ├─ User reads and accepts
  │   │  └─ Then go to dashboard
  │   │
  │   └─ Accepted? Continue...
  │
  ├─→ Login successful ✓
  │
  └─→ DASHBOARD
```

---

## Quick Reference: Decision Points

| Step | Decision | If No | If Yes |
|------|----------|-------|--------|
| 1 | Credentials valid? | Show error, retry | Go to step 2 |
| 2 | 2FA enabled & verified? | Go to step 3 | Go to 2FA verification |
| 3 | T&C accepted? | Go to T&C page | Go to step 4 |
| 4 | All checks pass? | Already checked | Login, go to dashboard |
| 2FA-1 | Code valid (TOTP)? | Show error, retry | Create session, login |
| 2FA-2 | Backup code valid? | Show error, retry | Remove code, create session |

