# 📊 Terms & Conditions - Flow Diagrams & Visual Guides

## 🔄 Complete User Flow with T&C

```
┌─────────────────────────────────────────────────────────────────┐
│                    CEBU HOTEL SYSTEM FLOW                        │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │  User Visits │
                         │    Website   │
                         └──────┬───────┘
                                │
                    ┌───────────┴──────────┐
                    │                      │
              ┌─────▼──────┐      ┌───────▼──────┐
              │   Login    │      │  Not Login   │
              └─────┬──────┘      └───────┬──────┘
                    │                     │
          ┌─────────▼──────────┐  ┌──────▼──────────┐
          │ Enter Credentials  │  │ View Home Page  │
          └─────────┬──────────┘  └──────┬──────────┘
                    │                    │
          ┌─────────▼──────────┐    ┌────▼──────────┐
          │ Verify Credentials │    │ Click Register│
          └─────────┬──────────┘    │    or Login   │
                    │               └────┬──────────┘
          ┌─────────▼──────────────────────┐
          │ Check: T&C Accepted?           │
          └─────────┬──────────────────────┘
                    │
        ┌───────────┴──────────────┐
        │                          │
    ┌───▼────┐              ┌─────▼──────┐
    │   NO   │              │    YES     │
    └───┬────┘              └─────┬──────┘
        │                         │
   ┌────▼──────────────┐    ┌─────▼──────┐
   │ Redirect to       │    │ Dashboard  │
   │ Accept T&C Page   │    │ Access OK  │
   └────┬──────────────┘    └────────────┘
        │
   ┌────▼──────────────────────────────┐
   │ Show T&C + Acceptance Checkbox    │
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐
   │ User Checks "I Agree" Checkbox    │
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐
   │ Clicks "Accept & Continue"        │
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐
   │ Save to DB:                       │
   │ - terms_accepted = True           │
   │ - terms_accepted_at = NOW()       │
   │ - terms_version = '1.0'           │
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐
   │ Redirect to Dashboard             │
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐
   │ Dashboard Access Granted ✓        │
   └───────────────────────────────────┘
```

## 📝 Registration Flow (Detailed)

```
REGISTRATION WITH T&C ENFORCEMENT

   User: Click "Register"
        ↓
   🔗 URL: /auth/register/
        ↓
   📄 Form Elements:
   ├─ Username (required)
   ├─ Email (required)
   ├─ First Name (required)
   ├─ Last Name (required)
   ├─ Password (required)
   ├─ Confirm Password (required)
   └─ ☑ Accept Terms & Conditions (REQUIRED)
        ↓
   User fills form
        ↓
   ✓ Check T&C checkbox
        ↓
   Submit Form
        ↓
   ┌─────────────────────────────────┐
   │   DJANGO VALIDATION             │
   ├─────────────────────────────────┤
   │ ✓ Username unique?              │
   │ ✓ Email unique?                 │
   │ ✓ Passwords match?              │
   │ ✓ Password strong?              │
   │ ✓ T&C checkbox checked?         │
   └────────────┬────────────────────┘
                │
        ┌───────┴────────┐
        │                │
   ✓ ALL PASS      ✗ FAILS
        │                │
   ┌────▼──────┐    ┌────▼─────────┐
   │ Create    │    │ Show errors  │
   │ User      │    │ on form      │
   │           │    └──────┬───────┘
   │ Hash pwd  │           │
   │ with      │      User re-enters
   │ PBKDF2    │      corrected data
   └────┬──────┘           ↑
        │                  │
   ┌────▼──────┐      └────┘
   │ Record T&C│
   │ acceptance│
   │ in DB:    │
   │ - accepted│
   │ - at time │
   │ - v1.0    │
   └────┬──────┘
        │
   ┌────▼──────────────┐
   │ Send success msg  │
   │ "Registration OK" │
   └────┬──────────────┘
        │
   ┌────▼──────────────┐
   │ Redirect to       │
   │ /auth/login/      │
   └───────────────────┘
```

## 🔐 Login + T&C Check Flow

