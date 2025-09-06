"""
Call queue service for managing high-volume outbound calls
"""

import os
import logging
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import uuid
from sqlalchemy.orm import Session
from ..models.database_models import CallQueue, get_db

logger = logging.getLogger(__name__)

class CallQueueService:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using database-only queue.")
            self.redis_client = None
        
        self.queue_name = "call_queue"
        self.processing_queue = "call_processing"
        self.failed_queue = "call_failed"
    
    def add_call_to_queue(self, phone_number: str, metadata: Dict[str, Any] = None, 
                         priority: int = 1, scheduled_at: Optional[datetime] = None) -> str:
        """Add a call to the queue"""
        call_id = str(uuid.uuid4())
        
        call_data = {
            "call_id": call_id,
            "phone_number": phone_number,
            "metadata": metadata or {},
            "priority": priority,
            "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0,
            "max_attempts": 3
        }
        
        # Add to Redis queue if available
        if self.redis_client:
            try:
                # Use priority queue (higher priority = lower score)
                score = -priority  # Negative for reverse order
                if scheduled_at:
                    score = scheduled_at.timestamp()
                
                self.redis_client.zadd(self.queue_name, {json.dumps(call_data): score})
                logger.info(f"Call {call_id} added to Redis queue")
            except Exception as e:
                logger.error(f"Failed to add to Redis queue: {e}")
        
        # Also add to database for persistence
        try:
            db = next(get_db())
            queue_item = CallQueue(
                phone_number=phone_number,
                priority=priority,
                metadata=call_data["metadata"],
                scheduled_at=scheduled_at,
                attempts=0
            )
            db.add(queue_item)
            db.commit()
            logger.info(f"Call {call_id} added to database queue")
        except Exception as e:
            logger.error(f"Failed to add to database queue: {e}")
        
        return call_id
    
    def get_next_call(self) -> Optional[Dict[str, Any]]:
        """Get the next call from the queue"""
        # Try Redis first
        if self.redis_client:
            try:
                # Get highest priority item (lowest score)
                items = self.redis_client.zrange(self.queue_name, 0, 0, withscores=True)
                if items:
                    call_data_json, score = items[0]
                    call_data = json.loads(call_data_json)
                    
                    # Check if scheduled time has passed
                    if call_data.get("scheduled_at"):
                        scheduled_time = datetime.fromisoformat(call_data["scheduled_at"])
                        if datetime.utcnow() < scheduled_time:
                            return None  # Not time yet
                    
                    # Move to processing queue
                    self.redis_client.zrem(self.queue_name, call_data_json)
                    self.redis_client.zadd(self.processing_queue, {call_data_json: datetime.utcnow().timestamp()})
                    
                    return call_data
            except Exception as e:
                logger.error(f"Failed to get from Redis queue: {e}")
        
        # Fallback to database
        try:
            db = next(get_db())
            queue_item = db.query(CallQueue).filter(
                CallQueue.status == "pending",
                CallQueue.attempts < CallQueue.max_attempts
            ).order_by(
                CallQueue.priority.desc(),
                CallQueue.created_at.asc()
            ).first()
            
            if queue_item:
                # Check if scheduled time has passed
                if queue_item.scheduled_at and datetime.utcnow() < queue_item.scheduled_at:
                    return None
                
                # Mark as processing
                queue_item.status = "processing"
                queue_item.processed_at = datetime.utcnow()
                db.commit()
                
                return {
                    "call_id": str(queue_item.id),
                    "phone_number": queue_item.phone_number,
                    "metadata": queue_item.metadata or {},
                    "priority": queue_item.priority,
                    "attempts": queue_item.attempts
                }
        except Exception as e:
            logger.error(f"Failed to get from database queue: {e}")
        
        return None
    
    def mark_call_completed(self, call_id: str, success: bool = True, 
                           result_data: Dict[str, Any] = None) -> bool:
        """Mark a call as completed"""
        # Update Redis
        if self.redis_client:
            try:
                # Remove from processing queue
                processing_items = self.redis_client.zrange(self.processing_queue, 0, -1)
                for item_json in processing_items:
                    item_data = json.loads(item_json)
                    if item_data.get("call_id") == call_id:
                        self.redis_client.zrem(self.processing_queue, item_json)
                        
                        if not success:
                            # Add to failed queue for retry
                            item_data["attempts"] += 1
                            if item_data["attempts"] < item_data.get("max_attempts", 3):
                                # Retry with delay
                                retry_time = datetime.utcnow() + timedelta(minutes=30)
                                self.redis_client.zadd(self.queue_name, 
                                                     {json.dumps(item_data): retry_time.timestamp()})
                            else:
                                self.redis_client.zadd(self.failed_queue, 
                                                     {json.dumps(item_data): datetime.utcnow().timestamp()})
                        break
            except Exception as e:
                logger.error(f"Failed to update Redis queue: {e}")
        
        # Update database
        try:
            db = next(get_db())
            queue_item = db.query(CallQueue).filter(CallQueue.id == int(call_id)).first()
            if queue_item:
                if success:
                    queue_item.status = "completed"
                else:
                    queue_item.attempts += 1
                    if queue_item.attempts >= queue_item.max_attempts:
                        queue_item.status = "failed"
                    else:
                        queue_item.status = "pending"
                        queue_item.scheduled_at = datetime.utcnow() + timedelta(minutes=30)
                
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update database queue: {e}")
        
        return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "total": 0
        }
        
        # Get Redis stats
        if self.redis_client:
            try:
                stats["pending"] += self.redis_client.zcard(self.queue_name)
                stats["processing"] += self.redis_client.zcard(self.processing_queue)
                stats["failed"] += self.redis_client.zcard(self.failed_queue)
            except Exception as e:
                logger.error(f"Failed to get Redis stats: {e}")
        
        # Get database stats
        try:
            db = next(get_db())
            db_stats = db.query(CallQueue.status, db.func.count(CallQueue.id)).group_by(CallQueue.status).all()
            for status, count in db_stats:
                if status in stats:
                    stats[status] += count
                stats["total"] += count
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
        
        return stats
    
    def clear_queue(self, queue_type: str = "all") -> bool:
        """Clear queue (for testing/maintenance)"""
        try:
            if self.redis_client:
                if queue_type in ["all", "pending"]:
                    self.redis_client.delete(self.queue_name)
                if queue_type in ["all", "processing"]:
                    self.redis_client.delete(self.processing_queue)
                if queue_type in ["all", "failed"]:
                    self.redis_client.delete(self.failed_queue)
            
            if queue_type in ["all", "database"]:
                db = next(get_db())
                db.query(CallQueue).delete()
                db.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            return False
    
    def add_batch_calls(self, calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add multiple calls to queue efficiently"""
        added_count = 0
        failed_count = 0
        call_ids = []
        
        for call_data in calls:
            try:
                call_id = self.add_call_to_queue(
                    phone_number=call_data["phone_number"],
                    metadata=call_data.get("metadata", {}),
                    priority=call_data.get("priority", 1),
                    scheduled_at=call_data.get("scheduled_at")
                )
                call_ids.append(call_id)
                added_count += 1
            except Exception as e:
                logger.error(f"Failed to add call to queue: {e}")
                failed_count += 1
        
        return {
            "added": added_count,
            "failed": failed_count,
            "call_ids": call_ids,
            "total": len(calls)
        }
    
    def get_failed_calls(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get failed calls for analysis"""
        failed_calls = []
        
        # Get from Redis
        if self.redis_client:
            try:
                items = self.redis_client.zrange(self.failed_queue, 0, limit-1)
                for item_json in items:
                    failed_calls.append(json.loads(item_json))
            except Exception as e:
                logger.error(f"Failed to get failed calls from Redis: {e}")
        
        # Get from database
        try:
            db = next(get_db())
            db_failed = db.query(CallQueue).filter(CallQueue.status == "failed").limit(limit).all()
            for item in db_failed:
                failed_calls.append({
                    "call_id": str(item.id),
                    "phone_number": item.phone_number,
                    "metadata": item.metadata or {},
                    "attempts": item.attempts,
                    "created_at": item.created_at.isoformat()
                })
        except Exception as e:
            logger.error(f"Failed to get failed calls from database: {e}")
        
        return failed_calls
    
    def retry_failed_calls(self, max_retries: int = 100) -> Dict[str, Any]:
        """Retry failed calls"""
        retried_count = 0
        
        # Retry from Redis
        if self.redis_client:
            try:
                items = self.redis_client.zrange(self.failed_queue, 0, max_retries-1)
                for item_json in items:
                    call_data = json.loads(item_json)
                    call_data["attempts"] = 0  # Reset attempts
                    
                    # Move back to main queue
                    self.redis_client.zrem(self.failed_queue, item_json)
                    self.redis_client.zadd(self.queue_name, {json.dumps(call_data): -call_data.get("priority", 1)})
                    retried_count += 1
            except Exception as e:
                logger.error(f"Failed to retry calls from Redis: {e}")
        
        # Retry from database
        try:
            db = next(get_db())
            failed_items = db.query(CallQueue).filter(CallQueue.status == "failed").limit(max_retries).all()
            for item in failed_items:
                item.status = "pending"
                item.attempts = 0
                item.scheduled_at = None
                retried_count += 1
            db.commit()
        except Exception as e:
            logger.error(f"Failed to retry calls from database: {e}")
        
        return {"retried": retried_count}
    
    def is_healthy(self) -> Dict[str, Any]:
        """Check queue health"""
        health = {
            "redis_connected": False,
            "database_connected": False,
            "queue_stats": {}
        }
        
        # Check Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                health["redis_connected"] = True
            except:
                pass
        
        # Check Database
        try:
            db = next(get_db())
            db.execute("SELECT 1")
            health["database_connected"] = True
        except:
            pass
        
        # Get stats
        try:
            health["queue_stats"] = self.get_queue_stats()
        except:
            pass
        
        return health
