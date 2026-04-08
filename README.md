# Cebu Hotel - Authentication System

A Django-based hotel management system with a complete authentication system featuring role-based access control and Terms & Conditions enforcement.

## 🔐 Authentication Features

### 1. **Register**
- User registration with email validation
- Password hashing using Django's default PBKDF2 algorithm
- Unique username and email enforcement
- First name and last name collection
- Default role assignment (Guest)
- **Terms & Conditions checkbox required**

### 2. **Login**
- Username or email-based login
- Session management
- Remember me functionality (30 days)
- Secure password verification
- Welcome message on successful login
- **Automatic redirect to T&C acceptance if not yet accepted**

### 3. **Logout**
- Session termination
- Secure logout functionality
- Redirect to login page

### 4. **Session Management**
- 24-hour default session timeout
- Configurable remember me (extends to 30 days)
- Secure session cookies

### 5. **Custom User Model**
- Email field (unique)
- Role field (Guest/Admin)
- Phone number (optional)
- Email verification status
- Terms acceptance tracking (terms_accepted, terms_accepted_at, terms_version)
- Timestamp tracking (created_at, updated_at)

### 6. **Role Support**
- **Guest**: Default role for new users, limited access
- **Admin**: Full access to admin panel and management features

### 7. **Terms & Conditions Management** 📜
- **T&C Acceptance during signup** - Checkbox required
- **T&C Acceptance after login** - If not yet accepted
- **Dashboard blocking** - Blocks access to dashboard if T&C not accepted
- **T&C Page** - View full Terms and Conditions
- **Accept page** - Dedicated page to review and accept T&C
- **Database storage** - All T&C versions and user acceptances tracked
- **Admin management** - Admins can add/update T&C versions

## 📁 Project Structure

```
cebuhotel/
├── manage.py
├── requirements.txt
├── README.md
│
├── cebuhotel/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── authentication/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py          # Admin panel configuration
│   ├── apps.py
│   ├── forms.py          # RegisterForm, LoginForm
│   ├── models.py         # CustomUser model with roles + TermsAndConditions
│   ├── views.py          # Auth views (register, login, logout, dashboard, terms)
│   ├── urls.py
│   ├── forms.py          # RegisterForm with T&C checkbox
│   ├── admin.py          # Admin panel with T&C management
│   ├── tests.py
│   └── management/
│       └── commands/
│           └── add_terms.py    # Command to add default T&C
│
└── templates/
    ├── base.html         # Base template with navbar
    ├── index.html        # Home page
    └── authentication/
        ├── login.html
        ├── register.html
        ├── dashboard.html
        ├── terms.html           # T&C page
        └── accept_terms.html    # Accept T&C page
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone/Navigate to the project**
   ```bash
   cd c:\Users\Admin\Downloads\cebuhotel
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Load default Terms and Conditions**
   ```bash
   python manage.py add_terms
   ```

6. **Create superuser (admin)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Home: http://127.0.0.1:8000/
   - Terms & Conditions: http://127.0.0.1:8000/auth/terms/
   - Login: http://127.0.0.1:8000/auth/login/
   - Register: http://127.0.0.1:8000/auth/register/
   - Dashboard: http://127.0.0.1:8000/auth/dashboard/
   - Accept Terms: http://127.0.0.1:8000/auth/accept-terms/
   - Admin: http://127.0.0.1:8000/admin/

## 🔑 Key Features Explained

### CustomUser Model
```python
- username: Unique identifier
- email: Unique email address
- first_name, last_name: User names
- role: GUEST or ADMIN
- phone_number: Contact information
- is_email_verified: Email verification status
- terms_accepted: Boolean flag for T&C acceptance
- terms_accepted_at: Timestamp of acceptance
- terms_version: Version of T&C accepted
- created_at, updated_at: Timestamps
```

### Authentication Flow
1. User registers with email, username, password, and T&C acceptance
2. Password is hashed using PBKDF2
3. T&C acceptance is recorded in database
4. User logs in with username/email and password
5. If T&C not accepted, user is redirected to accept page
6. Session is created and stored
7. User can check "Remember me" for extended session (30 days)
8. User can logout to terminate session

### Terms & Conditions Flow
1. **During Registration**: Checkbox required, must be checked to register
2. **During Login**: If not yet accepted, redirects to accept page
3. **Dashboard Access**: Blocked if T&C not accepted, redirects to accept page
4. **Accept Page**: User reviews and accepts T&C, acceptance recorded
5. **Admin Management**: Admins can add new T&C versions in admin panel

### TermsAndConditions Model
```python
- version: T&C version (e.g., "1.0", "2.0")
- content: Full T&C text content
- is_active: Flag to set current active version
- created_at, updated_at: Timestamps
```
### Security Features
- Password hashing (PBKDF2)
- CSRF protection
- Session-based authentication
- Email uniqueness validation
- Username uniqueness validation
- Secure password requirements
- T&C acceptance enforcement
- Dashboard access control

## 📝 Usage Examples

### Register
- Navigate to `/auth/register/`
- Fill in username, email, password, name
- **Must check "I agree to Terms and Conditions"**
- Click Register
- Auto-redirected to login page

### Login
- Navigate to `/auth/login/`
- Enter username/email and password
- Optional: Check "Remember me" for 30 days
- Click Login
- If T&C not yet accepted, redirects to accept page
- Otherwise, redirected to dashboard

### Accept Terms & Conditions (During Registration)
- Checkbox appears in registration form
- Must be checked to complete registration
- T&C acceptance recorded upon successful registration

### Accept Terms & Conditions (After Login)
- Automatically redirected if not yet accepted
- Must review and check "I have read and agree..."
- Click "Accept and Continue"
- Redirects to dashboard

### View Terms & Conditions
- Click "Terms & Conditions" link in navbar
- Full T&C text displayed
- Can view current version information

### Dashboard Access
- Only accessible after login and T&C acceptance
- Attempting to access without T&C acceptance redirects to accept page
- Displays user profile and account information

### Logout
- Click "Logout" button in dashboard
- Session terminated
- Redirected to login page

## 🎯 Next Steps

This authentication system is ready for expanding with:
- Email verification
- Password reset functionality
- Profile update page
- Room management system
- Booking system
- Payment integration

## 📄 License

This project is for educational purposes.

## ✨ Author

Developed for Cebu Hotel Management System
