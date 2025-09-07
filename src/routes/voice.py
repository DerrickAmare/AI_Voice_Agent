"""
Voice API routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.voice_service import VoiceService

router = APIRouter()

# Initialize voice service
voice_service = VoiceService()

class VoiceRequest(BaseModel):
    session_id: str
    text: str

class VoiceSessionRequest(BaseModel):
    session_id: str

class VoiceResponse(BaseModel):
    session_id: str
    success: bool
    message: str

@router.post("/speak")
async def speak_text(request: VoiceRequest):
    """Convert text to speech"""
    try:
        voice_service.speak_async(request.text)
        return {"session_id": request.session_id, "success": True, "message": "Speaking"}
    except Exception as e:
        return {"session_id": request.session_id, "success": False, "message": str(e)}

@router.post("/start-listening")
async def start_listening(request: VoiceSessionRequest):
    """Start voice listening"""
    try:
        # In a real implementation, you would handle voice input here
        return {"session_id": request.session_id, "success": True, "message": "Listening started"}
    except Exception as e:
        return {"session_id": request.session_id, "success": False, "message": str(e)}

@router.post("/stop-listening")
async def stop_listening(request: VoiceSessionRequest):
    """Stop voice listening"""
    try:
        # In a real implementation, you would handle stopping voice input here
        return {"session_id": request.session_id, "success": True, "message": "Listening stopped"}
    except Exception as e:
        return {"session_id": request.session_id, "success": False, "message": str(e)}
