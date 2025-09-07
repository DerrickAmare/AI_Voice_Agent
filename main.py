"""
AI Voice Agent - High-Volume Outbound Calling System
Redis-based architecture with object storage and webhook delivery
"""

import os
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse, Response
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
from src.agents.ai_conversation_manager import AIConversationManager
from src.agents.resume_analyzer_agent import ResumeAnalyzerAgent
from src.services.resume_builder import ResumeBuilder

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
phone_agent: AIConversationManager = None
resume_analyzer: ResumeAnalyzerAgent = None
resume_builder: ResumeBuilder = None

# Background task for webhook processing
webhook_processor_task: Optional[asyncio.Task] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global redis_service, storage_service, webhook_service, observability_service
    global telephony_service, phone_agent, resume_analyzer, resume_builder, webhook_processor_task
    
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
        
        # Initialize AI conversation manager
        phone_agent = AIConversationManager()
        logger.info("AI conversation manager initialized")
        
        # Initialize resume analyzer agent
        resume_analyzer = ResumeAnalyzerAgent()
        logger.info("Resume analyzer agent initialized")
        
        # Initialize resume builder
        resume_builder = ResumeBuilder()
        logger.info("Resume builder initialized")
        
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

def _create_twiml_response(twiml_response: VoiceResponse) -> Response:
    """Create properly formatted TwiML response with correct headers and validation"""
    try:
        # Convert TwiML to string
        twiml_content = str(twiml_response)
        
        # Validate XML structure
        import xml.etree.ElementTree as ET
        try:
            ET.fromstring(twiml_content)
        except ET.ParseError as e:
            logger.error("Invalid TwiML XML generated", error=str(e), twiml=twiml_content[:200])
            # Return safe fallback TwiML
            fallback_response = VoiceResponse()
            fallback_response.say("I'm sorry, there was a technical issue. Goodbye.", voice='alice', language='en-US')
            fallback_response.hangup()
            twiml_content = str(fallback_response)
        
        # Ensure proper XML declaration and encoding
        if not twiml_content.startswith('<?xml'):
            twiml_content = '<?xml version="1.0" encoding="UTF-8"?>' + twiml_content
        
        # Create response with proper headers
        return Response(
            content=twiml_content,
            status_code=200,
            media_type="application/xml; charset=utf-8",
            headers={
                "Content-Type": "application/xml; charset=utf-8",
                "Cache-Control": "no-cache"
            }
        )
        
    except Exception as e:
        logger.error("Error creating TwiML response", error=str(e))
        # Return minimal safe TwiML on any error
        safe_twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="alice">Technical error. Goodbye.</Say><Hangup /></Response>'
        return Response(
            content=safe_twiml,
            status_code=200,
            media_type="application/xml; charset=utf-8",
            headers={
                "Content-Type": "application/xml; charset=utf-8",
                "Cache-Control": "no-cache"
            }
        )

def _generate_speech_hints(conversation_state: Dict[str, Any]) -> List[str]:
    """Generate context-aware speech hints for better Twilio recognition"""
    hints = ["yes", "no", "okay", "sure", "work", "job", "company", "employer"]
    
    # Add stage-specific hints
    stage = conversation_state.get("conversation_stage", "greeting")
    
    if stage == "work_history":
        hints.extend([
            "manager", "supervisor", "technician", "operator", "driver", "clerk",
            "construction", "manufacturing", "retail", "restaurant", "healthcare",
            "walmart", "mcdonalds", "target", "amazon", "fedex", "ups",
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
            "2020", "2021", "2022", "2023", "2024"
        ])
    elif stage == "education":
        hints.extend([
            "high school", "college", "university", "degree", "diploma",
            "bachelor", "associate", "graduate", "graduated"
        ])
    elif stage == "skills":
        hints.extend([
            "computer", "excel", "microsoft", "forklift", "welding",
            "customer service", "teamwork", "leadership"
        ])
    
    # Add hints from extracted data
    next_focus = conversation_state.get("next_question_focus", "")
    if "date" in next_focus.lower():
        hints.extend(["year", "month", "started", "ended", "current", "present"])
    elif "location" in next_focus.lower():
        hints.extend(["city", "state", "street", "avenue", "road"])
    
    return hints[:20]  # Limit to 20 hints for Twilio

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

