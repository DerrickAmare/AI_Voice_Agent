#!/usr/bin/env python3
"""
Test script to isolate phone call integration issues
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append('src')

from services.redis_state_service import RedisStateService
from agents.phone_conversation_agent import PhoneConversationAgent

async def test_phone_integration():
    """Test the phone integration components individually"""
    print("🔧 Testing Phone Integration Components...")
    
    try:
        # Test 1: Redis Connection
        print("\n1. Testing Redis Connection...")
        redis_service = RedisStateService("redis://localhost:6379")
        health = redis_service.health_check()
        print(f"   Redis Status: {health['status']}")
        if health['status'] != 'healthy':
            print(f"   ❌ Redis Error: {health.get('error', 'Unknown')}")
            return False
        print("   ✅ Redis OK")
        
        # Test 2: Create Call Session with request_id
        print("\n2. Testing Call Session Creation...")
        call_id = "test_call_123"
        request_id = "test_req_456"
        
        session = redis_service.create_call_session(
            call_id=call_id,
            phone_number="+15551234567",
            consent_given=True,
            request_id=request_id  # This was the missing field!
        )
        print(f"   ✅ Call Session Created: {session.call_id}")
        print(f"   ✅ Request ID Linked: {session.request_id}")
        
        # Test 3: Retrieve Call Session
        print("\n3. Testing Call Session Retrieval...")
        retrieved_session = redis_service.get_call_session(call_id)
        if retrieved_session and retrieved_session.request_id == request_id:
            print("   ✅ Call Session Retrieved with request_id")
        else:
            print("   ❌ Call Session retrieval failed")
            return False
        
        # Test 4: Phone Conversation Agent
        print("\n4. Testing Phone Conversation Agent...")
        phone_agent = PhoneConversationAgent()
        
        test_input = {
            "user_input": "Hello, I worked at ABC Company from 2020 to 2023",
            "call_metadata": {
                "call_id": call_id,
                "conversation_state": {}
            }
        }
        
        response = phone_agent.process(test_input)
        print(f"   Agent Response: {response.success}")
        print(f"   Message: {response.message[:100]}...")
        if response.success:
            print("   ✅ Phone Agent OK")
        else:
            print("   ❌ Phone Agent Failed")
            return False
        
        # Test 5: Resume Request Storage
        print("\n5. Testing Resume Request Storage...")
        request_data = {
            "request_id": request_id,
            "phone_number": "+15551234567",
            "full_name": "Test User",
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        stored = redis_service.store_resume_request(request_id, request_data)
        if stored:
            print("   ✅ Resume Request Stored")
        else:
            print("   ❌ Resume Request Storage Failed")
            return False
        
        # Test 6: Resume Request Retrieval
        print("\n6. Testing Resume Request Retrieval...")
        retrieved_request = redis_service.get_resume_request(request_id)
        if retrieved_request and retrieved_request['request_id'] == request_id:
            print("   ✅ Resume Request Retrieved")
        else:
            print("   ❌ Resume Request Retrieval Failed")
            return False
        
        # Cleanup
        redis_service.delete_call_session(call_id)
        print("\n🎉 All Tests Passed! Phone integration should work.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test Failed with Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_phone_integration())
    if result:
        print("\n✅ Phone integration is working correctly!")
        print("The issue might be elsewhere. Check the server logs for the actual error.")
    else:
        print("\n❌ Phone integration has issues that need to be fixed.")
