from django import forms
from .models import Payment, PaymentStatus


class PaymentApprovalForm(forms.ModelForm):
    """Form for approving/rejecting payments"""
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add notes about this payment approval/rejection (optional)'
        }),
        required=False,
        help_text='Internal notes about the payment decision'
    )
    
    class Meta:
        model = Payment
        fields = ['notes']


class PaymentFilterForm(forms.Form):
    """Form for filtering payments"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + list(PaymentStatus.choices)
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_method = forms.ChoiceField(
        choices=[('', 'All Methods'), ('STRIPE', 'Stripe'), ('GCASH', 'GCash'), ('BANK_TRANSFER', 'Bank Transfer')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
