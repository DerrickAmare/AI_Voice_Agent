"""
Agent Service - Integrates the multi-agent system with the existing application
"""

from typing import Dict, Any, Optional
from ..agents.agent_coordinator import AgentCoordinator
from ..agents.base_agent import AgentResponse


class AgentService:
    """Service that integrates the multi-agent system with the existing application"""
    
    def __init__(self):
        self.coordinator = AgentCoordinator()
        self.active_sessions = {}
        
    def start_conversation(self, session_id: str, target_role: str = "", industry: str = "") -> Dict[str, Any]:
        """Start a new conversation session with the agent system"""
        try:
            # Start new session with coordinator
            response = self.coordinator.start_new_session(session_id, target_role, industry)
            
            if response.success:
                self.active_sessions[session_id] = {
                    "coordinator": self.coordinator,
                    "target_role": target_role,
                    "industry": industry,
                    "stage": "conversation"
                }
                
                return {
                    "success": True,
                    "message": response.message,
                    "session_id": session_id,
                    "stage": "conversation",
                    "next_action": response.next_action
                }
            else:
                return {
                    "success": False,
                    "message": response.message,
                    "error": "Failed to start agent session"
                }
                
        except Exception as e:
                return {
                "success": False,
                "message": "Error starting conversation. Please try again.",
                "error": str(e)
            }
    
    def continue_conversation(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Continue the conversation with the agent system"""
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "message": "Session not found. Please start a new conversation.",
                    "error": "Session not found"
                }
            
            # Continue conversation with coordinator
            response = self.coordinator.continue_conversation(session_id, user_input)
            
            if response.success:
                # Update session stage
                if response.data and "stage" in response.data:
                    self.active_sessions[session_id]["stage"] = response.data["stage"]
                
                return {
                    "success": True,
                    "message": response.message,
                    "session_id": session_id,
                    "stage": response.data.get("stage", "conversation") if response.data else "conversation",
                    "is_complete": response.data.get("is_complete", False) if response.data else False,
                    "next_action": response.next_action,
                    "resume_data": response.data.get("resume_data", {}) if response.data else {}
                }
            else:
                return {
                    "success": False,
                    "message": response.message,
                    "error": "Failed to process conversation"
                }
                
        except Exception as e:
                return {
                "success": False,
                "message": "Error processing your input. Please try again.",
                "error": str(e)
            }
    
    def format_resume(self, session_id: str, output_format: str = "html") -> Dict[str, Any]:
        """Format the resume using the agent system"""
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "message": "Session not found. Please start a new conversation.",
                    "error": "Session not found"
                }
            
            # Format resume with coordinator
            response = self.coordinator.format_resume(session_id, output_format)
            
            if response.success:
                return {
                    "success": True,
                    "message": response.message,
                    "session_id": session_id,
                    "formatted_resume": response.data.get("formatted_resume", {}),
                    "download_ready": True
                }
            else:
                return {
                    "success": False,
                    "message": response.message,
                    "error": "Failed to format resume"
                }
                
        except Exception as e:
                return {
                "success": False,
                "message": "Error formatting resume. Please try again.",
                "error": str(e)
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the status of a session"""
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "message": "Session not found",
                    "error": "Session not found"
                }
            
            status = self.coordinator.get_session_status(session_id)
            
            return {
                "success": True,
                "session_status": status
            }
            
        except Exception as e:
                return {
                "success": False,
                "message": "Error getting session status",
                "error": str(e)
            }
    
    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """Reset a session"""
        try:
            if session_id not in self.active_sessions:
                return {
                    "success": False,
                    "message": "Session not found",
                    "error": "Session not found"
                }
            
            response = self.coordinator.reset_session(session_id)
            
            if response.success:
                # Remove from active sessions
                del self.active_sessions[session_id]
                
                return {
                    "success": True,
                    "message": response.message
                }
            else:
                return {
                    "success": False,
                    "message": response.message,
                    "error": "Failed to reset session"
                }
                
        except Exception as e:
                return {
                "success": False,
                "message": "Error resetting session",
                "error": str(e)
            }
    
    def get_available_agents(self) -> Dict[str, Any]:
        """Get information about available agents"""
        try:
            agents = self.coordinator.get_available_agents()
            
            return {
                "success": True,
                "agents": agents,
                "total_agents": len(agents)
            }
            
        except Exception as e:
                return {
                "success": False,
                "message": "Error getting agent information",
                "error": str(e)
            }
    
    def is_agent_session(self, session_id: str) -> bool:
        """Check if a session is using the agent system"""
        return session_id in self.active_sessions
    
    def get_active_sessions_count(self) -> int:
        """Get the number of active agent sessions"""
        return len(self.active_sessions)
