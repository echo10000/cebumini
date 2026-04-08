"""
Form Validators Utility
Centralized validation logic for forms
"""

from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
import re


class DateValidator:
    """Validators for date fields"""
    
    @staticmethod
    def validate_future_date(date):
        """Ensure date is in the future"""
        if date < timezone.now().date():
            raise ValidationError("Date cannot be in the past.")
        return date
    
    @staticmethod
    def validate_date_range(check_in, check_out):
        """Ensure checkout is after checkin and minimum stay is met"""
        if not check_in or not check_out:
            return
        
        if check_out <= check_in:
            raise ValidationError("Check-out date must be after check-in date.")
        
        duration = (check_out - check_in).days
        if duration < 1:
            raise ValidationError("Minimum stay is 1 night.")
        
        if duration > 365:
            raise ValidationError("Maximum stay is 365 nights.")
        
        return duration
    
    @staticmethod
    def validate_within_advance_booking(check_in, max_days=365):
        """Ensure booking is not more than max days in advance"""
        days_ahead = (check_in - timezone.now().date()).days
        if days_ahead > max_days:
            raise ValidationError(
                f"Bookings can only be made up to {max_days} days in advance."
            )


class PriceValidator:
    """Validators for price fields"""
    
    @staticmethod
    def validate_price(price):
        """Validate price is positive and reasonable"""
        if price is None:
            raise ValidationError("Price is required.")
        
        if price <= 0:
            raise ValidationError("Price must be greater than 0.")
        
        if price > 999999:
            raise ValidationError("Price is unreasonably high.")
        
        # Check decimal places (max 2)
        price_str = str(price)
        if '.' in price_str:
            decimals = len(price_str.split('.')[1])
            if decimals > 2:
                raise ValidationError("Price can only have up to 2 decimal places.")
        
        return price
    
    @staticmethod
    def validate_discount_percentage(discount):
        """Validate discount percentage (0-100)"""
        if discount is None:
            return discount
        
        if discount < 0 or discount > 100:
            raise ValidationError("Discount must be between 0 and 100.")
        
        return discount


class FieldValidator:
    """Validators for common fields"""
    
    @staticmethod
    def validate_phone_number(phone):
        """Validate phone number format"""
        if not phone:
            return phone
        
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
        
        # Check if only digits and + sign
        if not re.match(r'^\+?[\d]{7,15}$', cleaned):
            raise ValidationError(
                "Phone number must be between 7-15 digits. "
                "Use format: +63 XXX XXX XXXX or 09XX XXX XXXX"
            )
        
        return phone
    
    @staticmethod
    def validate_room_number(room_number):
        """Validate room number format"""
        if not room_number:
            raise ValidationError("Room number is required.")
        
        # Room number should be alphanumeric, 1-10 chars
        if not re.match(r'^[A-Z0-9\-]{1,10}$', room_number.upper()):
            raise ValidationError(
                "Room number must be 1-10 characters (letters, numbers, hyphens)."
            )
        
        return room_number.upper()
    
    @staticmethod
    def validate_capacity(capacity):
        """Validate room capacity"""
        if capacity is None:
            raise ValidationError("Capacity is required.")
        
        if capacity < 1 or capacity > 20:
            raise ValidationError("Capacity must be between 1 and 20 guests.")
        
        return capacity
    
    @staticmethod
    def validate_text_field(text, min_length=1, max_length=500):
        """Validate text field length"""
        if not text:
            if min_length > 0:
                raise ValidationError(f"This field is required (minimum {min_length} characters).")
            return text
        
        text = text.strip()
        
        if len(text) < min_length:
            raise ValidationError(f"Minimum length is {min_length} characters.")
        
        if len(text) > max_length:
            raise ValidationError(f"Maximum length is {max_length} characters.")
        
        return text
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return email
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Please enter a valid email address.")
        
        return email
    
    @staticmethod
    def validate_url(url):
        """Validate URL format"""
        if not url:
            return url
        
        pattern = r'^https?://(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        if not re.match(pattern, url):
            raise ValidationError("Please enter a valid URL.")
        
        return url


class RoomValidator:
    """Validators for room-related fields"""
    
    @staticmethod
    def validate_room_type(room_type):
        """Validate room type"""
        from .models import RoomType
        valid_types = dict(RoomType.choices).keys()
        
        if room_type not in valid_types:
            raise ValidationError(f"Invalid room type. Must be one of: {', '.join(valid_types)}")
        
        return room_type
    
    @staticmethod
    def validate_amenities(amenities_text):
        """Validate amenities input"""
        if not amenities_text:
            return amenities_text
        
        amenities_list = [a.strip() for a in amenities_text.split(',')]
        
        if len(amenities_list) > 20:
            raise ValidationError("Maximum 20 amenities allowed.")
        
        for amenity in amenities_list:
            if len(amenity) > 50:
                raise ValidationError("Each amenity must be less than 50 characters.")
        
        return amenities_text


class BookingValidator:
    """Validators for booking-related fields"""
    
    @staticmethod
    def validate_special_requests(requests):
        """Validate special requests"""
        if not requests:
            return requests
        
        requests = requests.strip()
        
        if len(requests) > 1000:
            raise ValidationError("Special requests must be less than 1000 characters.")
        
        # Check for malicious content (basic check)
        if any(char in requests for char in ['<', '>', '{', '}', 'javascript']):
            raise ValidationError("Special requests contain invalid characters.")
        
        return requests
    
    @staticmethod
    def validate_booking_status(status):
        """Validate booking status"""
        from .models import BookingStatus
        valid_statuses = dict(BookingStatus.choices).keys()
        
        if status not in valid_statuses:
            raise ValidationError(f"Invalid booking status.")
        
        return status


def validate_form_data(form_data, validation_rules):
    """
    Generic validator for form data
    
    Args:
        form_data: Dictionary of form fields
        validation_rules: Dictionary of field -> [validators] mapping
    
    Returns:
        Dictionary of errors if any, else empty dict
    """
    errors = {}
    
    for field, validators in validation_rules.items():
        value = form_data.get(field)
        
        for validator in validators:
            try:
                validator(value)
            except ValidationError as e:
                if field not in errors:
                    errors[field] = []
                errors[field].append(str(e.message))
    
    return errors
