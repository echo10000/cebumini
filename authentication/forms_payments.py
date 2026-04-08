from django import forms
from .models import Payment, PaymentMethod


class PaymentMethodForm(forms.Form):
    """Form for selecting payment method"""
    payment_method = forms.ChoiceField(
        choices=[
            ('PAYMONGO', 'PayMongo - GCash, Cards, Maya'),
            ('STRIPE', 'Credit/Debit Card (Stripe)'),
            ('GCASH', 'GCash (Manual)'),
            ('BANK_TRANSFER', 'Bank Transfer'),
        ],
        widget=forms.RadioSelect(),
        label='Select Payment Method',
        required=True
    )


class StripePaymentForm(forms.Form):
    """Form for Stripe card payment in test mode"""
    card_number = forms.CharField(
        max_length=19,
        label='Card Number (Test: 4242 4242 4242 4242)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '4242 4242 4242 4242',
            'inputmode': 'numeric',
        }),
        required=True
    )
    card_expiry = forms.CharField(
        max_length=5,
        label='Expiry Date (MM/YY)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12/25',
            'pattern': '[0-9]{2}/[0-9]{2}',
        }),
        required=True
    )
    card_cvc = forms.CharField(
        max_length=4,
        label='CVC (any 3 digits in test mode)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'pattern': '[0-9]{3,4}',
        }),
        required=True
    )
    cardholder_name = forms.CharField(
        max_length=100,
        label='Cardholder Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John Doe',
        }),
        required=True
    )

    def clean_card_number(self):
        card_number = self.cleaned_data['card_number']
        # Remove spaces
        card_number = card_number.replace(' ', '')
        if not card_number.isdigit():
            raise forms.ValidationError('Card number must contain only digits.')
        if len(card_number) != 16:
            raise forms.ValidationError('Card number must be exactly 16 digits.')
        return card_number

    def clean_card_expiry(self):
        expiry = self.cleaned_data['card_expiry']
        if '/' not in expiry:
            raise forms.ValidationError('Expiry must be in MM/YY format.')
        try:
            month, year = expiry.split('/')
            month = int(month)
            year = int(year)
            if month < 1 or month > 12:
                raise forms.ValidationError('Invalid month.')
        except:
            raise forms.ValidationError('Expiry must be in MM/YY format.')
        return expiry

    def clean_card_cvc(self):
        cvc = self.cleaned_data['card_cvc']
        if not cvc.isdigit() or len(cvc) < 3 or len(cvc) > 4:
            raise forms.ValidationError('CVC must be 3 or 4 digits.')
        return cvc


class GCashPaymentForm(forms.Form):
    """Form for GCash payment verification after sending payment"""
    gcash_reference = forms.CharField(
        max_length=50,
        label='GCash Reference Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., G123456789ABC',
            'autofocus': True,
        }),
        help_text='Enter the reference number you received from GCash after sending the payment.',
        required=True
    )
    
    def clean_gcash_reference(self):
        reference = self.cleaned_data['gcash_reference'].strip()
        if not reference:
            raise forms.ValidationError('Reference number is required.')
        if len(reference) < 5:
            raise forms.ValidationError('Reference number appears too short.')
        return reference


class BankTransferForm(forms.Form):
    """Form for bank transfer payment"""
    bank_name = forms.CharField(
        max_length=100,
        label='Bank Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., BDO, BPI, Metrobank',
        }),
        required=True
    )
    reference_number = forms.CharField(
        max_length=50,
        label='Transfer Reference Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bank transaction reference',
        }),
        help_text='Provide the bank reference number for tracking.',
        required=True
    )
    notes = forms.CharField(
        label='Additional Notes',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any additional information about your transfer.',
        }),
        required=False
    )
