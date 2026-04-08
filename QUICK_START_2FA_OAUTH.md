# 2FA & OAuth Quick Reference Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Start the Server
```bash
cd c:\Users\echog\OneDrive\Desktop\cebuhotel
.\.venv\Scripts\python.exe manage.py runserver
```

### Step 2: Register a Test Account
- Go to http://localhost:8000/auth/register/
- Create account with email and password
- Accept terms

### Step 3: Enable 2FA
- Go to http://localhost:8000/auth/2fa/setup/
- Click "Generate QR Code"
- Scan with authenticator app (Google Authenticator, Authy, etc.)
- Enter 6-digit code from app
- Save backup codes

### Step 4: Test Login with 2FA
- Logout
- Log back in
- Enter 2FA code when prompted

---

## 📱 2FA Features

### Setup
| Action | URL |
|--------|-----|
| Setup 2FA | `/auth/2fa/setup/` |
| Verify during login | `/auth/2fa/verify/` |
| View backup codes | `/auth/2fa/backup-codes/` |
| Disable 2FA | `/auth/2fa/disable/` |

### What You Get
- ✅ QR code for authenticator apps
- ✅ Manual secret code entry option
- ✅ 10 backup codes for emergencies
- ✅ Download/copy/print backup codes
- ✅ Enable/disable anytime
- ✅ Session tracking for all logins

---

## 🔐 Google OAuth (Optional)

### Setup Google OAuth

#### Option A: Quick Setup Command
```bash
.\.venv\Scripts\python.exe manage.py setup_google_oauth \
    --client-id YOUR_CLIENT_ID \
    --secret YOUR_CLIENT_SECRET
```

#### Option B: Manual Setup in Admin
1. Go to http://localhost:8000/admin/
2. **Social Applications** → **Add**
3. Fill in:
   - Provider: `google`
   - Name: `Google OAuth`
   - Client ID: *[from Google Cloud]*
   - Secret key: *[from Google Cloud]*
   - Sites: Select `localhost:8000`
4. Save

### Get Google Credentials
1. Go to https://console.cloud.google.com/
2. Create new project
3. APIs & Services → Credentials
4. Create OAuth 2.0 Client ID (Web Application)
5. Add authorized redirect: `http://localhost:8000/accounts/google/login/callback/`
6. Copy Client ID and Secret

---

## 🧪 Testing Checklist

- [ ] Register new account
- [ ] Enable 2FA with authenticator app
- [ ] Login with 2FA code
- [ ] Use backup code to login
- [ ] Download backup codes
- [ ] Disable 2FA
- [ ] Re-enable 2FA
- [ ] Setup Google OAuth (optional)
- [ ] Login with Google

---

## 📝 Important Files

### Configuration
- `cebuhotel/settings.py` - OAuth & 2FA settings
- `authentication/models.py` - TwoFactorAuth & LoginSession models
- `authentication/views.py` - 2FA logic

### Templates
- `templates/authentication/login.html` - Login with Google button
- `templates/authentication/setup_2fa.html` - 2FA setup UI
- `templates/authentication/verify_2fa.html` - 2FA verification
- `templates/authentication/backup_codes.html` - Backup codes display

### Management
- `authentication/management/commands/setup_google_oauth.py` - OAuth setup

---

## 🔗 Login Flow

### Without 2FA
```
Login Page → Enter Credentials → Dashboard
```

### With 2FA Enabled
```
Login Page → Enter Credentials → 2FA Verification → Enter Code → Dashboard
```

### With Google OAuth
```
Login Page → Click Google Button → Google Login → Create/Link Account → Dashboard/2FA
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Google button missing | Run setup command or add in Django admin |
| 2FA code not working | Sync device time, wait 30 seconds for new code |
| Can't scan QR code | Click "Can't scan?" and manually enter secret |
| Backup code rejected | Code already used or invalid format |
| Authenticator not installed | Download Google Authenticator, Authy, or FreeOTP |

---

## 📊 What Gets Tracked

### LoginSession Records
- ✓ User IP address
- ✓ Browser information
- ✓ OAuth provider used
- ✓ 2FA verification status
- ✓ Login timestamp

View in admin: **Authentication** → **Login Sessions**

---

## 🛡️ Security Features

### 2FA
- TOTP codes valid for 30 seconds only
- Backup codes one-time use
- Secret keys encrypted
- Server-side validation

### OAuth
- HTTPS-only in production
- CSRF protection
- Secure token exchange
- Email verification

---

## 📚 Documentation

For detailed information:
- **Setup Guide**: `2FA_AND_OAUTH_SETUP.md`
- **Testing Guide**: `TESTING_2FA_AND_OAUTH.md`
- **Full Implementation**: `2FA_AND_OAUTH_IMPLEMENTATION.md`

---

## 💡 Pro Tips

1. **Backup Codes**: Store in password manager or safe location
2. **Time Sync**: Ensure device time is synchronized for TOTP
3. **Backup App**: Install authenticator app on multiple devices
4. **Device Trust**: Consider implementing "remember this device" (future feature)
5. **Audit Logs**: Check LoginSession for suspicious activity

---

## 🔒 Production Checklist

Before going live:
- [ ] Change Django SECRET_KEY
- [ ] Set DEBUG = False
- [ ] Use HTTPS for all URLs
- [ ] Configure ALLOWED_HOSTS
- [ ] Use PostgreSQL database
- [ ] Update Google OAuth callback URLs
- [ ] Enable secure session cookies
- [ ] Setup proper email verification
- [ ] Configure backup email address
- [ ] Test OAuth credentials in production domain

---

## ⚡ Quick Commands

```bash
# Start server
.\.venv\Scripts\python.exe manage.py runserver

# Setup Google OAuth
.\.venv\Scripts\python.exe manage.py setup_google_oauth --client-id ID --secret SECRET

# Access admin
http://localhost:8000/admin/

# Access login
http://localhost:8000/auth/login/

# Access 2FA setup (when logged in)
http://localhost:8000/auth/2fa/setup/

# Run migrations
.\.venv\Scripts\python.exe manage.py migrate
```

---

## 📞 Support URLs

- **Homepage**: http://localhost:8000/
- **Login**: http://localhost:8000/auth/login/
- **Register**: http://localhost:8000/auth/register/
- **Dashboard**: http://localhost:8000/auth/dashboard/
- **2FA Setup**: http://localhost:8000/auth/2fa/setup/
- **Admin**: http://localhost:8000/admin/

---

## 🎯 Next Steps

1. Start server and test traditional login
2. Enable 2FA on your account
3. Test login with 2FA
4. (Optional) Setup Google OAuth
5. Test all features
6. Deploy to production

---

**Status**: ✅ All features implemented and tested  
**Last Updated**: February 26, 2026  
**v1.0.0**