# Serve React frontend (if built)
try:
    app.mount("/assets", StaticFiles(directory="client/dist/assets"), name="assets")
except:
    logger.warning("React build assets not found - client app may not be built")

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
        with open("client/dist/index.html", "r") as f:
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

@app.api_route("/api/calls/webhook/{call_id}", methods=["GET", "POST"])
async def handle_twilio_webhook(call_id: str, request: Request, background_tasks: BackgroundTasks):
    """Handle Twilio webhook for call events"""
    try:
        # Handle both GET and POST requests
        if request.method == "POST":
            form_data = await request.form()
            call_status = form_data.get("CallStatus")
        else:
            # GET request - assume initial call setup
            call_status = "in-progress"
        
        logger.info("Twilio webhook received", call_id=call_id, method=request.method, status=call_status)
        
        session = redis_service.get_call_session(call_id)
        if not session:
            logger.warning("Webhook for unknown call", call_id=call_id)
            return PlainTextResponse("OK")
        
        if call_status == "in-progress":
            # Call connected, start conversation with proper speech recognition
            response = VoiceResponse()
            
            # Initial greeting with proper speech settings
            gather = response.gather(
                input='speech',
                timeout=10,
                speechTimeout='auto',  # You confirmed this works on your trial
                action=f"/api/calls/webhook/{call_id}/gather",
                method='POST',
                language='en-US'
            )
            gather.say("Hello! I'm calling to learn about your work experience. This call may be recorded for quality purposes. Do you consent to continue?", 
                      voice='alice', language='en-US')
            
            # Fallback if no input - redirect to same endpoint to try again
            response.say("I didn't hear anything. Let me try again.", voice='alice')
            response.redirect(f"/api/calls/webhook/{call_id}")
            
            return _create_twiml_response(response)
            
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

@app.post("/api/calls/webhook/{call_id}/status")
async def handle_twilio_status_callback(call_id: str, request: Request, background_tasks: BackgroundTasks):
    """Handle Twilio status callback for call state changes"""
    try:
        form_data = await request.form()
        call_status = form_data.get("CallStatus")
        call_sid = form_data.get("CallSid")
        
        logger.info("Twilio status callback received", call_id=call_id, status=call_status, call_sid=call_sid)
        
        session = redis_service.get_call_session(call_id)
        if not session:
            logger.warning("Status callback for unknown call", call_id=call_id)
            return PlainTextResponse("OK")
        
        # Update session status
        if call_status in ["completed", "failed", "busy", "no-answer"]:
            redis_service.update_call_session(call_id, {
                "status": "completed" if call_status == "completed" else "failed",
                "completed_at": datetime.now()
            })
            
            # Process call completion in background
            background_tasks.add_task(process_call_completion, call_id, call_status)
        
        return PlainTextResponse("OK")
        
    except Exception as e:
        logger.error("Error handling Twilio status callback", call_id=call_id, error=str(e))
        return PlainTextResponse("OK")

