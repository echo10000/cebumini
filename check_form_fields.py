#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from authentication.forms import RegisterForm

form = RegisterForm()
print("Form fields:")
for field_name, field in form.fields.items():
    print(f"  - {field_name}: {type(field).__name__}")
