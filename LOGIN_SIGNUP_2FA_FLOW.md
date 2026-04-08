# Login, Signup & 2FA System Flow Guide

## System Architecture Overview

Your system has several interconnected components that work together:

```
User Registration → Email Verification → T&C Acceptance → Dashboard
                                            ↓
                                      (Optional) Setup 2FA
                                            ↓
                                    Enable/Disable 2FA
```

---

## 1. SIGNUP FLOW (Registration)

### Step-by-Step Process

#### 1.1 User Registration (`/auth/register/`)
**What happens:**
- User fills in: Email, First Name, Last Name, Password, Confirm Password
- User **MUST** check "I agree to the Terms and Conditions"
- User clicks "Sign Up"

**Backend Processing:**
```python
# forms.py - RegisterForm
- Validates email uniqueness (no duplicates)
- Validates password strength (Django default + confirmation match)
- Validates T&C acceptance (required=True)
- Creates CustomUser with:
  * role = 'GUEST' (default for new users)
  * terms_accepted = True
  * terms_accepted_at = now
  * username = generated from email (auto-handled)
```

**Expected Outcome:**
- ✅ Success message: "Registration successful! Please log in."
- ℹ️ Redirect to login page
- ❌ Error: Duplicate email → "This email is already registered."
- ❌ Error: T&C not accepted → "You must accept Terms and Conditions"
- ❌ Error: Password mismatch → "Passwords do not match"

#### 1.2 After Registration
- User is **NOT automatically logged in**
- User must navigate to login page and enter credentials
- No email verification is currently enforced (you can add this later)

---

## 2. LOGIN FLOW (Standard Login without 2FA)

### Step-by-Step Process

#### 2.1 User Login (`/auth/login/`)
**User Inputs:**
- Username OR Email
- Password  
- Remember Me (checkbox - keeps session for 30 days)

**Backend Processing:**
```python
# views.py - login_view()
1. Accepts both username AND email (smart login)
   - First tries: authenticate(username=input, password=password)
   - If fails, tries: User.objects.get(email=input) → then authenticate

2. If credentials are valid:
   a) Check if user has 2FA enabled:
      - Get user.two_factor_auth (OneToOneField relationship)
      - If 2FA.is_enabled AND 2FA.is_verified:
        * Store user.id in session['2fa_user_id']
        * Redirect to 2FA verification page
        * SKIP normal login
      
      - If 2FA disabled or not verified:
        * Proceed with normal login
   
   b) Normal login process:
      - login(request, user) → Sets session cookie
      - If remember_me checked:
        * Set session expiry to 30 days
        * Otherwise default session expires when browser closes
      - Check if user accepted T&C:
        * If NOT accepted → Redirect to /auth/accept-terms/
        * If ACCEPTED → Redirect to dashboard ✅
```

**Expected Outcomes:**
- ✅ Valid credentials + 2FA disabled → Dashboard
- ✅ Valid credentials + 2FA enabled → 2FA verification page
- ✅ Valid credentials + T&C not accepted → T&C acceptance page
- ❌ Invalid credentials → "Invalid username or password."

---

## 3. TWO-FACTOR AUTHENTICATION (2FA) FLOW

### 3.1 Setup 2FA (`/auth/2fa/setup/` - AFTER login)

**Initial Setup Page:**
- Shows label "2FA Status: Disabled" or "Enabled"
- Button: "Generate QR Code" or "Already Enabled"

**When User Clicks "Generate QR Code":**
```python
# Step 1: Generate Secret Key
- secret = pyotp.random_base32()
- Stored temporarily in TwoFactorAuth.secret_key (NOT yet verified)

# Step 2: Generate QR Code
- Create TOTP provisioning URI
  * Email: user.email
  * Issuer: 'Cebu Hotel'
- Generate QRCode image
- Convert to base64 for HTML display

# Step 3: Generate Backup Codes (10 codes)
- format: random hex strings (e.g., "a1b2c3d4")
- Stored in TwoFactorAuth.backup_codes (JSON array)

# Step 4: Display Setup Page
- Show QR code image (user scans with authenticator app)
- Show secret key (user can manually enter if needed)
- Show 10 backup codes (user should save these!)
```

