#!/usr/bin/env python
"""
Reset guest accounts to allow re-signup with same email addresses.
Usage: python reset_guests.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import TwoFactorAuth, LoginSession

User = get_user_model()

# Delete all guest accounts
guests_deleted = User.objects.filter(role='GUEST').delete()
print(f"✓ Deleted {guests_deleted[0]} guest accounts")

# Delete orphaned 2FA records
twofa_deleted = TwoFactorAuth.objects.filter(user__isnull=True).delete()
print(f"✓ Deleted {twofa_deleted[0]} orphaned 2FA records")

# Delete orphaned login sessions
sessions_deleted = LoginSession.objects.filter(user__isnull=True).delete()
print(f"✓ Deleted {sessions_deleted[0]} orphaned login sessions")

print("\n✓ Guest accounts reset successfully!")
