#!/usr/bin/env python3
"""
Test script for the AI Voice Agent outbound calling system
Demonstrates SMS notification and call initiation using actual Twilio credentials
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.append('src')

from services.telephony_service import TelephonyService
from services.notification_service import NotificationService

def test_sms_and_call():
    """Test SMS notification and call initiation"""
    
    # Initialize services
    telephony_service = TelephonyService()
    notification_service = NotificationService()
    
    # Test phone number (from the example)
    test_phone = "+16154846056"
    test_name = "Michael"
    
    print("🚀 Testing AI Voice Agent Outbound Calling System")
    print("=" * 50)
    
    # 1. Send SMS notification
    print("📱 Step 1: Sending SMS notification...")
    sms_message = f"Hi {test_name}! Our AI assistant will call you within 5 minutes to help build your resume. This will only take a few minutes."
    
    sms_result = notification_service.send_immediate_notification(test_phone, sms_message)
    
    if sms_result.get("success"):
        print(f"✅ SMS sent successfully!")
        if sms_result.get("message_sid"):
            print(f"   Message SID: {sms_result['message_sid']}")
    else:
        print(f"❌ SMS failed: {sms_result.get('error', 'Unknown error')}")
    
    # Wait a moment
    print("\n⏳ Waiting 3 seconds before initiating call...")
    time.sleep(3)
    
    # 2. Initiate outbound call
    print("📞 Step 2: Initiating outbound call...")
    
    call_result = telephony_service.initiate_outbound_call(
        phone_number=test_phone,
        metadata={
            "name": test_name,
            "purpose": "resume_building",
            "test_call": True
        }
    )
    
    if call_result.get("success"):
        print(f"✅ Call initiated successfully!")
        print(f"   Call SID: {call_result.get('call_sid')}")
        print(f"   Status: {call_result.get('status')}")
        print(f"   To: {call_result.get('to')}")
        print(f"   From: {call_result.get('from')}")
        
        if call_result.get("demo_mode"):
            print("   ⚠️  Running in demo mode (Twilio not configured)")
    else:
        print(f"❌ Call failed: {call_result.get('error', 'Unknown error')}")
    
    # 3. Check service availability
    print("\n🔍 Step 3: Checking service status...")
    print(f"   Telephony service available: {telephony_service.is_available()}")
    
    print("\n" + "=" * 50)
    print("✨ Test completed!")
    
    return sms_result.get("success", False) and call_result.get("success", False)

def test_phone_validation():
    """Test phone number validation"""
    print("\n📋 Testing phone number validation...")
    
    telephony_service = TelephonyService()
    
    test_numbers = [
        "+16154846056",  # Valid US number
        "6154846056",    # US number without country code
        "+1234567890",   # Generic valid format
        "invalid",       # Invalid number
    ]
    
    for number in test_numbers:
        result = telephony_service.validate_phone_number(number)
        status = "✅" if result["valid"] else "❌"
        print(f"   {status} {number}: {result}")

if __name__ == "__main__":
    print("AI Voice Agent - System Test")
    print("This script tests the outbound calling system with actual credentials")
    print()
    
    # Check if environment variables are set
    required_vars = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please ensure your .env file is configured correctly.")
        sys.exit(1)
    
    try:
        # Run tests
        test_phone_validation()
        success = test_sms_and_call()
        
        if success:
            print("\n🎉 All tests passed! System is ready for production.")
        else:
            print("\n⚠️  Some tests failed. Check configuration and try again.")
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
