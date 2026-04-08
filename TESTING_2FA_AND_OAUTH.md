# 2FA and Google OAuth Testing Guide

## Quick Start

### 1. Start the Server
```bash
cd c:\Users\echog\OneDrive\Desktop\cebuhotel
.\.venv\Scripts\python.exe manage.py runserver
```

The application will be available at `http://localhost:8000`

---

## Feature 1: Traditional Login with 2FA

### Test Flow
1. **Register Account**
   - Go to `http://localhost:8000/auth/register/`
   - Create account with:
     - Email: `test2fa@hotel.com`
     - Password: `SecurePass123!`
   - Click Register

2. **Accept Terms**
   - Read Terms & Conditions
   - Check "I accept the Terms and Conditions"
   - Click Accept

3. **Access Dashboard**
   - You should be redirected to dashboard

4. **Enable 2FA**
   - Go to `http://localhost:8000/auth/2fa/setup/`
   - Click "Generate QR Code"
   - **Install Authenticator App** (if not already installed):
     - Google Authenticator (iOS/Android)
     - Authy (iOS/Android)
     - Microsoft Authenticator (iOS/Android)
     - FreeOTP (Android)
   - Scan the QR code with authenticator app
   - Enter the 6-digit code shown in your app
   - Click "Verify & Enable 2FA"

5. **Save Backup Codes**
   - Copy or download the backup codes
   - Click "2FA Setup Complete!"

6. **Test Login with 2FA**
   - Click Logout
   - Go to `http://localhost:8000/auth/login/`
   - Enter credentials:
     - Username: `test2fa@hotel.com`
     - Password: `SecurePass123!`
   - Click "Sign In"
   - You should be redirected to 2FA verification page
   - Open your authenticator app and enter the 6-digit code
   - Click "Verify Code"
   - You should be logged in to dashboard

### Expected Results
✓ QR code displays on 2FA setup page  
✓ Authenticator app can scan code  
✓ TOTP code validates correctly  
✓ Backup codes are generated  
✓ Login requires 2FA verification  
✓ Valid codes allow login  
✓ Invalid codes show error message  

---

## Feature 2: Backup Codes

### Test Flow
1. **View Backup Codes Page**
   - Go to `http://localhost:8000/auth/2fa/backup-codes/` (while logged in)
   - You should see all 10 backup codes

2. **Copy Codes**
   - Click "Copy All Codes" button
   - Paste somewhere to verify they copied

3. **Download Codes**
   - Click "Download as File" button
   - A text file should download with your backup codes

4. **Use Backup Code**
   - Go to `http://localhost:8000/auth/logout/`
   - Log back in:
     - Username: `test2fa@hotel.com`
     - Password: `SecurePass123!`
   - Click "Sign In"
   - On 2FA verification page, paste a backup code instead of TOTP
   - Click "Verify Code"
   - You should be logged in

5. **Verify Code Was Used**
   - Go to `http://localhost:8000/auth/2fa/backup-codes/`
   - That backup code should no longer appear in the list

### Expected Results
✓ All 10 backup codes display on page  
✓ Copy button copies all codes  
✓ Download button creates text file  
✓ Valid backup code logs in user  
✓ Used backup code is removed from list  
✓ Invalid/used codes show error  

---

## Feature 3: Disable and Re-enable 2FA

### Test Flow
1. **Disable 2FA**
   - Go to `http://localhost:8000/auth/2fa/setup/`
   - Scroll to "Two-Factor Authentication is Enabled" section
   - Click "Disable 2FA"
   - Confirm the action

2. **Test Login Without 2FA**
   - Go to `http://localhost:8000/auth/logout/`
   - Log back in:
     - Username: `test2fa@hotel.com`
     - Password: `SecurePass123!`
   - Click "Sign In"
   - You should be logged in directly WITHOUT 2FA verification

3. **Re-enable 2FA**
   - Go to `http://localhost:8000/auth/2fa/setup/`
   - You should see "Generate QR Code" button again
   - Repeat the setup process

### Expected Results
✓ 2FA can be disabled from setup page  
✓ Login bypasses 2FA after disabling  
✓ 2FA can be re-enabled anytime  
✓ Old codes don't work after disabling  

---

## Feature 4: Google OAuth Setup (Optional)

### Prerequisites
1. Google Cloud Console account
2. OAuth 2.0 Client ID and Secret

### Setup Steps
1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Create new project
   - Navigate to APIs & Services → Credentials

