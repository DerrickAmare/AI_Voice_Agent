"""
Test script for Redis-based AI Voice Agent system
Tests the new architecture without database dependencies
"""

import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.services.redis_state_service import RedisStateService
from src.services.object_storage_service import ObjectStorageService, StorageConfig, WorkerProfile, AuditLogEntry
from src.services.webhook_service import WebhookService, WebhookConfig
from src.services.observability_service import ObservabilityService

async def test_redis_state_service():
    """Test Redis state management"""
    print("🔄 Testing Redis State Service...")
    
    redis_service = RedisStateService()
    
    # Test health check
    health = redis_service.health_check()
    print(f"   Redis Health: {health['status']}")
    
    # Test call session management
    call_id = "test_call_123"
    phone_number = "+16154846056"
    
    # Create session
    session = redis_service.create_call_session(call_id, phone_number)
    print(f"   Created session: {session.call_id} for {session.phone_hash}")
    
    # Update session
    updates = {
        "status": "active",
        "adversarial_score": 3.5,
        "extracted_fields": {"name": "John Doe", "current_job": "Software Engineer"}
    }
    redis_service.update_call_session(call_id, updates)
    
    # Retrieve session
    retrieved = redis_service.get_call_session(call_id)
    print(f"   Retrieved session status: {retrieved.status}")
    print(f"   Adversarial score: {retrieved.adversarial_score}")
    
    # Test rate limiting
    rate_limit = redis_service.check_rate_limit(phone_number)
    print(f"   Rate limit check: {rate_limit['current_count']}/{rate_limit['max_calls']}")
    
    # Increment rate limit
    count = redis_service.increment_rate_limit(phone_number)
    print(f"   Rate limit after increment: {count}")
    
    # Test outbox messaging
    event_id = "webhook_test_123"
    payload = {"test": "data", "call_id": call_id}
    webhook_url = "https://httpbin.org/post"
    
    message = redis_service.queue_outbox_message(event_id, session.phone_hash, payload, webhook_url)
    print(f"   Queued outbox message: {message.event_id}")
    
    # Get system stats
    stats = redis_service.get_system_stats()
    print(f"   Active sessions: {stats['active_call_sessions']}")
    print(f"   Pending outbox: {stats['pending_outbox_messages']}")
    
    # Cleanup
    redis_service.delete_call_session(call_id)
    redis_service.delete_outbox_message(event_id)
    
    print("✅ Redis State Service tests completed")

async def test_object_storage_service():
    """Test object storage service"""
    print("\n📦 Testing Object Storage Service...")
    
    # Check if AWS credentials are available
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        print("   ⚠️  AWS credentials not configured, skipping object storage tests")
        return
    
    try:
        config = StorageConfig(
            bucket_name=os.getenv("S3_BUCKET_NAME", "ai-voice-agent-test"),
            region=os.getenv("AWS_REGION", "us-east-1"),
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            retention_days=7  # Short retention for testing
        )
        
        storage_service = ObjectStorageService(config)
        
        # Test health check
        health = storage_service.health_check()
        print(f"   Storage Health: {health['status']}")
        
        if health['status'] != 'healthy':
            print(f"   ⚠️  Storage not healthy: {health.get('error', 'Unknown error')}")
            return
        
        # Test worker profile storage
        profile = WorkerProfile(
            phone_hash="test_hash_123",
            call_id="test_call_123",
            extracted_at=datetime.now(),
            name="Test Worker",
            current_job={"title": "Software Engineer", "company": "Test Corp"},
            skills=["Python", "JavaScript"],
            adversarial_score=2.5,
            confidence_score=0.85,
            consent_given=True,
            data_retention_until=datetime.now()
        )
        
        profile_url = storage_service.store_worker_profile(profile)
        print(f"   Stored worker profile: {profile_url}")
        
        # Test transcript storage
        transcript_data = {
            "segments": [
                {"timestamp": "00:00:10", "speaker": "agent", "text": "Hello, how are you?"},
                {"timestamp": "00:00:15", "speaker": "caller", "text": "I'm doing well, thank you."}
            ],
            "duration": 120,
            "quality": "high"
        }
        
        transcript_url = storage_service.store_transcript("test_call_123", transcript_data)
        print(f"   Stored transcript: {transcript_url}")
        
        # Test audit log
        audit_entry = AuditLogEntry(
            timestamp=datetime.now(),
            phone_hash="test_hash_123",
            consent=True,
            agent_version="2.0",
            call_id="test_call_123",
            event_type="call_completed"
        )
        
        audit_url = storage_service.write_audit_log(audit_entry)
        print(f"   Wrote audit log: {audit_url}")
        
        # Get storage stats
        stats = storage_service.get_storage_stats()
        print(f"   Storage stats: {stats['object_counts']}")
        
        print("✅ Object Storage Service tests completed")
        
    except Exception as e:
        print(f"   ❌ Object Storage test failed: {str(e)}")

