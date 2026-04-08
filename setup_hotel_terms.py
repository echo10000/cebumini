#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from authentication.models import TermsAndConditions

# Hotel Terms and Conditions Content
HOTEL_TERMS = """TERMS AND CONDITIONS FOR CEBU HOTEL

Last Updated: February 2026

WELCOME TO CEBU HOTEL

These Terms and Conditions ("Terms") govern your use of the Cebu Hotel website, booking system, and services. By accessing, browsing, or using our website and booking accommodations with us, you agree to be bound by these Terms. If you disagree with any part of these Terms, please do not use our services.

1. BOOKING AND RESERVATION TERMS

1.1 BOOKING PROCESS
- All reservations must be made through our website, phone, or authorized booking partners
- A valid email address and payment method are required to complete a booking
- You are responsible for providing accurate personal and payment information
- You must be at least 18 years old to make a reservation

1.2 RESERVATION CONFIRMATION
- A booking confirmation email will be sent immediately after successful payment
- Please retain this confirmation for your records
- Confirmation does not guarantee room availability until final confirmation is issued

1.3 RATES AND PRICING
- All rates are in Philippine Peso (PHP) unless otherwise stated
- Prices are subject to change without notice
- Special promotional rates are valid only during specified periods
- Taxes and service charges are included in the quoted rate unless explicitly stated otherwise

1.4 PAYMENT TERMS
- Payment is required at the time of booking
- We accept major credit cards, debit cards, and online payment methods
- Payment cancellation fees may apply (see Cancellation Policy)
- Disputed charges must be reported within 30 days
- Payment processing may take 2-3 business days

2. CHECK-IN AND CHECK-OUT

2.1 CHECK-IN PROCEDURES
- Standard check-in time is 2:00 PM
- Early check-in is subject to availability and may incur additional charges
- A government-issued ID is required at check-in
- A credit card hold may be placed for incidental charges

2.2 CHECK-OUT PROCEDURES
- Standard checkout time is 12:00 PM (noon)
- Late checkout is subject to availability and may incur 50% of daily room rate
- All personal belongings must be removed by checkout time
- Room inspection will be conducted after checkout

2.3 KEY CARDS AND ACCESS
- Key cards remain hotel property and must be returned at checkout
- A fee of PHP 500 will be charged for unreturned key cards
- Key cards are non-transferable and for the booked guest only

3. CANCELLATION POLICY

3.1 CANCELLATION TERMS
- Free cancellation up to 7 days before arrival date
- Cancellation between 3-6 days before arrival: 50% of total room rate charged
- Cancellation within 72 hours of arrival: 100% of total room rate charged
- No-show reservations: Full payment forfeited with no refund

3.2 CANCELLATION PROCEDURE
- Cancellations must be made through your account or by contacting our front desk
- Cancellation confirmation email will be sent
- Refunds will be processed within 5-7 business days
- Promotional rates (non-refundable) cannot be cancelled

4. HOUSE RULES AND GUEST CONDUCT

4.1 PROPERTY RULES
- Guests must comply with all posted house rules
- Smoking is strictly prohibited in all rooms and indoor areas (designated smoking areas available)
- Pets are not permitted unless prior approval is granted in writing
- Guests are responsible for any damage caused to room or property

4.2 NOISE AND DISTURBANCE
- Quiet hours: 11:00 PM to 8:00 AM
- Excessive noise or disruptive behavior may result in immediate eviction
- No refund will be issued for early eviction due to violating house rules

4.3 PROHIBITED ITEMS AND ACTIVITIES
- Weapons, explosives, or illegal substances are strictly prohibited
- Commercial filming or photography without permission is not allowed
- Unauthorized guests/visitors are not permitted to stay overnight
- Theft, violence, or illegal activities will result in police involvement

4.4 GUEST RESPONSIBILITY
- Guests are responsible for their belongings
- Hotel is not liable for lost, stolen, or damaged personal items
- Safes are available in rooms for valuables
- Report any suspicious activity to the front desk immediately

5. LIABILITY AND DAMAGES

5.1 PROPERTY DAMAGE
- Guests are liable for damages to the room and hotel property during their stay
- Damage charges will be deducted from deposit or charged to the guest's payment method
- Damage assessment photos will be provided upon request

5.2 HOTEL LIABILITY LIMITATIONS
- Hotel is not responsible for lost or stolen personal belongings
- Hotel is not liable for accidents, injuries, or theft on the premises
- Guests assume all risks related to their stay
- Complaints must be reported immediately to the front desk

5.3 VALUABLES
- Use the in-room safe for valuables (code provided after check-in)
- Hotel accepts no liability for items left in public areas
- Front desk accepts valuables for safekeeping (sign-in required)

6. ROOM AMENITIES AND SERVICES

6.1 AMENITIES PROVIDED
- Room amenities, features, and complimentary services are as described on booking
- Amenities subject to availability and maintenance requirements
- Changes to scheduled services will be communicated in advance

6.2 MAINTENANCE AND DISRUPTIONS
- Hotel reserves the right to perform maintenance during stay
- Notification will be provided to guests in advance if possible
- Guest may request room change if services are unavailable
- Compensation for service disruptions will be evaluated on case-by-case basis

6.3 INTERNET AND CONNECTIVITY
- Wi-Fi is provided as a complimentary service but not guaranteed
- Hotel is not liable for data loss or connectivity issues
- Hotel processes deposits and payments through secure connections

7. SPECIAL REQUESTS AND MODIFICATIONS

7.1 SPECIAL REQUESTS
- Special requests (high floor, late check-in, etc.) cannot be guaranteed
- Confirmation of special requests will be made 24 hours before arrival
- Special requests may incur additional fees

7.2 RESERVATION MODIFICATIONS
- Changes to reservation dates must be made at least 7 days before arrival
- Modifications are subject to availability and rate changes
- Modificat changes must follow the current cancellation policy

8. PRIVACY AND DATA PROTECTION

8.1 PERSONAL INFORMATION
- Guest personal information is collected for booking and hospitality purposes
- Information is protected under data privacy laws
- Information will not be shared with third parties without consent
- Guests have the right to request data access or deletion

8.2 MARKETING COMMUNICATIONS
- Guests may opt in/out of marketing emails after signup
- Transactional emails (confirmation, receipt) are mandatory
- Hotel respects all privacy preferences

9. DISCLAIMER OF WARRANTIES

9.1 SERVICE DELIVERY
- Services are provided on an "as-is" basis
- Hotel makes no warranty regarding uninterrupted service
- Website functionality issues do not guarantee refunds
- Temporary service disruptions do not constitute breach of contract

10. DISPUTE RESOLUTION

10.1 COMPLAINTS AND GRIEVANCES
- Complaints must be reported to management within 24 hours of incident
- Hotel will investigate and respond within 3 business days
- Disputes will be resolved according to Philippine law

10.2 REFUND POLICIES
- Refunds are processed within 5-7 business days
- Refund amount will be as per cancellation policy
- Non-refundable bookings are final and cannot be reversed

11. WEBSITE AND BOOKING SYSTEM

11.1 SYSTEM USAGE
- Users must not engage in unauthorized access attempts
- Automated booking systems or bots are prohibited
- Rate tampering or fraud will result in immediate account termination
- Users must be 18+ years old

11.2 USER ACCOUNTS
- Users are responsible for maintaining account confidentiality
- Users are liable for all activities on their account
- Hotel reserves the right to suspend accounts for violations

12. MODIFICATIONS TO TERMS

12.1 UPDATES TO TERMS
- Hotel reserves the right to modify these Terms at any time
- Changes will be posted on the website with an updated date
- Continued use of services constitutes acceptance of modified Terms
- Material changes will be communicated via email

13. CONTACT INFORMATION

For questions or concerns regarding these Terms and Conditions:
📧 Email: info@cebuhotel.com
📞 Phone: +63-32-1234-5678
🏨 Address: Cebu City, Philippines
⏰ Hours: 24/7 Customer Support

ACKNOWLEDGMENT

By creating an account and/or completing a booking, you acknowledge that you have read, understood, and agree to be bound by these Terms and Conditions.

Last Updated: February 27, 2026
Version: 1.0"""

print("=" * 80)
print("CREATING HOTEL TERMS AND CONDITIONS")
print("=" * 80)

# Check if T&C already exists
existing = TermsAndConditions.objects.filter(version='1.0').exists()

if existing:
    print("\n⚠️  Terms and Conditions v1.0 already exists.")
    print("   Updating content...")
    terms = TermsAndConditions.objects.get(version='1.0')
    terms.content = HOTEL_TERMS
    terms.is_active = True
    terms.save()
    print("   ✓ Content updated successfully!")
else:
    print("\n📝 Creating new Terms and Conditions v1.0...")
    terms = TermsAndConditions.objects.create(
        version='1.0',
        content=HOTEL_TERMS,
        is_active=True
    )
    print("   ✓ Terms and Conditions created successfully!")

print(f"\n✓ Terms Version: {terms.version}")
print(f"✓ Active: {terms.is_active}")
print(f"✓ Content Length: {len(terms.content):,} characters")
print(f"✓ Created: {terms.created_at}")
print(f"✓ Updated: {terms.updated_at}")

print("\n" + "=" * 80)
print("✓ Setup Complete - Hotel T&C is now available on signup")
print("=" * 80)
