#!/usr/bin/env python3
"""
Test script to verify Twilio webhook endpoints are working
Run this after starting the Flask app and ngrok
"""

import requests
import sys

def test_webhook_endpoints(ngrok_url):
    """Test the webhook endpoints with curl-like requests"""
    print("🧪 Testing Twilio Webhook Endpoints")
    print("=" * 50)
    
    # Remove trailing slash if present
    base_url = ngrok_url.rstrip('/')
    
    # Test 1: Health check
    print("1️⃣ Testing health check endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print(f"✅ Health check passed: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Test endpoint
    print("\n2️⃣ Testing test endpoint...")
    try:
        response = requests.get(f"{base_url}/test")
        if response.status_code == 200:
            print(f"✅ Test endpoint passed: {response.json()}")
        else:
            print(f"❌ Test endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Test endpoint error: {e}")
    
    # Test 3: Call webhook (main endpoint)
    print("\n3️⃣ Testing call webhook endpoint...")
    test_call_id = "test_call_123"
    try:
        # Simulate Twilio's POST request
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
            print(f"✅ Call webhook passed: {response.status_code}")
            print(f"📄 Response content type: {response.headers.get('content-type')}")
            print(f"📄 Response preview: {response.text[:200]}...")
        else:
            print(f"❌ Call webhook failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
    except Exception as e:
        print(f"❌ Call webhook error: {e}")
    
    # Test 4: Status callback endpoint
    print("\n4️⃣ Testing status callback endpoint...")
    try:
        # Simulate Twilio's status callback
        status_data = {
            'CallSid': 'CA1234567890abcdef1234567890abcdef',
            'CallStatus': 'completed',
            'CallDuration': '45',
            'From': '+1234567890',
            'To': '+0987654321'
        }
        
        response = requests.post(
            f"{base_url}/api/calls/webhook/{test_call_id}/status",
            data=status_data
        )
        
        if response.status_code == 200:
            print(f"✅ Status callback passed: {response.status_code}")
        else:
            print(f"❌ Status callback failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
    except Exception as e:
        print(f"❌ Status callback error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("If all tests passed (✅), your webhook endpoints are ready!")
    print("You can now update your Twilio call URLs to use this ngrok URL.")
    print("\n📋 Example Twilio call configuration:")
    print(f"   url: {base_url}/api/calls/webhook/call_b7b44f018f2b")
    print(f"   status_callback: {base_url}/api/calls/webhook/call_b7b44f018f2b/status")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_webhook_endpoints.py <ngrok_url>")
        print("Example: python test_webhook_endpoints.py https://abcd1234.ngrok-free.app")
        sys.exit(1)
    
    ngrok_url = sys.argv[1]
    test_webhook_endpoints(ngrok_url)
