from django.core.management.base import BaseCommand
from authentication.models import TermsAndConditions


class Command(BaseCommand):
    help = 'Create default Terms and Conditions'

    def handle(self, *args, **options):
        # Check if T&C already exists
        if TermsAndConditions.objects.filter(version='1.0').exists():
            self.stdout.write(self.style.WARNING('Terms and Conditions v1.0 already exists'))
            return

        # Default T&C content
        terms_content = """CEBU HOTEL - TERMS AND CONDITIONS

Welcome to Cebu Hotel. These Terms and Conditions ("Terms") govern your use of our website, mobile applications, and services. By accessing and using our services, you agree to be bound by these Terms. If you do not agree to these Terms, please do not use our services.

1. USE LICENSE
Permission is granted to temporarily download one copy of the materials (information or software) on Cebu Hotel's website for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:
- Modifying or copying the materials
- Using the materials for any commercial purpose or for any public display
- Attempting to decompile or reverse engineer any software contained on Cebu Hotel's website
- Removing any copyright or other proprietary notations from the materials
- Transferring the materials to another person or "mirroring" the materials on any other server

2. DISCLAIMER
The materials on Cebu Hotel's website are provided on an 'as is' basis. Cebu Hotel makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.

3. LIMITATIONS
In no event shall Cebu Hotel or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on Cebu Hotel's website.

4. ACCURACY OF MATERIALS
The materials appearing on Cebu Hotel's website could include technical, typographical, or photographic errors. Cebu Hotel does not warrant that any of the materials on the website are accurate, complete, or current. Cebu Hotel may make changes to the materials contained on the website at any time without notice.

5. LINKS
Cebu Hotel has not reviewed all of the sites linked to its website and is not responsible for the contents of any such linked site. The inclusion of any link does not imply endorsement by Cebu Hotel of the site. Use of any such linked website is at the user's own risk.

6. MODIFICATIONS
Cebu Hotel may revise these terms of service for the website at any time without notice. By using this website, you are agreeing to be bound by the then current version of these terms of service.

7. GOVERNING LAW
These terms and conditions are governed by and construed in accordance with the laws of the Philippines, and you irrevocably submit to the exclusive jurisdiction of the courts located in Cebu.

8. USER ACCOUNTS
When you create an account with Cebu Hotel, you must provide accurate, complete, and current information. You are responsible for maintaining the confidentiality of your password and for all activities that occur under your account.

9. BOOKINGS AND RESERVATIONS
All bookings are subject to availability and confirmation by Cebu Hotel. Pricing is subject to change without notice. Cancellation policies apply as per our standard terms.

10. PAYMENT
Payment must be made through accepted methods. All transactions are secure and encrypted.

Last Updated: February 13, 2026
Version: 1.0"""

        terms = TermsAndConditions.objects.create(
            version='1.0',
            content=terms_content,
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created Terms and Conditions v{terms.version}'))
