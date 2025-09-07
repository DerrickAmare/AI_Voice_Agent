#!/usr/bin/env python3
"""
Test different phone number formats to see which ones work
"""

import phonenumbers

def test_phone_formats():
    """Test various phone number formats"""
    test_numbers = [
        "(555) 123-4567",
        "555-123-4567", 
        "5551234567",
        "+15551234567",
        "1-555-123-4567",
        "(555)123-4567",
        "555.123.4567",
        # Try some real area codes
        "(212) 555-1234",  # NYC
        "(415) 555-1234",  # SF
        "+12125551234",    # E164 format
        "12125551234"      # Full number
    ]
    
    print("🔧 Testing Phone Number Formats...")
    
    for number in test_numbers:
        try:
            parsed = phonenumbers.parse(number, "US")
            is_valid = phonenumbers.is_valid_number(parsed)
            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            
            status = "✅ VALID" if is_valid else "❌ INVALID"
            print(f"   {number:<15} -> {status} -> {formatted if is_valid else 'N/A'}")
            
        except Exception as e:
            print(f"   {number:<15} -> ❌ ERROR: {e}")

if __name__ == "__main__":
    test_phone_formats()
