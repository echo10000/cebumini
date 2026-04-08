# Login, Signup & 2FA - Quick Reference & Status

## CURRENT SYSTEM STATUS ✓

### Verified Components
```
[OK] All dependencies installed (pyotp, qrcode, PIL/Pillow)
[OK] Database models created
[OK] CustomUser model with all required fields
[OK] TwoFactorAuth model ready
[OK] LoginSession tracking model ready
[OK] User exists: echogoodkid@gmail.com
[OK] Terms accepted: YES
```

### Ready to Test
```
[READY] 2FA not yet enabled on current user
[READY] No test users created yet
[READY] No login sessions recorded (will be created on first login)
```

---

## SYSTEM FLOW DIAGRAMS

### 1. SIGNUP → LOGIN → DASHBOARD FLOW

```
┌─────────────────────┐
│   SIGNUP FLOW       │
└─────────────────────┘

User → /auth/register/
  ↓
Fill form:
- Email
- First Name
- Last Name
- Password
- Confirm Password
- ✓ Accept T&C (REQUIRED)
  ↓
POST → Backend validation
  ↓
✓ All valid?
  ├─ NO: Show error, stay on page
  └─ YES: Create user + mark T&C accepted
    ↓
    Message: "Registration successful! Please log in."
    ↓
    Redirect → /auth/login/


┌──────────────────────┐
│  LOGIN FLOW (No 2FA) │
└──────────────────────┘

User → /auth/login/
  ↓
Enter:
- Email or Username
- Password
- (Optional) Remember Me checkbox
  ↓
POST → Authentication
  ↓
✓ Credentials valid?
  ├─ NO: Show error "Invalid username or password"
  │       Stay on login page
  │
  └─ YES: Check 2FA status
         ├─ 2FA ENABLED: Go to 2FA Flow (see below)
         └─ 2FA DISABLED: Continue to step below
           ↓
           Check T&C accepted?
           ├─ NO: Redirect → /auth/accept-terms/
           │       Message: Accept terms first
           │
           └─ YES:
             ↓
             login(request, user)
             ↓
             If Remember Me checked:
               Session lasts 30 days
             Else:
               Session ends on browser close
             ↓
             Message: "Welcome back, [First Name]!"
             ↓
             Redirect → /auth/dashboard/ ✓


┌──────────────────────────────┐
│  T&C ACCEPTANCE FLOW         │
└──────────────────────────────┘

If user not accepted T&C:

User → /auth/accept-terms/
  ↓
Display:
- Current T&C version
- "I accept..." checkbox
- Accept button
  ↓
User checks box + clicks Accept
  ↓
POST verification
  ↓
Record in database:
- terms_accepted = True
- terms_accepted_at = now
- terms_version = "1.0"
  ↓
Message: "Terms accepted successfully!"
  ↓
Redirect → /auth/dashboard/ ✓
```

### 2. 2FA SETUP FLOW

```
┌─────────────────────────────┐
│  2FA SETUP FLOW (After Login)│
└─────────────────────────────┘

User (logged in) → /auth/2fa/setup/
  ↓
Display setup page:
- Current 2FA status
- Button: "Generate QR Code"
  ↓
User clicks "Generate QR Code"
  ↓
Backend:
1. Generate secret key: pyotp.random_base32()
2. Save to TwoFactorAuth.secret_key
3. Generate QR code image
4. Generate 10 backup codes
5. Save backup codes
  ↓
Display:
- QR Code image (user scans with app)
- Secret key (backup option)
- 10 backup codes (user saves these!)
  ↓
User opens authenticator app (Google Authenticator, Authy, etc.)
  ↓
User scans QR code
  ↓
App starts showing 6-digit codes (changes every 30 seconds)
  ↓
User enters 6-digit code on page
  ↓
POST with:
- 6-digit code
- Secret key (from hidden form field)
  ↓
Backend verification: pyotp.TOTP(secret).verify(code)
  ├─ INVALID: Show error "Invalid code. Try again."
  │           Re-display setup page
  │
  └─ VALID:
    Set in database:
    - TwoFactorAuth.is_enabled = True
    - TwoFactorAuth.is_verified = True
    - TwoFactorAuth.method = "TOTP"
    - TwoFactorAuth.secret_key = secret
    - TwoFactorAuth.backup_codes = [10 codes]
    ↓
    Message: "2FA enabled successfully!"
    ↓
    Redirect → /auth/2fa/backup-codes/
    ↓
    CRITICAL: Show all 10 backup codes
    - Codes shown ONLY ONCE
    - User must save them!
    - Can't be regenerated
    - Only way to login if phone lost
```

### 3. LOGIN WITH 2FA ENABLED FLOW

