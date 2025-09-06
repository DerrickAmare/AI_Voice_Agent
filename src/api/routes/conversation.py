"""
Conversation API routes
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

from src.services.conversation_engine import ConversationEngine

router = APIRouter()

# Initialize conversation engine
conversation_engine = ConversationEngine()

# Global state (in production, use a proper database)
conversation_sessions = {}

class ConversationRequest(BaseModel):
    session_id: str
    user_input: str

class ConversationResponse(BaseModel):
    session_id: str
    response: str
    is_complete: bool
    resume_data: Dict[str, Any] = None

@router.post("/start")
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
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/continue")
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
        raise HTTPException(status_code=500, detail=str(e))