**User Action - Scan QR Code:**
1. User opens authenticator app (Google Authenticator, Authy, etc.)
2. Scans the QR code displayed
3. App now displays 6-digit code that changes every 30 seconds

#### 3.2 Verify 2FA Code (`/auth/2fa/setup/` - POST with action=verify)

```python
# User enters 6-digit code from authenticator app
# Backend verification:

code = request.POST.get('code', '').replace(' ', '')
secret = request.POST.get('secret')  # Hidden field from form

totp = pyotp.TOTP(secret)
if totp.verify(code):  # ✅ Code is valid
    - TwoFactorAuth.is_enabled = True
    - TwoFactorAuth.is_verified = True
    - TwoFactorAuth.method = 'TOTP'
    - Save to database
    
    - Redirect to /auth/2fa/backup-codes/
    - SUCCESS: "2FA has been enabled successfully!"

else:  # ❌ Code is invalid
    - Show error: "Invalid code. Please try again."
    - Re-display setup page with QR code
    - User can try again or cancel
```

**CRITICAL: Backup Codes Page**
```
User MUST save backup codes because they are shown only ONCE.
If user loses backup codes and loses access to authenticator app,
they cannot log in again (unless disable 2FA via settings).

Backup codes can be:
- Downloaded as text file
- Copied to clipboard
- Printed
- Saved manually
```

#### 3.3 Login With 2FA Enabled

**Login Flow (Standard Login + 2FA):**
```
User enters email/username + password
→ Credentials valid?
   - YES: Continue to Step 2
   - NO: Show error, ask for retry

→ Check if user has 2FA enabled
   - YES (2FA enabled + verified):
     * Store session['2fa_user_id'] = user.id
     * Store session['2fa_remember_me'] = remember_me_value
     * Redirect to /auth/verify-2fa-login/
   
   - NO: Proceed with normal login → Dashboard

→ On /auth/verify-2fa-login/ page:
   * User sees: "Enter 6-digit code from your authenticator app"
   * User sees: "OR enter one of your backup codes"
   
   * Backend accepts BOTH:
     a) TOTP code (6-digit from authenticator)
        - Verify with pyotp.TOTP(two_fa.secret_key).verify(code)
     
     b) Backup code (hex string)
        - Check if code in two_fa.backup_codes
        - If exists: Remove it and mark as used
        - Cannot be used again

   * If valid code:
     - Create LoginSession (for audit trail)
     - login(request, user)
     - Clear session['2fa_user_id']
     - Redirect to dashboard ✅
     - Message: "You have been logged in successfully!"
   
   * If invalid code:
     - Show error: "Invalid code or backup code."
     - Keep same page, user can retry
```

**LoginSession Tracking:**
```python
LoginSession object created with:
- user = authenticated user
- ip_address = client IP
- user_agent = browser info
- is_2fa_verified = True (if 2FA was used)
- is_oauth = False (if email/password login)
- created_at = now
```

#### 3.4 Viewing & Managing Backup Codes

**Backup Codes Page (`/auth/2fa/backup-codes/` - AFTER both setup + login)**
```python
- Shows all remaining backup codes
- Cannot regenerate backup codes (security measure)
- Can download as file
- Can copy to clipboard

If user clicks "I've Lost My Codes" option:
- Recommended to disable 2FA and re-enable
- This generates new codes
- Old codes become invalid
```

#### 3.5 Disable 2FA