```
┌─────────────────────────────────┐
│  LOGIN WITH 2FA FLOW (2 steps)   │
└─────────────────────────────────┘

STEP 1: Normal Login
─────────────────────
User → /auth/login/
  ↓
Enter email + password
  ↓
POST → Authentication
  ↓
✓ Credentials valid?
  ├─ NO: Error message, retry
  │
  └─ YES: Check TwoFactorAuth
         ├─ is_enabled = False: Login normally (done)
         └─ is_enabled = True AND is_verified = True:
           Go to STEP 2


STEP 2: 2FA Verification
────────────────────────
Backend:
- Store session['2fa_user_id'] = user.id
- Store session['2fa_remember_me'] = remember_me_value
  ↓
Redirect → /auth/verify-2fa-login/
  ↓
Display:
- "Enter 6-digit code from authenticator"
- Input field for code
- (Can also accept backup codes here)
  ↓
User opens authenticator app
  ↓
User sees 6-digit code (changes every 30 seconds)
  ↓
User enters code (spaces auto-removed)
  ↓
POST code
  ↓
Backend verification:

Option A: TOTP Code (6-digit)
───────────────────────────
pyotp.TOTP(two_fa.secret_key).verify(code)
  ├─ INVALID: Error "Invalid code. Try again."
  │           Stay on page
  │
  └─ VALID: Continue to "LOGIN"

Option B: Backup Code (hex string)
───────────────────────────────────
if code in two_fa.backup_codes:
  - Mark as used: two_fa.use_backup_code(code)
  - Code deleted from list
  - Continue to "LOGIN"
else:
  - Error: "Invalid backup code"
  - Stay on page


LOGIN (After code verified)
───────────────────────────
Create LoginSession:
  - user = authenticated user
  - ip_address = client IP
  - user_agent = browser info
  - is_2fa_verified = True
  - created_at = now
  ↓
login(request, user)
  ↓
Clear session['2fa_user_id']
  ↓
Message: "You have been logged in successfully!"
  ↓
Redirect → /auth/dashboard/ ✓
```

### 4. BACKUP CODES MANAGEMENT

```
┌──────────────────────────────────┐
│  BACKUP CODE LIFECYCLE           │
└──────────────────────────────────┘

GENERATION (During 2FA Setup)
─────────────────────────────
- 10 codes generated using: secrets.token_hex(4)
- Example: "a1b2c3d4", "e5f6g7h8", etc.
- Stored as JSON array in TwoFactorAuth.backup_codes
  ↓
USAGE (During 2FA Login)
───────────────────────
- User enters backup code instead of TOTP code
- Backend checks: if code in backup_codes list
- If yes: Call use_backup_code(code)
  - Code deleted from list
  - Code can NEVER be used again
  - User can now login
- If no: Show error, user cannot login
  ↓
VIEWING (After 2FA Enabled)
──────────────────────────
User → /auth/2fa/backup-codes/ (while logged in)
  ↓
Display all remaining codes
- Cannot regenerate (security)
- Can download as file
- Can copy to clipboard
  ↓
RECOVERY (Lost All Codes)
──────────────────────────
If user loses all backup codes:
1. Cannot login if phone lost/app broken
2. Solution: Disable 2FA
3. Do: login to settings → Disable 2FA
4. Then: Re-enable 2FA with new QR code
5. New backup codes generated
```

---

## QUICK TEST CHECKLIST

### Before Testing
- [ ] Server running: `python manage.py runserver`
- [ ] Authenticator app installed on phone or computer
- [ ] Verification script passed: `python verify_2fa_simple.py`

### Test 1: Registration (5 minutes)
- [ ] Go to http://localhost:8000/auth/register/
- [ ] Create account with email, name, password
- [ ] Check "I agree to Terms"
- [ ] Click Sign Up
- [ ] Should see: "Registration successful! Please log in."
- [ ] Should redirect to login page

### Test 2: Login Without 2FA (3 minutes)
- [ ] Go to http://localhost:8000/auth/login/
- [ ] Enter email + password
- [ ] Click Sign In
- [ ] Check "Remember Me" to test 30-day session
- [ ] Should redirect to dashboard (or T&C page if first time)

### Test 3: Accept Terms (2 minutes)
- [ ] If on T&C page:
  - [ ] Read terms
  - [ ] Check "I accept..."
  - [ ] Click Accept
- [ ] Should redirect to dashboard

### Test 4: Setup 2FA (10 minutes)
- [ ] From dashboard, click "Set Up 2FA"
- [ ] Click "Generate QR Code"
- [ ] Copy secret key from page
- [ ] Open phone with Authenticator app
- [ ] Scan QR code
- [ ] App shows "Cebu Hotel" with 6-digit code
- [ ] Enter 6-digit code on page
- [ ] Click "Verify & Enable"
- [ ] Should see all 10 backup codes
- [ ] Download OR screenshot backup codes
- [ ] Verify backup codes are in a safe place

