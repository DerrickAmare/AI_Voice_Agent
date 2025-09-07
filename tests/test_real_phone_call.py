#!/usr/bin/env python3
"""
Test a real phone call to verify the system is working
"""

import requests
import time
import json

def test_real_phone_call():
    """Test with a real phone call"""
    print("📞 Testing Real Phone Call")
    print("=" * 40)
    
    base_url = "https://YOUR_NGROK_URL_HERE.ngrok-free.app"  # Update this with your current ngrok URL
    phone_number = "+17209545909"  # Your verified number
    
    # Step 1: Submit a resume request that will trigger a real call
    print("1️⃣ Submitting resume request for immediate call...")
    
    form_data = {
        'phoneNumber': phone_number,
        'fullName': 'Test User',
        'email': 'test@example.com',
        'callTime': 'immediate'
    }
    
    try:
        response = requests.post(f"{base_url}/api/submit-request", data=form_data)
        if response.status_code == 200:
            result = response.json()
            request_id = result.get('requestId')
            print(f"✅ Request submitted successfully: {request_id}")
            print(f"📱 A real phone call should be initiated to {phone_number} in ~10 seconds")
        else:
            print(f"❌ Request submission failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Request submission error: {e}")
        return
    
    # Step 2: Monitor the request status
    print("\n2️⃣ Monitoring request status...")
    
    for i in range(12):  # Monitor for 2 minutes
        try:
            response = requests.get(f"{base_url}/api/request-status/{request_id}")
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                print(f"   Status update {i+1}: {status}")
                
                if status == "completed":
                    print("🎉 Call completed successfully!")
                    break
                elif status == "failed":
                    print("❌ Call failed")
                    break
            else:
                print(f"   Status check failed: {response.status_code}")
        except Exception as e:
            print(f"   Status check error: {e}")
        
        time.sleep(10)  # Check every 10 seconds
    
    print("\n" + "=" * 40)
    print("📞 Real phone call test completed!")
    print("If you received the call, the system is working perfectly!")

if __name__ == "__main__":
    test_real_phone_call()
