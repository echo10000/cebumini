from django import forms
from django.core.exceptions import ValidationError
from .models import Room, RoomImage
from .validators import PriceValidator, FieldValidator, RoomValidator


class RoomForm(forms.ModelForm):
    """Room management form"""
    
    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'description', 'price_per_night', 
                  'capacity', 'is_available', 'amenities', 'image']
        widgets = {
            'room_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Room number (e.g., 101, 102)',
            }),
            'room_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Room description',
            }),
            'price_per_night': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price per night',
                'step': '0.01',
                'min': '0',
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Guest capacity',
                'min': '1',
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'amenities': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Amenities (comma-separated)\nExample: WiFi, TV, AC, Minibar',
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }

    def clean_price_per_night(self):
        price = self.cleaned_data.get('price_per_night')
        if price is not None:
            PriceValidator.validate_price(price)
        return price

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None:
            FieldValidator.validate_capacity(capacity)
        return capacity
    
    def clean_room_number(self):
        room_number = self.cleaned_data.get('room_number')
        if room_number:
            room_number = FieldValidator.validate_room_number(room_number)
        return room_number
    
    def clean_amenities(self):
        amenities = self.cleaned_data.get('amenities')
        if amenities:
            RoomValidator.validate_amenities(amenities)
        return amenities
    
    def clean(self):
        """Additional form-wide validation"""
        cleaned_data = super().clean()
        
        min_price = cleaned_data.get('price_per_night')
        capacity = cleaned_data.get('capacity')
        
        # Ensure price and capacity are set
        if min_price is None:
            self.add_error('price_per_night', 'Price per night is required.')
        
        if capacity is None:
            self.add_error('capacity', 'Capacity is required.')
        
        return cleaned_data


class RoomImageForm(forms.ModelForm):
    """Room image upload form"""
    
    class Meta:
        model = RoomImage
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Image caption (optional)',
            }),
        }


class RoomFilterForm(forms.Form):
    """Filter rooms"""
    room_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(Room.room_type.field.choices),
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Price',
            'step': '0.01',
        })
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Price',
            'step': '0.01',
        })
    )
    capacity = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Capacity',
            'min': '1',
        })
    )
    available_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Available only'
    )
