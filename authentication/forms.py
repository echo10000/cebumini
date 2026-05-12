import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .models import AdminProfile, ManagerProfile, StaffProfile, UserProfile

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
    agree_to_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='I agree to the Terms and Conditions',
        error_messages={
            'required': 'You must accept the Terms and Conditions.'
        }
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError('Email is required.')
        if User.objects.filter(email__iexact=email).exists():
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

    def clean_agree_to_terms(self):
        agree_to_terms = self.cleaned_data.get('agree_to_terms')
        if not agree_to_terms:
            raise ValidationError('You must accept the Terms and Conditions.')
        return agree_to_terms

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


class UserProfileForm(forms.ModelForm):
    """Form for common profile details."""

    class Meta:
        model = UserProfile
        exclude = ['user']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Short bio'}),
        }


class StaffProfileForm(forms.ModelForm):
    """Form for staff profile details."""

    class Meta:
        model = StaffProfile
        exclude = ['user']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee ID'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Position'}),
            'hired_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ManagerProfileForm(forms.ModelForm):
    """Form for manager profile details."""

    class Meta:
        model = ManagerProfile
        exclude = ['user']
        widgets = {
            'managed_departments': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Front Desk, Housekeeping, Management',
            }),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'manager_since': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class AdminProfileForm(forms.ModelForm):
    """Form for admin-only profile details."""

    class Meta:
        model = AdminProfile
        exclude = ['user']
        widgets = {
            'system_access_level': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Internal admin notes'}),
            'last_audit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ChangePasswordForm(forms.Form):
    """Password change form that keeps validation close to the current user."""
    current_password = forms.CharField(
        label='Current password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'})
    )
    new_password = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'})
    )
    confirm_new_password = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError('Your current password is incorrect.')
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')

        if new_password and confirm_new_password and new_password != confirm_new_password:
            self.add_error('confirm_new_password', 'The new passwords do not match.')

        if new_password:
            try:
                password_validation.validate_password(new_password, self.user)
            except ValidationError as error:
                self.add_error('new_password', error)

        return cleaned_data


class UpdateEmailForm(forms.Form):
    """Email update form with confirmation and uniqueness checks."""
    new_email = forms.EmailField(
        label='New email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'New email address'})
    )
    confirm_email = forms.EmailField(
        label='Confirm email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Confirm email address'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_email(self):
        email = (self.cleaned_data.get('new_email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('This email address is already in use.')
        return email

    def clean_confirm_email(self):
        return (self.cleaned_data.get('confirm_email') or '').strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        new_email = cleaned_data.get('new_email')
        confirm_email = cleaned_data.get('confirm_email')

        if new_email and confirm_email and new_email != confirm_email:
            self.add_error('confirm_email', 'Email addresses do not match.')

        return cleaned_data