**Disable Action (`/auth/2fa/disable/` - POST only):**
```python
- Sets TwoFactorAuth.is_enabled = False
- Sets TwoFactorAuth.is_verified = False
- Clears secret_key = ''
- Clears backup_codes = []
- Success message: "2FA has been disabled."
- Redirect to 2FA setup page

User can set it up again by clicking "Generate QR Code"
```

---

## 4. COMPLETE USER JOURNEY MAP

### Scenario A: New User with 2FA

```
1. Visit /auth/register/
   ↓
2. Fill form + Accept T&C
   ↓
3. POST → Validation passes
   ↓
4. User created (role='GUEST', terms_accepted=True)
   ↓
5. Redirect to /auth/login/
   MESSAGE: "Registration successful! Please log in."
   
   ┌─────────────────────────────────────┐
   │ User Logs Out or Session Expires    │
   └─────────────────────────────────────┘
   
6. Visit /auth/login/
   ↓
7. Enter email + password + check "Remember Me"
   ↓
8. POST → Credentials valid?
   ↓ YES
9. Check TwoFactorAuth.is_enabled?
   ↓ NOT ENABLED
10. Check if T&C accepted?
    ↓ YES
11. login(request, user) + set 30-day session
    ↓
12. Redirect to /auth/dashboard/
    MESSAGE: "Welcome back, [First Name]!"
    
    [User opens Dashboard - Can see 2FA option]
    
13. Click "Set Up 2FA" link
    ↓
14. Redirected to /auth/2fa/setup/
    ↓
15. Click "Generate QR Code"
    ↓
16. Backend generates secret + QR code + backup codes
    ↓
17. View QR Code page
    - Scan QR code with Authenticator app
    - Authenticator app generates 6-digit code
    
18. Enter 6-digit code
    ↓
19. POST action='verify'
    ↓
20. Backend validates code with pyotp
    ↓ VALID
21. Set TwoFactorAuth:
    - is_enabled=True
    - is_verified=True
    - method='TOTP'
    ↓
22. Redirect to /auth/2fa/backup-codes/
    MESSAGE: "2FA enabled successfully!"
    
    [User sees 10 backup codes]
    
23. User downloads/copies/saves backup codes
    ↓
24. Next login will require 2FA verification
```

### Scenario B: Login with 2FA Enabled

```
1. Visit /auth/login/
   ↓
2. Enter email + password
   ↓
3. POST to login_view()
   ↓
4. validate credentials → VALID
   ↓
5. Check two_factor_auth:
   ↓
   ├─ is_enabled=True AND is_verified=True
   │  ↓
   │  Store session['2fa_user_id'] = user.id
   │  Store session['2fa_remember_me'] = remember_me
   │  ↓
   │  Redirect to /auth/verify-2fa-login/
   │  
   └─ is_enabled=False OR is_verified=False
      ↓
      Proceed with login() → Dashboard
```

```
6. User on /auth/verify-2fa-login/ page
   ↓
7. User opens authenticator app
   ↓
8. Sees 6-digit code (changes every 30 seconds)
   ↓
9. Enters 6-digit code in form
   ↓
10. POST to verify_2fa_login()
    ↓
11. Backend:
    - Get user from session['2fa_user_id']
    - Get user.two_factor_auth
    - Verify code: pyotp.TOTP(secret_key).verify(code)
    ↓ SUCCESS (or BACKUP CODE matches)
12. Create LoginSession (audit trail)
    ↓
13. login(request, user)
    ↓
14. Clear session['2fa_user_id']
    ↓
15. Redirect to /auth/dashboard/
    MESSAGE: "You have been logged in successfully!"
    
    ↓ FAILED (code invalid)
    Show error: "Invalid code or backup code."
    Stay on verification page for retry
```

---

## 5. DATABASE RELATIONSHIPS

