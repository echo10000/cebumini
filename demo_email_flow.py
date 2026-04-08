#!/usr/bin/env python
"""
Simulate what you see in the console when an email is sent
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.core.mail import send_mail
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 80)
print("EMAIL FLOW DEMONSTRATION")
print("=" * 80)

print("\n🔍 CURRENT EMAIL CONFIGURATION:")
print("-" * 80)

from django.conf import settings
print(f"DEBUG Mode: {settings.DEBUG}")
print(f"Email Backend: {settings.EMAIL_BACKEND}")
print(f"Email Host: {settings.EMAIL_HOST}")
print(f"Email Port: {settings.EMAIL_PORT}")
print(f"Email Use TLS: {settings.EMAIL_USE_TLS}")

print("\n" + "=" * 80)
print("SENDING TEST EMAIL...")
print("=" * 80)

# Send test email
try:
    send_mail(
        subject='[Cebu Hotel] Test Email - Password Reset',
        message='''
Dear Guest,

You requested a password reset for your Cebu Hotel account.

Click the link below to reset your password:
http://localhost:8000/accounts/password-reset/abc123def456/

This link expires in 1 hour.

If you did not request this reset, please ignore this email.

Best Regards,
Cebu Hotel Team
        ''',
        from_email='noreply@cebuhotel.com',
        recipient_list=['jericho@example.com'],
        fail_silently=False,
    )
    print("\n✓ Email sent successfully!")
except Exception as e:
    print(f"\n❌ Error sending email: {e}")

print("\n" + "=" * 80)
print("WHAT YOU SEE IN CONSOLE:")
print("=" * 80)
print("""
If EMAIL_BACKEND = 'console.EmailBackend' (CURRENT):

---------- MESSAGE ----------
Subject: [Cebu Hotel] Test Email - Password Reset
From: noreply@cebuhotel.com
To: jericho@example.com

Dear Guest,

You requested a password reset for your Cebu Hotel account.

Click the link below to reset your password:
http://localhost:8000/accounts/password-reset/abc123def456/

This link expires in 1 hour.

If you did not request this reset, please ignore this email.

Best Regards,
Cebu Hotel Team

---------- END MESSAGE ----------


If EMAIL_BACKEND = 'smtp.EmailBackend':

(No console output - email goes directly to Gmail inbox)
✓ Email received in inbox at: jericho@example.com
""")

print("\n" + "=" * 80)
print("HOW TO GET REAL EMAILS:")
print("=" * 80)
print("""
Step 1: Go to https://myaccount.google.com/security
Step 2: Enable "2-Step Verification"
Step 3: Go to "App passwords"
Step 4: Select "Mail" and "Windows Computer"
Step 5: Copy the 16-character password
Step 6: Update cebuhotel/settings.py with:

    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'your-email@gmail.com'
    EMAIL_HOST_PASSWORD = 'xxxxxxxxxxxxxxxx'  # App password from Step 5

Step 7: Restart django server
Step 8: Test password reset again - email goes to real inbox!
""")