@app.api_route("/api/calls/webhook/{call_id}/gather", methods=["GET", "POST"])
async def handle_speech_input(call_id: str, request: Request):
    """Handle speech input from Twilio"""
    try:
        # Handle both GET and POST requests
        if request.method == "POST":
            form_data = await request.form()
            speech_result = form_data.get("SpeechResult", "").strip()
        else:
            # GET request - no speech result
            speech_result = ""
        
        logger.info("Speech input received", call_id=call_id, method=request.method, 
                   speech=speech_result[:100] if speech_result else "No speech data")
        
        session = redis_service.get_call_session(call_id)
        if not session:
            response = VoiceResponse()
            response.say("I'm sorry, there was an error. Goodbye.", voice='alice', language='en-US')
            response.hangup()
            return _create_twiml_response(response)
        
        # Process speech with optimized phone agent
        agent_input = {
            "user_input": speech_result,
            "call_metadata": {
                "call_id": call_id,
                "conversation_state": session.conversation_state or {}
            }
        }
        
        agent_response = phone_agent.process(agent_input)
        
        # Extract data from agent response
        extracted_fields = agent_response.data.get("employment_timeline", [])
        adversarial_score = agent_response.data.get("adversarial_score", 0)
        is_complete = agent_response.data.get("is_complete", False)
        conversation_state = agent_response.data.get("conversation_state", {})
        
        # Update session with new state
        redis_service.update_call_session(call_id, {
            "conversation_state": agent_response.data,
            "extracted_fields": {"timeline_entries": len(extracted_fields)},
            "adversarial_score": adversarial_score
        })
        
        # Generate proper TwiML response with speech recognition
        response = VoiceResponse()
        
        if is_complete or agent_response.next_action == "complete_call":
            response.say(agent_response.message + " Thank you for your time. Goodbye!", 
                        voice='alice', language='en-US')
            response.hangup()
        else:
            # Continue conversation with proper speech settings
            gather = response.gather(
                input='speech',
                timeout=10,
                speechTimeout='auto',
                action=f"/api/calls/webhook/{call_id}/gather",
                method='POST',
                language='en-US'
            )
            gather.say(agent_response.message, voice='alice', language='en-US')
            
            # Fallback if no input - ask again
            response.say("I didn't hear anything. Let me ask that again.", voice='alice')
            
            # Second gather attempt
            gather2 = response.gather(
                input='speech',
                timeout=8,
                speechTimeout='auto',
                action=f"/api/calls/webhook/{call_id}/gather",
                method='POST',
                language='en-US'
            )
            gather2.say(agent_response.message, voice='alice', language='en-US')
            
            # Final fallback
            response.say("I'm having trouble hearing you. Thank you for your time. Goodbye.", voice='alice')
            response.hangup()
        
        return _create_twiml_response(response)
        
    except Exception as e:
        logger.error("Error handling speech input", call_id=call_id, error=str(e))
        
        # Return safe TwiML on any error - always ensure valid response
        response = VoiceResponse()
        response.say("I'm sorry, there was a technical issue. Let me try to continue.", 
                    voice='alice', language='en-US')
        
        # Try to continue with basic question
        gather = response.gather(
            input='speech',
            timeout=8,
            speechTimeout='auto',
            action=f"/api/calls/webhook/{call_id}/gather",
            method='POST',
            language='en-US'
        )
        gather.say("Can you tell me about your work experience?", voice='alice', language='en-US')
        
        # Final fallback if still having issues
        response.say("I'm having technical difficulties. Thank you for your time. Goodbye.", 
                    voice='alice', language='en-US')
        response.hangup()
        
        return _create_twiml_response(response)

