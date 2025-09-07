#!/usr/bin/env python3
"""
Test with the verified phone number to see if Twilio call succeeds
"""

import requests
import time
import sys
import os

# Add src to path
sys.path.append('src')

from services.redis_state_service import RedisStateService

def test_verified_number():
    """Test with verified phone number"""
    print("🔍 Testing with Verified Phone Number: +17209545909")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    redis_service = RedisStateService("redis://localhost:6379")
    
    # Clear old sessions first
    print("\n1. 🧹 Clearing old call sessions...")
    try:
        keys = redis_service.redis_client.keys("CALL_SESSION:*")
        if keys:
            redis_service.redis_client.delete(*keys)
            print(f"   Cleared {len(keys)} old sessions")
        else:
            print("   No old sessions to clear")
    except Exception as e:
        print(f"   Warning: {e}")
    
    # Submit request with verified number
    print("\n2. 📝 Submitting Request with Verified Number...")
    form_data = {
        'phoneNumber': '+17209545909',
        'fullName': 'Test User',
        'email': 'test@example.com',
        'callTime': 'immediate'
    }
    
    response = requests.post(f"{base_url}/api/submit-request", data=form_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Form submission failed: {response.text}")
        return
    
    result = response.json()
    request_id = result.get('requestId')
    print(f"✅ Request ID: {request_id}")
    
    # Wait for background processing
    print("\n3. ⏳ Waiting for background call initiation...")
    for i in range(15):  # Wait up to 15 seconds
        time.sleep(1)
        
        # Check for new call sessions
        keys = redis_service.redis_client.keys("CALL_SESSION:*")
        if keys:
            print(f"   Found call session after {i+1} seconds")
            break
        print(f"   Waiting... ({i+1}/15)")
    
    # Check what happened
    print("\n4. 🔍 Checking Results...")
    keys = redis_service.redis_client.keys("CALL_SESSION:*")
    
    if keys:
        for key in keys:
            call_id = key.replace("CALL_SESSION:", "")
            session = redis_service.get_call_session(call_id)
            if session and session.phone_number == "+17209545909":
                print(f"✅ Found call session for verified number:")
                print(f"   📞 Call ID: {call_id}")
                print(f"   📱 Phone: {session.phone_number}")
                print(f"   📋 Request ID: {session.request_id}")
                print(f"   📊 Status: {session.status}")
                print(f"   🔗 Twilio SID: {session.twilio_call_sid}")
                
                if session.twilio_call_sid:
                    print("🎉 SUCCESS! Twilio call was initiated successfully!")
                    print("   The phone should ring shortly.")
                    print("   If you're still getting 'application error', it might be")
                    print("   during the actual phone conversation, not the initiation.")
                else:
                    print("❌ Twilio call was not initiated")
                    print("   Check the server logs for Twilio errors")
                
                return
    
    print("❌ No call session found for the verified number")
    print("   This means the background task failed to create the call")
    
    # Check resume request status
    print("\n5. 📋 Checking Resume Request Status...")
    try:
        request_data = redis_service.get_resume_request(request_id)
        if request_data:
            print(f"   Status: {request_data.get('status')}")
            print(f"   Call ID: {request_data.get('call_id', 'None')}")
        else:
            print("   ❌ Resume request not found")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_verified_number()
