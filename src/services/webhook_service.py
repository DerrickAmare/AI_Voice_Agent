"""
Webhook delivery service with retry logic and exponential backoff.
Handles reliable delivery of worker profiles to sponsor webhooks.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel
import structlog

from .redis_state_service import RedisStateService, OutboxMessage
from .object_storage_service import ObjectStorageService, WorkerProfile

logger = structlog.get_logger()

class WebhookConfig(BaseModel):
    """Configuration for webhook delivery"""
    timeout_seconds: int = 30
    max_retries: int = 5
    initial_retry_delay: int = 60  # seconds
    max_retry_delay: int = 3600    # 1 hour
    backoff_multiplier: float = 2.0

class WebhookDeliveryResult(BaseModel):
    """Result of webhook delivery attempt"""
    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    delivery_time_ms: int
    attempt_number: int

class WebhookService:
    """Service for reliable webhook delivery"""
    
    def __init__(self, redis_service: RedisStateService, 
                 storage_service: ObjectStorageService,
                 config: WebhookConfig = None):
        self.redis_service = redis_service
        self.storage_service = storage_service
        self.config = config or WebhookConfig()
        self.logger = logger.bind(service="webhook")
        
        # HTTP client for webhook delivery
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout_seconds),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
    
    async def deliver_worker_profile(self, call_id: str, webhook_url: str, 
                                   profile: WorkerProfile) -> WebhookDeliveryResult:
        """Deliver worker profile to webhook URL"""
        start_time = datetime.now()
        
        # Prepare payload
        payload = {
            "event_type": "worker_profile_completed",
            "timestamp": datetime.now().isoformat(),
            "call_id": call_id,
            "profile": profile.model_dump(mode='json')
        }
        
        try:
            response = await self.http_client.post(
                webhook_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "AI-Voice-Agent/1.0",
                    "X-Event-Type": "worker_profile_completed",
                    "X-Call-ID": call_id
                }
            )
            
            delivery_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            success = 200 <= response.status_code < 300
            
            result = WebhookDeliveryResult(
                success=success,
                status_code=response.status_code,
                response_body=response.text[:1000],  # Limit response body size
                delivery_time_ms=delivery_time,
                attempt_number=1
            )
            
            if success:
                self.logger.info("Webhook delivered successfully", 
                               call_id=call_id, status_code=response.status_code,
                               delivery_time_ms=delivery_time)
            else:
                self.logger.warning("Webhook delivery failed", 
                                  call_id=call_id, status_code=response.status_code,
                                  response=response.text[:200])
            
            return result
            
        except httpx.TimeoutException:
            delivery_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.error("Webhook delivery timeout", call_id=call_id, 
                            webhook_url=webhook_url)
            
            return WebhookDeliveryResult(
                success=False,
                error_message="Request timeout",
                delivery_time_ms=delivery_time,
                attempt_number=1
            )
            
        except Exception as e:
            delivery_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.error("Webhook delivery error", call_id=call_id, 
                            error=str(e))
            
            return WebhookDeliveryResult(
                success=False,
                error_message=str(e),
                delivery_time_ms=delivery_time,
                attempt_number=1
            )
    
    def queue_for_delivery(self, call_id: str, webhook_url: str, 
                          profile: WorkerProfile) -> str:
        """Queue worker profile for webhook delivery"""
        event_id = f"webhook_{call_id}_{uuid.uuid4().hex[:8]}"
        
        # Store profile in object storage first
        profile_url = self.storage_service.store_worker_profile(profile)
        
        # Queue for webhook delivery
        payload = profile.model_dump()
        
        self.redis_service.queue_outbox_message(
            event_id=event_id,
            phone_hash=profile.phone_hash,
            payload=payload,
            webhook_url=webhook_url
        )
        
        self.logger.info("Queued profile for webhook delivery", 
                        call_id=call_id, event_id=event_id)
        
        return event_id
    
    async def process_outbox_queue(self, batch_size: int = 10) -> Dict[str, int]:
        """Process pending webhook deliveries from outbox queue"""
        stats = {"processed": 0, "successful": 0, "failed": 0, "requeued": 0}
        
        # Get pending messages
        pending_events = self.redis_service.get_pending_outbox_messages(batch_size)
        
        for event_id in pending_events:
            try:
                message = self.redis_service.get_outbox_message(event_id)
                if not message:
                    # Message not found, remove from queue
                    self.redis_service.remove_from_outbox_queue(event_id)
                    continue
                
                stats["processed"] += 1
                
                # Check if we should retry this message
                if message.retry_count >= self.config.max_retries:
                    self.logger.warning("Message exceeded max retries", 
                                      event_id=event_id, retry_count=message.retry_count)
                    self.redis_service.remove_from_outbox_queue(event_id)
                    stats["failed"] += 1
                    continue
                
                # Check if it's time to retry
                if message.next_retry_at and datetime.now() < message.next_retry_at:
                    continue  # Not time to retry yet
                
                # Attempt delivery
                profile = WorkerProfile.model_validate(message.payload)
                result = await self.deliver_worker_profile(
                    profile.call_id, 
                    message.webhook_url, 
                    profile
                )
                
                if result.success:
                    # Success - remove from queue
                    self.redis_service.remove_from_outbox_queue(event_id)
                    self.redis_service.delete_outbox_message(event_id)
                    stats["successful"] += 1
                    
                    self.logger.info("Webhook delivery successful", 
                                   event_id=event_id, call_id=profile.call_id)
                else:
                    # Failed - update retry info
                    retry_count = message.retry_count + 1
                    delay = min(
                        self.config.initial_retry_delay * (self.config.backoff_multiplier ** retry_count),
                        self.config.max_retry_delay
                    )
                    next_retry = datetime.now() + timedelta(seconds=delay)
                    
                    self.redis_service.update_outbox_message(event_id, {
                        "retry_count": retry_count,
                        "next_retry_at": next_retry
                    })
                    
                    stats["requeued"] += 1
                    
                    self.logger.warning("Webhook delivery failed, will retry", 
                                      event_id=event_id, retry_count=retry_count,
                                      next_retry_at=next_retry.isoformat())
                
            except Exception as e:
                self.logger.error("Error processing outbox message", 
                                event_id=event_id, error=str(e))
                stats["failed"] += 1
        
        if stats["processed"] > 0:
            self.logger.info("Processed outbox queue", **stats)
        
        return stats
    
    async def retry_failed_deliveries(self) -> Dict[str, int]:
        """Retry failed webhook deliveries that are ready for retry"""
        return await self.process_outbox_queue()
    
    def calculate_next_retry_time(self, retry_count: int) -> datetime:
        """Calculate next retry time with exponential backoff"""
        delay = min(
            self.config.initial_retry_delay * (self.config.backoff_multiplier ** retry_count),
            self.config.max_retry_delay
        )
        return datetime.now() + timedelta(seconds=delay)
    
    async def test_webhook_endpoint(self, webhook_url: str) -> WebhookDeliveryResult:
        """Test webhook endpoint with a ping message"""
        start_time = datetime.now()
        
        payload = {
            "event_type": "webhook_test",
            "timestamp": datetime.now().isoformat(),
            "message": "This is a test webhook delivery"
        }
        
        try:
            response = await self.http_client.post(
                webhook_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "AI-Voice-Agent/1.0",
                    "X-Event-Type": "webhook_test"
                }
            )
            
            delivery_time = int((datetime.now() - start_time).total_seconds() * 1000)
            success = 200 <= response.status_code < 300
            
            return WebhookDeliveryResult(
                success=success,
                status_code=response.status_code,
                response_body=response.text[:1000],
                delivery_time_ms=delivery_time,
                attempt_number=1
            )
            
        except Exception as e:
            delivery_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return WebhookDeliveryResult(
                success=False,
                error_message=str(e),
                delivery_time_ms=delivery_time,
                attempt_number=1
            )
    
    def get_outbox_stats(self) -> Dict[str, Any]:
        """Get statistics about the outbox queue"""
        pending_count = len(self.redis_service.get_pending_outbox_messages(1000))
        
        # Count messages by retry count
        retry_stats = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5+": 0}
        
        for event_id in self.redis_service.get_pending_outbox_messages(1000):
            message = self.redis_service.get_outbox_message(event_id)
            if message:
                retry_key = str(min(message.retry_count, 5)) if message.retry_count < 5 else "5+"
                retry_stats[retry_key] += 1
        
        return {
            "pending_messages": pending_count,
            "retry_distribution": retry_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.http_client.aclose()
        self.logger.info("Webhook service cleaned up")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on webhook service"""
        try:
            # Check if HTTP client is working
            test_url = "https://httpbin.org/status/200"
            start_time = datetime.now()
            
            response = await self.http_client.get(test_url)
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            http_healthy = response.status_code == 200
            
            # Check outbox queue
            outbox_stats = self.get_outbox_stats()
            
            return {
                "status": "healthy" if http_healthy else "unhealthy",
                "http_client_working": http_healthy,
                "response_time_ms": response_time,
                "outbox_stats": outbox_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Webhook service health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "http_client_working": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
