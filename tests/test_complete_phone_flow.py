#!/usr/bin/env python3
"""
Complete phone call flow test with the new AI conversation manager
Tests the entire pipeline from form submission to phone call completion
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def test_complete_flow():
    """Test the complete phone call flow"""
    print("🚀 Testing Complete Phone Call Flow")
    print("=" * 50)
    
    base_url = "https://f1902accb1c3.ngrok-free.app"
    phone_number = "+17209545909"  # Your verified number
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Submit a resume request
        print("1️⃣ Submitting resume request...")
        
        form_data = aiohttp.FormData()
        form_data.add_field('phoneNumber', phone_number)
        form_data.add_field('fullName', 'Test User')
        form_data.add_field('email', 'test@example.com')
        form_data.add_field('callTime', 'immediate')
        
        try:
            async with session.post(f"{base_url}/api/submit-request", data=form_data) as response:
                if response.status == 200:
                    result = await response.json()
                    request_id = result.get('requestId')
                    print(f"✅ Request submitted successfully: {request_id}")
                else:
                    print(f"❌ Request submission failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Request submission error: {e}")
            return
        
        # Step 2: Wait a bit for call initiation
        print("2️⃣ Waiting for call initiation...")
        await asyncio.sleep(15)
        
        # Step 3: Check request status
        print("3️⃣ Checking request status...")
        try:
            async with session.get(f"{base_url}/api/request-status/{request_id}") as response:
                if response.status == 200:
                    status_data = await response.json()
                    print(f"✅ Request status: {status_data.get('status')}")
                else:
                    print(f"❌ Status check failed: {response.status}")
        except Exception as e:
            print(f"❌ Status check error: {e}")
        
        # Step 4: Test webhook endpoints directly
        print("4️⃣ Testing webhook endpoints...")
        
        # Create a test call session first
        call_id = f"test_{int(time.time())}"
        
        # Test main webhook
        webhook_data = {
            "CallStatus": "in-progress",
            "CallSid": f"CA{call_id}",
            "From": phone_number,
            "To": "+19787652012"
        }
        
        try:
            async with session.post(f"{base_url}/api/calls/webhook/{call_id}", data=webhook_data) as response:
                if response.status == 200:
                    twiml_response = await response.text()
                    print(f"✅ Webhook response received")
                    print(f"📄 TwiML: {twiml_response[:100]}...")
                    
                    # Check if it's valid TwiML
                    if "<?xml" in twiml_response or "<Response>" in twiml_response:
                        print("✅ Valid TwiML generated")
                    else:
                        print("❌ Invalid TwiML response")
                else:
                    print(f"❌ Webhook failed: {response.status}")
        except Exception as e:
            print(f"❌ Webhook error: {e}")
        
        # Step 5: Test speech processing
        print("5️⃣ Testing speech processing...")
        
        speech_data = {
            "SpeechResult": "Yes, I consent to continue. I worked at ABC Company from 2020 to 2023 as a software engineer.",
            "CallSid": f"CA{call_id}",
            "CallStatus": "in-progress"
        }
        
        try:
            async with session.post(f"{base_url}/api/calls/webhook/{call_id}/gather", data=speech_data) as response:
                if response.status == 200:
                    twiml_response = await response.text()
                    print(f"✅ Speech processing successful")
                    print(f"📄 AI Response TwiML: {twiml_response[:200]}...")
                    
                    # Check for AI-generated response
                    if "<Say>" in twiml_response and len(twiml_response) > 100:
                        print("✅ AI conversation response generated")
                    else:
                        print("❌ No AI response in TwiML")
                else:
                    print(f"❌ Speech processing failed: {response.status}")
        except Exception as e:
            print(f"❌ Speech processing error: {e}")
        
        # Step 6: Test multiple conversation turns
        print("6️⃣ Testing conversation flow...")
        
        conversation_inputs = [
            "I worked at XYZ Corp from 2018 to 2020 as a manager",
            "Before that I was at DEF Inc from 2015 to 2018 doing sales",
            "I have a bachelor's degree in business from State University",
            "My skills include leadership, communication, and project management"
        ]
        
        for i, user_input in enumerate(conversation_inputs):
            print(f"   Turn {i+1}: Testing with '{user_input[:50]}...'")
            
            speech_data = {
                "SpeechResult": user_input,
                "CallSid": f"CA{call_id}",
                "CallStatus": "in-progress"
            }
            
            try:
                async with session.post(f"{base_url}/api/calls/webhook/{call_id}/gather", data=speech_data) as response:
                    if response.status == 200:
                        twiml_response = await response.text()
                        
                        # Extract the AI response from TwiML
                        if "<Say>" in twiml_response:
                            start = twiml_response.find("<Say>") + 5
                            end = twiml_response.find("</Say>")
                            if end > start:
                                ai_response = twiml_response[start:end]
                                print(f"   🤖 AI: {ai_response[:100]}...")
                        
                        # Check if conversation is complete
                        if "Thank you" in twiml_response and "Goodbye" in twiml_response:
                            print("   ✅ Conversation completed naturally")
                            break
                    else:
                        print(f"   ❌ Turn {i+1} failed: {response.status}")
            except Exception as e:
                print(f"   ❌ Turn {i+1} error: {e}")
            
            await asyncio.sleep(2)  # Brief pause between turns
        
        print("\n" + "=" * 50)
        print("🎉 Complete phone flow test finished!")
        print("Check the server logs for detailed information.")

if __name__ == "__main__":
    asyncio.run(test_complete_flow())
