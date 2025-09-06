"""
Agent API routes
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from src.services.agent_service import AgentService
from src.api.routes.conversation import ConversationRequest

router = APIRouter()

# Initialize agent service
agent_service = AgentService()

@router.post("/start")
async def start_agent_conversation(request: Dict[str, str]):
    """Start a new agent-powered conversation session"""
    session_id = request.get("session_id", f"agent_session_{len(agent_service.sessions)}")
    target_role = request.get("target_role", "")
    industry = request.get("industry", "")
    
    try:
        result = agent_service.start_conversation(session_id, target_role, industry)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/continue")
async def continue_agent_conversation(request: ConversationRequest):
    """Continue an agent-powered conversation"""
    session_id = request.session_id
    user_input = request.user_input
    
    try:
        result = agent_service.continue_conversation(session_id, user_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/format")
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{session_id}")
async def get_agent_session_status(session_id: str):
    """Get the status of an agent session"""
    try:
        result = agent_service.get_session_status(session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info")
async def get_agent_info():
    """Get information about available agents"""
    try:
        result = agent_service.get_available_agents()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def reset_agent_session(session_id: str):
    """Reset an agent session"""
    try:
        result = agent_service.reset_session(session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
