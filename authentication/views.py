from urllib.parse import urlencode

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import IntegrityError
from django.db.models import Avg
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import RegisterForm, LoginForm
from .models import Room, TermsAndConditions, TwoFactorAuth
from .decorators import guest_required
from .otp_utils import EmailOTPDeliveryError, send_otp_email, verify_otp

User = get_user_model()

@require_http_methods(["GET"])
def allauth_login_redirect(request):
    """Redirect allauth login to our custom login page"""
    next_url = request.GET.get('next', '')
    if next_url:
        login_url = reverse('auth:login')
        return redirect(f"{login_url}?{urlencode({'next': next_url})}")
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
    from allauth.socialaccount.models import SocialApp

    if request.user.is_authenticated:
        return redirect('auth:dashboard')

    google_oauth_configured = SocialApp.objects.filter(provider='google').exists()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                # Explicitly set first_name and last_name before saving
                user.first_name = form.cleaned_data.get('first_name', '')
                user.last_name = form.cleaned_data.get('last_name', '')
                user.role = 'GUEST'  # New users are guests by default
                user.save()

                # Record T&C acceptance
                if form.cleaned_data.get('agree_to_terms'):
                    user.accept_terms(version='1.0')

                messages.success(request, 'Registration successful! Please log in.')
                return redirect('auth:login')
            except IntegrityError:
                form.add_error('email', 'This email is already registered.')
                messages.error(request, 'email: This email is already registered.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()

    context = {'form': form, 'google_oauth_configured': google_oauth_configured}
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
                    if two_fa.is_enabled:
                        if two_fa.method == 'EMAIL':
                            try:
                                send_otp_email(user)
                            except EmailOTPDeliveryError as exc:
                                if getattr(settings, 'DEBUG', False) and exc.otp_code:
                                    messages.warning(
                                        request,
                                        f'Email delivery failed, so your local development verification code is {exc.otp_code}.',
                                    )
                                else:
                                    messages.error(request, 'We could not send your verification code. Please contact an administrator.')
                                    return redirect('auth:login')
                            request.session['email_otp_user_id'] = user.id
                            request.session['email_otp_remember_me'] = remember_me
                            return redirect('auth:verify_otp')
                        elif two_fa.method == 'TOTP' and two_fa.is_verified:
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
                
                # Redirect to terms acceptance if not yet accepted
                if not user.has_accepted_terms():
                    return redirect('auth:accept_terms')

                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                
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

    # Redirect manager users to manager dashboard
    if request.user.is_manager():
        return redirect('auth:manager_dashboard')
    
    # Get available rooms for guest dashboard
    from .models import Booking, Room
    rooms = Room.objects.filter(is_available=True)[:6]  # Show 6 featured rooms
    guest_bookings = (
        Booking.objects
        .filter(guest=request.user)
        .select_related('room')
        .order_by('-created_at')[:5]
    )
    
    # Regular guest dashboard
    try:
        two_fa = request.user.two_factor_auth
    except TwoFactorAuth.DoesNotExist:
        two_fa = None

    context = {
        'user': request.user,
        'is_admin': False,
        'rooms': rooms,
        'guest_bookings': guest_bookings,
        'two_fa': two_fa,
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
            guest = request.user if request.user.is_authenticated else None
            contact = form.save(guest=guest)
            # Send confirmation email
            contact.send_confirmation_email()
            messages.success(request, 'Thank you! We will get back to you soon.')
            return redirect('home')
    else:
        form = ContactForm()
    
    context = {'form': form}
    return render(request, 'authentication/contact.html', context)


@require_http_methods(["POST"])
def contact_form_api(request):
    """API endpoint for contact form submissions - returns JSON for AJAX requests"""
    from .forms_bookings import ContactForm
    
    form = ContactForm(request.POST)
    if form.is_valid():
        # Pass authenticated user as guest
        guest = request.user if request.user.is_authenticated else None
        contact = form.save(guest=guest)
        
        # Send confirmation email to guest
        contact.send_confirmation_email()
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your message! We will get back to you soon.',
            'message_type': 'success'
        })
    else:
        # Return form errors
        errors = form.errors
        error_list = []
        for field, field_errors in errors.items():
            for error in field_errors:
                error_list.append(f"{field}: {error}")
        
        return JsonResponse({
            'success': False,
            'message': 'Please fix the following errors:',
            'errors': error_list,
            'message_type': 'error'
        }, status=400)


