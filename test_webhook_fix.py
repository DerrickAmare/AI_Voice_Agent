#!/usr/bin/env python3
"""
Test script to verify the webhook fix works properly
"""

import requests
import sys

def test_webhook_endpoints(base_url):
    """Test the fixed webhook endpoints"""
    print("🧪 Testing Fixed Webhook Endpoints")
    print("=" * 50)
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    test_call_id = "test_call_123"
    
    # Test 1: Test TwiML generation endpoint
    print("1️⃣ Testing TwiML generation...")
    try:
        response = requests.post(f"{base_url}/api/test-twiml/{test_call_id}")
        if response.status_code == 200:
            print(f"✅ TwiML test passed: {response.status_code}")
            print(f"📄 Response content type: {response.headers.get('content-type')}")
            print(f"📄 TwiML preview: {response.text[:200]}...")
        else:
            print(f"❌ TwiML test failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
    except Exception as e:
        print(f"❌ TwiML test error: {e}")
    
    # Test 2: Test main webhook endpoint (simulating Twilio call) - POST
    print("\n2️⃣ Testing main webhook endpoint (POST)...")
    try:
        form_data = {
            'CallSid': 'CA1234567890abcdef1234567890abcdef',
            'CallStatus': 'in-progress',
            'From': '+1234567890',
            'To': '+0987654321'
        }
        
        response = requests.post(
            f"{base_url}/api/calls/webhook/{test_call_id}",
            data=form_data
        )
        
        if response.status_code == 200:
            print(f"✅ Main webhook POST passed: {response.status_code}")
            print(f"📄 Response content type: {response.headers.get('content-type')}")
            if 'xml' in response.headers.get('content-type', '').lower():
                print(f"📄 TwiML preview: {response.text[:300]}...")
                # Check for XML declaration
                if response.text.startswith('<?xml'):
                    print("✅ XML declaration present")
                else:
                    print("⚠️  XML declaration missing")
            else:
                print(f"📄 Response: {response.text}")
        else:
            print(f"❌ Main webhook POST failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
    except Exception as e:
        print(f"❌ Main webhook POST error: {e}")
    
    # Test 2b: Test main webhook endpoint with GET (avoid 405)
    print("\n2️⃣b Testing main webhook endpoint (GET)...")
    try:
        response = requests.get(f"{base_url}/api/calls/webhook/{test_call_id}")
        
        if response.status_code == 200:
            print(f"✅ Main webhook GET passed: {response.status_code}")
            print(f"📄 Response content type: {response.headers.get('content-type')}")
        else:
            print(f"❌ Main webhook GET failed: {response.status_code}")
            if response.status_code == 405:
                print("⚠️  405 Method Not Allowed - this would cause Twilio errors!")
    except Exception as e:
        print(f"❌ Main webhook GET error: {e}")
    
    # Test 3: Test gather endpoint (simulating user speech)
    print("\n3️⃣ Testing gather endpoint...")
    try:
        form_data = {
            'CallSid': 'CA1234567890abcdef1234567890abcdef',
            'SpeechResult': 'yes I consent',
            'Confidence': '0.9'
        }
        
        response = requests.post(
            f"{base_url}/api/calls/webhook/{test_call_id}/gather",
            data=form_data
        )
        
        if response.status_code == 200:
            print(f"✅ Gather endpoint passed: {response.status_code}")
            print(f"📄 Response content type: {response.headers.get('content-type')}")
            if 'xml' in response.headers.get('content-type', '').lower():
                print(f"📄 TwiML preview: {response.text[:300]}...")
            else:
                print(f"📄 Response: {response.text}")
        else:
            print(f"❌ Gather endpoint failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
    except Exception as e:
        print(f"❌ Gather endpoint error: {e}")
    
    # Test 4: Test status callback
    print("\n4️⃣ Testing status callback...")
    try:
        form_data = {
            'CallSid': 'CA1234567890abcdef1234567890abcdef',
            'CallStatus': 'completed',
            'CallDuration': '45'
        }
        
        response = requests.post(
            f"{base_url}/api/calls/webhook/{test_call_id}/status",
            data=form_data
        )
        
        if response.status_code == 200:
            print(f"✅ Status callback passed: {response.status_code}")
        else:
            print(f"❌ Status callback failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status callback error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("If all tests passed (✅), your webhook should work with Twilio!")
    print("The key fixes applied:")
    print("• Fixed Content-Type: Proper application/xml with UTF-8 charset")
    print("• Added XML declaration: <?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    print("• Fixed 405 errors: All webhook routes accept both GET and POST")
    print("• Proper TwiML formatting: Always returns valid <Response> wrapper")
    print("• Restored speechTimeout='auto' (confirmed working on your trial)")
    print("• Added proper voice='alice' and language='en-US' settings")
    print("• Comprehensive error handling with valid TwiML fallbacks")
    print("• Status=200 explicitly set with proper headers")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_webhook_fix.py <base_url>")
        print("Example: python test_webhook_fix.py http://localhost:8000")
        print("Example: python test_webhook_fix.py https://abcd1234.ngrok-free.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    test_webhook_endpoints(base_url)
