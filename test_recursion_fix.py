"""Test script to verify RecursionError fix"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cebuhotel.settings')
django.setup()

from django.template.loader import render_to_string
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()

def test_recommendations_widget():
    """Test if recommendations widget renders without recursion error"""
    
    print("\n" + "="*50)
    print("Testing Recommendations Widget")
    print("="*50 + "\n")
    
    # Create test request
    request = RequestFactory().get('/rooms/')
    request.user = User.objects.filter(username='admin').first() or User.objects.first()
    
    # Test with empty recommendations
    print("Test 1: Empty recommendations...")
    context = {
        'recommendations': [],
        'has_recommendations': False,
    }
    
    try:
        template = render_to_string('recommendations/recommendations_widget.html', context, request=request)
        print("✓ PASS: Template renders with empty recommendations")
    except RecursionError as e:
        print("✗ FAIL: RecursionError with empty recommendations")
        print(f"Error: {str(e)[:200]}")
        import traceback
        tb = traceback.format_exc()
        print("\nTraceback (last 500 chars):")
        print(tb[-500:])
        return False
    except Exception as e:
        print(f"✗ FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test with sample recommendations
    print("\nTest 2: Sample recommendations...")
    sample_recs = [
        {
            'room': {
                'id': 1,
                'room_number': '101',
                'room_type': 'STANDARD',
                'room_type_display': 'Standard Room',
                'price_per_night': 99.99,
                'capacity': 2,
                'is_available': True,
                'description': 'A nice room',
            },
            'score': 95.5,
            'reason': 'Based on your preferences',
            'booking_count': 5,
            'popularity': 'Popular',
        }
    ]
    
    context = {
        'recommendations': sample_recs,
        'has_recommendations': True,
    }
    
    try:
        template = render_to_string('recommendations/recommendations_widget.html', context, request=request)
        print("✓ PASS: Template renders with sample recommendations")
        if len(template) > 100:
            print(f"  Template generated {len(template)} characters")
    except RecursionError:
        print("✗ FAIL: RecursionError with sample recommendations")
        return False
    except Exception as e:
        print(f"✗ FAIL: {type(e).__name__}: {e}")
        return False
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50 + "\n")
    return True

if __name__ == '__main__':
    try:
        test_recommendations_widget()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
