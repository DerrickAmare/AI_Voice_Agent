#!/usr/bin/env python3
"""
Test OpenAI integration to see if that's causing the application error
"""

import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add src to path
sys.path.append('src')

from agents.phone_conversation_agent import PhoneConversationAgent

def test_openai_integration():
    """Test if OpenAI API calls are working"""
    print("🔍 Testing OpenAI Integration...")
    print("=" * 60)
    
    # Check if API key is configured
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    if api_key.startswith("sk-"):
        print(f"✅ OpenAI API key configured: {api_key[:20]}...")
    else:
        print("❌ Invalid OpenAI API key format")
        return False
    
    # Test the phone conversation agent
    print("\n2. 🤖 Testing Phone Conversation Agent...")
    
    try:
        phone_agent = PhoneConversationAgent()
        print("✅ Phone agent initialized")
        
        # Test with simple input
        test_input = {
            "user_input": "Yes, I consent to continue",
            "call_metadata": {
                "call_id": "test_call_123",
                "conversation_state": {}
            }
        }
        
        print("\n3. 🎤 Testing speech processing...")
        response = phone_agent.process(test_input)
        
        print(f"   Success: {response.success}")
        print(f"   Message: {response.message}")
        print(f"   Next Action: {response.next_action}")
        print(f"   Confidence: {response.confidence}")
        
        if response.success:
            print("✅ OpenAI integration working!")
            return True
        else:
            print("❌ Phone agent processing failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing phone agent: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_base_agent_openai():
    """Test the base agent OpenAI call directly"""
    print("\n4. 🧠 Testing Base Agent OpenAI Call...")
    
    try:
        from agents.base_agent import BaseAgent
        
        # Create a simple test agent
        test_agent = BaseAgent(
            name="TestAgent",
            role="Test",
            system_prompt="You are a test agent. Respond with 'Hello, test successful!'"
        )
        
        response = test_agent.call_openai("Say hello")
        print(f"   OpenAI Response: {response[:100]}...")
        
        if response and len(response) > 0:
            print("✅ Direct OpenAI call working!")
            return True
        else:
            print("❌ OpenAI call returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OpenAI: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚨 Testing OpenAI Integration - This might be causing the application error")
    print()
    
    openai_ok = test_openai_integration()
    base_ok = test_base_agent_openai()
    
    if openai_ok and base_ok:
        print("\n🎉 OpenAI integration is working correctly!")
        print("   The application error must be something else.")
    else:
        print("\n❌ OpenAI integration has issues!")
        print("   This is likely causing the 'application error' during phone calls.")
        print("   Check your OPENAI_API_KEY and internet connection.")
