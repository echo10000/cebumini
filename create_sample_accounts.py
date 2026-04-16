#!/usr/bin/env python
"""
Create comprehensive sample accounts and test data for all entities
Includes: Users (all roles), Bookings, Payments, Testimonials, Contact Messages
"""
import os
import django
from datetime import datetime, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from authentication.models import (
    Room, Booking, Payment, Testimonial, ContactMessage,
    BookingStatus, CancellationPolicy, PaymentStatus, PaymentMethod, UserRole
)

User = get_user_model()

print("=" * 70)
print("SAMPLE ACCOUNTS & TEST DATA GENERATOR".center(70))
print("=" * 70)

# ============================================================================
# 1. CREATE SAMPLE USERS (ALL ROLES)
# ============================================================================
print("\n[1] CREATING SAMPLE USERS...")
print("-" * 70)

# Users to create: (username, email, password, first_name, last_name, role)
users_data = [
    # Guest Users
    ('guest_john', 'john.guest@example.com', 'GuestPass123!', 'John', 'Doe', UserRole.GUEST),
    ('guest_jane', 'jane.guest@example.com', 'GuestPass123!', 'Jane', 'Smith', UserRole.GUEST),
    ('guest_mark', 'mark.guest@example.com', 'GuestPass123!', 'Mark', 'Johnson', UserRole.GUEST),
    ('guest_sarah', 'sarah.guest@example.com', 'GuestPass123!', 'Sarah', 'Williams', UserRole.GUEST),
    ('guest_mike', 'mike.guest@example.com', 'GuestPass123!', 'Mike', 'Brown', UserRole.GUEST),
    
    # Staff Users
    ('staff_emily', 'emily.staff@example.com', 'StaffPass123!', 'Emily', 'Davis', UserRole.STAFF),
    ('staff_robert', 'robert.staff@example.com', 'StaffPass123!', 'Robert', 'Miller', UserRole.STAFF),
    ('staff_lisa', 'lisa.staff@example.com', 'StaffPass123!', 'Lisa', 'Wilson', UserRole.STAFF),
    
    # Manager User
    ('manager_alex', 'alex.manager@example.com', 'ManagerPass123!', 'Alex', 'Taylor', UserRole.MANAGER),
    
    # Admin User
    ('admin_super', 'admin@example.com', 'AdminPass123!', 'Super', 'Admin', UserRole.ADMIN),
]

created_users = {}
for username, email, password, first_name, last_name, role in users_data:
    # Delete existing user if any
    User.objects.filter(username=username).delete()
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=True,
        is_email_verified=True,
        terms_accepted=True,
        terms_accepted_at=timezone.now(),
    )
    created_users[username] = user
    role_display = dict(UserRole.choices).get(role, role)
    print(f"  ✓ {username:20} | {email:30} | {role_display}")

print(f"\n  ✓ Created {len(created_users)} users")

# ============================================================================
# 2. CREATE SAMPLE BOOKINGS
# ============================================================================
print("\n[2] CREATING SAMPLE BOOKINGS...")
print("-" * 70)

# Get some rooms (should exist from create_sample_rooms.py)
rooms = Room.objects.all()[:3]
if not rooms:
    print("  ⚠ No rooms found! Please run 'python create_sample_rooms.py' first.")
else:
    guest_users = [u for u in created_users.values() if u.role == UserRole.GUEST]
    booking_count = 0
    
    for idx, guest in enumerate(guest_users[:4]):  # Create 4 test bookings
        room = rooms[idx % len(rooms)]
        check_in = timezone.now().date() + timedelta(days=5 + idx)
        check_out = check_in + timedelta(days=3 + idx)
        
        # Delete existing bookings for this guest
        Booking.objects.filter(guest=guest, room=room).delete()
        
        booking = Booking.objects.create(
            room=room,
            guest=guest,
            check_in=check_in,
            check_out=check_out,
            status=BookingStatus.CONFIRMED if idx % 2 == 0 else BookingStatus.PENDING,
            cancellation_policy=CancellationPolicy.FREE if idx % 2 == 0 else CancellationPolicy.STANDARD,
            special_requests=f"Room #{room.room_number} - Request {idx+1}" if idx % 2 == 0 else None,
        )
        booking.total_price = booking.calculate_total_price()
        booking.save()
        
        booking_count += 1
        nights = booking.get_duration()
        print(f"  ✓ Booking #{booking.id:4} | {guest.first_name:10} | Room {room.room_number} | "
              f"{check_in} to {check_out} ({nights} nights) | {booking.get_status_display()}")
    
    print(f"\n  ✓ Created {booking_count} bookings")

