# Google OAuth Sign-Up Implementation Guide

## Overview
Your Django project already has `django-allauth` configured with Google OAuth support. This guide walks you through the complete setup and testing process.

## What's Already Done ✅
- ✅ `django-allauth` installed and configured
- ✅ Google OAuth provider registered in Django settings
- ✅ Login template updated with Google OAuth button
- ✅ Custom authentication adapters created
- ✅ Signal handlers for role assignment

## Step 1: Create Google OAuth Credentials

### 1.1 Access Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Search for "Google+ API" and enable it
4. Go to **Credentials** in the left sidebar

### 1.2 Create OAuth 2.0 Credentials
1. Click **+ Create Credentials** → **OAuth Client ID**
2. Choose **Web application**
3. Add authorized redirect URIs:
   ```
   http://localhost:8000/accounts/google/login/callback/
   http://localhost:8000/accounts/google/login/callback
   https://yourdomain.com/accounts/google/login/callback/
   ```
4. Copy your **Client ID** and **Client Secret**

## Step 2: Configure Google OAuth in Django Admin

### 2.1 Start Your Development Server
```powershell
python manage.py runserver
```

### 2.2 Create Django Superuser (if needed)
```powershell
python manage.py createsuperuser
```

### 2.3 Add Google OAuth Credentials
1. Navigate to `http://localhost:8000/admin`
2. Go to **Sites** section:
   - Ensure you have a site with domain matching your `ALLOWED_HOSTS`
   - For local dev: `127.0.0.1:8000` or `localhost:8000`
   - For production: your actual domain
3. Go to **Social Applications** → **Add Social Application**
4. Fill in the form:
   - **Provider**: Google
   - **Name**: Google
   - **Client ID**: (paste from Google Cloud Console)
   - **Secret key**: (paste from Google Cloud Console)
   - **Sites**: Select your site
5. Click **Save**

## Step 3: Test the Implementation

### 3.1 Test Login with Google
1. Go to `http://localhost:8000/auth/login/`
2. Click **Continue with Google**
3. You should be redirected to Google's login
4. After authentication, you'll be redirected back and logged in

### 3.2 Test Sign-Up with Google
1. Go to `http://localhost:8000/auth/register/`
2. Click **Sign up with Google**
3. Complete Google authentication
4. You'll be automatically logged in and redirected to dashboard

### 3.3 Verify User Creation
1. Go to `http://localhost:8000/admin/authentication/customuser/`
2. Check that new user has:
   - ✅ Email populated
   - ✅ First name and last name (if provided by Google)
   - ✅ Role set to **GUEST**
   - ✅ Email verified set to **True**

## How It Works

### User Flow
```
User clicks "Sign up with Google"
    ↓
Redirected to Google OAuth login
    ↓
User grants permissions
    ↓
Redirected back to your app
    ↓
django-allauth processes the OAuth response
    ↓
CustomAccountAdapter creates/updates user
    ↓
Signal handlers set GUEST role
    ↓
User logged in and redirected to dashboard
```

### Key Components

#### 1. **Signal Handlers** (`authentication/signals.py`)
- `handle_user_signed_up`: Sets GUEST role for new OAuth users
- `handle_pre_social_login`: Connects OAuth to existing accounts by email
- `handle_social_account_updated`: Keeps user profile in sync with provider

#### 2. **Custom Adapters** (`authentication/adapters.py`)
- `CustomAccountAdapter`: Generates usernames, handles redirects
- `CustomSocialAccountAdapter`: Handles OAuth-specific logic

#### 3. **Templates**
- `login.html`: Google login button
- `register.html`: Google sign-up button

## Configuration Details

### Django Settings (`cebuhotel/settings.py`)
```python
# OAuth Configuration
SOCIALACCOUNT_AUTO_SIGNUP = True          # Auto-create accounts
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none' # No email verification needed
SOCIALACCOUNT_QUERY_EMAIL = True          # Query by email for existing accounts
SOCIALACCOUNT_STORE_TOKENS = True         # Store OAuth tokens for future API calls

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'FIELDS': ['email', 'first_name', 'last_name', 'picture']
    }
}
```

## Troubleshooting

### Issue: "Invalid client" error
**Solution**: Verify Client ID and Secret in Django admin match Google Cloud Console

### Issue: Redirect URI mismatch error
**Solution**: 
- Check that your redirect URIs in Google Cloud Console match your domain
- Ensure the Site domain in Django admin matches your actual domain
- For local dev, use `127.0.0.1:8000` or `localhost:8000`

### Issue: User created but not logged in
**Solution**: Check logs for signal handler errors. Verify role is being set to GUEST.

### Issue: Email conflicts when linking accounts
**Solution**: The adapter automatically connects OAuth accounts to existing users by email. Make sure email-based authentication is enabled.

## Advanced Configuration

### Custom Redirect After Login
Edit `CustomAccountAdapter.get_login_redirect_url()` in `authentication/adapters.py`:
```python
def get_login_redirect_url(self, request):
    # Add custom logic here
    return '/auth/dashboard/'
```

### Storing Additional Data from Google
Modify `handle_social_account_updated` in `authentication/signals.py` to capture more fields:
```python
user.profile_picture = extra_data.get('picture')
user.locale = extra_data.get('locale')
```

### Requiring Additional Permissions
Update `SOCIALACCOUNT_PROVIDERS` in settings:
```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email', 'https://www.googleapis.com/auth/calendar'],
        # ...
    }
}
```

## Security Considerations

1. **Never commit Client Secret**: Use environment variables
   ```python
   # Better approach:
   SOCIALACCOUNT_PROVIDERS = {
       'google': {
           'APP': {
               'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
               'secret': os.getenv('GOOGLE_OAUTH_SECRET'),
               'key': ''
           }
       }
   }
   ```

2. **Email Verification**: Currently set to 'none' but can be changed:
   - `'optional'`: Email verification suggested but not required
   - `'mandatory'`: Email verification required

3. **CSRF Protection**: Django and allauth handle CSRF automatically

## Next Steps

### To Implement Additional OAuth Providers (e.g., GitHub, Facebook):
1. Install their provider: `pip install django-allauth`
2. Add to `INSTALLED_APPS`:
   ```python
   'allauth.socialaccount.providers.github',
   'allauth.socialaccount.providers.facebook',
   ```
3. Add credentials in Django admin
4. Add buttons to templates

### To Add 2FA for Google Sign-Ups:
The 2FA system is already implemented. Google sign-up users can enable 2FA from their dashboard settings.

### To Track OAuth Usage:
Add a field to CustomUser:
```python
oauth_provider = models.CharField(max_length=50, blank=True, choices=[('google', 'Google'), ('github', 'GitHub')])
```

## Files Modified

1. ✅ `authentication/adapters.py` - Enhanced with social account adapter
2. ✅ `authentication/signals.py` - Created new signal handlers
3. ✅ `authentication/apps.py` - Added signal registration
4. ✅ `templates/authentication/register.html` - Added Google sign-up button
5. ✅ `cebuhotel/settings.py` - Updated OAuth configuration

## Testing Checklist

- [ ] Google OAuth credentials created
- [ ] Credentials added in Django admin
- [ ] Google login button appears on login page
- [ ] Google sign-up button appears on register page
- [ ] Can login with Google account
- [ ] Can sign up with Google account
- [ ] New user created with GUEST role
- [ ] User email matches Google account
- [ ] User first/last name populated from Google
- [ ] Dashboard accessible after OAuth login
- [ ] Can perform actions (bookings, etc.) as OAuth user
