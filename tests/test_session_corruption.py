#!/usr/bin/env python3
"""
Test for session corruption issues that might cause application error
"""

import requests
import sys
import os

# Add src to path
sys.path.append('src')

from services.redis_state_service import RedisStateService

def test_session_corruption():
    """Test for session corruption that might cause application error"""
    print("🔍 Testing Session Corruption Issues...")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    redis_service = RedisStateService("redis://localhost:6379")
    
    # Find your active call session
    print("\n1. 🔍 Finding your active call session...")
    
    keys = redis_service.redis_client.keys("CALL_SESSION:*")
    your_call_id = None
    
    for key in keys:
        call_id = key.replace("CALL_SESSION:", "")
        session = redis_service.get_call_session(call_id)
        if session and session.phone_number == "+17209545909":
            your_call_id = call_id
            print(f"✅ Found call session: {call_id}")
            print(f"   Status: {session.status}")
            print(f"   Request ID: {session.request_id}")
            print(f"   Conversation State: {session.conversation_state}")
            break
    
    if not your_call_id:
        print("❌ No active call session found")
        return
    
    # Test different speech inputs that might cause errors
    test_inputs = [
        "",  # Empty input
        "   ",  # Whitespace only
        "I don't know",  # Evasive response
        "What?",  # Confused response
        "No",  # Negative response
        "Stop calling me",  # Hostile response
        "A" * 1000,  # Very long input
        "🎉💯🔥",  # Emoji input
    ]
    
    print(f"\n2. 🧪 Testing various speech inputs that might cause errors...")
    
    for i, speech_input in enumerate(test_inputs):
        print(f"\n   Test {i+1}: '{speech_input[:50]}{'...' if len(speech_input) > 50 else ''}'")
        
        speech_data = {
            'SpeechResult': speech_input
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/calls/webhook/{your_call_id}/gather", 
                data=speech_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if "I'm sorry, there was an error" in response.text:
                print(f"   ❌ APPLICATION ERROR with input: '{speech_input}'")
                print(f"   This input causes the error you heard!")
                return speech_input
            else:
                print(f"   ✅ Handled correctly")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n3. 🔍 Testing session state corruption...")
    
    # Test what happens if session gets corrupted
    session = redis_service.get_call_session(your_call_id)
    if session:
        # Temporarily corrupt the session
        redis_service.update_call_session(your_call_id, {
            "conversation_state": None  # This might cause issues
        })
        
        speech_data = {'SpeechResult': 'Test with corrupted state'}
        
        try:
            response = requests.post(
                f"{base_url}/api/calls/webhook/{your_call_id}/gather", 
                data=speech_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if "I'm sorry, there was an error" in response.text:
                print("❌ Corrupted session state causes application error!")
                
                # Restore the session
                redis_service.update_call_session(your_call_id, {
                    "conversation_state": {}
                })
                
                return "corrupted_session"
            else:
                print("✅ Handles corrupted session gracefully")
                
        except Exception as e:
            print(f"❌ Exception with corrupted session: {e}")
    
    print("\n✅ No session corruption issues found")
    return None

if __name__ == "__main__":
    error_cause = test_session_corruption()
    
    if error_cause:
        print(f"\n🎯 FOUND THE ISSUE: {error_cause}")
        print("   This is what's causing the 'application error' during phone calls!")
    else:
        print("\n🤔 No obvious issues found in testing")
        print("   The application error might be intermittent or environment-specific")
