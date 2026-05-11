from django.core.management.base import BaseCommand
from authentication.models import TermsAndConditions


class Command(BaseCommand):
    help = 'Create default Terms and Conditions'

    def handle(self, *args, **options):
        # Check if T&C already exists
        if TermsAndConditions.objects.filter(version='1.0').exists():
            self.stdout.write(self.style.WARNING('Terms and Conditions v1.0 already exists'))
            return

        # Default T&C content with professional formatting
        terms_content = """CEBU HOTEL - TERMS AND CONDITIONS

Version 1.0 | Last Updated: February 2026 | Effective Date: February 1, 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INTRODUCTION & ACCEPTANCE

Welcome to Cebu Hotel ("us," "we," "our," or the "Hotel"). These Terms and Conditions ("Terms") establish a legally binding agreement between you ("Guest," "Staff," "User," or "you") and Cebu Hotel regarding your use of our website, mobile application (the "Platform"), booking services, and hospitality services.

By accessing or using the Platform, creating an account, making a reservation, or utilizing our services, you acknowledge that you have read, understood, and agree to be bound by these Terms. If you do not agree to any part of these Terms, you may not use the Platform or our services.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. USER ACCOUNT RESPONSIBILITIES

1.1 Account Creation
• You must be at least 18 years old to create an account
• You agree to provide accurate, complete, and current information
• You are responsible for all activities under your account
• You must keep your password confidential and notify us immediately of unauthorized use

1.2 Account Types
• Guest Accounts: For making reservations and bookings
• Staff Accounts: For employees managing bookings and guest services
• Admin Accounts: For management and administrative functions

1.3 Account Termination
We reserve the right to suspend or terminate accounts that violate these Terms or engage in fraudulent activity.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. BOOKING AND RESERVATION TERMS

2.1 Reservation Process
• All reservations are subject to availability and confirmation by Cebu Hotel
• Bookings are confirmed once payment is received
• A confirmation email will be sent immediately after successful booking
• Check-in time: 3:00 PM | Check-out time: 12:00 PM (exceptions available upon request)

2.2 Room Availability & Accuracy
• Room descriptions, photos, and amenities are accurate to the best of our knowledge
• Specific room types are subject to availability
• We reserve the right to offer a room of equal or superior quality if your requested room is unavailable
• Prices are subject to change without notice until booking is confirmed

2.3 Guest Information Requirements
• A valid government-issued ID is required at check-in
• Credit card information is required for reservation guarantee
• Guests must be at least 18 years old to check in independently
• Group bookings require a valid authorization letter for corporate accounts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. CANCELLATION AND REFUND POLICY

3.1 Standard Cancellation Policy
• Free Cancellation: 100% refund if cancelled more than 48 hours before check-in
• Non-Refundable: No refund for cancellations made 48 hours or less before check-in
• No-Show: No refund if the guest does not arrive and the reservation is not cancelled
• Special promo, discounted, or event bookings may have separate refund terms

3.2 Special Circumstances
• Approved refunds are processed within 5-7 business days
• Non-refundable rates clearly marked at time of booking
• Group bookings have specific cancellation terms
• Exceptions subject to management review

3.3 Cancellation Process
• Contact our front desk or use the online portal to cancel
• Cancellation confirmation will be sent via email
• Keep cancellation confirmation for refund verification

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. PAYMENT TERMS

4.1 Accepted Payment Methods
• Credit/Debit Cards (Visa, Mastercard, American Express)
• Digital Payment Methods (GCash, PayMaya, PayPal)
• Bank Transfer
• OnSite Payment (subject to availability)

4.2 Payment Security
• All transactions are encrypted using industry-standard SSL technology
• Credit card information is not stored on our servers
• Payment processing is handled by PCI-DSS compliant third parties
• We are never liable for payment gateway failures

4.3 Pricing & Additional Charges
• Room rates include accommodation only (unless otherwise specified)
• Additional charges: Breakfast packages, late check-out, room service, etc.
• Taxes and government fees are included in quoted rates
• Damage charges will be billed separately
• Incidental charges will be provided at check-out

4.4 Currency
• All prices are displayed in Philippine Peso (PHP)
• International guests may be subject to currency conversion fees by their financial institutions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. GUEST CONDUCT & HOUSE RULES

5.1 Prohibited Activities
Guests and users agree NOT to:
• Engage in illegal activities or create disturbances
• Smoke in designated non-smoking areas
• Bring unauthorized guests or animals (except certified service animals)
• Use rooms for commercial purposes without authorization
• Damage hotel property (damages will be charged to your account)
• Use excessive noise after 11:00 PM
• Violate other guests' privacy and safety
• Engage in harassment, discrimination, or hate speech

5.2 Property Respect
• Guests are responsible for any damage caused during their stay
• Intentional or negligent damage will be charged to the guest's account
• We reserve the right to evict guests violating these rules

5.3 Lost and Found
• Lost items should be reported to the front desk immediately
• We hold lost items for 30 days before disposal
• Valuable items in guest safe are the guest's responsibility
• Lost valuables cannot be replaced by the hotel

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. LIABILITY & LIMITATION OF DAMAGES

6.1 Liability Disclaimer
• Our services are provided "AS IS" without warranties of any kind
• We are not liable for indirect, incidental, consequential damages
• We do not warrant service uninterruption or error-free operation
• Maximum liability is limited to the nightly rate of the booked room

6.2 Website Availability
• Website maintenance may cause temporary unavailability
• We are not liable for technical issues, server errors, or data loss
• Force majeure events exempt us from liability

6.3 Excluded Liability
• Lost or stolen personal items (unless in hotel safe)
• Weather-related incidents or natural disasters
• Third-party service failures
• Medical emergencies (hospitals/clinics are recommended)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7. PRIVACY & DATA PROTECTION

7.1 Data Collection
• We collect personal information necessary for bookings and services
• Data includes: name, email, phone, payment information, preferences
• We comply with Philippine Data Privacy Act of 2012

7.2 Data Usage
• Guest data is used for reservations, confirmations, and marketing (with consent)
• We do not share data with third parties without consent (except for booking confirmations)
• Payment data is processed by secure third-party processors

7.3 Cookies & Tracking
• We use cookies to improve your experience
• You can disable cookies in your browser settings
• Third-party websites may have their own privacy policies

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8. INTELLECTUAL PROPERTY RIGHTS

8.1 Platform Content
• All website content (text, images, videos, designs) is owned by Cebu Hotel or licensed partners
• You may not copy, reproduce, or distribute content without permission
• Unauthorized use violates intellectual property laws

8.2 User Content
• By posting reviews or photos, you grant us permission to display them
• You warrant that your content does not infringe third-party rights
• We may remove inappropriate or false content

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

9. STAFF & ADMINISTRATIVE TERMS (Applicable to Staff and Admin Accounts)

9.1 Employment/Access Terms
• Staff accounts are provided for authorized employees only
• Account access must be for business purposes only
• Unauthorized sharing of access credentials is prohibited
• Employees agree to follow all company policies and procedures

9.2 Confidentiality
• Staff members must maintain confidentiality of guest information
• Breach of confidentiality may result in account suspension and legal action
• All access is logged and monitored for security

9.3 Administrative Functions
• Admin accounts have full system access and control
• Admins are responsible for accurate data management
• Audit trails are maintained for compliance and security purposes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

10. PLATFORM USAGE TERMS

10.1 Permitted Use
• You may use the Platform for legitimate booking and information purposes
• Commercial scraping or bots are prohibited
• You agree not to interfere with Platform functionality
• You agree not to attempt unauthorized system access

10.2 Prohibited Activities
• Hacking, malware, or phishing attempts
• Automated data collection without permission
• Creating false reviews or manipulating ratings
• Spam or abusive messaging to other users

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

11. MODIFICATIONS TO TERMS

We reserve the right to modify these Terms at any time. Changes will be posted on the website with an updated "Last Modified" date. Your continued use of the Platform constitutes acceptance of modified Terms. We recommend reviewing these Terms periodically for updates.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

12. DISPUTE RESOLUTION & GOVERNING LAW

12.1 Governing Law
These Terms are governed by and construed in accordance with the laws of the Philippines, without regard to its conflict of law principles.

12.2 Jurisdiction
• Both parties irrevocably submit to the exclusive jurisdiction of courts in Cebu City
• Venue is waived except for Philippine courts
• Any legal action must be initiated within one (1) year of the dispute arising

12.3 Dispute Resolution Process
• First attempt: Direct communication with our management (contact: support@cebuhotel.com)
• Second attempt: Written complaint with detailed information
• Final: Binding arbitration or court proceedings if unresolved

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

13. CONTACT INFORMATION

For questions, complaints, or clarifications regarding these Terms:

Cebu Hotel Management
📧 Email: support@cebuhotel.com
📞 Phone: +63 (32) 123-4567
📍 Address: Cebu City, Philippines
⏰ Operating Hours: 24/7

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACKNOWLEDGMENT

By clicking "Accept and Continue," you confirm that you have read and understood these Terms and Conditions and agree to be bound by them. This agreement is effective immediately upon acceptance.

Last Updated: February 2, 2026
Version: 1.0 | Effective from: February 1, 2026"""

        terms = TermsAndConditions.objects.create(
            version='1.0',
            content=terms_content,
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created Terms and Conditions v{terms.version}'))