```
CustomUser (1) ─── (1) TwoFactorAuth
  - id
  - email
  - username
  - password
  - role
  - terms_accepted
  - created_at

              TwoFactorAuth
              - user_id (FK → CustomUser)
              - is_enabled (Boolean)
              - is_verified (Boolean)
              - secret_key (CharField) ← TOTP secret
              - backup_codes (JSONField) ← Array of codes
              - method (CharField) ← 'TOTP', 'SMS', 'EMAIL'
              - created_at
              - last_verified


CustomUser (1) ─── (N) LoginSession
              
              LoginSession
              - user_id (FK → CustomUser)
              - ip_address
              - user_agent
              - is_2fa_verified
              - is_oauth
              - created_at
              - last_activity
```

---

## 6. HOW TO TEST 2FA IS WORKING PROPERLY

### Prerequisites
- Have authenticator app installed:
  - Google Authenticator (free)
  - Authy (free)
  - Microsoft Authenticator (free)
  - FreeOTP (free)

### Test Case 1: Setup 2FA
```
✅ SHOULD HAPPEN:
1. QR code displays on setup page
2. Authenticator app can scan it
3. App starts showing 6-digit codes
4. Entering correct code enables 2FA
5. Backup codes are generated and shown
6. Button shows "2FA is Enabled" after setup

❌ IF NOT HAPPENING:
- Check TwoFactorAuth record created: 
  python manage.py shell
  >>> from authentication.models import TwoFactorAuth, CustomUser
  >>> user = CustomUser.objects.get(email='youremail@test.com')
  >>> user.two_factor_auth
  >>> # Should show object, not error
  
- Check pyotp installed:
  >>> import pyotp
  >>> # Should work without error
```

### Test Case 2: TOTP Code Verification
```
✅ SHOULD HAPPEN:
1. Code expires after ~30 seconds
2. Both old code AND new code work for ~1 minute (time window)
3. Entering invalid code shows error
4. Valid code allows login

❌ IF NOT WORKING:
- Check system time on server (must be accurate)
- Check if using TOTP versus HOTP
- Verify secret_key is not corrupted in DB
```

### Test Case 3: Backup Code Usage
```
✅ SHOULD HAPPEN:
1. Can login with backup code instead of app code
2. Backup code disappears from list after use
3. Code cannot be used twice
4. Each user has unique backup codes

❌ IF BACKUP CODES NOT WORKING:
- Check backup_codes stored as JSON array
- Verify code removal logic in use_backup_code()
```

### Test Case 4: 2FA Required on Login
```
✅ SHOULD HAPPEN:
1. User logs out
2. User logs in with email + password
3. IS redirected to 2FA verification page (not dashboard)
4. Cannot access dashboard without 2FA code
5. Entering wrong code shows error, stays on verification page
6. Entering right code logs in successfully

❌ IF 2FA NOT ENFORCED:
Check login_view():
- Is it checking two_factor_auth.is_enabled?
- Is it checking two_factor_auth.is_verified?
- Is it setting session['2fa_user_id']?
- Is it redirecting to verify_2fa_login?
```

### Test Case 5: Session Management
```
✅ SHOULD HAPPEN:
1. Login with "Remember Me" → session lasts 30 days
2. Login without "Remember Me" → session ends when browser closes
3. session['2fa_user_id'] exists during 2FA verification
4. session['2fa_user_id'] deleted after successful 2FA login
5. Session['2fa_user_id'] prevents access without 2FA__verify

❌ IF SESSION ISSUES:
python manage.py shell
>>> from django.contrib.sessions.models import Session
>>> Session.objects.all()
>>> # Check session data
```

---

## 7. VERIFICATION CHECKLIST

### Critical Points to Verify

#### Registration Flow
- [ ] Can register with email + password + T&C acceptance
- [ ] Duplicate email rejected
- [ ] Missing T&C checkbox rejected
- [ ] User created with role='GUEST'
- [ ] User redirected to login (not auto-logged in)

#### Login Without 2FA
- [ ] Email or username both work
- [ ] Invalid credentials rejected
- [ ] Valid credentials without T&C → redirect to T&C page
- [ ] Valid credentials with T&C → redirect to dashboard
- [ ] Remember Me extends session to 30 days

