"""
AI Voice Agent - High-Volume Outbound Calling System
Redis-based architecture with object storage and webhook delivery
"""

import os
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import phonenumbers
from twilio.twiml.voice_response import VoiceResponse

# Import our services
from src.services.redis_state_service import RedisStateService, CallSession
from src.services.object_storage_service import (
    ObjectStorageService, StorageConfig, WorkerProfile, AuditLogEntry
)
from src.services.webhook_service import WebhookService, WebhookConfig
from src.services.observability_service import ObservabilityService
from src.services.telephony_service import TelephonyService
from src.agents.phone_conversation_agent import PhoneConversationAgent

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global services
redis_service: RedisStateService = None
storage_service: ObjectStorageService = None
webhook_service: WebhookService = None
observability_service: ObservabilityService = None
telephony_service: TelephonyService = None
phone_agent: PhoneConversationAgent = None

# Background task for webhook processing
webhook_processor_task: Optional[asyncio.Task] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global redis_service, storage_service, webhook_service, observability_service
    global telephony_service, phone_agent, webhook_processor_task
    
    logger.info("Starting AI Voice Agent system")
    
    try:
        # Initialize Redis service
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_service = RedisStateService(redis_url)
        logger.info("Redis service initialized")
        
        # Initialize object storage
        storage_type = os.getenv("STORAGE_TYPE", "local")
        
        if storage_type == "local":
            local_path = os.getenv("LOCAL_STORAGE_PATH", "./storage")
            storage_service = ObjectStorageService(
                storage_type="local",
                local_path=local_path
            )
            logger.info("Local storage service initialized", path=local_path)
        else:
            # S3-compatible storage
            storage_config = StorageConfig(
                bucket_name=os.getenv("S3_BUCKET_NAME", "ai-voice-agent-storage"),
                region=os.getenv("AWS_REGION", "us-east-1"),
                access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                endpoint_url=os.getenv("S3_ENDPOINT_URL"),  # For S3-compatible services
                retention_days=int(os.getenv("STORAGE_RETENTION_DAYS", "30"))
            )
            storage_service = ObjectStorageService(
                config=storage_config,
                storage_type="s3"
            )
            logger.info("S3 storage service initialized", bucket=storage_config.bucket_name)
        
        # Initialize webhook service
        webhook_config = WebhookConfig(
            timeout_seconds=int(os.getenv("WEBHOOK_TIMEOUT", "30")),
            max_retries=int(os.getenv("WEBHOOK_MAX_RETRIES", "5"))
        )
        webhook_service = WebhookService(redis_service, storage_service, webhook_config)
        logger.info("Webhook service initialized")
        
        # Initialize observability service
        observability_service = ObservabilityService(redis_service)
        logger.info("Observability service initialized")
        
        # Initialize telephony service
        telephony_service = TelephonyService(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            phone_number=os.getenv("TWILIO_PHONE_NUMBER")
        )
        logger.info("Telephony service initialized")
        
        # Initialize phone conversation agent
        phone_agent = PhoneConversationAgent()
        logger.info("Phone conversation agent initialized")
        
        # Start background webhook processor
        webhook_processor_task = asyncio.create_task(webhook_processor())
        logger.info("Background webhook processor started")
        
        # Perform health checks
        await perform_startup_health_checks()
        
        logger.info("AI Voice Agent system started successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start system", error=str(e))
        raise
    finally:
        # Cleanup
        logger.info("Shutting down AI Voice Agent system")
        
        if webhook_processor_task:
            webhook_processor_task.cancel()
            try:
                await webhook_processor_task
            except asyncio.CancelledError:
                pass
        
        if webhook_service:
            await webhook_service.cleanup()
        
        logger.info("System shutdown complete")