@require_http_methods(["GET", "POST"])
def home_view(request):
    """Home page - Modern luxury hotel landing page"""
    from .forms_bookings import ContactForm
    from .models import Testimonial
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            guest = request.user if request.user.is_authenticated else None
            contact = form.save(guest=guest)
            # Send confirmation email
            contact.send_confirmation_email()
            messages.success(request, 'Thank you! We will get back to you soon.')
            return redirect('home')
    else:
        form = ContactForm()
    
    featured_rooms = Room.objects.filter(is_available=True).order_by('room_number')[:3]
    approved_testimonials = Testimonial.objects.filter(status=Testimonial.Status.APPROVED).select_related('guest').order_by('-created_at')[:6]
    average_rating = Testimonial.objects.filter(status=Testimonial.Status.APPROVED).aggregate(avg=Avg('rating'))['avg'] or 0
    context = {
        'form': form,
        'featured_rooms': featured_rooms,
        'testimonials': approved_testimonials,
        'average_rating': average_rating,
    }
    return render(request, 'hotel_landing.html', context)


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
                request.session['2fa_verified_user_id'] = request.user.id
                
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
                    request.session['2fa_verified_user_id'] = user.id
                    if request.session.get('2fa_remember_me'):
                        request.session.set_expiry(86400 * 30)
                    
                    # Log the session
                    LoginSession.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        is_2fa_verified=True,
                    )
                    
                    del request.session['2fa_user_id']
                    request.session.pop('2fa_remember_me', None)
                    request.session['otp_verified_notice'] = 'Two-factor authentication verified successfully. Redirecting you to your dashboard.'
                    return redirect('auth:otp_success')
                
                # Check backup codes
                elif two_fa.use_backup_code(code):
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    request.session['2fa_verified_user_id'] = user.id
                    if request.session.get('2fa_remember_me'):
                        request.session.set_expiry(86400 * 30)
                    LoginSession.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        is_2fa_verified=True,
                    )
                    
                    del request.session['2fa_user_id']
                    request.session.pop('2fa_remember_me', None)
                    request.session['otp_verified_notice'] = 'Backup code verified. Redirecting you to the 2FA setup page to manage your backup codes.'
                    return redirect('auth:otp_success')
                else:
                    messages.error(request, 'Invalid code or backup code.')
        
        except TwoFactorAuth.DoesNotExist:
            pass
    
    return render(request, 'authentication/verify_2fa.html', {'user': user})