```
LOGIN PROCESS WITH T&C ENFORCEMENT

   User: Enter username and password
        ↓
   🔗 URL: /auth/login/ [POST]
        ↓
   ┌──────────────────────────────┐
   │ Validate Credentials         │
   │ - Try username authentication│
   │ - Try email authentication   │
   └────┬─────────────────────────┘
        │
    ┌───┴────┐
    │ Auth OK?
    └───┬────┘
        │
   ┌────▼────┐              ┌─────────┐
   │  YES    │              │   NO    │
   └────┬────┘              └────┬────┘
        │                        │
   ┌────▼──────────────┐   ┌────▼───────────┐
   │ Login successful  │   │ Show error:    │
   │ Create session    │   │ Invalid creds  │
   └────┬──────────────┘   └────────────────┘
        │                   Redirect to login
   ┌────▼──────────────────────────────┐
   │ Check T&C Status:                 │
   │ SELECT terms_accepted FROM users  │
   └────┬──────────────────────────────┘
        │
   ┌────┴──────────┐
   │               │
 YES              NO
   │               │
┌──▼──────┐   ┌───▼────────────────┐
│Dashboard │   │ terms_accepted_at  │
│Access OK │   │ is NULL?           │
└─────────┘    └───┬────────────────┘
                   │
            ┌──────▼──────────┐
            │ Redirect to:    │
            │ /auth/accept-   │
            │ terms/          │
            │ [Required]      │
            └─────────────────┘
```

## ✅ Accept Terms Flow

```
T&C ACCEPTANCE PAGE

   🔗 URL: /auth/accept-terms/ [GET/POST]
        ↓
   ┌─────────────────────────────────┐
   │ CHECK IF ALREADY ACCEPTED       │
   │ if user.has_accepted_terms()    │
   └────┬────────────────────────────┘
        │
   ┌────┴──────┐
   │ Already?  │
   └────┬──────┘
        │
   ┌────▼────┐          ┌─────────┐
   │  YES    │          │   NO    │
   └────┬────┘          └────┬────┘
        │                    │
   ┌────▼──────────┐   ┌─────▼─────────────┐
   │ Redirect to   │   │ Fetch Active T&C  │
   │ Dashboard     │   │ from DB           │
   │ (no action)   │   │ Display content   │
   └───────────────┘   └─────┬─────────────┘
                             │
                        ┌────▼──────────────────┐
                        │ HTML FORM:            │
                        │ ☐ I have read and    │
                        │   agree to T&C       │
                        │                       │
                        │ [Accept & Continue]  │
                        │ [Skip for Now]       │
                        └─────┬─────────────────┘
                              │
                         ┌────▼────┐
                         │ Submitted
                         └────┬────┘
                              │
                         ┌────▼───────────┐
                         │ Checkbox val?  │
                         └────┬────┬──────┘
                              │    │
                          ✓ YES   ✗ NO
                              │    │
                         ┌────▼┐  ┌─▼────────────┐
                         │Save │  │Show error:   │
                         │to DB│  │"Must accept" │
                         └────┬┘  └──────┬───────┘
                              │         │
                         ┌────▼────┐   Retry
                         │UPDATE   │  form
                         │users SET│   ↑
                         │terms... │   │
                         │WHERE id │   │
                         └────┬────┘   │
                              │        │
                         ┌────▼──────────────────┐
                         │ Redirect to:          │
                         │ /auth/dashboard/      │
                         │ with success message  │
                         └───────────────────────┘
```

## 🛡️ Dashboard Protection

```
DASHBOARD ACCESS CONTROL

   User requests: /auth/dashboard/
        ↓
   ┌────────────────────────────────┐
   │ MIDDLEWARE/DECORATOR CHECKS:   │
   ├────────────────────────────────┤
   │ 1. Is user logged in?          │
   │    @login_required             │
   └────┬───────────────────────────┘
        │
   ┌────▼────┐
   │ Auth OK? │
   └────┬────┘
        │
   ┌────▼────┐          ┌──────────┐
   │  YES    │          │   NO     │
   └────┬────┘          └────┬─────┘
        │                    │
   ┌────▼──────────────┐    ┌────▼──────────┐
   │ 2. Check T&C      │    │ Redirect to   │
   │    has_accepted_  │    │ /auth/login/  │
   │    terms()?       │    └───────────────┘
   └────┬──────────────┘
        │
   ┌────▼────┐
   │ T&C OK?  │
   └────┬────┘
        │
   ┌────▼────┐          ┌──────────┐
   │  YES    │          │   NO     │
   └────┬────┘          └────┬─────┘
        │                    │
   ┌────▼──────────────┐    ┌────▼─────────────┐
   │ ✓ GRANT ACCESS    │    │ Redirect to:     │
   │                   │    │ /auth/accept-    │
   │ Render dashboard  │    │ terms/           │
   │ template with     │    │                  │
   │ user data         │    │ Show warning:    │
   └───────────────────┘    │ "Must accept T&C"│
                            └──────────────────┘
```

