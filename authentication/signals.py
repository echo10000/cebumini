"""
Signal handlers for OAuth and authentication events
"""
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.contrib.messages import get_messages
from allauth.socialaccount.signals import social_account_updated, pre_social_login
from allauth.account.signals import user_signed_up

User = get_user_model()


@receiver(user_logged_in)
def clear_allauth_messages(request, user, **kwargs):
    """
    Clear allauth's built-in success messages after login.
    We don't want to show "Successfully signed in as <user>" messages.
    """
    try:
        # Get all messages from storage
        storage = get_messages(request)
        # Clear all messages by consuming them
        for message in storage:
            pass
        # Mark as used to prevent further processing
        if hasattr(storage, 'used'):
            storage.used = True
    except Exception as e:
        # Silently fail - this is just for message cleanup
        pass


@receiver(user_signed_up)
def handle_user_signed_up(request, user, sociallogin=None, **kwargs):
    """
    Handle user sign-up event (both traditional and social auth).
    Ensure new users get the GUEST role.
    """
    if sociallogin:
        # OAuth user
        user.role = 'GUEST'
        user.is_email_verified = True  # OAuth providers verify email
        user.save()


@receiver(pre_social_login)
def handle_pre_social_login(request, sociallogin, **kwargs):
    """
    Handle pre-social login event.
    This is called before the social auth login is processed.
    """
    # Get the email from the social account
    email = sociallogin.account.extra_data.get('email')
    
    if email:
        try:
            user = User.objects.get(email=email)
            # If user exists, connect the social account
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            # New user will be created by allauth
            pass


@receiver(social_account_updated)
def handle_social_account_updated(request, sociallogin, **kwargs):
    """
    Handle social account updates.
    Keep user profile in sync with social provider.
    """
    user = sociallogin.user
    
    # Update user info from social provider
    extra_data = sociallogin.account.extra_data
    
    # Update first and last name if available
    if 'given_name' in extra_data and extra_data['given_name']:
        user.first_name = extra_data['given_name']
    
    if 'family_name' in extra_data and extra_data['family_name']:
        user.last_name = extra_data['family_name']
    
    # Ensure GUEST role for OAuth users
    if not user.role:
        user.role = 'GUEST'
    
    user.save()
