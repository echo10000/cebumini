from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
import uuid

from .otp_utils import EmailOTPDeliveryError

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter to handle username generation for email-based authentication.
    Since ACCOUNT_USER_MODEL_USERNAME_FIELD is set to None, we need to
    automatically generate unique usernames from email addresses.
    """

    def save_user(self, request, sociallogin=None, form=None):
        """
        Save user and auto-generate username if not provided.
        Also handles T&C acceptance from signup form.
        """
        user = super().save_user(request, sociallogin, form)
        
        # If username is empty or not set, generate one from email
        if not user.username or user.username == '':
            # Use the email prefix as the base for username
            email_prefix = user.email.split('@')[0]
            
            # Create a base username
            base_username = email_prefix[:20]  # Max 20 chars to leave room for suffix
            username = base_username
            
            # If username already exists, append a short UUID suffix
            counter = 1
            while User.objects.filter(username=username).exists():
                suffix = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
                username = f"{base_username}_{suffix}"[:30]  # Keep under 30 char limit
                counter += 1
                if counter > 10:  # Failsafe
                    username = f"user_{uuid.uuid4().hex[:8]}"
                    break
            
            user.username = username
        
        # Handle T&C acceptance from AllAuth signup form
        if request and hasattr(request, 'POST'):
            accept_terms = request.POST.get('accept_terms') or request.POST.get('terms_acceptance')
            if accept_terms:
                user.terms_accepted = True
                user.terms_accepted_at = __import__('django.utils.timezone', fromlist=['now']).now()
                user.terms_version = '1.0'
        
        # Set role for new users (GUEST for social logins)
        if sociallogin and not user.role:
            user.role = 'GUEST'
        
        user.save()
        return user

    def get_login_redirect_url(self, request):
        """
        Redirect to dashboard after successful login/signup
        """
        path = super().get_login_redirect_url(request)
        return '/auth/dashboard/'


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for social account handling (OAuth providers)
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Handle any pre-login logic for social accounts.
        If the existing account has 2FA enabled, redirect through the OTP verification flow.
        """
        email = sociallogin.account.extra_data.get('email') or sociallogin.user.email
        email_verified = sociallogin.account.extra_data.get('email_verified', True)
        if email and email_verified is False:
            messages.error(request, 'Google did not verify this email address. Please use a verified Google account.')
            raise ImmediateHttpResponse(redirect('auth:login'))

        if not email:
            return

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return

        if not sociallogin.is_existing and not user.is_guest():
            messages.error(request, 'Google sign-in is only available for guest accounts with a verified Google email.')
            raise ImmediateHttpResponse(redirect('auth:login'))

        try:
            from .models import TwoFactorAuth
            if user.two_factor_auth.is_enabled:
                if user.two_factor_auth.method == 'EMAIL':
                    from .otp_utils import send_otp_email
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
                            raise ImmediateHttpResponse(redirect('auth:login'))
                    request.session['email_otp_user_id'] = user.id
                    request.session['email_otp_remember_me'] = False
                    raise ImmediateHttpResponse(redirect('auth:verify_otp'))
                elif user.two_factor_auth.method == 'TOTP' and user.two_factor_auth.is_verified:
                    request.session['2fa_user_id'] = user.id
                    request.session['2fa_remember_me'] = False
                    raise ImmediateHttpResponse(redirect('auth:verify_2fa_login'))
        except TwoFactorAuth.DoesNotExist:
            pass

        if sociallogin.is_existing:
            return

        try:
            sociallogin.connect(request, user)
        except Exception:
            pass

    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance from social provider data
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Set role to GUEST for new social auth users
        if not user.id:  # New user
            user.role = 'GUEST'
        
        # Mark email as verified only when Google reports a verified email.
        user.is_email_verified = sociallogin.account.extra_data.get('email_verified', True) is not False
        
        return user
