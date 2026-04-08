#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from authentication.models import TermsAndConditions, CustomUser

# Check existing T&C
print("=" * 70)
print("CHECKING EXISTING TERMS AND CONDITIONS")
print("=" * 70)

existing_terms = TermsAndConditions.objects.all()
print(f"\nFound {existing_terms.count()} T&C versions:")

for term in existing_terms:
    print(f"\n📋 Version: {term.version}")
    print(f"   Active: {term.is_active}")
    print(f"   Created: {term.created_at}")
    print(f"   Content length: {len(term.content)} characters")
    print(f"   Preview: {term.content[:100]}...")

# Check users
print(f"\n\n📊 CHECKING USER T&C ACCEPTANCE:")
print("=" * 70)

users = CustomUser.objects.all()
for user in users:
    status = "✓" if user.terms_accepted else "✗"
    print(f"{status} {user.email:35} - Accepted: {user.terms_accepted}")