# ============================================================================
# 3. CREATE SAMPLE PAYMENTS
# ============================================================================
print("\n[3] CREATING SAMPLE PAYMENTS...")
print("-" * 70)

bookings = Booking.objects.filter(status=BookingStatus.CONFIRMED)[:3]
payment_count = 0
payment_methods = [PaymentMethod.STRIPE, PaymentMethod.PAYMONGO, PaymentMethod.CASH]

for idx, booking in enumerate(bookings):
    # Delete existing payment
    Payment.objects.filter(booking=booking).delete()
    
    payment_method = payment_methods[idx % len(payment_methods)]
    is_completed = idx % 2 == 0  # Alternate between completed and pending
    
    payment = Payment.objects.create(
        booking=booking,
        amount=booking.total_price,
        payment_method=payment_method,
        status=PaymentStatus.COMPLETED if is_completed else PaymentStatus.PENDING,
        transaction_id=f"TXN{idx+1:06d}" if is_completed else None,
        reference_number=f"REF{idx+1:06d}" if payment_method == PaymentMethod.BANK_TRANSFER else None,
        notes=f"Sample payment for testing" if is_completed else "Pending payment",
        completed_at=timezone.now() if is_completed else None,
    )
    
    payment_count += 1
    print(f"  ✓ Payment #{payment.id:4} | Booking #{booking.id:4} | ₱{payment.amount:9.2f} | "
          f"{payment.get_payment_method_display():20} | {payment.get_status_display()}")

print(f"\n  ✓ Created {payment_count} payments")

# ============================================================================
# 4. CREATE SAMPLE TESTIMONIALS
# ============================================================================
print("\n[4] CREATING SAMPLE TESTIMONIALS...")
print("-" * 70)

Rating = [5, 4, 5, 3, 4]
testimonial_data = [
    {
        'guest_name': 'John Doe',
        'guest_email': 'john.doe@example.com',
        'title': 'Excellent Service and Beautiful Rooms',
        'comment': 'Had a wonderful stay at Cebu Hotel. The staff was very helpful and the rooms were clean and comfortable. Highly recommended!',
        'is_approved': True,
        'rating': 5,
    },
    {
        'guest_name': 'Sarah Johnson',
        'guest_email': 'sarah.j@example.com',
        'title': 'Great Location and Good Value',
        'comment': 'Perfect location for exploring the city. The room was spacious and the breakfast was delicious. Will definitely stay again.',
        'is_approved': True,
        'rating': 4,
    },
    {
        'guest_name': 'Michael Chen',
        'guest_email': 'mchen@example.com',
        'title': 'Outstanding Experience',
        'comment': 'The hotel exceeded my expectations. Friendly staff, beautiful facilities, and excellent amenities. Looking forward to the next visit!',
        'is_approved': True,
        'rating': 5,
    },
    {
        'guest_name': 'Emma Wilson',
        'guest_email': 'emma.w@example.com',
        'title': 'Nice Hotel with Minor Issues',
        'comment': 'Overall good experience. The room was nice but the internet was a bit slow. Otherwise, everything was satisfactory.',
        'is_approved': False,
        'rating': 3,
    },
    {
        'guest_name': 'David Martinez',
        'guest_email': 'david.m@example.com',
        'title': 'Comfortable Stay',
        'comment': 'Good hotel with comfortable beds and great service. The view from the room was amazing. Recommended for families.',
        'is_approved': True,
        'rating': 4,
    },
]

testimonial_count = 0
for test_data in testimonial_data:
    # Check if testimonial already exists
    existing = Testimonial.objects.filter(
        guest_email=test_data['guest_email'],
        title=test_data['title']
    ).first()
    
    if existing:
        existing.delete()
    
    testimonial = Testimonial.objects.create(**test_data)
    testimonial_count += 1
    
    status = "✓ Approved" if test_data['is_approved'] else "⏳ Pending"
    print(f"  ✓ Testimonial #{testimonial.id:4} | {test_data['guest_name']:20} | "
          f"{test_data['rating']}⭐ | {status}")

