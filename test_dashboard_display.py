#!/usr/bin/env python
"""
Test dashboard rendering with a user that has first_name and last_name
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Create or get test user
user = User.objects.filter(username='testdashboard').first()
if not user:
    print("Test user not found. Please run create_test_user.py first")
    exit(1)

print(f"Testing with user: {user.username}")
print(f"  First Name: {user.first_name}")
print(f"  Last Name: {user.last_name}")

# Update user to have accepted terms
user.terms_accepted = True
from django.utils import timezone
user.terms_accepted_at = timezone.now()
user.terms_version = '1.0'
user.save()

# Create a test client and login
client = Client()
logged_in = client.login(username='testdashboard', password='TestPass123!')

if not logged_in:
    print("✗ Login failed")
    exit(1)

print("✓ Login successful")
print("✓ Terms accepted")

# Request the dashboard (follow redirects)
response = client.get('/auth/dashboard/', follow=True)

print(f"\nDashboard response status: {response.status_code}")

if response.status_code == 200:
    html = response.content.decode('utf-8')
    
    # Check if name appears in welcome message
    if 'Welcome, Test User!' in html:
        print("✓ Welcome message shows name correctly!")
    elif 'Welcome, !' in html or 'Welcome,  !' in html:
        print("✗ Welcome message is empty (name not rendering)")
    else:
        print("? Unexpected welcome format")
    
    # Check profile information section
    if '<span class="info-value">Test</span>' in html and 'User' in html:
        print("✓ Profile information shows names!")
    elif '<span class="info-value"></span>' in html:
        print("✗ Profile information does not show names (empty)")
    else:
        print("? Could not find profile info in expected format")
        
    # Debug: show relevant HTML sections
    if 'Welcome' in html:
        start = html.find('<h1')
        if start > -1:
            end = html.find('</h1>', start) + 5
            welcome = html[start:end]
            print(f"\nWelcome section:\n{welcome}")
else:
    print(f"✗ Dashboard request failed with status {response.status_code}")

