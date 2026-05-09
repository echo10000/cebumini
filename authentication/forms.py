import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()

class RegisterForm(UserCreationForm):
    """Custom user registration form - email based"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 09123456789',
            'type': 'tel',
            'maxlength': '15',
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        }),
        label='Password'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
        }),
        label='Confirm Password'
    )
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='I agree to the Terms and Conditions',
        error_messages={
            'required': 'Please accept the Terms and Conditions to create an account.'
        }
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise ValidationError('Phone number is required.')

        phone_pattern = re.compile(r'^(\+63|09)\d{9,10}$')
        if not phone_pattern.match(phone):
            raise ValidationError('Please enter a valid Philippine phone number.')
        return phone

    def clean_accept_terms(self):
        accept_terms = self.cleaned_data.get('accept_terms')
        if not accept_terms:
            raise ValidationError('You must accept the Terms and Conditions to proceed.')
        return accept_terms

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.phone_number = self.cleaned_data.get('phone', '')
        # Auto-generate username from email for internal use
        user.username = self.cleaned_data.get('email', '').split('@')[0]
        # Ensure unique username
        if User.objects.filter(username=user.username).exists():
            counter = 1
            base_username = user.username
            while User.objects.filter(username=f"{base_username}{counter}").exists():
                counter += 1
            user.username = f"{base_username}{counter}"
        if commit:
            user.save()
        return user



class LoginForm(forms.Form):
    """Custom login form"""
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Remember me'
    )
