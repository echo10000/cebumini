#!/usr/bin/env python
"""
Check if we can trace the exact issue by looking at form binding
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from authentication.forms import RegisterForm

# Simulate what SHOULD be posted
post_data_with_names = {
    'email': 'test.withnames@example.com',
    'first_name': 'John',
    'last_name': 'Doe',
    'password1': 'TestPass123!',
    'password2': 'TestPass123!',
    'accept_terms': 'on',
}

print("Testing form binding...")
print(f"POST data: {post_data_with_names}\n")

form = RegisterForm(data=post_data_with_names)

print(f"Form valid: {form.is_valid()}")
print(f"Form fields: {list(form.fields.keys())}")
print(f"Form errors: {form.errors}\n")

if form.is_valid():
    print("Cleaned data:")
    for key in ['email', 'first_name', 'last_name', 'password1', 'password2', 'accept_terms']:
        val = form.cleaned_data.get(key, 'NOT IN CLEANED_DATA')
        print(f"  {key}: {val}")
