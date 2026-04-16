#!/usr/bin/env python
"""
Debug: test registration form with actual POST data like from HTML
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.test import Client

client = Client()

# Simulate form submission with POST data
post_data = {
    'email': 'testregister@example.com',
    'first_name': 'Registration',
    'last_name': 'Test',
    'password1': 'TestPass123!',
    'password2': 'TestPass123!',
    'accept_terms': 'on',  # Checkbox value
}

print("Simulating registration form submission...")
print(f"POST data: {post_data}")
print()

# POST to registration endpoint
response = client.post('/auth/register/', data=post_data)

print(f"Response status: {response.status_code}")

# Check if redirect (which would mean success)
if response.status_code == 302:
    print("✓ Form accepted - redirected to login")
    
    # Check database
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(email='testregister@example.com').first()
    
    if user:
        print(f"\n✓ User created: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  First Name: |{user.first_name}|")
        print(f"  Last Name: |{user.last_name}|")
        
        if user.first_name and user.last_name:
            print("\n✓ NAMES WERE SAVED CORRECTLY!")
        else:
            print("\n✗ NAMES WERE NOT SAVED!")
    else:
        print("✗ User not found in database")
else:
    print(f"✗ Form rejected with status {response.status_code}")
    html = response.content.decode('utf-8')
    
    # Try to extract form errors
    if 'error' in html.lower():
        start = html.find('<div class="alert alert-error')
        if start > -1:
            end = html.find('</div>', start) + 6
            print("\nForm errors:")
            print(html[start:end])