#### 2FA Setup
- [ ] QR code displays correctly
- [ ] Secret key shown to user
- [ ] Backup codes generated (10 codes)
- [ ] Invalid TOTP code rejected
- [ ] Valid TOTP code enables 2FA
- [ ] TwoFactorAuth object created with is_enabled=True

#### Login With 2FA
- [ ] Valid credentials + 2FA enabled → redirect to verify page
- [ ] session['2fa_user_id'] set correctly
- [ ] User cannot access dashboard without 2FA code
- [ ] Valid TOTP code → successful login
- [ ] Valid backup code → successful login
- [ ] Invalid code → error message, stay on page
- [ ] LoginSession created with is_2fa_verified=True

#### Backup Codes
- [ ] Can view backup codes after 2FA setup
- [ ] Can download backup codes
- [ ] Can copy backup codes
- [ ] Backup code deletes from list after use
- [ ] Backup code cannot be reused

#### Disable 2FA
- [ ] Can disable 2FA from settings
- [ ] TwoFactorAuth is_enabled set to False
- [ ] Next login does NOT require 2FA
- [ ] Can re-enable 2FA with new codes

---

## 8. COMMON ISSUES & SOLUTIONS

### Issue: "Time discrepancy" - Code never validates
- **Cause:** Server time out of sync with authenticator app
- **Solution:** 
  ```bash
  # Check Windows time
  Get-Date
  
  # Synchronize time
  w32tm /resync
  ```

### Issue: Session expires too quickly
- **Cause:** Django session timeout too short
- **Solution:** Check settings.py:
  ```python
  SESSION_COOKIE_AGE = 86400 * 30  # 30 days
  SESSION_EXPIRE_AT_BROWSER_CLOSE = False
  ```

### Issue: Backup codes not working
- **Cause:** Codes stored/retrieved incorrectly
- **Solution:** Check TwoFactorAuth.backup_codes in DB:
  ```bash
  python manage.py shell
  >>> user.two_factor_auth.backup_codes
  >>> # Should show list, not string
  ```

### Issue: QR code doesn't display
- **Cause:** QR code generation or image conversion failed
- **Solution:**
  - Check if qrcode library installed: `pip install qrcode python-qrcode`
  - Check if Pillow installed: `pip install Pillow`

### Issue: User redirects to login but shows as logged in
- **Cause:** Session not properly cleared
- **Solution:** Clear sessions in DB:
  ```bash
  python manage.py clearsessions
  ```

---

## 9. DATABASE QUERIES FOR DEBUGGING

```python
# Check 2FA setup status
from authentication.models import CustomUser, TwoFactorAuth

user = CustomUser.objects.get(email='test@test.com')
print(user.two_factor_auth.is_enabled)  # True/False
print(user.two_factor_auth.is_verified)  # True/False
print(user.two_factor_auth.secret_key)  # Should be 32-char string
print(len(user.two_factor_auth.backup_codes))  # Should be 10

# View all login sessions
from authentication.models import LoginSession
sessions = LoginSession.objects.filter(user=user)
for session in sessions:
    print(f"{session.created_at} - 2FA: {session.is_2fa_verified}")

# List all users with 2FA enabled
two_fa_users = CustomUser.objects.filter(two_factor_auth__is_enabled=True)
```

---

## 10. NEXT STEPS TO IMPROVE SYSTEM

1. **Email Verification:** Send verification email on signup
2. **Login Attempt Tracking:** Lock account after 5 failed attempts
3. **Admin Dashboard:** View user sessions and disable 2FA for users
4. **SMS 2FA:** Implement SMS as alternative to authenticator app
5. **Recovery Email:** Allow users to set recovery email
6. **Device Trust:** "Trust this device for 30 days" option
7. **Login Alerts:** Email user when new device logs in

