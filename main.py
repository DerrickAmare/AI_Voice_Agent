import logging
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import tempfile
import json

from src.services.voice_service import VoiceService
from src.services.conversation_engine import ConversationEngine
from src.services.resume_parser import ResumeParser
from src.services.resume_builder import ResumeBuilder
from src.services.agent_service import AgentService
from src.models.resume_models import Resume

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice AI Resume Builder", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
voice_service = VoiceService()
conversation_engine = ConversationEngine()
resume_parser = ResumeParser()
resume_builder = ResumeBuilder()
agent_service = AgentService()

# Global state (in production, use a proper database)
conversation_sessions = {}

class ConversationRequest(BaseModel):
    session_id: str
    user_input: str

class ConversationResponse(BaseModel):
    session_id: str
    response: str
    is_complete: bool
    resume_data: Optional[Dict[str, Any]] = None

class VoiceRequest(BaseModel):
    session_id: str
    text: str

class VoiceSessionRequest(BaseModel):
    session_id: str

class VoiceResponse(BaseModel):
    session_id: str
    success: bool
    message: str

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """Serve the main application page"""
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/api/conversation/start")
async def start_conversation(request: Dict[str, str]):
    """Start a new conversation session"""
    session_id = request["session_id"]
    
    try:
        # Initialize conversation
        response = conversation_engine.start_conversation()
        conversation_sessions[session_id] = {
            "engine": conversation_engine,
            "resume": conversation_engine.get_resume()
        }
        
        return {"session_id": session_id, "response": response, "is_complete": False}
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversation/continue")
async def continue_conversation(request: ConversationRequest):
    """Continue an existing conversation"""
    session_id = request.session_id
    
    if session_id not in conversation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = conversation_sessions[session_id]
        engine = session["engine"]
        
        response, is_complete = engine.process_response(request.user_input)
        
        # Update session
        session["resume"] = engine.get_resume()
        
        result = {
            "session_id": session_id,
            "response": response,
            "is_complete": is_complete
        }
        
        if is_complete:
            result["resume_data"] = session["resume"].dict()
        
        return result
    except Exception as e:
        logger.error(f"Error continuing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse an existing resume"""
    try:
        # Read file content
        content = await file.read()
        
        if file.filename.endswith('.txt'):
            text_content = content.decode('utf-8')
        else:
            # For PDF files, you would need additional processing
            raise HTTPException(status_code=400, detail="PDF parsing not implemented yet")
        
        # Parse resume
        parsed_resume = resume_parser.parse_text_resume(text_content)
        
        # Start conversation with existing resume
        session_id = f"session_{len(conversation_sessions)}_{file.filename}"
        conversation_engine.start_conversation(parsed_resume)
        
        conversation_sessions[session_id] = {
            "engine": conversation_engine,
            "resume": parsed_resume
        }
        
        # Get first question
        response = conversation_engine._get_next_question()
        
        return {
            "success": True,
            "session_id": session_id,
            "message": response
        }
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/speak")
async def speak_text(request: VoiceRequest):
    """Convert text to speech"""
    try:
        voice_service.speak_async(request.text)
        return {"session_id": request.session_id, "success": True, "message": "Speaking"}
    except Exception as e:
        logger.error(f"Error with TTS: {e}")
        return {"session_id": request.session_id, "success": False, "message": str(e)}

@app.post("/api/voice/start-listening")
async def start_listening(request: VoiceSessionRequest):
    """Start voice listening"""
    try:
        # In a real implementation, you would handle voice input here
        return {"session_id": request.session_id, "success": True, "message": "Listening started"}
    except Exception as e:
        logger.error(f"Error starting listening: {e}")
        return {"session_id": request.session_id, "success": False, "message": str(e)}

@app.post("/api/voice/stop-listening")
async def stop_listening(request: VoiceSessionRequest):
    """Stop voice listening"""
    try:
        # In a real implementation, you would handle stopping voice input here
        return {"session_id": request.session_id, "success": True, "message": "Listening stopped"}
    except Exception as e:
        logger.error(f"Error stopping listening: {e}")
        return {"session_id": request.session_id, "success": False, "message": str(e)}

@app.get("/api/resume/download/{format}")
async def download_resume(format: str, session_id: str):
    """Download resume in specified format"""
    if session_id not in conversation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = conversation_sessions[session_id]
        resume = session["resume"]
        
        if format == "html":
            content = resume_builder.build_html_resume(resume)
            return HTMLResponse(content=content)
        elif format == "text":
            content = resume_builder.build_text_resume(resume)
            return {"content": content}
        elif format == "pdf":
            # Generate PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                success = resume_builder.build_pdf_resume(resume, tmp_file.name)
                if success:
                    return FileResponse(tmp_file.name, filename="resume.pdf")
                else:
                    raise HTTPException(status_code=500, detail="PDF generation failed")
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
    except Exception as e:
        logger.error(f"Error downloading resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "voice_service_available": voice_service.is_available(),
        "active_sessions": len(conversation_sessions)
    }



# Agent System Endpoints
@app.post("/api/agents/start")
async def start_agent_conversation(request: Dict[str, str]):
    """Start a new agent-powered conversation session"""
    session_id = request.get("session_id", f"agent_session_{len(conversation_sessions)}")
    target_role = request.get("target_role", "")
    industry = request.get("industry", "")
    
    try:
        result = agent_service.start_conversation(session_id, target_role, industry)
        return result
    except Exception as e:
        logger.error(f"Error starting agent conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/continue")
async def continue_agent_conversation(request: ConversationRequest):
    """Continue an agent-powered conversation"""
    session_id = request.session_id
    user_input = request.user_input
    
    try:
        result = agent_service.continue_conversation(session_id, user_input)
        return result
    except Exception as e:
        logger.error(f"Error continuing agent conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/format")
async def format_resume_with_agents(request: Dict[str, str]):
    """Format resume using the agent system"""
    session_id = request.get("session_id")
    output_format = request.get("format", "html")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    try:
        result = agent_service.format_resume(session_id, output_format)
        return result
    except Exception as e:
        logger.error(f"Error formatting resume with agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/status/{session_id}")
async def get_agent_session_status(session_id: str):
    """Get the status of an agent session"""
    try:
        result = agent_service.get_session_status(session_id)
        return result
    except Exception as e:
        logger.error(f"Error getting agent session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/info")
async def get_agent_info():
    """Get information about available agents"""
    try:
        result = agent_service.get_available_agents()
        return result
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agents/session/{session_id}")
async def reset_agent_session(session_id: str):
    """Reset an agent session"""
    try:
        result = agent_service.reset_session(session_id)
        return result
    except Exception as e:
        logger.error(f"Error resetting agent session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