### Test 5: Login With 2FA Enabled (5 minutes)
- [ ] Click Logout
- [ ] Go to http://localhost:8000/auth/login/
- [ ] Enter email + password
- [ ] Click Sign In
- [ ] Should see 2FA verification page (NOT dashboard yet!)
- [ ] Open authenticator app
- [ ] Get 6-digit code
- [ ] Enter code on page
- [ ] Click "Verify Code"
- [ ] Should successfully login to dashboard

### Test 6: Backup Code Usage (5 minutes)
- [ ] Logout again
- [ ] Login with email + password
- [ ] On 2FA verification page
- [ ] Paste one backup code from your saved list
- [ ] Click "Verify Code"
- [ ] Should login successfully
- [ ] Check: That backup code should NO LONGER be in your list

### Test 7: Session Timeout (10 minutes)
- [ ] Login with "Remember Me" checked
- [ ] Close browser completely
- [ ] Reopen browser and go to dashboard
- [ ] Should still be logged in (session persists 30 days)

### Test 8: Invalid Code Handling (3 minutes)
- [ ] Logout and login with email + password
- [ ] On 2FA verification page
- [ ] Enter wrong code: "000000"
- [ ] Should see error: "Invalid code. Try again."
- [ ] Should stay on same page
- [ ] Enter correct code and login

---

## TROUBLESHOOTING

### Issue: QR Code Not Displaying
**Cause:** Pillow (PIL) not installed
**Fix:** `pip install Pillow`
**Verify:** `python verify_2fa_simple.py`

### Issue: Code Verification Always Fails
**Cause:** Server time out of sync
**Windows Fix:** 
```powershell
w32tm /resync
```
**Verify:** Time displayed should match your phone's time

### Issue: Can't Login After Losing Codes
**Steps to Recover:**
1. Contact admin or use recovery email
2. Admin disables 2FA for user
3. User logs in normally
4. User re-enables 2FA with new codes

### Issue: Session Expires Too Quickly
**Check settings.py:**
```python
SESSION_COOKIE_AGE = 86400 * 30  # Should be 30 days
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
```

### Issue: Backup Code Won't Work
**Possible Causes:**
- Code already used (deleted)
- Code contains spaces (should be auto-removed)
- Code from different account
- Code corrupted (typo)

---

## DATABASE INSPECTION

Check any user's 2FA status:
```bash
python manage.py shell
>>> from authentication.models import CustomUser, TwoFactorAuth
>>> user = CustomUser.objects.get(email='echogoodkid@gmail.com')
>>> user.two_factor_auth.is_enabled
True  # or False
>>> user.two_factor_auth.backup_codes
['a1b2c3d4', 'e5f6g7h8', ...]  # List of remaining codes
>>> user.two_factor_auth.secret_key
'JBSWY3DPEBLW64TMMQ...'  # TOTP secret
```

Check login history:
```bash
>>> from authentication.models import LoginSession
>>> LoginSession.objects.filter(user=user).order_by('-created_at')[:5]
```

View all users with 2FA enabled:
```bash
>>> CustomUser.objects.filter(two_factor_auth__is_enabled=True)
```

---

## FILES CREATED FOR YOU

1. **LOGIN_SIGNUP_2FA_FLOW.md** - Detailed flow documentation
2. **verify_2fa_simple.py** - Automated verification script
3. **This file** - Quick reference guide

## NEXT RECOMMENDED STEPS

1. **Test the full flow** using the checklist above
2. **Document any issues** you find
3. **Check edge cases:**
   - What if user tries to enable 2FA twice?
   - What happens if session expires during 2FA?
   - Can user disable 2FA and re-enable?
4. **Frontend improvements:**
   - Add loading spinner on 2FA verification
   - Show time remaining for code
   - Copy code button
5. **Security additions:**
   - Account lockout after 5 failed attempts
   - Email notification on successful 2FA enable
   - Suspicious login alerts

---

## KEY TAKEAWAYS

### The System Works Like This:

**Without 2FA:**
1. User logs in with email + password
2. If valid → Directly to dashboard

**With 2FA Enabled:**
1. User logs in with email + password
2. If valid → Sent to 2FA verification page
3. User enters 6-digit code OR backup code
4. If valid → Directly to dashboard
5. Session created, tracking that 2FA was used

### Critical Files

- [authentication/views.py](authentication/views.py#L50) - Login logic
- [authentication/models.py](authentication/models.py#L311) - TwoFactorAuth model  
- [authentication/forms.py](authentication/forms.py) - Login/Signup forms

### Critical Field Check

User MUST have `terms_accepted = True` to access dashboard (added automatically on signup if checkbox checked)

