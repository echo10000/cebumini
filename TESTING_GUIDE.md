# 🧪 Terms & Conditions - Testing Guide

## Quick Start Testing

### 1. Setup & Initialization

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Mac/Linux

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Load default T&C
python manage.py add_terms

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Manual Testing Scenarios

### Scenario 1: Registration Without T&C Checkbox ❌

**Objective**: Verify that unchecking T&C blocks registration

**Steps**:
1. Navigate to http://127.0.0.1:8000/auth/register/
2. Fill in all fields:
   - Username: `testuser1`
   - Email: `test1@example.com`
   - First Name: `Test`
   - Last Name: `User`
   - Password: `TestPass123!`
   - Confirm Password: `TestPass123!`
3. **Do NOT check** the T&C checkbox
4. Click "Register"

**Expected Result**:
- ❌ Registration fails
- Error message: "You must accept the Terms and Conditions to proceed."
- Form is redisplayed with error highlighted

---

### Scenario 2: Registration With T&C Checkbox ✅

**Objective**: Verify successful registration with T&C acceptance

**Steps**:
1. Navigate to http://127.0.0.1:8000/auth/register/
2. Fill in all fields (same as Scenario 1)
3. **CHECK** the T&C checkbox
4. Click "Register"

**Expected Result**:
- ✅ Registration succeeds
- Success message: "Registration successful! Please log in."
- Redirected to login page
- Check database: User record created with `terms_accepted=True`

**Database Verification**:
```bash
python manage.py shell
>>> from authentication.models import CustomUser
>>> user = CustomUser.objects.get(username='testuser1')
>>> user.terms_accepted
True
>>> user.terms_accepted_at
datetime.datetime(2026, 2, 13, 10, 30, 45, tzinfo=<UTC>)
>>> user.terms_version
'1.0'
```

---

### Scenario 3: Login and T&C Enforcement ✅

**Objective**: Verify that users must accept T&C after login if not yet accepted

**Steps**:
1. Create a test user in database with `terms_accepted=False`:
   ```bash
   python manage.py shell
   >>> from authentication.models import CustomUser
   >>> user = CustomUser.objects.create_user(
   ...     username='noterms',
   ...     email='noterms@example.com',
   ...     password='TestPass123!'
   ... )
   >>> user.terms_accepted = False
   >>> user.save()
   ```

2. Navigate to http://127.0.0.1:8000/auth/login/
3. Login with credentials:
   - Username: `noterms`
   - Password: `TestPass123!`
4. Click "Login"

**Expected Result**:
- ✅ Login succeeds (credentials verified)
- Automatically redirected to `/auth/accept-terms/`
- Dashboard is NOT accessible
- Page shows: "Review and Accept Terms"

---

### Scenario 4: Accept Terms After Login ✅

**Objective**: Verify user can accept T&C and access dashboard

**Continuing from Scenario 3**:

**Steps**:
1. Already on accept-terms page (from previous scenario)
2. Read the displayed T&C content
3. **CHECK** the checkbox: "I have read and agree..."
4. Click "Accept and Continue"

**Expected Result**:
- ✅ T&C acceptance recorded
- Success message: "Terms and Conditions accepted successfully!"
- Redirected to `/auth/dashboard/`
- Dashboard content displayed

**Database Verification**:
```bash
python manage.py shell
>>> from authentication.models import CustomUser
>>> user = CustomUser.objects.get(username='noterms')
>>> user.terms_accepted
True
>>> user.terms_accepted_at  # Should have timestamp
>>> user.terms_version
'1.0'
```

---

### Scenario 5: Dashboard Access Without T&C ❌

**Objective**: Verify dashboard access is blocked for users without T&C

**Steps**:
1. Create user without T&C acceptance
2. Manually navigate to http://127.0.0.1:8000/auth/dashboard/
   (Without logging in or after manually clearing terms_accepted in DB)

**Expected Result**:
- ❌ Access blocked
- Warning message: "Please accept the Terms and Conditions to access the dashboard."
- Redirected to `/auth/accept-terms/`
- User cannot proceed to dashboard

---

