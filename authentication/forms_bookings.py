from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking, BookingStatus, RoomType


class BookingForm(forms.ModelForm):
    """Form for creating/editing bookings"""
    
    check_in = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': timezone.now().date().isoformat(),
        }),
        label='Check-in Date',
        help_text='Select your arrival date'
    )
    
    check_out = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': timezone.now().date().isoformat(),
        }),
        label='Check-out Date',
        help_text='Select your departure date'
    )
    
    special_requests = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Any special requests? (e.g., high floor, late checkout, etc.)'
        }),
        required=False,
        label='Special Requests',
        max_length=500
    )

    class Meta:
        model = Booking
        fields = ['check_in', 'check_out', 'special_requests']

    def __init__(self, *args, room=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.room = room
        self.fields['special_requests'].widget.attrs['placeholder'] = 'Enter any special requests...'

    def clean(self):
        """Validate booking form"""
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        if check_in and check_out:
            # Check that check-out is after check-in
            if check_out <= check_in:
                raise ValidationError("Check-out date must be after check-in date.")
            
            # Check minimum stay (1 night)
            duration = (check_out - check_in).days
            if duration < 1:
                raise ValidationError("Minimum stay is 1 night.")

            # Check that dates are not in the past
            today = timezone.now().date()
            if check_in < today:
                raise ValidationError("Check-in date cannot be in the past.")

            # Check availability if room is provided
            if self.room:
                exclude_booking_id = None
                if self.instance and self.instance.pk:
                    exclude_booking_id = self.instance.pk

                is_available = Booking.check_availability(
                    self.room.id,
                    check_in,
                    check_out,
                    exclude_booking_id=exclude_booking_id
                )
                
                if not is_available:
                    raise ValidationError(
                        f"Room {self.room.room_number} is not available for the selected dates. "
                        "Please choose different dates."
                    )

        return cleaned_data


class BookingFilterForm(forms.Form):
    """Form for filtering bookings (admin)"""
    
    ROOM_TYPE_CHOICES = [('', 'All Room Types')] + list(RoomType.choices)
    STATUS_CHOICES = [('', 'All Statuses')] + list(BookingStatus.choices)
    
    room_type = forms.ChoiceField(
        choices=ROOM_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
        }),
        label='Room Type'
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
        }),
        label='Status'
    )
    
    check_in_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
        }),
        label='Check-in From'
    )
    
    check_in_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
        }),
        label='Check-in To'
    )
    
    guest_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Search by guest name or email...'
        }),
        label='Guest Search'
    )

    def clean(self):
        """Validate filter form"""
        cleaned_data = super().clean()
        check_in_from = cleaned_data.get('check_in_from')
        check_in_to = cleaned_data.get('check_in_to')

        if check_in_from and check_in_to:
            if check_in_to < check_in_from:
                raise ValidationError("'Check-in To' date must be after 'Check-in From' date.")

        return cleaned_data


class BookingConfirmationForm(forms.Form):
    """Form for confirming booking"""
    
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='I agree to the booking terms and conditions',
        error_messages={'required': 'You must agree to the terms to confirm booking.'}
    )


class CancelBookingForm(forms.Form):
    """Form for cancelling booking"""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Why are you cancelling this booking?'
        }),
        required=False,
        label='Cancellation Reason',
        max_length=500
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='I confirm this booking cancellation',
        error_messages={'required': 'You must confirm the cancellation.'}
    )


class ContactForm(forms.Form):
    """Form for contact messages"""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name',
        }),
        label='Full Name'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email',
        }),
        label='Email Address'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Phone Number',
        }),
        label='Phone Number'
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject',
        }),
        label='Subject'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your Message...',
        }),
        label='Message'
    )
    
    def save(self, guest=None):
        """Save contact message to database"""
        from .models import ContactMessage
        
        contact_msg = ContactMessage(
            name=self.cleaned_data['name'],
            email=self.cleaned_data['email'],
            phone=self.cleaned_data.get('phone', ''),
            subject=self.cleaned_data['subject'],
            message=self.cleaned_data['message'],
        )
        if guest:
            contact_msg.guest = guest
        contact_msg.save()
        return contact_msg


class TestimonialForm(forms.Form):
    """Form for submitting testimonials/reviews"""
    
    RATING_CHOICES = [
        (5, '⭐⭐⭐⭐⭐ Excellent'),
        (4, '⭐⭐⭐⭐ Very Good'),
        (3, '⭐⭐⭐ Good'),
        (2, '⭐⭐ Fair'),
        (1, '⭐ Poor'),
    ]
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name',
        }),
        label='Your Name'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email',
        }),
        label='Email Address'
    )
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        label='Rating'
    )
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Review Title (e.g., "Amazing Experience!")',
        }),
        label='Review Title'
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Share your experience...',
        }),
        label='Your Review'
    )
    
    def save(self, guest=None):
        """Save testimonial to database"""
        from .models import Testimonial
        
        testimonial = Testimonial(
            guest=guest,
            guest_name=self.cleaned_data['name'],
            guest_email=self.cleaned_data['email'],
            rating=int(self.cleaned_data['rating']),
            title=self.cleaned_data['title'],
            comment=self.cleaned_data['comment'],
            content=self.cleaned_data['comment'],
            status=Testimonial.Status.PENDING,
            is_approved=False,
        )
        testimonial.save()
        return testimonial
