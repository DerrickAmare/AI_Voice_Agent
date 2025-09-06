#!/usr/bin/env python3
"""
Example usage of the Voice AI Resume Builder Agent System
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_agent_system():
    """Test the complete agent system workflow"""
    
    print("🤖 Testing Voice AI Resume Builder Agent System")
    print("=" * 50)
    
    # Test 1: Get agent information
    print("\n1. Getting agent information...")
    try:
        response = requests.get(f"{BASE_URL}/api/agents/info")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data.get('total_agents', 0)} agents:")
            for agent in data.get('agents', []):
                print(f"   - {agent['name']}: {agent['role']}")
        else:
            print(f"❌ Failed to get agent info: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Start agent conversation
    print("\n2. Starting agent conversation...")
    session_id = "test_session_123"
    
    try:
        response = requests.post(f"{BASE_URL}/api/agents/start", json={
            "session_id": session_id,
            "target_role": "Software Engineer",
            "industry": "Technology"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Session started: {data.get('session_id')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Stage: {data.get('stage')}")
        else:
            print(f"❌ Failed to start session: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Continue conversation
    print("\n3. Continuing conversation...")
    conversation_inputs = [
        "I'm John Smith, a software engineer with 5 years of experience",
        "I work with Python, JavaScript, and React",
        "I have a Bachelor's degree in Computer Science from MIT",
        "I've led a team of 5 developers and increased productivity by 30%"
    ]
    
    for i, user_input in enumerate(conversation_inputs, 1):
        print(f"\n   Input {i}: {user_input}")
        try:
            response = requests.post(f"{BASE_URL}/api/agents/continue", json={
                "session_id": session_id,
                "user_input": user_input
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Response: {data.get('message', '')[:100]}...")
                print(f"   Stage: {data.get('stage')}")
                
                if data.get('is_complete'):
                    print("   🎉 Conversation completed!")
                    break
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(1)  # Small delay between requests
    
    # Test 4: Get session status
    print("\n4. Getting session status...")
    try:
        response = requests.get(f"{BASE_URL}/api/agents/status/{session_id}")
        if response.status_code == 200:
            data = response.json()
            status = data.get('session_status', {})
            print(f"✅ Session Status:")
            print(f"   Stage: {status.get('stage')}")
            print(f"   Completeness: {status.get('resume_completeness', 0)}%")
            print(f"   Has Analysis: {status.get('has_analysis')}")
            print(f"   Has Optimized Content: {status.get('has_optimized_content')}")
        else:
            print(f"❌ Failed to get status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Format resume
    print("\n5. Formatting resume...")
    try:
        response = requests.post(f"{BASE_URL}/api/agents/format", json={
            "session_id": session_id,
            "format": "html"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Resume formatted successfully!")
            print(f"   Format: {data.get('formatted_resume', {}).get('format')}")
            print(f"   Download ready: {data.get('download_ready')}")
        else:
            print(f"❌ Failed to format: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Agent system test completed!")

def test_health_check():
    """Test basic health check"""
    print("\n🏥 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Application is healthy")
            print(f"   Voice service available: {data.get('voice_service_available')}")
            print(f"   Active sessions: {data.get('active_sessions')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Voice AI Resume Builder - Agent System Test")
    print("Make sure the application is running on http://localhost:8000")
    print()
    
    # Test health first
    test_health_check()
    
    # Test agent system
    test_agent_system()
    
    print("\n💡 Tips:")
    print("- Set OPENAI_API_KEY in .env for full agent functionality")
    print("- Install audio dependencies for voice features")
    print("- Check the documentation for more examples")
