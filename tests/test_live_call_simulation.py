#!/usr/bin/env python3
"""
Simulate exactly what happens during a live phone call to find the application error
"""

import requests
import time
import sys
import os

# Add src to path
sys.path.append('src')

from services.redis_state_service import RedisStateService

def simulate_live_call():
    """Simulate the exact sequence that happens during a live call"""
    print("🔍 Simulating Live Phone Call Sequence...")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    redis_service = RedisStateService("redis://localhost:6379")
    
    # Step 1: Find the most recent call session for your number
    print("\n1. 🔍 Finding your recent call session...")
    
    keys = redis_service.redis_client.keys("CALL_SESSION:*")
    your_session = None
    your_call_id = None
    
    for key in keys:
        call_id = key.replace("CALL_SESSION:", "")
        session = redis_service.get_call_session(call_id)
        if session and session.phone_number == "+17209545909":
            your_session = session
            your_call_id = call_id
            print(f"✅ Found your call session:")
            print(f"   📞 Call ID: {call_id}")
            print(f"   📱 Phone: {session.phone_number}")
            print(f"   📊 Status: {session.status}")
            print(f"   🔗 Twilio SID: {session.twilio_call_sid}")
            break
    
    if not your_session:
        print("❌ No call session found for +17209545909")
        print("   Submit a new request first")
        return
    
    # Step 2: Simulate Twilio calling the webhook when call connects
    print(f"\n2. 📞 Simulating call connection webhook...")
    
    webhook_data = {
        'CallSid': your_session.twilio_call_sid or 'CA_test_call_sid',
        'CallStatus': 'in-progress',
        'From': '+17209545909',
        'To': '+19787652012'
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/calls/webhook/{your_call_id}", 
            data=webhook_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"   Webhook Status: {response.status_code}")
        print(f"   Webhook Response: {response.text[:300]}...")
        
        if response.status_code != 200:
            print("❌ Webhook failed!")
            return
        
        if "Hello! I'm calling to learn about your work experience" in response.text:
            print("✅ Initial greeting working correctly")
        else:
            print("❌ Unexpected webhook response")
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return
    
    # Step 3: Simulate user saying "Yes" to consent
    print(f"\n3. 🎤 Simulating user consent ('Yes')...")
    
    speech_data = {
        'SpeechResult': 'Yes'
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/calls/webhook/{your_call_id}/gather", 
            data=speech_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"   Speech Status: {response.status_code}")
        print(f"   Speech Response: {response.text[:300]}...")
        
        if "I'm sorry, there was an error" in response.text:
            print("❌ THIS IS THE APPLICATION ERROR!")
            print("   The error occurs when processing speech input")
            print("   Let me check what's wrong...")
            
            # Check the session state
            updated_session = redis_service.get_call_session(your_call_id)
            if updated_session:
                print(f"   Session Status: {updated_session.status}")
                print(f"   Conversation State: {updated_session.conversation_state}")
                print(f"   Request ID: {updated_session.request_id}")
            else:
                print("   ❌ Session not found - this might be the issue!")
            
        else:
            print("✅ Speech processing working correctly!")
            print("   The AI should continue the conversation")
            
    except Exception as e:
        print(f"❌ Speech processing error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS:")
    print("   If you see 'I'm sorry, there was an error' above,")
    print("   that's exactly what you heard on the phone!")

if __name__ == "__main__":
    simulate_live_call()