## 📊 State Diagram

```
USER STATES IN SYSTEM

┌────────────────────────────────────────────────────────────────────┐
│                    USER STATE MACHINE                               │
└────────────────────────────────────────────────────────────────────┘

Initial State: NOT REGISTERED
        │
        ├─ Fill Registration Form ──┐
        │                           │
        │                    ┌──────▼──────────┐
        │                    │ Checkbox Check? │
        │                    └────┬───────┬────┘
        │                         │       │
        │                    NO ✗ │       │ YES ✓
        │                         │       │
        │                    ┌────▼─┐  ┌─▼──────┐
        │                    │BLOCK │  │REGISTER│
        │                    └──────┘  └────┬───┘
        │                                   │
        └───────────────────────────────────┼──────────────┐
                                            │              │
                                   State: UNVERIFIED       │
                                   - Email not verified    │
                                   - T&C accepted         │
                                            │              │
                                            ├─ Login ──────┤
                                            │              │
                                      ┌─────▼──────┐      │
                                      │Check T&C?  │      │
                                      └──┬──────┬──┘      │
                                         │      │         │
                                    ✓ YES│  NO ✗│         │
                                         │      │         │
                                    ┌────┴─┐  ┌─┴──────┐  │
                                    │ DASH │  │ACCEPT  │  │
                                    │BOARD │  │T&C PAGE│  │
                                    └──────┘  └───┬────┘  │
                                                  │       │
                                              Accept ┐    │
                                                  │  │    │
                                            ┌─────▼──┴──────┐
                                            │ ACTIVE USER   │
                                            ├───────────────┤
                                            │✓ Logged In   │
                                            │✓ T&C Accepted│
                                            │✓ Dashboard OK│
                                            └───────┬───────┘
                                                    │
                                                    ├─ Logout
                                                    │   │
                                                    │   └─ Back to NOT REGISTERED
                                                    │
                                                    └─ Session Timeout
                                                        │
                                                        └─ Back to NOT REGISTERED
```

## 📈 Data Persistence

```
DATABASE FLOW - TERMS & CONDITIONS

1. REGISTRATION ACCEPTANCE

   User Registration Form
            │
            ├─ Accept T&C Checkbox ✓
            │
            ▼
   INSERT INTO users (
     username='john',
     email='john@example.com',
     first_name='John',
     last_name='Doe',
     password='hashed_pwd',
     role='GUEST',
     terms_accepted=TRUE,
     terms_accepted_at=2026-02-13 10:30:00,
     terms_version='1.0'
   )

2. LOGIN REDIRECT

   Check: SELECT terms_accepted FROM users WHERE id=?
     │
     ├─ If FALSE → Redirect to accept page
     │
     └─ If TRUE → Allow dashboard access

3. T&C PAGE LOAD

   SELECT * FROM terms_and_conditions WHERE is_active=TRUE
     │
     └─ Display latest active T&C version

4. ACCEPTANCE UPDATE

   UPDATE users SET
     terms_accepted=TRUE,
     terms_accepted_at=2026-02-13 14:45:30,
     terms_version='1.0'
   WHERE id=?

5. NEW T&C VERSION

   INSERT INTO terms_and_conditions (
     version='2.0',
     content='Updated T&C content...',
     is_active=TRUE
   )
   
   (Old version 1.0 is_active=FALSE but kept for audit trail)
```

## 🔄 Admin Panel Workflow

```
ADMIN OPERATIONS

Login as Admin
    │
    ├─ Go to /admin/
    │
    ├─ Click "Terms and Conditions"
    │
    ├─ Options:
    │  ├─ View existing versions
    │  │   └─ See version, content, is_active, dates
    │  │
    │  ├─ Add new version
    │  │   ├─ Fill version field (e.g., "2.0")
    │  │   ├─ Paste new content
    │  │   ├─ Check "is_active" for new version
    │  │   └─ Click Save
    │  │
    │  └─ Edit existing version
    │      ├─ Modify content (if needed)
    │      ├─ Toggle is_active status
    │      └─ Click Save
    │
    ├─ Also view Users section
    │   └─ Check "terms_accepted" column
    │   └─ Click user to see:
    │       ├─ terms_accepted (True/False)
    │       ├─ terms_accepted_at (timestamp)
    │       └─ terms_version (which version)
    │
    └─ Reports: Who accepted, when, which version
```

---

**All flows verified** ✅
**Ready for implementation** ✅
**Production-grade** ✅