### Scenario 6: View Terms Page ✅

**Objective**: Verify T&C page is accessible and displays content

**Steps**:
1. Navigate to http://127.0.0.1:8000/auth/terms/
   (Can be accessed without login)

**Expected Result**:
- ✅ Page loads successfully
- Displays current active T&C version content
- Shows version number (e.g., "Version: 1.0")
- T&C text is readable and scrollable
- Buttons: "Accept Terms" and "Back to Home"

---

### Scenario 7: Multiple T&C Versions ✅

**Objective**: Verify system can handle multiple T&C versions

**Steps**:
1. Go to Django admin: http://127.0.0.1:8000/admin/
2. Navigate to "Terms and Conditions"
3. Click existing T&C version 1.0
4. Change `is_active` to False
5. Click "Save"
6. Click "Add Terms and Conditions"
7. Fill in:
   - Version: `2.0`
   - Content: `New T&C content for version 2...`
   - is_active: ✓ (checked)
8. Click "Save"

**Expected Result**:
- ✅ Both versions exist in database
- Version 1.0: `is_active=False`
- Version 2.0: `is_active=True`
- New users see version 2.0 when registering
- Existing users with version 1.0 still have access

**Database Check**:
```bash
python manage.py shell
>>> from authentication.models import TermsAndConditions
>>> TermsAndConditions.objects.all()
<QuerySet [<T&C v1.0>, <T&C v2.0>]>
>>> TermsAndConditions.objects.filter(is_active=True)
<QuerySet [<T&C v2.0>]>
```

---

## API/Endpoint Testing

### Test with cURL or Postman

#### Get Terms Page
```bash
curl http://127.0.0.1:8000/auth/terms/
# Expected: 200 OK, HTML with T&C content
```

#### Register (Without T&C)
```bash
curl -X POST http://127.0.0.1:8000/auth/register/ \
  -d "username=test&email=test@test.com&first_name=Test&last_name=User&password1=Pass123!&password2=Pass123!" \
  -c cookies.txt
# Expected: 200 OK, but form with error message
```

#### Register (With T&C)
```bash
curl -X POST http://127.0.0.1:8000/auth/register/ \
  -d "username=test&email=test@test.com&first_name=Test&last_name=User&password1=Pass123!&password2=Pass123!&accept_terms=on" \
  -c cookies.txt
# Expected: 302 redirect to login (Success)
```

---

## Browser Testing Checklist

### Registration Flow ✅
- [ ] T&C link opens in new tab
- [ ] T&C page displays full content
- [ ] Can scroll through T&C
- [ ] Back to register page works
- [ ] Checkbox toggles on/off
- [ ] Error message shows if unchecked
- [ ] Checkbox state persists on form error

### Login & Accept Flow ✅
- [ ] Login form works normally
- [ ] Without T&C: Redirects to accept page
- [ ] Accept page displays T&C content
- [ ] Checkbox is required to proceed
- [ ] Clicking accept redirects to dashboard
- [ ] Dashboard shows user info
- [ ] Navbar shows logged-in state

### Dashboard Protection ✅
- [ ] Can't access dashboard without T&C
- [ ] Direct URL access redirects to accept
- [ ] Back button on accept page works
- [ ] "Skip for Now" button appears (if needed)
- [ ] User profile shows T&C status

### Navigation ✅
- [ ] "Terms & Conditions" link in navbar works
- [ ] T&C page accessible from anywhere
- [ ] All redirects work properly
- [ ] No broken links

---

## Performance Testing

### Response Time
```bash
# Measure page load times
time curl http://127.0.0.1:8000/auth/register/
time curl http://127.0.0.1:8000/auth/terms/
time curl http://127.0.0.1:8000/auth/accept-terms/
time curl http://127.0.0.1:8000/auth/dashboard/
```

**Expected**: < 200ms per page

### Database Queries
```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as context:
    # Access dashboard
    response = client.get('/auth/dashboard/')
    
print(f"Queries: {len(context.captured_queries)}")
for query in context.captured_queries:
    print(query['sql'])
```

**Expected**: < 5 queries per page