async def perform_startup_health_checks():
    """Perform health checks on all services"""
    checks = []
    critical_failures = []
    
    # Redis health check (critical)
    redis_health = redis_service.health_check()
    redis_healthy = redis_health["status"] == "healthy"
    checks.append(("Redis", redis_healthy))
    if not redis_healthy:
        critical_failures.append("Redis")
    
    # Storage health check (critical)
    storage_health = storage_service.health_check()
    storage_healthy = storage_health["status"] == "healthy"
    checks.append(("Object Storage", storage_healthy))
    if not storage_healthy:
        critical_failures.append("Object Storage")
    
    # Webhook service health check (non-critical)
    webhook_health = await webhook_service.health_check()
    webhook_healthy = webhook_health["status"] == "healthy"
    checks.append(("Webhook Service", webhook_healthy))
    
    # Telephony service health check (non-critical in demo mode)
    telephony_health = telephony_service.health_check()
    telephony_healthy = telephony_health["status"] == "healthy"
    demo_mode = telephony_health.get("demo_mode", False)
    checks.append(("Telephony Service", telephony_healthy or demo_mode))
    
    # Only fail on critical services
    if critical_failures:
        logger.error("Critical health check failures", failed_services=critical_failures)
        raise RuntimeError(f"Critical health check failed for: {', '.join(critical_failures)}")
    
    # Log warnings for non-critical failures
    all_failed = [name for name, healthy in checks if not healthy]
    if all_failed:
        logger.warning("Some services unhealthy but system can continue", 
                      failed_services=all_failed)
    
    logger.info("Health checks completed", 
               healthy_services=[name for name, healthy in checks if healthy],
               demo_mode=demo_mode)

async def webhook_processor():
    """Background task to process webhook deliveries"""
    logger.info("Webhook processor started")
    
    while True:
        try:
            # Process outbox queue
            stats = await webhook_service.process_outbox_queue(batch_size=10)
            
            if stats["processed"] > 0:
                logger.info("Processed webhook queue", **stats)
            
            # Wait before next processing cycle
            await asyncio.sleep(30)  # Process every 30 seconds
            
        except asyncio.CancelledError:
            logger.info("Webhook processor cancelled")
            break
        except Exception as e:
            logger.error("Error in webhook processor", error=str(e))
            await asyncio.sleep(60)  # Wait longer on error

# Initialize FastAPI app
app = FastAPI(
    title="AI Voice Agent - Outbound Calling System",
    description="High-volume outbound calling system with Redis state management",
    version="2.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Request/Response Models
class InitiateCallRequest(BaseModel):
    phone_number: str
    webhook_url: Optional[str] = None
    resume_data: Optional[Dict[str, Any]] = None

class CallStatusResponse(BaseModel):
    call_id: str
    status: str
    phone_hash: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    adversarial_score: float = 0.0
    extracted_fields: Dict[str, Any] = {}

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI"""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>AI Voice Agent</title></head>
        <body>
            <h1>AI Voice Agent - Outbound Calling System</h1>
            <p>Redis-based high-volume calling system</p>
            <p><a href="/docs">API Documentation</a></p>
            <p><a href="/health">System Health</a></p>
            <p><a href="/metrics">Metrics</a></p>
        </body>
        </html>
        """)

