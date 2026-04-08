# 2FA and Google OAuth Setup Guide

This guide explains how to set up Two-Factor Authentication (2FA) and Google OAuth for the Cebu Hotel application.

## Table of Contents
1. [2FA Setup](#2fa-setup)
2. [Google OAuth Configuration](#google-oauth-configuration)
3. [Testing](#testing)

---

## 2FA Setup

### Overview
The application supports TOTP (Time-based One-Time Password) for 2FA. Users can:
- Enable 2FA from their dashboard settings
- Use any authenticator app (Google Authenticator, Authy, Microsoft Authenticator, etc.)
- Generate and save backup codes for emergency access
- Verify their identity with TOTP codes during login

### How It Works

1. **Setup Page** (`/auth/2fa/setup/`)
   - Users generate a QR code that works with their authenticator app
   - Manual entry option for apps that don't support QR codes
   - TOTP code verification before enabling 2FA
   - Automatic backup code generation

2. **Login Flow**
   - Users log in with their credentials
   - If 2FA is enabled, they're redirected to verification page
   - They enter the 6-digit TOTP code or a backup code
   - System records the login session with 2FA verification status

3. **Backup Codes**
   - 10 unique backup codes generated when 2FA is enabled
   - Each code can only be used once
   - Users can download, copy, or print codes for safekeeping
   - Codes can be regenerated from the 2FA settings page

### User Flow

```
Login Page
    ↓
Enter Credentials
    ↓
    ├─ 2FA Enabled? 
    │   ├─ Yes → Verify 2FA Code Page
    │   │          ↓
    │   │      Enter TOTP/Backup Code
    │   │          ↓
    │   │      Dashboard
    │   │
    │   └─ No → Check Terms & Conditions
    │            ↓
    │        Dashboard
    │
    └─ Credentials Invalid → Error Message
```

---

## Google OAuth Configuration

### Prerequisites
- Google Cloud Console account
- OAuth 2.0 Client ID and Secret from Google

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Navigate to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
4. Select "Web Application"
5. Set Authorization Redirect URIs:
   - Development: `http://localhost:8000/accounts/google/login/callback/`
   - Production: `https://yourdomain.com/accounts/google/login/callback/`

### Step 2: Get OAuth Credentials

1. Copy your:
   - **Client ID** (long string ending in .googleusercontent.com)
   - **Client Secret** (random string)

### Step 3: Add to Django Admin

1. Start the server: `.\.venv\Scripts\python.exe manage.py runserver`
2. Go to `http://localhost:8000/admin/`
3. Log in with admin credentials
4. Navigate to "Sites" and ensure Site with domain `localhost:8000` or your domain exists
5. Go to "Social applications" → "Add Social Application"
6. Fill in:
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: [Your Google Client ID]
   - **Secret key**: [Your Google Client Secret]
   - **Sites**: Select your site
7. Click Save

### Step 4: Test the Configuration

1. Go to `http://localhost:8000/auth/login/`
2. You should see the "Sign in with Google" button
3. Click it to test the OAuth flow

### OAuth Configuration in Settings

The app is pre-configured with:
```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'FIELDS': ['email', 'first_name', 'last_name', 'picture']
    }
}
```

### Google OAuth Flow

```
User Clicks "Sign in with Google"
    ↓
Redirect to Google Login
    ↓
User Grants Permission
    ↓
Google Redirects to Callback
    ↓
    ├─ New User?
    │   ├─ Yes → Create Account
    │   │        ↓
    │   │   Check 2FA Required
    │   │        ↓
    │   │   Dashboard/2FA Setup
    │   │
    │   └─ No → Existing Account
    │
    └─ Check 2FA
        ├─ Enabled? 
        │   ├─ Yes → Verify 2FA
        │   │        ↓
        │   │    Dashboard
        │   │
        │   └─ No → Dashboard
```

---

## Testing

### Test Case 1: Traditional Login with 2FA

1. Register a test account: `test@hotel.com` / `Password123`
2. Go to `/auth/2fa/setup/`
3. Click "Generate QR Code"
4. Scan with Google Authenticator or similar app
5. Enter the 6-digit code from the app
6. Save backup codes
7. Logout and try logging back in with 2FA

### Test Case 2: Google OAuth Login

1. Go to `/auth/login/`
2. Click "Sign in with Google"
3. Grant permissions when prompted
4. Account should be created automatically
5. Dashboard should load

### Test Case 3: Using Backup Codes

1. Enable 2FA on an account
2. Logout
3. Try to login
4. Instead of TOTP code, paste a backup code
5. You should be logged in
6. View `/auth/2fa/backup-codes/` to verify code was used

### Test Case 4: 2FA Disable/Re-enable

1. Go to `/auth/2fa/setup/`
2. Scroll down to "Your 2FA is Enabled" section
3. Click "Disable 2FA"
4. Confirm the action
5. Go back to `/auth/2fa/setup/` to re-enable

---

## Database Models

### TwoFactorAuth
```python
- user: ForeignKey to CustomUser
- secret_key: Encrypted TOTP secret
- backup_codes: JSON array of backup codes
- is_enabled: Boolean
- is_verified: Boolean
- method: Choice of TOTP/SMS/EMAIL
- created_at, updated_at: Timestamps
```

### LoginSession
```python
- user: ForeignKey to CustomUser
- ip_address: User's IP
- user_agent: Browser info
- oauth_provider: google/null
- is_2fa_verified: Boolean
- created_at, expires_at: Timestamps
```

---

## Important Files

### Views
- `authentication/views.py` - All 2FA and login logic
  - `setup_2fa()` - 2FA setup page
  - `verify_2fa_login()` - 2FA verification during login
  - `view_backup_codes()` - Backup codes display
  - `disable_2fa()` - Disable 2FA
  - `login_view()` - Enhanced with 2FA redirection

### Templates
- `templates/authentication/setup_2fa.html` - 2FA setup UI
- `templates/authentication/verify_2fa.html` - 2FA code entry
- `templates/authentication/backup_codes.html` - Backup codes display
- `templates/authentication/login.html` - Login with Google OAuth button

### URLs
- `/auth/login/` - Traditional login with Google OAuth button
- `/auth/2fa/setup/` - 2FA setup and management
- `/auth/2fa/verify/` - 2FA code verification during login
- `/auth/2fa/backup-codes/` - View and manage backup codes
- `/auth/2fa/disable/` - Disable 2FA

---

## Troubleshooting

### Google OAuth Button Not Appearing
- Check if SocialApp is created in Django admin
- Verify Client ID and Secret are correct
- Ensure Site is selected for the SocialApp

### 2FA Code Not Working
- Verify device time is synchronized
- Code is only valid for 30 seconds
- Try backup code if TOTP code fails

### User Can't Login After Enabling 2FA
- Check if authenticator app time is synchronized
- Try using a backup code
- Disable 2FA from backup admin account if needed

### Sessions Not Being Tracked
- Ensure `LoginSession` model migration is applied
- Check `MIDDLEWARE` includes `django_otp.middleware.OTPMiddleware`

---

## Security Best Practices

1. **Backup Codes**: Users should store in a secure location (password manager, safe, etc.)
2. **TOTP Apps**: Recommend multiple authenticator apps for redundancy
3. **Session Timeout**: Consider implementing session timeout based on `LoginSession.expires_at`
4. **OAuth Scopes**: Only request necessary scopes (email, profile)
5. **HTTPS**: Always use HTTPS in production
6. **Secret Key**: Change Django `SECRET_KEY` in production

---

## Future Enhancements

- [ ] SMS/Email 2FA options
- [ ] WebAuthn/FIDO2 support
- [ ] Admin panel for session management
- [ ] 2FA statistics and analytics
- [ ] Custom backup code prefixes
- [ ] Passwordless authentication via email link
- [ ] Social account linking (link Google to existing account)

