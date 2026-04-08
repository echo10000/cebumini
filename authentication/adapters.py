from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model
import uuid

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
        
        user.save()
        return user
