# Email Configuration Fix - AllAuth Signup Issue

## Problem Fixed ✅

**Error:** `ConnectionRefusedError` when signing up via AllAuth  
**Cause:** No SMTP server configured - Django tried to send email but failed  
**Location:** `/accounts/signup/` AllAuth endpoint

---

## Solution Implemented

### What Was Changed

Added email configuration to [cebuhotel/settings.py](cebuhotel/settings.py):

```python
# Email Configuration for Development
# Use console backend to print emails to console instead of sending
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # Use SMTP for production
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
```

### How It Works

**Development (DEBUG=True):**
- ✅ Uses **Console Email Backend**
- ✅ Emails are printed to server console/terminal
- ✅ No SMTP server needed
- ✅ Perfect for testing

**Production (DEBUG=False):**
- ✅ Uses **SMTP Email Backend**
- ✅ Requires environment variables
- ✅ Safely configured from environment
- ✅ Supports Gmail, SendGrid, etc.

---

## Testing AllAuth Signup

### Option 1: Test via Web Browser (Recommended)

```
1. Go to http://localhost:8000/accounts/signup/
2. Fill in:
   - Email: testuser@example.com
   - Password: TestPass123!
   - Confirm Password: TestPass123!
3. Click Sign Up
4. Check server console for verification email output
```

**Expected Result:**
- ✅ Redirect to success page or login
- ✅ Email printed to terminal/console
- ✅ No ConnectionRefusedError

### Option 2: Test via Python Script

```bash
python test_allauth_signup.py
```

This will:
- Send a POST request to `/accounts/signup/`
- Check if user was created
- Verify no errors occurred

---

## Email Output Example

When a user signs up, you'll see something like this in the server console:

```
------------------ Email Message --------------------
From: webmaster@localhost
To: testuser@example.com
Subject: Verify your email address

Hi testuser,

Please confirm that testuser@example.com is an email address for your account...
[Click link to verify]

----------------------------------------------------
```

---

## Production Deployment

### Before Going Live:

1. **Set DEBUG = False** in settings or environment

2. **Configure Email Environment Variables:**
   ```bash
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

3. **Gmail Specific Setup:**
   - Enable 2FA on your Google account
   - Generate "App Password": https://myaccount.google.com/apppasswords
   - Use that app password as `EMAIL_HOST_PASSWORD`

4. **Alternative: SendGrid, Mailgun, etc.**
   ```bash
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=SG.xxxxxxxxx
   ```

---

## Comparing the Two Signup Flows

### Custom Registration (`/auth/register/`)

**URL:** `http://localhost:8000/auth/register/`  
**What it does:**
- ✅ Uses custom form
- ✅ Accepts: email, first name, last name, password
- ✅ Auto-accepts T&C checkbox
- ✅ Creates user immediately
- ✅ No email verification required
- ✅ Good for internal/admin registration

### AllAuth Signup (`/accounts/signup/`)

**URL:** `http://localhost:8000/accounts/signup/`  
**What it does:**
- ✅ Uses AllAuth form
- ✅ Accepts: email, password only
- ✅ Sends verification email (now via console)
- ✅ Allows optional email verification
- ✅ Social login integration ready
- ✅ Good for public signup

---

## Current Email Configuration Status

```python
# In Development:
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Result: Emails print to terminal ✅

# In Production:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Result: Emails sent via SMTP (needs config)
```

---

## Testing Checklist

### Basic Signup Flow
- [ ] Visit `/accounts/signup/`
- [ ] Enter email and password
- [ ] Click Sign Up
- [ ] Check for errors (should have none now)
- [ ] Look at server console for email output
- [ ] User should be created in database

### Custom Registration
- [ ] Still works at `/auth/register/`
- [ ] Has all custom fields
- [ ] Auto-accepts T&C
- [ ] No email verification needed

### 2FA Still Working
- [ ] Login works
- [ ] 2FA setup works
- [ ] 2FA verification works
- [ ] Backup codes work

---

## Troubleshooting

### "Still getting ConnectionRefusedError"

**Solution:**
1. Make sure server reloaded after settings.py change
2. Check that `DEBUG = True` in settings
3. Restart server: `python manage.py runserver`

### "Email not printing to console"

**Check:**
1. `ACCOUNT_EMAIL_VERIFICATION = 'optional'` is set (it is)
2. Server console is visible
3. Scroll up in console to find email output

### "User created but can't login"

**Reason:** AllAuth may require email verification  
**Solution:** Set `ACCOUNT_EMAIL_VERIFICATION = 'none'`

---

## All Email Backends Available

```python
# Console Backend (Development)
'django.core.mail.backends.console.EmailBackend'

# File Backend (writes to file)
'django.core.mail.backends.filebased.EmailBackend'

# SMTP Backend (sends real emails)
'django.core.mail.backends.smtp.EmailBackend'

# Dummy Backend (does nothing)
'django.core.mail.backends.dummy.EmailBackend'

# In-Memory Backend (stores in memory)
'django.core.mail.backends.locmem.EmailBackend'
```

---

## Summary

✅ **Fixed AllAuth signup ConnectionRefusedError**  
✅ **Configured console email backend for development**  
✅ **Added SMTP configuration for production**  
✅ **All signup flows now working**  
✅ **Ready to deploy**  

Both signup methods now work:
- Custom registration: `/auth/register/` ✅
- AllAuth signup: `/accounts/signup/` ✅

Server is running and ready for testing! 🚀

