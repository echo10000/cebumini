# Terms & Conditions Feature - Setup Guide

## Overview
The Terms & Conditions (T&C) feature enforces user agreement to your hotel's terms before allowing access to key features.

## Database Models

### TermsAndConditions Model
Stores T&C versions with the following fields:
- `version` (CharField): Version identifier (e.g., "1.0", "2.0")
- `content` (TextField): Full T&C text
- `is_active` (BooleanField): Marks current active version
- `created_at`, `updated_at` (DateTimeField): Timestamps

### CustomUser Model Updates
Added T&C tracking fields:
- `terms_accepted` (BooleanField): Whether user accepted T&C
- `terms_accepted_at` (DateTimeField): When acceptance occurred
- `terms_version` (CharField): Which T&C version was accepted

## Views & URLs

### New URLs
| URL | View | Purpose |
|-----|------|---------|
| `/auth/terms/` | `terms_view` | Display current T&C |
| `/auth/accept-terms/` | `accept_terms_view` | User acceptance page |

### Updated Views
| View | Changes |
|------|---------|
| `register_view` | Records T&C acceptance on signup |
| `login_view` | Redirects to accept if needed |
| `dashboard_view` | Blocks access if T&C not accepted |

## Templates

### New Templates
1. **terms.html** - Read-only view of T&C
2. **accept_terms.html** - Checkbox acceptance form

### Updated Templates
- **register.html** - Added T&C checkbox with link to full T&C
- **base.html** - Added "Terms & Conditions" navbar link

## Management Command

### add_terms
```bash
python manage.py add_terms
```
Creates default T&C version 1.0 with hotel terms content.

## Admin Panel Integration

### TermsAndConditionsAdmin
- View all T&C versions
- Add new versions
- Activate/deactivate versions
- Read-only: Can't delete T&C records (audit trail)

### CustomUserAdmin Updates
- New "Terms & Conditions" fieldset
- Shows: terms_accepted, terms_accepted_at, terms_version
- Display: terms_accepted in user list

## User Flow

### Registration Flow
```
User Registration
    ↓
Fill form + Check T&C checkbox
    ↓
Submit registration
    ↓
T&C acceptance recorded
    ↓
Redirect to login
```

### Login + T&C Flow
```
User Login
    ↓
Check if T&C accepted
    ├─ YES → Redirect to dashboard
    └─ NO → Redirect to accept_terms
         ↓
     User reviews and accepts T&C
         ↓
     T&C recorded in DB
         ↓
     Redirect to dashboard
```

### Dashboard Protection
```
Access /auth/dashboard/
    ↓
Check terms_accepted
    ├─ YES → Show dashboard
    └─ NO → Redirect to accept_terms
```

## Customization

### Modify T&C Content
1. Go to `/admin/`
2. Find "Terms and Conditions" section
3. Click existing version or add new
4. Update content
5. Check "is_active" for new versions
6. Old versions remain as audit trail

### Custom T&C Versions
```python
from authentication.models import TermsAndConditions

# Create new version
TermsAndConditions.objects.create(
    version='2.0',
    content='Updated T&C content here...',
    is_active=True
)

# Previous version is kept for audit
```

### Require Re-acceptance of Updated T&C
Update `accept_terms_view` to check version:
```python
if user.terms_version != terms.version:
    user.accept_terms(version=terms.version)
```

## Security Considerations

1. **Database Audit Trail**: All T&C versions stored
2. **Timestamp Tracking**: Know exactly when acceptance occurred
3. **Version Tracking**: Know which version user accepted
4. **Mandatory Acceptance**: Cannot access dashboard without T&C
5. **Registration Block**: Cannot register without T&C checkbox

## Testing the Feature

### Test Registration with T&C
1. Navigate to `/auth/register/`
2. Try submitting without checking T&C → Should fail
3. Check T&C box and submit → Should succeed
4. Verify user can login

### Test Login Redirect
1. Manually set `user.terms_accepted = False` in admin
2. Login as that user
3. Should redirect to `/auth/accept-terms/`
4. Accept T&C
5. Should redirect to dashboard

### Test Dashboard Block
1. Try accessing `/auth/dashboard/` without accepting T&C
2. Should redirect to accept page

## Database Queries

### Check who accepted T&C
```python
from authentication.models import CustomUser

# Users who accepted
CustomUser.objects.filter(terms_accepted=True)

# Users who haven't accepted
CustomUser.objects.filter(terms_accepted=False)

# When specific user accepted
user = CustomUser.objects.get(username='john')
print(f"Accepted at: {user.terms_accepted_at}")
print(f"Version: {user.terms_version}")
```

### View all T&C versions
```python
from authentication.models import TermsAndConditions

# All versions (oldest first)
TermsAndConditions.objects.all()

# Only active version
TermsAndConditions.objects.get(is_active=True)

# Latest version
TermsAndConditions.objects.latest('created_at')
```

## Troubleshooting

### Migration Issues
```bash
python manage.py makemigrations authentication
python manage.py migrate authentication
```

### T&C Not Showing in Admin
1. Check TermsAndConditionsAdmin is registered
2. Verify INSTALLED_APPS includes 'authentication'
3. Run migrations

### Users Stuck on Accept Page
1. Check `terms_accepted` field in admin
2. Manually set to True if needed
3. User should have access to dashboard

### Default T&C Not Created
```bash
python manage.py add_terms
```
This should create version 1.0

## Next Steps

- Add email notifications when user accepts T&C
- Implement forced re-acceptance for new T&C versions
- Add T&C acceptance history/audit log
- Send acceptance confirmation email
- Add multi-language support for T&C