async def process_call_completion(call_id: str, call_status: str):
    """Process call completion in background"""
    try:
        session = redis_service.get_call_session(call_id)
        if not session:
            return
        
        logger.info("Processing call completion", call_id=call_id, status=call_status)
        
        # Get linked resume request if exists
        request_id = getattr(session, 'request_id', None)
        request_data = None
        if request_id:
            request_data = redis_service.get_resume_request(request_id)
        
        if call_status == "completed" and session.extracted_fields:
            # If this is linked to a resume request, generate final resume
            if request_data:
                await complete_resume_generation(call_id, request_id, session, request_data)
            else:
                # Original worker profile creation for non-resume calls
                profile = WorkerProfile(
                    phone_hash=session.phone_hash,
                    call_id=call_id,
                    extracted_at=datetime.now(),
                    adversarial_score=session.adversarial_score,
                    confidence_score=0.8,
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
            
            # Update resume request status if linked
            if request_data:
                redis_service.update_resume_request(request_id, {"status": "failed"})
        
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
        
    except Exception as e:
        logger.error("Error processing call completion", call_id=call_id, error=str(e))

async def complete_resume_generation(call_id: str, request_id: str, session: CallSession, request_data: Dict[str, Any]):
    """Generate final resume from call data and uploaded resume"""
    try:
        logger.info("Generating final resume", request_id=request_id, call_id=call_id)
        
        # Combine uploaded resume + phone interview data
        final_resume_data = {
            "personal_info": {
                "name": request_data.get("full_name", ""),
                "email": request_data.get("email", ""),
                "phone": request_data.get("phone_number", "")
            },
            "uploaded_resume": request_data.get("resume_data", {}),
            "interview_data": session.conversation_state,
            "employment_timeline": session.extracted_fields.get("employment_timeline", []),
            "adversarial_score": session.adversarial_score,
            "confidence_score": 0.8,
            "generated_at": datetime.now().isoformat()
        }
        
        # Use resume builder to create structured resume
        try:
            structured_resume = resume_builder.build_resume(final_resume_data)
            final_resume_data["structured_resume"] = structured_resume
        except Exception as e:
            logger.warning("Resume builder failed, using raw data", error=str(e))
            # Continue with raw data if resume builder fails
        
        # Update request status to completed
        redis_service.update_resume_request(request_id, {
            "status": "completed",
            "final_resume_data": final_resume_data,
            "completed_at": datetime.now().isoformat(),
            "call_id": call_id
        })
        
        logger.info("Resume generation completed", request_id=request_id)
        
    except Exception as e:
        logger.error("Error completing resume generation", request_id=request_id, error=str(e))
        redis_service.update_resume_request(request_id, {"status": "failed"})

# Resume Request API Endpoints (for React UI)

@app.post("/api/submit-request")
async def submit_request(
    phoneNumber: str = Form(...),
    fullName: str = Form(...),
    email: str = Form(""),
    callTime: str = Form("immediate"),
    resume: UploadFile = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Handle form submission with optional resume upload"""
    try:
        # Generate request ID
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        # Validate phone number
        try:
            parsed_number = phonenumbers.parse(phoneNumber, "US")
            if not phonenumbers.is_valid_number(parsed_number):
                raise HTTPException(status_code=400, detail="Invalid phone number")
            
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        
        # Process uploaded resume if provided
        resume_data = None
        conversation_hints = None
        if resume and resume.size > 0:
            try:
                file_content = await resume.read()
                file_type = resume.filename.split('.')[-1] if resume.filename else 'txt'
                resume_data = resume_analyzer.process_uploaded_file(file_content, file_type)
                
                # Extract conversation hints for better phone interview
                conversation_hints = resume_data.get("conversation_hints")
                logger.info("Resume processed successfully", request_id=request_id, file_type=file_type, 
                           has_hints=bool(conversation_hints))
            except Exception as e:
                logger.warning("Resume processing failed", request_id=request_id, error=str(e))
                # Continue without resume data
                resume_data = {"error": f"Failed to process resume: {str(e)}"}
        
        # Store request in Redis
        request_data = {
            "request_id": request_id,
            "phone_number": formatted_number,
            "full_name": fullName,
            "email": email,
            "call_time": callTime,
            "resume_data": resume_data,
            "conversation_hints": conversation_hints,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "scheduled_call_time": datetime.now().isoformat()
        }
        
        redis_service.store_resume_request(request_id, request_data)
        
        # Schedule phone call (immediate or later)
        if callTime == "immediate":
            # Initiate call immediately in background
            background_tasks.add_task(initiate_phone_call, request_id, formatted_number)
        
        logger.info("Resume request submitted", request_id=request_id, phone_number=formatted_number)
        
        return {"requestId": request_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error submitting request", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to submit request")

@app.get("/api/request-status/{request_id}")
async def get_request_status(request_id: str):
    """Get status of a resume request"""
    try:
        request_data = redis_service.get_resume_request(request_id)
        if not request_data:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return {
            "status": request_data.get("status", "pending"),
            "resumeData": request_data.get("final_resume_data") if request_data.get("status") == "completed" else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting request status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get status")

@app.get("/api/download-resume/{request_id}")
async def download_resume(request_id: str):
    """Download generated resume as PDF"""
    try:
        request_data = redis_service.get_resume_request(request_id)
        if not request_data or request_data.get("status") != "completed":
            raise HTTPException(status_code=404, detail="Resume not ready")
        
        # Generate PDF using ResumeBuilder
        resume_data = request_data.get("final_resume_data")
        if not resume_data:
            raise HTTPException(status_code=404, detail="Resume data not found")
        
        # Use resume builder to generate PDF
        pdf_content = resume_builder.generate_pdf(resume_data)
        
        # Save to temporary file and return
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_content)
            temp_path = temp_file.name
        
        return FileResponse(
            temp_path,
            media_type="application/pdf",
            filename=f"resume-{request_id}.pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error downloading resume", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to download resume")

@app.get("/api/user/{phone_number}/requests")
async def get_user_requests(phone_number: str):
    """Get all requests for a phone number"""
    try:
        # Validate and format phone number
        try:
            parsed_number = phonenumbers.parse(phone_number, "US")
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            formatted_number = phone_number  # Use as-is if parsing fails
        
        # Get all requests for this phone number from Redis
        requests = redis_service.get_user_requests(formatted_number)
        
        return {"requests": requests}
        
    except Exception as e:
        logger.error("Error getting user requests", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get requests")

async def initiate_phone_call(request_id: str, phone_number: str):
    """Background task to initiate phone call for resume request"""
    try:
        # Update status to SMS sent (simulated)
        redis_service.update_resume_request(request_id, {"status": "sms_sent"})
        
        # Wait a bit, then initiate call
        await asyncio.sleep(10)  # 10 second delay for demo
        
        # Get request data to access conversation hints
        request_data = redis_service.get_resume_request(request_id)
        conversation_hints = request_data.get("conversation_hints") if request_data else None
        
        # Generate call ID
        call_id = f"call_{uuid.uuid4().hex[:12]}"
        
        # Set up conversation hints in phone agent if available
        if conversation_hints and phone_agent:
            phone_agent.set_resume_hints(
                companies=conversation_hints.get("companies", []),
                titles=conversation_hints.get("titles", []),
                date_range=conversation_hints.get("date_range", ""),
                skills=conversation_hints.get("skills", [])
            )
            logger.info("Set conversation hints for call", call_id=call_id, hints_available=True)
        
        # Create call session linked to resume request
        session = redis_service.create_call_session(
            call_id=call_id,
            phone_number=phone_number,
            consent_given=True,
            request_id=request_id  # Link to resume request
        )
        
        # Update request status
        redis_service.update_resume_request(request_id, {
            "status": "in_call",
            "call_id": call_id
        })
        
        # Initiate Twilio call
        webhook_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/api/calls/webhook/{call_id}"
        
        try:
            twilio_call = telephony_service.initiate_call(phone_number, webhook_url)
            
            # Update session with Twilio call SID
            redis_service.update_call_session(call_id, {
                "twilio_call_sid": twilio_call.sid,
                "status": "active",
                "started_at": datetime.now()
            })
            
            logger.info("Phone call initiated for resume request", 
                       request_id=request_id, call_id=call_id, twilio_sid=twilio_call.sid)
                       
        except Exception as e:
            logger.error("Failed to initiate Twilio call", request_id=request_id, error=str(e))
            # Update status to failed
            redis_service.update_resume_request(request_id, {"status": "failed"})
        
    except Exception as e:
        logger.error("Error initiating phone call", request_id=request_id, error=str(e))
        redis_service.update_resume_request(request_id, {"status": "failed"})

# Health and Monitoring Endpoints

@app.get("/health")
async def health_check():
    """System health check"""
    return observability_service.get_system_health()

@app.api_route("/api/test-twiml/{call_id}", methods=["GET", "POST"])
async def test_twiml_endpoint(call_id: str):
    """Test endpoint to verify TwiML generation works with proper speech settings"""
    try:
        response = VoiceResponse()
        gather = response.gather(
            input='speech',
            timeout=10,
            speechTimeout='auto',
            action=f"/api/calls/webhook/{call_id}/gather",
            method='POST',
            language='en-US'
        )
        gather.say("This is a test. Please say something.", voice='alice', language='en-US')
        response.say("Test completed. Goodbye.", voice='alice', language='en-US')
        response.hangup()
        
        return _create_twiml_response(response)
    except Exception as e:
        logger.error("TwiML test failed", error=str(e))
        return PlainTextResponse("TwiML generation failed", status_code=500)

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

# Serve React app for client-side routing
@app.get("/{path:path}")
async def serve_react_app(path: str):
    """Serve React app for all non-API routes"""
    # Don't serve React for API routes
    if path.startswith("api/") or path.startswith("health") or path.startswith("metrics"):
        raise HTTPException(status_code=404, detail="Not found")
    
    try:
        # Try to serve the React build
        return FileResponse("client/dist/index.html")
    except FileNotFoundError:
        # Fallback to basic HTML if React build not found
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Resume Builder</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>AI Resume Builder</h1>
            <p>React build not found. To use the full UI:</p>
            <ol>
                <li>cd client</li>
                <li>npm install</li>
                <li>npm run build</li>
            </ol>
            <p><a href="/docs">API Documentation</a></p>
            <p><a href="/health">System Health</a></p>
        </body>
        </html>
        """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