2. **Create OAuth 2.0 Credentials**
   - Click "Create Credentials" → OAuth 2.0 Client IDs
   - Select "Web Application"
   - Add Authorized Redirect URI: `http://localhost:8000/accounts/google/login/callback/`
   - Copy Client ID and Secret

3. **Run Setup Command**
   ```bash
   .\.venv\Scripts\python.exe manage.py setup_google_oauth --client-id YOUR_CLIENT_ID --secret YOUR_SECRET
   ```
   Or manually in Django Admin:
   - Go to `http://localhost:8000/admin/`
   - Social Applications → Add
   - Provider: Google
   - Name: Google OAuth
   - Client ID: [paste your ID]
   - Secret key: [paste your secret]
   - Sites: Select localhost:8000
   - Save

### Test Google OAuth Login
1. **Button Should Appear**
   - Go to `http://localhost:8000/auth/login/`
   - "Sign in with Google" button should appear

2. **Test OAuth Flow**
   - Click "Sign in with Google"
   - Grant permissions
   - You should be logged in

3. **Test Google OAuth with 2FA**
   - Create another account via Google OAuth
   - Go to `http://localhost:8000/auth/2fa/setup/`
   - Enable 2FA on Google OAuth account
   - Log out
   - Log back in via Google
   - Should require 2FA verification

### Expected Results
✓ Google OAuth button appears after setup  
✓ Google login flow works  
✓ New accounts auto-created from Google  
✓ Existing accounts can be linked  
✓ 2FA works with Google OAuth accounts  

---

## Feature 5: Session Tracking (Login Sessions)

### Test Details
Each login creates a `LoginSession` record with:
- User IP address
- Browser user-agent
- OAuth provider (if applicable)
- 2FA verification status
- Login timestamp

### View in Admin
1. Go to `http://localhost:8000/admin/`
2. Authentication → Login Sessions
3. You should see entries for each login with:
   - IP address (e.g., 127.0.0.1)
   - User agent info
   - 2FA verification status

---

## Testing Checklist

### Basic Authentication
- [ ] Register new account
- [ ] Login with credentials
- [ ] Remember Me functionality works
- [ ] Logout works
- [ ] Terms acceptance required

### 2FA Setup
- [ ] QR code generation works
- [ ] Authenticator app can scan QR
- [ ] Manual secret entry works
- [ ] 2FA code verification works
- [ ] Backup codes are generated

### Login with 2FA
- [ ] 2FA page appears after password
- [ ] TOTP code from app works
- [ ] Invalid code shows error
- [ ] Backup code works
- [ ] Used backup code is removed

### Backup Codes
- [ ] Can view all backup codes
- [ ] Can copy codes
- [ ] Can download codes
- [ ] Can print codes
- [ ] Codes are properly formatted

### 2FA Management
- [ ] Can disable 2FA
- [ ] Login works without 2FA after disabling
- [ ] Can re-enable 2FA
- [ ] Regenerate codes button works

### Google OAuth (if configured)
- [ ] Button appears on login
- [ ] OAuth flow redirects correctly
- [ ] User automatically created
- [ ] Can login via Google
- [ ] Google accounts work with 2FA

---

## Common Test Data

### Account 1: Traditional Login with 2FA
- Email: `test2fa@hotel.com`
- Password: `SecurePass123!`
- Status: 2FA Enabled

### Account 2: Traditional Login without 2FA
- Email: `test@hotel.com`
- Password: `NoTwoFactor1!`
- Status: 2FA Disabled

### Account 3: Google OAuth User
- Login via Google button
- Status: 2FA Optional

---

## Troubleshooting Test Issues

### "SocialApp.DoesNotExist" Error
- Google OAuth app not configured
- Run: `.\.venv\Scripts\python.exe manage.py setup_google_oauth`
- Or manually add in Django admin

### 2FA Code Not Accepted
- Device time not synchronized
- Open Settings on your device and sync time
- Try generating new 2FA code (wait 30 seconds for new code)

### Authenticator App Can't Scan QR
- Click "Can't scan QR" on setup page
- Manually enter the secret code shown
- Add account manually in authenticator app

### Session Not Tracking
- Migrations not applied
- Run: `.\.venv\Scripts\python.exe manage.py migrate`
- Check database for LoginSession records

### Templates Not Loading
- Static files not collected
- Run: `.\.venv\Scripts\python.exe manage.py collectstatic`

---

## Performance Testing

### Expected Load Times
- Login page: < 200ms
- 2FA setup: < 500ms
- QR code generation: < 1s
- Backup code page: < 100ms

### Database Queries
- Login page: ~3-5 queries
- 2FA setup: ~4-6 queries
- 2FA verification: ~5-7 queries