@app.post("/api/calls/initiate")
async def initiate_call(request: InitiateCallRequest, background_tasks: BackgroundTasks):
    """Initiate an outbound call"""
    try:
        # Validate phone number
        try:
            parsed_number = phonenumbers.parse(request.phone_number, "US")
            if not phonenumbers.is_valid_number(parsed_number):
                raise HTTPException(status_code=400, detail="Invalid phone number")
            
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        
        # Check rate limiting
        rate_limit = redis_service.check_rate_limit(formatted_number)
        if rate_limit["is_rate_limited"]:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limited. Reset at: {rate_limit['reset_at']}"
            )
        
        # Generate call ID
        call_id = f"call_{uuid.uuid4().hex[:12]}"
        
        # Create call session in Redis
        session = redis_service.create_call_session(
            call_id=call_id,
            phone_number=formatted_number,
            consent_given=True  # Assume consent for demo
        )
        
        # Write audit log
        audit_entry = AuditLogEntry(
            timestamp=datetime.now(),
            phone_hash=session.phone_hash,
            consent=True,
            agent_version="2.0",
            call_id=call_id,
            event_type="call_started"
        )
        storage_service.write_audit_log(audit_entry)
        
        # Record metrics
        observability_service.record_call_started(call_id, session.phone_hash)
        
        # Increment rate limit
        redis_service.increment_rate_limit(formatted_number)
        
        # Initiate Twilio call
        webhook_url_for_twilio = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/api/calls/webhook/{call_id}"
        
        twilio_call = telephony_service.initiate_call(
            to_number=formatted_number,
            webhook_url=webhook_url_for_twilio
        )
        
        # Update session with Twilio call SID
        redis_service.update_call_session(call_id, {
            "twilio_call_sid": twilio_call.sid,
            "status": "active",
            "started_at": datetime.now()
        })
        
        logger.info("Call initiated", call_id=call_id, phone_hash=session.phone_hash, 
                   twilio_sid=twilio_call.sid)
        
        return {
            "call_id": call_id,
            "status": "initiated",
            "phone_hash": session.phone_hash,
            "twilio_call_sid": twilio_call.sid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to initiate call", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to initiate call")

