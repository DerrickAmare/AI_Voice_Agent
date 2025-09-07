#!/usr/bin/env python3
"""
Real-time call monitoring and debugging script
Monitors all aspects of the phone call flow to identify application errors
"""

import asyncio
import aiohttp
import json
import logging
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Set up comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'call_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

class CallMonitor:
    """Monitor all aspects of phone call flow"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.active_calls = {}
        
    async def monitor_webhook_accessibility(self):
        """Test if webhooks are accessible from external sources"""
        logger.info("🔍 Testing webhook accessibility...")
        
        test_endpoints = [
            "/health",
            "/api/calls/initiate",
            "/metrics"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in test_endpoints:
                url = f"{self.base_url}{endpoint}"
                try:
                    async with session.get(url, timeout=10) as response:
                        status = response.status
                        logger.info(f"✅ {endpoint}: {status}")
                        if status != 200 and endpoint == "/health":
                            logger.error(f"❌ Health check failed: {status}")
                except Exception as e:
                    logger.error(f"❌ {endpoint}: {e}")
    
    async def test_webhook_endpoints(self, call_id: str = "test_call_123"):
        """Test webhook endpoints with mock data"""
        logger.info(f"🔍 Testing webhook endpoints for call_id: {call_id}")
        
        # Test main webhook endpoint
        webhook_url = f"{self.base_url}/api/calls/webhook/{call_id}"
        
        # Mock Twilio webhook data
        test_data = {
            "CallStatus": "in-progress",
            "CallSid": f"CA{call_id}",
            "From": "+17209545909",
            "To": "+19787652012"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(webhook_url, data=test_data, timeout=10) as response:
                    status = response.status
                    content = await response.text()
                    logger.info(f"📞 Webhook response: {status}")
                    logger.info(f"📄 TwiML content: {content[:200]}...")
                    
                    # Validate TwiML
                    if "<?xml" in content or "<Response>" in content:
                        logger.info("✅ Valid TwiML response generated")
                    else:
                        logger.error("❌ Invalid TwiML response")
                        
            except Exception as e:
                logger.error(f"❌ Webhook test failed: {e}")
    
    async def test_speech_processing(self, call_id: str = "test_call_123"):
        """Test speech input processing"""
        logger.info(f"🎤 Testing speech processing for call_id: {call_id}")
        
        gather_url = f"{self.base_url}/api/calls/webhook/{call_id}/gather"
        
        # Mock speech input
        test_speech_data = {
            "SpeechResult": "I worked at ABC Company from 2020 to 2023 as a manager",
            "CallSid": f"CA{call_id}",
            "CallStatus": "in-progress"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(gather_url, data=test_speech_data, timeout=30) as response:
                    status = response.status
                    content = await response.text()
                    logger.info(f"🎤 Speech processing response: {status}")
                    logger.info(f"📄 TwiML response: {content[:200]}...")
                    
                    # Check for OpenAI processing
                    if "say" in content.lower():
                        logger.info("✅ AI response generated successfully")
                    else:
                        logger.error("❌ No AI response in TwiML")
                        
            except Exception as e:
                logger.error(f"❌ Speech processing failed: {e}")
    
    async def monitor_redis_operations(self, call_id: str = "test_call_123"):
        """Monitor Redis operations during call"""
        logger.info(f"💾 Monitoring Redis operations for call_id: {call_id}")
        
        try:
            # Check if Redis is accessible
            self.redis_client.ping()
            logger.info("✅ Redis connection successful")
            
            # Check for call session
            session_key = f"call_session:{call_id}"
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                session = json.loads(session_data)
                logger.info(f"📊 Call session found: {session.get('status', 'unknown')}")
                logger.info(f"📊 Conversation state: {bool(session.get('conversation_state'))}")
            else:
                logger.warning(f"⚠️ No session found for {call_id}")
                
            # Monitor Redis keys
            all_keys = self.redis_client.keys("call_session:*")
            logger.info(f"📊 Total active call sessions: {len(all_keys)}")
            
        except Exception as e:
            logger.error(f"❌ Redis monitoring failed: {e}")
    
    async def test_openai_integration(self):
        """Test OpenAI API integration"""
        logger.info("🤖 Testing OpenAI integration...")
        
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            
            # Test simple API call
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            
            logger.info("✅ OpenAI API connection successful")
            logger.info(f"🤖 Response: {response.choices[0].message.content}")
            
        except Exception as e:
            logger.error(f"❌ OpenAI integration failed: {e}")
    
    async def check_twilio_logs(self, call_sid: str = None):
        """Check Twilio logs for errors"""
        logger.info("📞 Checking Twilio logs...")
        
        if not self.twilio_account_sid or not self.twilio_auth_token:
            logger.warning("⚠️ Twilio credentials not configured")
            return
        
        try:
            from twilio.rest import Client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            # Get recent calls
            calls = client.calls.list(limit=5)
            
            for call in calls:
                logger.info(f"📞 Call {call.sid}: {call.status} - {call.direction}")
                if call.status in ['failed', 'busy', 'no-answer']:
                    logger.error(f"❌ Failed call: {call.sid} - {call.status}")
                
                # Check for application errors
                if hasattr(call, 'error_code') and call.error_code:
                    logger.error(f"❌ Twilio error {call.error_code}: {call.error_message}")
            
        except Exception as e:
            logger.error(f"❌ Twilio log check failed: {e}")
    
    async def simulate_full_call_flow(self, phone_number: str = "+17209545909"):
        """Simulate complete call flow to identify issues"""
        logger.info(f"🔄 Simulating full call flow to {phone_number}")
        
        call_id = f"debug_{int(time.time())}"
        
        # Step 1: Create call session
        logger.info("1️⃣ Creating call session...")
        session_data = {
            "call_id": call_id,
            "phone_number": phone_number,
            "status": "initiated",
            "created_at": datetime.now().isoformat(),
            "conversation_state": {},
            "adversarial_score": 0,
            "extracted_fields": {}
        }
        
        session_key = f"call_session:{call_id}"
        self.redis_client.setex(session_key, 3600, json.dumps(session_data))
        logger.info(f"✅ Session created: {call_id}")
        
        # Step 2: Test webhook flow
        logger.info("2️⃣ Testing webhook flow...")
        await self.test_webhook_endpoints(call_id)
        
        # Step 3: Test speech processing
        logger.info("3️⃣ Testing speech processing...")
        await self.test_speech_processing(call_id)
        
        # Step 4: Check final state
        logger.info("4️⃣ Checking final state...")
        final_session = self.redis_client.get(session_key)
        if final_session:
            final_data = json.loads(final_session)
            logger.info(f"✅ Final session status: {final_data.get('status')}")
            logger.info(f"📊 Conversation entries: {len(final_data.get('conversation_state', {}))}")
        
        # Cleanup
        self.redis_client.delete(session_key)
        logger.info("🧹 Test session cleaned up")
    
    async def run_comprehensive_debug(self):
        """Run all debugging tests"""
        logger.info("🚀 Starting comprehensive call debugging...")
        logger.info("=" * 60)
        
        # Test 1: Basic connectivity
        await self.monitor_webhook_accessibility()
        logger.info("-" * 40)
        
        # Test 2: OpenAI integration
        await self.test_openai_integration()
        logger.info("-" * 40)
        
        # Test 3: Redis operations
        await self.monitor_redis_operations()
        logger.info("-" * 40)
        
        # Test 4: Twilio logs
        await self.check_twilio_logs()
        logger.info("-" * 40)
        
        # Test 5: Full call simulation
        await self.simulate_full_call_flow()
        logger.info("-" * 40)
        
        logger.info("✅ Comprehensive debugging complete!")
        logger.info("📝 Check the log file for detailed results")

async def main():
    """Main debugging function"""
    print("🔍 AI Voice Agent - Live Call Debugging")
    print("=" * 50)
    print("This script will test all components of the phone call system")
    print("to identify the source of 'application error' issues.")
    print()
    
    monitor = CallMonitor()
    
    try:
        await monitor.run_comprehensive_debug()
    except KeyboardInterrupt:
        print("\n⏹️ Debugging stopped by user")
    except Exception as e:
        logger.error(f"❌ Debugging failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
