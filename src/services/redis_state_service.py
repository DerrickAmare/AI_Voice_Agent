"""
Redis-based state management for call sessions and system state.
Handles ephemeral call data, rate limiting, and outbox queuing.
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

class CallSession(BaseModel):
    """Call session state stored in Redis"""
    call_id: str
    phone_number: str
    phone_hash: str
    status: str  # 'queued', 'active', 'completed', 'failed'
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    twilio_call_sid: Optional[str] = None
    
    # Conversation state
    conversation_state: Optional[Dict[str, Any]] = None
    extracted_fields: Dict[str, Any] = {}
    adversarial_score: float = 0.0
    employment_gaps: List[Dict] = []
    
    # Audio and transcription
    audio_urls: List[str] = []
    transcript_segments: List[Dict] = []
    
    # Metadata
    agent_version: str = "1.0"
    consent_given: bool = False
    retry_count: int = 0
    
    # Resume request integration
    request_id: Optional[str] = None

class OutboxMessage(BaseModel):
    """Message queued for webhook delivery"""
    event_id: str
    phone_hash: str
    payload: Dict[str, Any]
    webhook_url: str
    created_at: datetime
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None
    max_retries: int = 5

class RedisStateService:
    """Redis-based state management service"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.logger = logger.bind(service="redis_state")
        
        # TTL configurations (in seconds)
        self.CALL_SESSION_TTL = 48 * 60 * 60  # 48 hours
        self.RATE_LIMIT_TTL = 24 * 60 * 60    # 24 hours
        self.OUTBOX_TTL = 7 * 24 * 60 * 60    # 7 days
        
    def _hash_phone(self, phone_number: str) -> str:
        """Create a hash of phone number for privacy"""
        return hashlib.sha256(phone_number.encode()).hexdigest()[:16]
    
    def _call_session_key(self, call_id: str) -> str:
        """Generate Redis key for call session"""
        return f"CALL_SESSION:{call_id}"
    
    def _rate_limit_key(self, phone_number: str) -> str:
        """Generate Redis key for rate limiting"""
        phone_hash = self._hash_phone(phone_number)
        return f"RATE_LIMIT:{phone_hash}"
    
    def _outbox_key(self, event_id: str) -> str:
        """Generate Redis key for outbox message"""
        return f"OUTBOX:{event_id}"
    
    # Call Session Management
    
    def create_call_session(self, call_id: str, phone_number: str, **kwargs) -> CallSession:
        """Create a new call session in Redis"""
        phone_hash = self._hash_phone(phone_number)
        
        session = CallSession(
            call_id=call_id,
            phone_number=phone_number,
            phone_hash=phone_hash,
            status="queued",
            **kwargs
        )
        
        key = self._call_session_key(call_id)
        self.redis_client.setex(
            key, 
            self.CALL_SESSION_TTL, 
            session.model_dump_json()
        )
        
        self.logger.info("Created call session", call_id=call_id, phone_hash=phone_hash)
        return session
    
    def get_call_session(self, call_id: str) -> Optional[CallSession]:
        """Retrieve call session from Redis"""
        key = self._call_session_key(call_id)
        data = self.redis_client.get(key)
        
        if not data:
            return None
            
        return CallSession.model_validate_json(data)
    
    def update_call_session(self, call_id: str, updates: Dict[str, Any]) -> bool:
        """Update call session with new data"""
        session = self.get_call_session(call_id)
        if not session:
            self.logger.warning("Call session not found for update", call_id=call_id)
            return False
        
        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        # Save back to Redis
        redis_key = self._call_session_key(call_id)
        self.redis_client.setex(
            redis_key,
            self.CALL_SESSION_TTL,
            session.model_dump_json()
        )
        
        self.logger.info("Updated call session", call_id=call_id, updates=list(updates.keys()))
        return True
    
    def delete_call_session(self, call_id: str) -> bool:
        """Delete call session from Redis"""
        key = self._call_session_key(call_id)
        result = self.redis_client.delete(key)
        
        if result:
            self.logger.info("Deleted call session", call_id=call_id)
        
        return bool(result)
    
    # Rate Limiting
    
    def check_rate_limit(self, phone_number: str, max_calls_per_day: int = 3) -> Dict[str, Any]:
        """Check if phone number is rate limited"""
        key = self._rate_limit_key(phone_number)
        
        # Get current count
        current_count = self.redis_client.get(key)
        current_count = int(current_count) if current_count else 0
        
        # Check if rate limited
        is_rate_limited = current_count >= max_calls_per_day
        
        # Get TTL for reset time
        ttl = self.redis_client.ttl(key)
        reset_at = None
        if ttl > 0:
            reset_at = datetime.now() + timedelta(seconds=ttl)
        
        return {
            "is_rate_limited": is_rate_limited,
            "current_count": current_count,
            "max_calls": max_calls_per_day,
            "reset_at": reset_at
        }
    
    def increment_rate_limit(self, phone_number: str) -> int:
        """Increment rate limit counter for phone number"""
        key = self._rate_limit_key(phone_number)
        
        # Increment counter
        count = self.redis_client.incr(key)
        
        # Set TTL if this is the first increment
        if count == 1:
            self.redis_client.expire(key, self.RATE_LIMIT_TTL)
        
        phone_hash = self._hash_phone(phone_number)
        self.logger.info("Incremented rate limit", phone_hash=phone_hash, count=count)
        
        return count
    
    # Outbox Management
    
    def queue_outbox_message(self, event_id: str, phone_hash: str, payload: Dict[str, Any], 
                           webhook_url: str) -> OutboxMessage:
        """Queue a message for webhook delivery"""
        message = OutboxMessage(
            event_id=event_id,
            phone_hash=phone_hash,
            payload=payload,
            webhook_url=webhook_url,
            created_at=datetime.now()
        )
        
        key = self._outbox_key(event_id)
        self.redis_client.setex(
            key,
            self.OUTBOX_TTL,
            message.model_dump_json()
        )
        
        # Add to processing queue
        self.redis_client.lpush("OUTBOX_QUEUE", event_id)
        
        self.logger.info("Queued outbox message", event_id=event_id, phone_hash=phone_hash)
        return message
    
    def get_outbox_message(self, event_id: str) -> Optional[OutboxMessage]:
        """Retrieve outbox message"""
        key = self._outbox_key(event_id)
        data = self.redis_client.get(key)
        
        if not data:
            return None
            
        return OutboxMessage.model_validate_json(data)
    
    def update_outbox_message(self, event_id: str, updates: Dict[str, Any]) -> bool:
        """Update outbox message"""
        message = self.get_outbox_message(event_id)
        if not message:
            return False
        
        for key, value in updates.items():
            if hasattr(message, key):
                setattr(message, key, value)
        
        redis_key = self._outbox_key(event_id)
        self.redis_client.setex(
            redis_key,
            self.OUTBOX_TTL,
            message.model_dump_json()
        )
        
        return True
    
    def delete_outbox_message(self, event_id: str) -> bool:
        """Delete outbox message"""
        key = self._outbox_key(event_id)
        result = self.redis_client.delete(key)
        return bool(result)
    
    def get_pending_outbox_messages(self, limit: int = 100) -> List[str]:
        """Get pending outbox messages for processing"""
        return self.redis_client.lrange("OUTBOX_QUEUE", 0, limit - 1)
    
    def remove_from_outbox_queue(self, event_id: str) -> bool:
        """Remove message from outbox processing queue"""
        result = self.redis_client.lrem("OUTBOX_QUEUE", 1, event_id)
        return bool(result)
    
    # System Health and Metrics
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics from Redis"""
        info = self.redis_client.info()
        
        # Count active sessions
        active_sessions = 0
        for key in self.redis_client.scan_iter(match="CALL_SESSION:*"):
            session_data = self.redis_client.get(key)
            if session_data:
                session = CallSession.model_validate_json(session_data)
                if session.status == "active":
                    active_sessions += 1
        
        # Count pending outbox messages
        pending_outbox = self.redis_client.llen("OUTBOX_QUEUE")
        
        return {
            "redis_info": {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            },
            "active_call_sessions": active_sessions,
            "pending_outbox_messages": pending_outbox,
            "timestamp": datetime.now().isoformat()
        }
    
    def cleanup_expired_keys(self) -> Dict[str, int]:
        """Clean up expired keys (manual cleanup if needed)"""
        cleaned = {
            "call_sessions": 0,
            "rate_limits": 0,
            "outbox_messages": 0
        }
        
        # This is mainly for monitoring - Redis handles TTL automatically
        # But we can use this to get counts of what would be cleaned
        
        current_time = time.time()
        
        # Check call sessions
        for key in self.redis_client.scan_iter(match="CALL_SESSION:*"):
            ttl = self.redis_client.ttl(key)
            if ttl == -1:  # No TTL set
                self.redis_client.expire(key, self.CALL_SESSION_TTL)
                cleaned["call_sessions"] += 1
        
        return cleaned
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis connection"""
        try:
            # Test basic operations
            test_key = "HEALTH_CHECK"
            self.redis_client.set(test_key, "ok", ex=10)
            result = self.redis_client.get(test_key)
            self.redis_client.delete(test_key)
            
            return {
                "status": "healthy" if result == "ok" else "unhealthy",
                "redis_connected": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error("Redis health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # Resume Request Management
    
    def _resume_request_key(self, request_id: str) -> str:
        """Generate Redis key for resume request"""
        return f"RESUME_REQUEST:{request_id}"
    
    def _user_requests_key(self, phone_number: str) -> str:
        """Generate Redis key for user requests list"""
        phone_hash = self._hash_phone(phone_number)
        return f"USER_REQUESTS:{phone_hash}"
    
    def store_resume_request(self, request_id: str, request_data: Dict[str, Any]) -> bool:
        """Store resume request data in Redis"""
        try:
            key = self._resume_request_key(request_id)
            self.redis_client.setex(
                key,
                self.CALL_SESSION_TTL,  # Same TTL as call sessions
                json.dumps(request_data, default=str)
            )
            
            # Add to user's request list
            phone_number = request_data.get("phone_number")
            if phone_number:
                user_key = self._user_requests_key(phone_number)
                self.redis_client.lpush(user_key, request_id)
                self.redis_client.expire(user_key, self.CALL_SESSION_TTL)
            
            self.logger.info("Stored resume request", request_id=request_id)
            return True
            
        except Exception as e:
            self.logger.error("Failed to store resume request", request_id=request_id, error=str(e))
            return False
    
    def get_resume_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve resume request data from Redis"""
        try:
            key = self._resume_request_key(request_id)
            data = self.redis_client.get(key)
            
            if not data:
                return None
                
            return json.loads(data)
            
        except Exception as e:
            self.logger.error("Failed to get resume request", request_id=request_id, error=str(e))
            return None
    
    def update_resume_request(self, request_id: str, updates: Dict[str, Any]) -> bool:
        """Update resume request with new data"""
        try:
            request_data = self.get_resume_request(request_id)
            if not request_data:
                self.logger.warning("Resume request not found for update", request_id=request_id)
                return False
            
            # Update fields
            request_data.update(updates)
            request_data["updated_at"] = datetime.now().isoformat()
            
            # Save back to Redis
            key = self._resume_request_key(request_id)
            self.redis_client.setex(
                key,
                self.CALL_SESSION_TTL,
                json.dumps(request_data, default=str)
            )
            
            self.logger.info("Updated resume request", request_id=request_id, updates=list(updates.keys()))
            return True
            
        except Exception as e:
            self.logger.error("Failed to update resume request", request_id=request_id, error=str(e))
            return False
    
    def get_user_requests(self, phone_number: str) -> List[Dict[str, Any]]:
        """Get all resume requests for a phone number"""
        try:
            user_key = self._user_requests_key(phone_number)
            request_ids = self.redis_client.lrange(user_key, 0, -1)
            
            requests = []
            for request_id in request_ids:
                request_data = self.get_resume_request(request_id)
                if request_data:
                    requests.append(request_data)
            
            # Sort by creation time (newest first)
            requests.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return requests
            
        except Exception as e:
            self.logger.error("Failed to get user requests", phone_number=phone_number, error=str(e))
            return []