@require_http_methods(["GET", "POST"])
def verify_otp_view(request):
    """Verify email OTP during login."""
    user_id = request.session.get('email_otp_user_id')
    if not user_id:
        return redirect('auth:login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('auth:login')

    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        if verify_otp(user, otp_code):
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session['2fa_verified_user_id'] = user.id
            if request.session.get('email_otp_remember_me'):
                request.session.set_expiry(86400 * 30)
            request.session.pop('email_otp_user_id', None)
            request.session.pop('email_otp_remember_me', None)
            request.session['otp_verified_notice'] = 'Email OTP verified successfully. Redirecting you to your dashboard.'
            return redirect('auth:otp_success')
        messages.error(request, 'Invalid or expired code. Please try again.')

    masked_email = None
    if user.email:
        local, _, domain = user.email.partition('@')
        if len(local) > 2:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        else:
            masked_local = local[0] + '*'
        masked_email = f"{masked_local}@{domain}"

    context = {
        'user': user,
        'masked_email': masked_email,
    }
    return render(request, 'authentication/verify_otp.html', context)


@login_required(login_url='auth:login')
@require_http_methods(["GET", "POST"])
def setup_email_2fa(request):
    """Dedicated onboarding flow for email OTP 2FA."""
    try:
        two_fa = request.user.two_factor_auth
    except TwoFactorAuth.DoesNotExist:
        two_fa = TwoFactorAuth.objects.create(user=request.user)

    if request.method == 'POST':
        two_fa.is_enabled = True
        two_fa.is_verified = True
        two_fa.method = 'EMAIL'
        two_fa.save()
        request.session['2fa_verified_user_id'] = request.user.id
        messages.success(request, 'Email OTP two-factor authentication has been enabled.')
        return redirect('auth:dashboard')

    return render(request, 'authentication/setup_email_2fa.html', {'two_fa': two_fa})


@require_http_methods(["GET"])
def resend_otp_view(request):
    """Resend the email OTP code."""
    user_id = request.session.get('email_otp_user_id')
    if not user_id:
        return redirect('auth:login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('auth:login')

    try:
        send_otp_email(user)
    except EmailOTPDeliveryError as exc:
        if getattr(settings, 'DEBUG', False) and exc.otp_code:
            messages.warning(
                request,
                f'Email delivery failed, so your local development verification code is {exc.otp_code}.',
            )
        else:
            messages.error(request, 'We could not send a new verification code. Please contact an administrator.')
            return redirect('auth:login')
    else:
        messages.info(request, 'A new code has been sent to your email.')
    return redirect('auth:verify_otp')


@login_required(login_url='auth:login')
@require_http_methods(["GET"])
def otp_success_view(request):
    """Show OTP verification success feedback before redirecting to dashboard."""
    if not request.user.is_authenticated:
        return redirect('auth:login')

    notice = request.session.pop('otp_verified_notice', None)
    if not notice:
        return redirect('auth:dashboard')

    return render(request, 'authentication/otp_success.html', {'notice': notice})


@login_required(login_url='auth:login')
@require_http_methods(["POST"])
def toggle_2fa_view(request):
    """Enable or disable email OTP 2FA from the dashboard."""
    if request.user.is_admin() or request.user.is_manager():
        messages.error(request, '2FA is required for admin and manager accounts and cannot be disabled.')
        return redirect('auth:dashboard')

    try:
        two_fa = request.user.two_factor_auth
    except TwoFactorAuth.DoesNotExist:
        two_fa = TwoFactorAuth.objects.create(user=request.user)

    if two_fa.is_enabled and two_fa.method == 'EMAIL':
        two_fa.is_enabled = False
        two_fa.is_verified = False
        two_fa.save()
        request.session.pop('2fa_verified_user_id', None)
        messages.success(request, 'Two-factor authentication has been disabled.')
    else:
        two_fa.is_enabled = True
        two_fa.is_verified = True
        two_fa.method = 'EMAIL'
        two_fa.save()
        messages.success(request, 'Email OTP two-factor authentication has been enabled.')

    return redirect('auth:dashboard')


@login_required(login_url='auth:login')
@require_http_methods(["POST"])
def disable_2fa(request):
    """Disable 2FA"""
    from .models import TwoFactorAuth

    if request.user.is_admin() or request.user.is_manager():
        messages.error(request, '2FA is required for admin and manager accounts and cannot be disabled.')
        return redirect('auth:setup_2fa')
    
    try:
        two_fa = request.user.two_factor_auth
        two_fa.is_enabled = False
        two_fa.is_verified = False
        two_fa.secret_key = ''
        two_fa.backup_codes = []
        two_fa.save()
        request.session.pop('2fa_verified_user_id', None)
        
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


@login_required(login_url='auth:login')
@require_http_methods(["GET"])
@guest_required
def guest_messages_view(request):
    """View guest's own contact messages"""
    from .models import ContactMessage
    
    # Get guest's messages ordered by most recent
    guest_messages = ContactMessage.objects.filter(guest=request.user).order_by('-created_at')
    
    # Count unread/unreplied messages
    unreplied_count = guest_messages.filter(is_replied=False).count()
    unnotified_count = guest_messages.filter(is_replied=True, notification_sent=False).count()
    
    context = {
        'messages': guest_messages,
        'unreplied_count': unreplied_count,
        'unnotified_count': unnotified_count,
        'total_count': guest_messages.count(),
    }
    
    return render(request, 'authentication/guest_messages.html', context)


@login_required(login_url='auth:login')
@require_http_methods(["POST"])
@guest_required
def start_guest_conversation_view(request):
    """Create a guest support conversation and open its message thread."""
    from .models import ContactMessage

    guest_name = request.user.get_full_name() or request.user.username
    contact = ContactMessage.objects.create(
        name=guest_name,
        email=request.user.email,
        phone=getattr(request.user, 'phone_number', '') or '',
        subject='Guest Support Conversation',
        message='Conversation started. Please type your message below.',
        guest=request.user,
        notification_sent=True,
    )

    return redirect('auth:guest_message_detail', message_id=contact.id)


@login_required(login_url='auth:login')
@require_http_methods(["GET"])
@guest_required
def guest_message_detail_view(request, message_id):
    """View detail of a specific guest message"""
    from .models import ContactMessage, MessageReply
    import re
    
    try:
        message = ContactMessage.objects.get(id=message_id, guest=request.user)
        had_new_response = message.is_replied and not message.notification_sent
        # Clear the guest-facing new-response indicator when the guest opens it.
        if had_new_response:
            message.notification_sent = True
            message.save(update_fields=['notification_sent', 'updated_at'])
        
        # Get structured replies from MessageReply. Legacy guest replies are
        # still parsed below so older conversations remain visible.
        structured_replies = MessageReply.objects.filter(contact_message=message).order_by('created_at')

        # Parse guest replies from staff_response field
        guest_replies_raw = []
        if message.staff_response:
            pattern = r'--- Guest Reply \((.*?)\): ---\n(.*?)(?=\n\n(?:---|$)|$)'
            matches = re.finditer(pattern, message.staff_response, re.DOTALL)
            for match in matches:
                guest_replies_raw.append({
                    'timestamp': match.group(1),
                    'text': match.group(2).strip()
                })

        # --- Build chronologically-sorted combined reply list ---
        from datetime import datetime
        combined_replies = []

        for reply in structured_replies:
            sender_name = message.name if reply.sender_type == MessageReply.SenderType.GUEST else 'Staff'
            if reply.staff_member and reply.sender_type != MessageReply.SenderType.GUEST:
                sender_name = reply.staff_member.get_full_name() or reply.staff_member.username
            combined_replies.append({
                'type': reply.sender_type,
                'sender': sender_name,
                'text': reply.reply_text,
                'dt': reply.created_at,
                'timestamp': reply.created_at.strftime('%b %d, %Y %I:%M %p'),
            })

        for gr in guest_replies_raw:
            # Parse the human-readable timestamp back to datetime for sorting
            try:
                dt = datetime.strptime(gr['timestamp'], '%B %d, %Y at %I:%M %p')
                dt = timezone.make_aware(dt)
            except Exception:
                dt = message.created_at  # fallback
            combined_replies.append({
                'type': 'guest',
                'sender': message.name,
                'text': gr['text'],
                'dt': dt,
                'timestamp': gr['timestamp'],
            })

        combined_replies.sort(key=lambda r: r['dt'])

        context = {
            'message': message,
            'combined_replies': combined_replies,
            'had_new_response': had_new_response,
        }
        return render(request, 'authentication/guest_message_detail.html', context)
    except ContactMessage.DoesNotExist:
        messages.error(request, 'Message not found.')
        return redirect('auth:guest_messages')


@login_required(login_url='auth:login')
@require_http_methods(["POST"])
@guest_required
def reply_message_view(request, message_id):
    """Guest reply to a staff message"""
    from .models import ContactMessage, MessageReply
    
    try:
        message = ContactMessage.objects.get(id=message_id, guest=request.user)
        reply_text = request.POST.get('reply_text', '').strip()
        
        if not reply_text:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Please type a message before sending.'}, status=400)
            messages.error(request, 'Please type a message before sending.')
            return redirect('auth:guest_message_detail', message_id=message_id)
        
        reply = MessageReply.objects.create(
            contact_message=message,
            staff_member=request.user,
            sender_type=MessageReply.SenderType.GUEST,
            reply_text=reply_text,
        )

        # A guest follow-up puts the inquiry back in the staff queue.
        message.is_replied = False
        message.notification_sent = True
        message.save(update_fields=['is_replied', 'notification_sent', 'updated_at'])

        timestamp_str = reply.created_at.strftime('%B %d, %Y at %I:%M %p')
        
        # AJAX response: return JSON so the front-end can inject the bubble immediately
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'reply_text': reply_text,
                'timestamp': timestamp_str,
                'sender_name': request.user.get_full_name() or request.user.username,
            })
        
        messages.success(request, 'Your reply has been sent successfully!')
        return redirect('auth:guest_message_detail', message_id=message_id)
        
    except ContactMessage.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Message not found.'}, status=404)
        messages.error(request, 'Message not found.')
        return redirect('auth:guest_messages')
