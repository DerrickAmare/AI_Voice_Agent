#!/usr/bin/env python3
"""
Test the Twilio webhook endpoints that are causing the application error
"""

import requests
import json
from datetime import datetime

def test_twilio_webhook():
    """Test the Twilio webhook endpoints directly"""
    print("🔧 Testing Twilio Webhook Endpoints...")
    
    base_url = "http://localhost:8000"
    
    # Test 1: Submit a resume request first
    print("\n1. Submitting a test resume request...")
    
    form_data = {
        'phoneNumber': '(212) 555-1234',
        'fullName': 'Test User',
        'email': 'test@example.com',
        'callTime': 'immediate'
    }
    
    try:
        response = requests.post(f"{base_url}/api/submit-request", data=form_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            request_id = result.get('requestId')
            print(f"   ✅ Request submitted: {request_id}")
        else:
            print(f"   ❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Request error: {e}")
        return False
    
    # Wait a moment for background processing
    import time
    time.sleep(2)
    
    # Test 2: Simulate Twilio webhook call
    print("\n2. Simulating Twilio webhook call...")
    
    # This simulates what Twilio sends when a call is initiated
    webhook_data = {
        'CallSid': 'CA1234567890abcdef',
        'CallStatus': 'in-progress',
        'From': '+15551234567',
        'To': '+19787652012'
    }
    
    # Find a call_id from Redis (this would normally be generated)
    call_id = "test_call_webhook"
    
    try:
        response = requests.post(
            f"{base_url}/api/calls/webhook/{call_id}", 
            data=webhook_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("   ✅ Webhook processed successfully")
        else:
            print(f"   ❌ Webhook failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Webhook error: {e}")
        return False
    
    # Test 3: Simulate speech input
    print("\n3. Simulating speech input...")
    
    speech_data = {
        'SpeechResult': 'Hello, I worked at ABC Company from 2020 to 2023'
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/calls/webhook/{call_id}/gather", 
            data=speech_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("   ✅ Speech processing successful")
        else:
            print(f"   ❌ Speech processing failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Speech processing error: {e}")
        return False
    
    print("\n🎉 All webhook tests passed!")
    return True

if __name__ == "__main__":
    print("🚨 Make sure the server is running on http://localhost:8000")
    print("   Run: python main.py")
    print()
    
    try:
        # Test if server is running
        response = requests.get("http://localhost:8000/health", timeout=5)
        print("✅ Server is running")
    except:
        print("❌ Server is not running or not responding")
        print("   Start the server first: python main.py")
        exit(1)
    
    result = test_twilio_webhook()
    if result:
        print("\n✅ All webhook tests passed! The issue might be in the actual Twilio integration.")
    else:
        print("\n❌ Webhook tests failed. This is likely where the application error occurs.")
