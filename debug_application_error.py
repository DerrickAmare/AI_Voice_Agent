#!/usr/bin/env python3
"""
Debug the exact application error by tracing the complete flow
"""

import requests
import time
import sys
import os

# Add src to path
sys.path.append('src')

from services.redis_state_service import RedisStateService

def debug_application_error():
    """Debug the complete flow to find the application error"""
    print("🔍 Debugging Application Error...")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    redis_service = RedisStateService("redis://localhost:6379")
    
    # Step 1: Submit a resume request
    print("\n1. 📝 Submitting Resume Request...")
    form_data = {
        'phoneNumber': '+17209545909',
        'fullName': 'Debug User',
        'email': 'debug@example.com',
        'callTime': 'immediate'
    }
    
    response = requests.post(f"{base_url}/api/submit-request", data=form_data)
    if response.status_code != 200:
        print(f"❌ Form submission failed: {response.text}")
        return
    
    result = response.json()
    request_id = result.get('requestId')
    print(f"✅ Request ID: {request_id}")
    
    # Step 2: Wait for background processing and check what call_id was created
    print("\n2. ⏳ Waiting for background processing...")
    time.sleep(5)  # Wait for background task
    
    # Check what call sessions exist in Redis
    print("\n3. 🔍 Checking Redis for Call Sessions...")
    try:
        # Get all call session keys
        keys = redis_service.redis_client.keys("CALL_SESSION:*")
        print(f"Found {len(keys)} call sessions in Redis:")
        
        for key in keys:
            call_id = key.replace("CALL_SESSION:", "")
            session = redis_service.get_call_session(call_id)
            if session:
                print(f"   📞 Call ID: {call_id}")
                print(f"      Status: {session.status}")
                print(f"      Phone: {session.phone_number}")
                print(f"      Request ID: {session.request_id}")
                
                # Step 4: Test webhook with the ACTUAL call_id
                print(f"\n4. 🔗 Testing Webhook with Real Call ID: {call_id}")
                
                webhook_data = {
                    'CallSid': 'CA1234567890abcdef',
                    'CallStatus': 'in-progress',
                    'From': session.phone_number,
                    'To': '+19787652012'
                }
                
                webhook_response = requests.post(
                    f"{base_url}/api/calls/webhook/{call_id}", 
                    data=webhook_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                print(f"   Webhook Status: {webhook_response.status_code}")
                print(f"   Webhook Response: {webhook_response.text[:200]}...")
                
                if webhook_response.status_code == 200:
                    print("   ✅ Webhook successful!")
                    
                    # Step 5: Test speech input
                    print(f"\n5. 🎤 Testing Speech Input...")
                    speech_data = {
                        'SpeechResult': 'Hello, I worked at ABC Company from 2020 to 2023'
                    }
                    
                    speech_response = requests.post(
                        f"{base_url}/api/calls/webhook/{call_id}/gather", 
                        data=speech_data,
                        headers={'Content-Type': 'application/x-www-form-urlencoded'}
                    )
                    
                    print(f"   Speech Status: {speech_response.status_code}")
                    print(f"   Speech Response: {speech_response.text[:200]}...")
                    
                    if "I'm sorry, there was an error" in speech_response.text:
                        print("   ❌ Speech processing failed - this is the APPLICATION ERROR!")
                        print("   🔍 The error is in the speech processing logic")
                    else:
                        print("   ✅ Speech processing successful!")
                else:
                    print("   ❌ Webhook failed!")
                
                break
        
        if not keys:
            print("❌ No call sessions found in Redis!")
            print("   This means the background task to initiate calls is not working.")
            
    except Exception as e:
        print(f"❌ Redis error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS:")
    print("   If you see 'I'm sorry, there was an error' in speech processing,")
    print("   that's your APPLICATION ERROR. The issue is in the phone agent")
    print("   or session retrieval logic, not the webhook itself.")

if __name__ == "__main__":
    debug_application_error()
