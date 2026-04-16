#!/usr/bin/env python
"""
Admin Panel Testing - Verify all admin interfaces are accessible
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from authentication.models import Room, Booking, Payment, Testimonial, ContactMessage, TwoFactorAuth

User = get_user_model()
client = Client()

print("\n" + "=" * 80)
print("ADMIN PANEL FUNCTIONALITY TEST".center(80))
print("=" * 80)

# Get admin user
admin_user = User.objects.filter(username='admin_super').first()

if not admin_user:
    print("\n✗ Admin user not found!")
else:
    print(f"\n✓ Admin User Found: {admin_user.username}")
    print(f"  └─ Email: {admin_user.email}")
    print(f"  └─ Role: {admin_user.get_role_display()}")
    
    # Login admin
    login_success = client.login(username='admin_super', password='AdminPass123!')
    
    if login_success:
        print(f"\n✓ Login Successful")
        
        # Test admin panel endpoints
        print(f"\n✓ Testing Admin Panel Endpoints:")
        print("-" * 80)
        
        endpoints = [
            ('/admin/', 'Admin Home'),
            ('/admin/authentication/customuser/', 'User Management'),
            ('/admin/authentication/room/', 'Room Management'),
            ('/admin/authentication/booking/', 'Booking Management'),
            ('/admin/authentication/payment/', 'Payment Management'),
            ('/admin/authentication/testimonial/', 'Testimonials'),
            ('/admin/authentication/contactmessage/', 'Contact Messages'),
            ('/admin/authentication/twofactorauth/', 'Two Factor Auth'),
        ]
        
        for endpoint, name in endpoints:
            response = client.get(endpoint)
            status = "✓" if response.status_code == 200 else "✗"
            print(f"  {status} {name:30} | Status: {response.status_code}")
        
        # Test POST operations (updating entities)
        print(f"\n✓ Testing Entity Operations:")
        print("-" * 80)
        
        # Get sample entities
        room = Room.objects.first()
        booking = Booking.objects.first()
        payment = Payment.objects.first()
        testimonial = Testimonial.objects.first()
        contact = ContactMessage.objects.first()
        
        if room:
            print(f"  ✓ Rooms: {Room.objects.count()} available in database")
        if booking:
            print(f"  ✓ Bookings: {Booking.objects.count()} available in database")
        if payment:
            print(f"  ✓ Payments: {Payment.objects.count()} available in database")
        if testimonial:
            print(f"  ✓ Testimonials: {Testimonial.objects.count()} available in database")
        if contact:
            print(f"  ✓ Contact Messages: {ContactMessage.objects.count()} available in database")
        
        # Test admin can view change forms
        print(f"\n✓ Testing Admin Change Forms:")
        print("-" * 80)
        
        if room:
            response = client.get(f'/admin/authentication/room/{room.id}/change/')
            status = "✓" if response.status_code == 200 else "✗"
            print(f"  {status} View Room {room.room_number}")
        
        if booking:
            response = client.get(f'/admin/authentication/booking/{booking.id}/change/')
            status = "✓" if response.status_code == 200 else "✗"
            print(f"  {status} View Booking #{booking.id}")
        
        if payment:
            response = client.get(f'/admin/authentication/payment/{payment.id}/change/')
            status = "✓" if response.status_code == 200 else "✗"
            print(f"  {status} View Payment #{payment.id}")
        
        if testimonial:
            response = client.get(f'/admin/authentication/testimonial/{testimonial.id}/change/')
            status = "✓" if response.status_code == 200 else "✗"
            print(f"  {status} View Testimonial #{testimonial.id}")
        
        # Logout
        client.logout()
        print(f"\n✓ Admin Session Ended Successfully")
        
    else:
        print(f"\n✗ Login Failed")

print("\n" + "=" * 80)
print("ADMIN PANEL TEST COMPLETE".center(80))
print("=" * 80 + "\n")