print(f"\n  ✓ Created {testimonial_count} testimonials")

# ============================================================================
# 5. CREATE SAMPLE CONTACT MESSAGES
# ============================================================================
print("\n[5] CREATING SAMPLE CONTACT MESSAGES...")
print("-" * 70)

contact_data = [
    {
        'name': 'Carlos Rodriguez',
        'email': 'carlos@example.com',
        'phone': '+63-917-123-4567',
        'subject': 'Booking Inquiry',
        'message': 'Hi, I would like to inquire about room availability for next month. Can you provide more details about your suites?',
        'is_read': False,
        'is_replied': False,
    },
    {
        'name': 'Maria Santos',
        'email': 'maria.santos@example.com',
        'phone': '+63-918-234-5678',
        'subject': 'Special Event Inquiry',
        'message': 'We are interested in hosting our company event at your hotel. Can you provide details about event packages?',
        'is_read': True,
        'is_replied': True,
    },
    {
        'name': 'Juan Dela Cruz',
        'email': 'juan.dc@example.com',
        'phone': '+63-919-345-6789',
        'subject': 'Room Issues During Stay',
        'message': 'I stayed at Room 201 last week and noticed that the air conditioning was not working properly. Any compensation available?',
        'is_read': True,
        'is_replied': False,
    },
    {
        'name': 'Angela Torres',
        'email': 'angela.torres@example.com',
        'phone': '+63-920-456-7890',
        'subject': 'Wedding Venue Inquiry',
        'message': 'Interested in booking your hotel for my wedding reception. Can you tell me about wedding packages and the grandest ballroom?',
        'is_read': False,
        'is_replied': False,
    },
    {
        'name': 'Miguel Fernandez',
        'email': 'miguel.f@example.com',
        'phone': '+63-921-567-8901',
        'subject': 'Membership Program',
        'message': 'Can you provide information about loyalty programs or membership discounts for frequent travelers?',
        'is_read': True,
        'is_replied': True,
    },
]

contact_count = 0
for contact in contact_data:
    # Check if contact message already exists
    existing = ContactMessage.objects.filter(
        email=contact['email'],
        subject=contact['subject']
    ).first()
    
    if existing:
        existing.delete()
    
    msg = ContactMessage.objects.create(**contact)
    contact_count += 1
    
    status = "✓ Read" if contact['is_read'] else "✓ Unread"
    replied = "✓ Replied" if contact['is_replied'] else "⏳ Pending"
    print(f"  ✓ Message #{msg.id:4} | {contact['name']:20} | {contact['subject']:25} | {status} | {replied}")

print(f"\n  ✓ Created {contact_count} contact messages")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("SUMMARY".center(70))
print("=" * 70)

print(f"\n✓ Users created:           {len(created_users)}")
print(f"  • Guest accounts:        {len([u for u in created_users.values() if u.role == UserRole.GUEST])}")
print(f"  • Staff accounts:        {len([u for u in created_users.values() if u.role == UserRole.STAFF])}")
print(f"  • Manager accounts:      {len([u for u in created_users.values() if u.role == UserRole.MANAGER])}")
print(f"  • Admin accounts:        {len([u for u in created_users.values() if u.role == UserRole.ADMIN])}")

print(f"\n✓ Bookings created:        {Booking.objects.count()}")
print(f"✓ Payments created:        {Payment.objects.count()}")
print(f"✓ Testimonials created:    {Testimonial.objects.count()}")
print(f"✓ Contact Messages:        {ContactMessage.objects.count()}")

print("\n" + "=" * 70)
print("TEST ACCOUNTS READY FOR TESTING".center(70))
print("=" * 70)

print("\n📋 TEST ACCOUNTS LOGIN CREDENTIALS:")
print("-" * 70)

for username, email, password, first_name, last_name, role in users_data[:5]:
    print(f"\n  👤 {first_name} {last_name} ({dict(UserRole.choices)[role]})")
    print(f"     Username: {username}")
    print(f"     Email:    {email}")
    print(f"     Password: {password}")

print("\n  ... and more accounts (check database for full list)")

print("\n" + "=" * 70)
print("✓ Sample data generation completed successfully!".center(70))
print("=" * 70)