---

## Security Testing

### CSRF Protection ✅
1. Open form but don't submit
2. Copy the CSRF token from page source
3. Try submitting without token:
   ```bash
   curl -X POST http://127.0.0.1:8000/auth/register/ \
     -d "username=test&email=test@test.com&..." \
     --referer http://127.0.0.1:8000/auth/register/
   # Expected: 403 Forbidden (CSRF failure)
   ```

### Password Hashing ✅
```python
from authentication.models import CustomUser

user = CustomUser.objects.get(username='testuser1')
print(user.password)
# Expected: Output like: pbkdf2_sha256$180000$abcd...
# NOT plain text password
```

### SQL Injection ✅
Try logging in with malicious input:
- Username: `admin' --`
- Password: `' OR '1'='1`

**Expected**: "Invalid username or password" message (Protected)

---

## Admin Panel Testing

### User Admin ✅
1. Go to /admin/
2. Click "Users"
3. Select a user who accepted T&C

**Verify you see**:
- [ ] `terms_accepted` field
- [ ] `terms_accepted_at` timestamp
- [ ] `terms_version` value (e.g., "1.0")

### T&C Admin ✅
1. Go to /admin/
2. Click "Terms and Conditions"
3. View existing version

**Verify you can**:
- [ ] View version number
- [ ] See full content
- [ ] See is_active status
- [ ] See created_at, updated_at
- [ ] Edit existing (but can't delete)
- [ ] Add new version

---

## Error Scenario Testing

### What if T&C is missing?
```python
from authentication.models import TermsAndConditions
TermsAndConditions.objects.all().delete()

# Try accepting T&C
# Expected: Shows alert "Terms and Conditions not available"
```

### What if user data is corrupted?
```python
user = CustomUser.objects.get(username='test')
user.terms_accepted_at = None
user.terms_version = None
user.save()

# Login as user
# Expected: Redirects to accept page
# After acceptance: All fields updated
```

### Session timeout
1. Login successfully
2. Modify session expiry to 1 second:
   ```python
   session = Session.objects.first()
   session.expire_date = timezone.now() - timedelta(seconds=1)
   session.save()
   ```
3. Reload page
4. Expected: Logged out, redirected to login

---

## Test Cases Summary

| # | Scenario | Expected | Status |
|---|----------|----------|--------|
| 1 | Register without T&C | ❌ Fail | [ ] |
| 2 | Register with T&C | ✅ Success | [ ] |
| 3 | Login without T&C acceptance | ✅ Redirect to accept | [ ] |
| 4 | Accept T&C after login | ✅ Access dashboard | [ ] |
| 5 | Dashboard access without T&C | ❌ Blocked | [ ] |
| 6 | View T&C page | ✅ Display content | [ ] |
| 7 | Multiple T&C versions | ✅ Both stored | [ ] |
| 8 | CSRF protection | ✅ Protected | [ ] |
| 9 | Password hashing | ✅ PBKDF2 hashed | [ ] |
| 10 | SQL injection | ✅ Protected | [ ] |
| 11 | Admin T&C management | ✅ Works | [ ] |
| 12 | User profile T&C status | ✅ Visible | [ ] |

---

## Troubleshooting Test Failures

### "T&C not showing in form"
- [ ] Run migrations: `python manage.py migrate`
- [ ] Check forms.py has `accept_terms` field
- [ ] Restart Django server

### "Dashboard still accessible without T&C"
- [ ] Check dashboard_view has T&C check
- [ ] Verify user.has_accepted_terms() returns correct value
- [ ] Check database: `terms_accepted` field exists

### "Migration conflicts"
- [ ] Reset migrations: `python manage.py migrate authentication zero`
- [ ] Delete migration files (keep __init__.py)
- [ ] Run makemigrations and migrate again

### "Admin panel changes not visible"
- [ ] Clear browser cache (Ctrl+Shift+Delete)
- [ ] Restart Django server
- [ ] Verify database was actually updated

---

**All tests should pass before production deployment** ✅
**Expected test time**: ~30 minutes
**Required coverage**: 100% of flows
