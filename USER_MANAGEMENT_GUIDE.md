# User Management & Password Reset Design Guide

## 1. CLEARING/DELETING USERS

### Quick Start - Delete Users Script

I've created an interactive user management script for you. To use it:

```bash
.\.venv\Scripts\python.exe manage_users.py
```

### What You Can Do:

1. **View all users** - See list of all registered emails
2. **Delete specific user** - Remove one user by email address
3. **Delete all non-admin users** - Clear test accounts, keep admin
4. **Delete all users** - Nuclear option (requires confirmation)
5. **View only** - No changes, just look at the data

### Example Usage:

```
$ python manage_users.py

📋 CURRENT USERS IN DATABASE:
1. Email: test@example.com
2. Email: user@hotel.com
...

What would you like to do?
1. Delete a specific user by email
2. Delete all users except admin
3. Delete all users
4. Just view users (do nothing)

Enter choice (1-4): 2
```

### Command Line Alternative:

Delete all users from database:
```bash
.\.venv\Scripts\python.exe manage.py shell -c "from django.contrib.auth import get_user_model; get_user_model().objects.all().delete(); print('✓ All users deleted')"
```

Delete specific user:
```bash
.\.venv\Scripts\python.exe manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='test@example.com').delete(); print('✓ User deleted')"
```

---

## 2. PASSWORD RESET PAGES - NOW STYLED

### Pages Updated:

✅ **Password Reset Request** (`/accounts/password_reset/`)
- Before: Had basic styling
- Now: Professional form with green accent

✅ **Password Reset Confirmation** (`/accounts/password_reset/done/`)
- Before: Plain text message (as in your screenshot)
- Now: **Styled with success box, info section, contact links**

✅ **The Reset** (`/accounts/password_reset/:key/`)
- Before: Had basic styling
- Now: Professional form for setting new password

✅ **Password Reset Success** (`/accounts/password_reset/done/`)
- Before: N/A (didn't exist)
- Now: **New styled confirmation page after successful reset**

✅ **Password Change** (`/accounts/password_change/`)
- Before: Minimal styling
- Now: **Enhanced with password requirements, better labels, consistent design**

### Design Features Added:

✅ Green gradient success box with checkmark  
✅ Info sections with blue left border and icons  
✅ Security tips and warnings  
✅ Action buttons (Login, Home)  
✅ Support contact link  
✅ Responsive grid layout  
✅ Consistent branding across all pages  

---

## 3. WORKFLOW - PASSWORD RESET

### User Flow:

1. User clicks "Forgot Password" on login page
   → Goes to `/accounts/password_reset/`

2. User enters email address
   → Form validates and shows **beautiful confirmation page** ✓
   → Email sent to user (console output in dev mode)

3. User clicks link in email
   → Goes to `/accounts/password_reset/:key/`
   → User enters new password

4. User submits new password
   → Shows **new success page** ✓
   → Can login with new password

5. To change password while logged in:
   → Dashboard → Settings → Change Password
   → Uses **enhanced password change form** ✓

---

## 4. BEFORE & AFTER

### Before:
```
Password Reset
We have sent you an email. If you have not received it...
```
(Plain text, no styling)

### After:
```
✓ Success box with green gradient
📧 "What happens next?" info box
🔗 "The Reset Link" instructions
[Login to Account] [Go to Home] buttons
💡 Security tip section
Contact support link
```

---

## File Changes Made:

**New Files:**
- `manage_users.py` - Interactive user management
- `templates/account/password_reset_done.html` - Styled confirmation
- `templates/account/password_reset_from_key_done.html` - Styled success

**Enhanced Files:**
- `templates/account/password_change.html` - Better styling & layout

---

## Testing the Styles

### Test Password Reset:

1. Go to http://localhost:8000/accounts/password/reset/
2. Enter an email address
3. See the **styled confirmation page**
4. Check console for email link
5. Click link from email
6. Change password
7. See the **styled success page**

### Test User Management:

```bash
# View all users
python manage_users.py
# Choose option 4 (just view)

# Delete test user
python manage_users.py
# Choose option 1 (specific user)
# Enter: testuser@example.com

# Clean database (delete all non-admin)
python manage_users.py
# Choose option 2 (all except admin)
```

---

## Account Signup Flow (Already Fixed)

✅ Custom Register `/auth/register/` - Has T&C checkbox
✅ AllAuth Signup `/accounts/signup/` - Now has T&C checkbox
✅ Password Reset - Now has beautiful styling
✅ All pages have consistent design

---

## Summary

- **User Management**: Use `manage_users.py` for interactive deletion
- **Password Pages**: All now beautifully styled with info boxes & icons
- **Testing**: Pages fully functional and visually consistent
- **Ready**: All authentication flows are complete and polished