@app.get("/api/calls/status/{call_id}")
async def get_call_status(call_id: str) -> CallStatusResponse:
    """Get call status"""
    session = redis_service.get_call_session(call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return CallStatusResponse(
        call_id=session.call_id,
        status=session.status,
        phone_hash=session.phone_hash,
        started_at=session.started_at,
        completed_at=session.completed_at,
        adversarial_score=session.adversarial_score,
        extracted_fields=session.extracted_fields
    )

@app.post("/api/calls/webhook/{call_id}")
async def handle_twilio_webhook(call_id: str, request: Request, background_tasks: BackgroundTasks):
    """Handle Twilio webhook for call events"""
    try:
        form_data = await request.form()
        call_status = form_data.get("CallStatus")
        
        logger.info("Twilio webhook received", call_id=call_id, status=call_status)
        
        session = redis_service.get_call_session(call_id)
        if not session:
            logger.warning("Webhook for unknown call", call_id=call_id)
            return PlainTextResponse("OK")
        
        if call_status == "in-progress":
            # Call connected, start conversation
            response = VoiceResponse()
            
            # Initial greeting
            response.say("Hello! I'm calling to learn about your work experience. This call may be recorded for quality purposes. Do you consent to continue?")
            
            # Gather consent response
            gather = response.gather(
                input='speech',
                timeout=10,
                action=f"/api/calls/webhook/{call_id}/gather"
            )
            
            return PlainTextResponse(str(response), media_type="application/xml")
            
        elif call_status in ["completed", "failed", "busy", "no-answer"]:
            # Call ended
            redis_service.update_call_session(call_id, {
                "status": "completed" if call_status == "completed" else "failed",
                "completed_at": datetime.now()
            })
            
            # Process call completion in background
            background_tasks.add_task(process_call_completion, call_id, call_status)
        
        return PlainTextResponse("OK")
        
    except Exception as e:
        logger.error("Error handling Twilio webhook", call_id=call_id, error=str(e))
        return PlainTextResponse("OK")

@app.post("/api/calls/webhook/{call_id}/gather")
async def handle_speech_input(call_id: str, request: Request):
    """Handle speech input from Twilio"""
    try:
        form_data = await request.form()
        speech_result = form_data.get("SpeechResult", "").strip()
        
        logger.info("Speech input received", call_id=call_id, speech=speech_result[:100])
        
        session = redis_service.get_call_session(call_id)
        if not session:
            response = VoiceResponse()
            response.say("I'm sorry, there was an error. Goodbye.")
            response.hangup()
            return PlainTextResponse(str(response), media_type="application/xml")
        
        # Process speech with phone agent
        agent_input = {
            "user_input": speech_result,
            "call_metadata": {
                "call_id": call_id,
                "conversation_state": session.conversation_state
            }
        }
        
        agent_response = phone_agent.process(agent_input)
        
        # Extract data from agent response
        extracted_fields = agent_response.data.get("employment_timeline", [])
        adversarial_score = agent_response.data.get("adversarial_score", 0)
        is_complete = agent_response.data.get("is_complete", False)
        
        # Update session with new state
        redis_service.update_call_session(call_id, {
            "conversation_state": agent_response.data,
            "extracted_fields": {"timeline_entries": len(extracted_fields)},
            "adversarial_score": adversarial_score
        })
        
        # Generate TwiML response
        response = VoiceResponse()
        
        if is_complete or agent_response.next_action == "complete_call":
            response.say(agent_response.message + " Thank you for your time. Goodbye!")
            response.hangup()
        else:
            response.say(agent_response.message)
            
            # Continue gathering speech
            gather = response.gather(
                input='speech',
                timeout=10,
                action=f"/api/calls/webhook/{call_id}/gather"
            )
        
        return PlainTextResponse(str(response), media_type="application/xml")
        
    except Exception as e:
        logger.error("Error handling speech input", call_id=call_id, error=str(e))
        
        response = VoiceResponse()
        response.say("I'm sorry, there was an error. Goodbye.")
        response.hangup()
        return PlainTextResponse(str(response), media_type="application/xml")

async def process_call_completion(call_id: str, call_status: str):
    """Process call completion in background"""
    try:
        session = redis_service.get_call_session(call_id)
        if not session:
            return
        
        logger.info("Processing call completion", call_id=call_id, status=call_status)
        
        if call_status == "completed" and session.extracted_fields:
            # Create worker profile
            profile = WorkerProfile(
                phone_hash=session.phone_hash,
                call_id=call_id,
                extracted_at=datetime.now(),
                adversarial_score=session.adversarial_score,
                confidence_score=0.8,  # Calculate based on extraction quality
                consent_given=session.consent_given,
                data_retention_until=datetime.now() + timedelta(days=30),
                **session.extracted_fields
            )
            
            # Store profile in object storage
            storage_service.store_worker_profile(profile)
            
            # Queue for webhook delivery if webhook URL provided
            webhook_url = os.getenv("DEFAULT_WEBHOOK_URL")
            if webhook_url:
                webhook_service.queue_for_delivery(call_id, webhook_url, profile)
            
            # Record metrics
            observability_service.record_call_completed(
                call_id, 
                session.adversarial_score, 
                len(session.extracted_fields)
            )
            
            logger.info("Call processing completed", call_id=call_id)
        else:
            # Record failed call
            observability_service.record_call_failed(call_id, call_status)
        
        # Write completion audit log
        audit_entry = AuditLogEntry(
            timestamp=datetime.now(),
            phone_hash=session.phone_hash,
            consent=session.consent_given,
            agent_version="2.0",
            call_id=call_id,
            event_type="call_completed" if call_status == "completed" else "call_failed"
        )
        storage_service.write_audit_log(audit_entry)
        
        # Clean up session after some time (keep for debugging)
        # Could implement TTL extension here if needed
        
    except Exception as e:
        logger.error("Error processing call completion", call_id=call_id, error=str(e))

# Health and Monitoring Endpoints

@app.get("/health")
async def health_check():
    """System health check"""
    return observability_service.get_system_health()

@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    return PlainTextResponse(
        observability_service.get_prometheus_metrics(),
        media_type="text/plain"
    )

@app.get("/api/analytics")
async def get_analytics():
    """Get call analytics"""
    return {
        "analytics_24h": observability_service.get_call_analytics(24),
        "analytics_1h": observability_service.get_call_analytics(1),
        "system_health": observability_service.get_system_health()
    }

@app.get("/api/system/stats")
async def get_system_stats():
    """Get detailed system statistics"""
    return {
        "redis_stats": redis_service.get_system_stats(),
        "storage_stats": storage_service.get_storage_stats(),
        "webhook_stats": webhook_service.get_outbox_stats(),
        "observability_summary": observability_service.export_metrics_summary()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