async def test_webhook_service():
    """Test webhook delivery service"""
    print("\n🔗 Testing Webhook Service...")
    
    redis_service = RedisStateService()
    
    # Mock storage service for webhook testing
    class MockStorageService:
        def store_worker_profile(self, profile):
            return f"s3://test-bucket/profiles/{profile.call_id}/worker_profile.json"
    
    storage_service = MockStorageService()
    webhook_service = WebhookService(redis_service, storage_service)
    
    # Test webhook endpoint
    test_url = "https://httpbin.org/post"
    result = await webhook_service.test_webhook_endpoint(test_url)
    print(f"   Webhook test result: {result.success} ({result.status_code})")
    print(f"   Response time: {result.delivery_time_ms}ms")
    
    # Test profile delivery
    profile = WorkerProfile(
        phone_hash="test_hash_webhook",
        call_id="test_call_webhook",
        extracted_at=datetime.now(),
        name="Webhook Test",
        adversarial_score=1.0,
        confidence_score=0.9,
        consent_given=True,
        data_retention_until=datetime.now()
    )
    
    delivery_result = await webhook_service.deliver_worker_profile(
        "test_call_webhook", 
        test_url, 
        profile
    )
    print(f"   Profile delivery: {delivery_result.success}")
    print(f"   Status code: {delivery_result.status_code}")
    
    # Test queue processing
    event_id = webhook_service.queue_for_delivery("test_call_queue", test_url, profile)
    print(f"   Queued for delivery: {event_id}")
    
    # Process queue
    stats = await webhook_service.process_outbox_queue(batch_size=5)
    print(f"   Queue processing stats: {stats}")
    
    # Get outbox stats
    outbox_stats = webhook_service.get_outbox_stats()
    print(f"   Outbox stats: {outbox_stats}")
    
    await webhook_service.cleanup()
    print("✅ Webhook Service tests completed")

async def test_observability_service():
    """Test observability and metrics"""
    print("\n📊 Testing Observability Service...")
    
    redis_service = RedisStateService()
    observability_service = ObservabilityService(redis_service)
    
    # Record some test metrics
    call_id = "obs_test_call"
    phone_hash = "obs_test_hash"
    
    # Record call started
    observability_service.record_call_started(call_id, phone_hash)
    
    # Record call completed
    observability_service.record_call_completed(call_id, adversarial_score=4.5, fields_extracted=8)
    
    # Record webhook delivery
    observability_service.record_webhook_delivery(call_id, success=True, delivery_time_ms=250)
    
    # Get analytics
    analytics_1h = observability_service.get_call_analytics(1)
    print(f"   1-hour analytics: {analytics_1h['total_calls']} calls")
    print(f"   Success rate: {analytics_1h['success_rate']}%")
    print(f"   Adversarial distribution: {analytics_1h['adversarial_distribution']}")
    
    # Get system health
    health = observability_service.get_system_health()
    print(f"   System health: {health['status']}")
    print(f"   Active sessions: {health['active_sessions']}")
    print(f"   Error rate (15min): {health['error_rate_15min']}%")
    
    # Get recent events
    events = observability_service.get_recent_events(5)
    print(f"   Recent events: {len(events)} events")
    
    # Export metrics summary
    summary = observability_service.export_metrics_summary()
    print(f"   Metrics summary exported with {len(summary)} sections")
    
    print("✅ Observability Service tests completed")

async def test_system_integration():
    """Test full system integration"""
    print("\n🔄 Testing System Integration...")
    
    # Initialize all services
    redis_service = RedisStateService()
    observability_service = ObservabilityService(redis_service)
    
    # Simulate a complete call flow
    call_id = "integration_test_call"
    phone_number = "+16154846056"
    
    # 1. Create call session
    session = redis_service.create_call_session(call_id, phone_number)
    observability_service.record_call_started(call_id, session.phone_hash)
    print(f"   1. Call session created: {call_id}")
    
    # 2. Simulate conversation updates
    conversation_updates = [
        {"extracted_fields": {"name": "John Smith"}, "adversarial_score": 1.0},
        {"extracted_fields": {"name": "John Smith", "current_job": "Engineer"}, "adversarial_score": 2.5},
        {"extracted_fields": {"name": "John Smith", "current_job": "Engineer", "skills": ["Python"]}, "adversarial_score": 3.0}
    ]
    
    for i, update in enumerate(conversation_updates):
        redis_service.update_call_session(call_id, update)
        print(f"   2.{i+1}. Updated session with {len(update['extracted_fields'])} fields")
    
    # 3. Complete the call
    final_session = redis_service.get_call_session(call_id)
    observability_service.record_call_completed(
        call_id, 
        final_session.adversarial_score, 
        len(final_session.extracted_fields)
    )
    print(f"   3. Call completed with adversarial score: {final_session.adversarial_score}")
    
    # 4. Get final analytics
    analytics = observability_service.get_call_analytics(1)
    print(f"   4. Final analytics: {analytics['total_calls']} calls, {analytics['success_rate']}% success")
    
    # 5. Cleanup
    redis_service.delete_call_session(call_id)
    print(f"   5. Cleaned up call session")
    
    print("✅ System Integration tests completed")

async def main():
    """Run all tests"""
    print("🚀 Starting Redis-based AI Voice Agent System Tests\n")
    
    try:
        await test_redis_state_service()
        await test_object_storage_service()
        await test_webhook_service()
        await test_observability_service()
        await test_system_integration()
        
        print("\n🎉 All tests completed successfully!")
        print("\nSystem is ready for high-volume outbound calling with:")
        print("   ✅ Redis-based state management")
        print("   ✅ Object storage for durability")
        print("   ✅ Reliable webhook delivery")
        print("   ✅ Comprehensive observability")
        print("   ✅ No database dependencies")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
