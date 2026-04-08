# Email Flow & Configuration Guide

## 🔴 CURRENT SITUATION

Your system is running in **DEVELOPMENT MODE** with:
```python
DEBUG = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

This means:
❌ Emails are **NOT** sent to real inboxes  
✅ Emails are **printed to the console** instead  
✅ This is intentional for development/testing  

---

## 📧 How Email Flow Works Currently

### Scenario: User Clicks "Forgot Password"

```
1. User enters email: user@gmail.com
   ↓
2. Django generates password reset token
   ↓
3. Django creates email message with reset link
   ↓
4. EMAIL_BACKEND = 'console.EmailBackend' is used
   ↓
5. Email is PRINTED TO CONSOLE (not sent to Gmail)
   ↓
6. User sees: "Check your email for reset link"
   ↓
7. Developer checks console output to find the reset link
```

### What You See in Console:

```
---------- MESSAGE ----------
Subject: [Cebu Hotel] Please Confirm Your E-mail Address
From: webmaster@localhost
To: user@gmail.com

Dear Jericho,

Please confirm your email address by visiting:
https://www.example.com/accounts/email/verification/...

Best Regards,
Cebu Hotel
---------- END MESSAGE ----------
```

---

## 🎯 Two Options to Fix This

### OPTION 1: Console Emails (Keep Development Setup) ✅ FASTEST

**When user requests password reset:**
1. They don't receive a real email ✓ (expected in dev)
2. You check the Django console
3. Copy the reset link from console
4. Send manually or use link yourself

**How to see emails in console:**
```bash
.\.venv\Scripts\python.exe manage.py runserver
# OR already running in terminal
# Just look at the terminal output when someone resets password
```

**Pros:** 
- No external services needed
- No security credentials required
- Fast setup ✓

**Cons:**
- Users don't get real emails
- You have to manually check console

---

### OPTION 2: Real Email Sending 📧 SETUP REQUIRED

Send actual emails via Gmail SMTP.

#### Step 1: Create Gmail App Password

1. Go to https://myaccount.google.com/
2. Click "Security" (left menu)
3. Enable "2-Step Verification" if not already done
4. Go back to Security
5. Find "App passwords" (appears after 2FA enabled)
6. Select "Mail" + "Windows Computer"
7. Google generates a 16-character password
8. **Copy this password** (you'll need it)

#### Step 2: Update Settings File

Edit `cebuhotel/settings.py`:

```python
# Email Configuration
if DEBUG:
    # Development: Send REAL emails
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'your-email@gmail.com'          # Your Gmail
    EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'       # App password from Step 1
    DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
else:
    # Production: Use environment variables
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@cebuhotel.com')
```

#### Step 3: Restart Django Server

```bash
# Stop current server (Ctrl+C)
# Restart:
.\.venv\Scripts\python.exe manage.py runserver
```

#### Step 4: Test Email

Go to: http://localhost:8000/accounts/password/reset/
- Enter **your** Gmail address
- You should receive the email in your inbox!

---

## 📊 Complete Email Flow Diagram

```
PASSWORD RESET FLOW:
═════════════════════════════════════════════════════════════

User navigates to /accounts/password/reset/
    ↓
User enters email: user@gmail.com
    ↓
Form validates email exists
    ↓
Django creates password reset token
    ↓
Django creates email message with reset link
    ↓
    ├─ OPTION 1 (Console Backend)
    │  └─ Email printed to console terminal
    │     └─ Developer copies link from console
    │
    └─ OPTION 2 (SMTP Backend)
       └─ Email sent to Gmail SMTP server
          └─ Gmail routes to user's inbox
          └─ User receives real email
             └─ User clicks link in email
                └─ Reset password
                └─ Login with new password

═════════════════════════════════════════════════════════════
```

---

## 🔄 Signup Email Flow

### AllAuth Signup:
```
User fills signup form
    ↓
Clicks "Create Account"
    ↓
User created in database
    ↓
Email verification sent
    ├─ Console: Shows in terminal
    └─ SMTP: Goes to user's inbox
```

### Custom Register (/auth/register/):
```
User fills register form
    ↓
Accepts T&C checkbox
    ↓
User created
    ↓
No email sent (custom form)
    ↓
User can login immediately
```

---

## 📋 Current Email Events That Trigger

1. **Signup Email Verification** (AllAuth only)
   - `POST /accounts/signup/`
   - Email: Confirmation link
   - Currently: Printed to console

2. **Password Reset**
   - `POST /accounts/password/reset/`
   - Email: Reset link
   - Currently: Printed to console

3. **Email Change Verification** (if enabled)
   - Email: Confirmation link
   - Currently: Not applicable yet

4. **Social Auth Emails**
   - Google login emails: Not needed (no verification)

---

## 🧪 How to Test Email Flow

### Test 1: See Console Emails

1. Start server: `.\.venv\Scripts\python.exe manage.py runserver`
2. Go to: http://localhost:8000/accounts/password/reset/
3. Enter email: `test@example.com`
4. Check **Django console output** for email content
5. Copy reset link from console
6. Use link to reset password

### Test 2: Send Real Emails (after Gmail setup)

1. Update settings.py with Gmail credentials
2. Restart server
3. Go to: http://localhost:8000/accounts/password/reset/
4. Enter **your real email address**
5. Check your **inbox** (not console!)
6. Click real email link to reset password

### Test 3: Signup Verification

1. Go to: http://localhost:8000/accounts/signup/
2. Fill form and create account
3. Check console OR inbox for verification email
4. Click verification link (if using SMTP)

---

## ⚡ Quick Setup - Choose Your Path

### Path A: Keep Console (No Setup) ⏱️ 0 minutes
- Current setup works
- Just check console for emails
- Good for development

### Path B: Use Gmail SMTP ⏱️ 5 minutes
1. Create Gmail App Password (3 min)
2. Update settings.py (1 min)
3. Restart server (1 min)
4. Test sending (10 sec)

---

## 🔐 Security Notes

**DO NOT:**
- Put real Gmail password in code (use environment variables for production)
- Share App Password - it's like a real password
- Commit settings.py with credentials to GitHub

**DO:**
- Use Gmail App Passwords (not your main password)
- Store passwords as environment variables on server
- Keep development/production separate

---

## Summary

**Current State:**
- ✅ Email system is working
- ✅ Emails are being generated
- ❌ But they're printed to console, not sent
- ✅ This is expected and safe for development

**To receive real emails:**
- Either: Check console output (FREE, 0 setup)
- Or: Configure Gmail SMTP (5 min setup, real emails)

Would you like me to:
1. Keep using console emails (check console for recovery links)?
2. Set up Gmail SMTP (real emails to your inbox)?
3. Set up alternative (SendGrid, Mailgun, etc.)?
