#!/usr/bin/env python
"""
Check what HTML is being rendered for form fields
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from authentication.forms import RegisterForm

form = RegisterForm()

print("Form field names: ", list(form.fields.keys()))
print(f"\nField types:")
for name, field in form.fields.items():
    print(f"  {name}: {type(field).__name__}")

print(f"\nRendering first_name field:")
if 'first_name' in form.fields:
    print(form['first_name'])
else:
    print("  NOT IN FORM!")

print(f"\nRendering last_name field:")
if 'last_name' in form.fields:
    print(form['last_name'])
else:
    print("  NOT IN FORM!")
