from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import RegisterForm, LoginForm
from .models import TermsAndConditions

User = get_user_model()

@require_http_methods(["GET"])
def allauth_login_redirect(request):
    """Redirect allauth login to our custom login page"""
    next_url = request.GET.get('next', '')
    if next_url:
        return redirect(f"auth:login?next={next_url}")
    return redirect('auth:login')

@require_http_methods(["GET"])
def terms_view(request):
    """Display Terms and Conditions"""
    try:
        terms = TermsAndConditions.objects.filter(is_active=True).latest('created_at')
    except TermsAndConditions.DoesNotExist:
        terms = None
    
    context = {'terms': terms}
    return render(request, 'authentication/terms.html', context)


@require_http_methods(["GET", "POST"])
def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('auth:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Explicitly set first_name and last_name before saving
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name = form.cleaned_data.get('last_name', '')
            user.role = 'GUEST'  # New users are guests by default
            user.save()
            
            # Record T&C acceptance
            if form.cleaned_data.get('accept_terms'):
                user.accept_terms(version='1.0')
            
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('auth:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()

    context = {'form': form}
    return render(request, 'authentication/register.html', context)


@require_http_methods(["GET", "POST"])
def login_view(request):
    """User login view"""
    from .models import TwoFactorAuth
    from allauth.socialaccount.models import SocialApp
    
    if request.user.is_authenticated:
        return redirect('auth:dashboard')

    # Check if Google OAuth is configured
    google_oauth_configured = False
    try:
        SocialApp.objects.get(provider='google')
        google_oauth_configured = True
    except SocialApp.DoesNotExist:
        google_oauth_configured = False

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']

            # Try to authenticate with username or email
            user = authenticate(request, username=username, password=password)
            
            if user is None:
                # Try with email
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if user is not None:
                # Check if 2FA is enabled
                try:
                    two_fa = user.two_factor_auth
                    if two_fa.is_enabled and two_fa.is_verified:
                        # Store user id in session for 2FA verification
                        request.session['2fa_user_id'] = user.id
                        request.session['2fa_remember_me'] = remember_me
                        return redirect('auth:verify_2fa_login')
                except TwoFactorAuth.DoesNotExist:
                    pass
                
                # No 2FA required, login the user
                login(request, user)
                
                # Remember me functionality
                if remember_me:
                    request.session.set_expiry(86400 * 30)  # 30 days
                
                messages.success(request, f'Welcome back, {user.first_name}!')
                
                # Redirect to terms acceptance if not yet accepted
                if not user.has_accepted_terms():
                    return redirect('auth:accept_terms')
                
                return redirect('auth:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    context = {
        'form': form,
        'google_oauth_configured': google_oauth_configured,
    }
    return render(request, 'authentication/login.html', context)


@login_required(login_url='auth:login')
@require_http_methods(["GET", "POST"])
def accept_terms_view(request):
    """
    View for accepting terms and conditions
    
    ENTITY-SPECIFIC FLOW:
    - Guests: Optional acceptance (can skip, but features may be limited)
    - Staff: Required acceptance for employee accounts
    - Admin: Required acceptance for administrative access
    """
    # If already accepted, redirect to dashboard
    if request.user.has_accepted_terms():
        return redirect('auth:dashboard')
    
    try:
        terms = TermsAndConditions.objects.filter(is_active=True).latest('created_at')
    except TermsAndConditions.DoesNotExist:
        terms = None
    
    if request.method == 'POST':
        accept = request.POST.get('accept_terms')
        if accept == 'on':
            request.user.accept_terms(version='1.0')
            
            # Entity-specific success message
            if request.user.is_staff_member():
                messages.success(request, 'Terms and Conditions accepted! Welcome to the Staff Portal.')
            elif request.user.is_admin():
                messages.success(request, 'Terms and Conditions accepted! Welcome to Admin Panel.')
            else:
                messages.success(request, 'Terms and Conditions accepted successfully!')
            
            return redirect('auth:dashboard')
        else:
            messages.error(request, 'You must accept the Terms and Conditions to continue.')
    
    # Determine message based on user role
    role_message = ""
    if request.user.is_admin():
        role_message = "As an Administrator, you must accept these terms before accessing the admin panel."
    elif request.user.is_staff_member():
        role_message = "As a Staff member, you must accept these terms before accessing the staff portal."
    else:
        role_message = "Please review and accept our Terms and Conditions to continue."
    
    context = {
        'terms': terms,
        'user_role': request.user.role,
        'role_message': role_message
    }
    return render(request, 'authentication/accept_terms.html', context)


@login_required(login_url='auth:login')
@require_http_methods(["GET", "POST"])
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('auth:login')


@login_required(login_url='auth:login')
def dashboard_view(request):
    """Dashboard view - Redirects based on user role"""
    # Block access if terms not accepted
    if not request.user.has_accepted_terms():
        messages.warning(request, 'Please accept the Terms and Conditions to access the dashboard.')
        return redirect('auth:accept_terms')
    
    # Redirect admin users to admin dashboard
    if request.user.is_admin():
        return redirect('admin_panel:dashboard')
    
    # Redirect staff users to staff dashboard
    if request.user.is_staff_member():
        return redirect('staff:dashboard')
    
    # Get available rooms for guest dashboard
    from .models import Room
    rooms = Room.objects.filter(is_available=True)[:6]  # Show 6 featured rooms
    
    # Regular guest dashboard
    context = {
        'user': request.user,
        'is_admin': False,
        'rooms': rooms,
    }
    return render(request, 'authentication/dashboard.html', context)


@require_http_methods(["GET", "POST"])
def contact_view(request):
    """Contact form view"""
    from .models import ContactMessage
    from .forms_bookings import ContactForm
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            if request.user.is_authenticated:
                contact.guest = request.user
            contact.save()
            messages.success(request, 'Thank you! We will get back to you soon.')
            return redirect('home')
    else:
        form = ContactForm()
    
    context = {'form': form}
    return render(request, 'authentication/contact.html', context)


@require_http_methods(["GET"])
def home_view(request):
    """Home page - Modern luxury hotel landing page"""
    return render(request, 'hotel_landing.html')


@login_required(login_url='auth:login')
@require_http_methods(["GET", "POST"])
def setup_2fa(request):
    """Setup 2FA for user"""
    from .models import TwoFactorAuth
    import qrcode
    from io import BytesIO
    import base64
    import pyotp
    
    try:
        two_fa = request.user.two_factor_auth
    except TwoFactorAuth.DoesNotExist:
        two_fa = TwoFactorAuth.objects.create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'setup':
            # Generate new secret
            secret = pyotp.random_base32()
            two_fa.secret_key = secret
            two_fa.save()
            
            # Generate QR code
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(
                name=request.user.email,
                issuer_name='Cebu Hotel'
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            qr_code = base64.b64encode(buffer.getvalue()).decode()
            
            context = {
                'qr_code': qr_code,
                'secret': secret,
                'backup_codes': two_fa.generate_backup_codes(),
            }
            return render(request, 'authentication/setup_2fa.html', context)
        
        elif action == 'verify':
            code = request.POST.get('code', '').replace(' ', '')
            secret = request.POST.get('secret')
            
            totp = pyotp.TOTP(secret)
            if totp.verify(code):
                two_fa.secret_key = secret
                two_fa.is_enabled = True
                two_fa.is_verified = True
                two_fa.method = 'TOTP'
                two_fa.save()
                
                messages.success(request, '2FA has been enabled successfully!')
                return redirect('auth:2fa_backup_codes')
            else:
                messages.error(request, 'Invalid code. Please try again.')
    
    context = {'two_fa': two_fa}
    return render(request, 'authentication/setup_2fa.html', context)


@login_required(login_url='auth:login')
@require_http_methods(["GET"])
def view_backup_codes(request):
    """View and download backup codes"""
    from .models import TwoFactorAuth
    
    try:
        two_fa = request.user.two_factor_auth
    except TwoFactorAuth.DoesNotExist:
        return redirect('auth:setup_2fa')
    
    if not two_fa.is_enabled:
        messages.warning(request, '2FA is not enabled yet.')
        return redirect('auth:setup_2fa')
    
    context = {'backup_codes': two_fa.backup_codes}
    return render(request, 'authentication/backup_codes.html', context)


@require_http_methods(["GET", "POST"])
def verify_2fa_login(request):
    """Verify 2FA code during login"""
    from .models import TwoFactorAuth, LoginSession
    
    if not request.session.get('2fa_user_id'):
        return redirect('auth:login')
    
    user_id = request.session.get('2fa_user_id')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('auth:login')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').replace(' ', '')
        
        try:
            two_fa = user.two_factor_auth
            
            # Check TOTP code
            if two_fa.is_enabled and two_fa.method == 'TOTP':
                import pyotp
                totp = pyotp.TOTP(two_fa.secret_key)
                
                if totp.verify(code):
                    # Valid code
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    
                    # Log the session
                    LoginSession.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        is_2fa_verified=True,
                    )
                    
                    del request.session['2fa_user_id']
                    messages.success(request, 'You have been logged in successfully!')
                    return redirect('auth:dashboard')
                
                # Check backup codes
                elif two_fa.use_backup_code(code):
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    LoginSession.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        is_2fa_verified=True,
                    )
                    
                    del request.session['2fa_user_id']
                    messages.warning(request, 'Backup code used. Please save your remaining backup codes.')
                    return redirect('auth:setup_2fa')
                else:
                    messages.error(request, 'Invalid code or backup code.')
        
        except TwoFactorAuth.DoesNotExist:
            pass
    
    return render(request, 'authentication/verify_2fa.html', {'user': user})


@login_required(login_url='auth:login')
@require_http_methods(["POST"])
def disable_2fa(request):
    """Disable 2FA"""
    from .models import TwoFactorAuth
    
    try:
        two_fa = request.user.two_factor_auth
        two_fa.is_enabled = False
        two_fa.is_verified = False
        two_fa.secret_key = ''
        two_fa.backup_codes = []
        two_fa.save()
        
        messages.success(request, '2FA has been disabled.')
    except TwoFactorAuth.DoesNotExist:
        pass
    
    return redirect('auth:setup_2fa')


def get_client_ip(request):
    """Get client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')
