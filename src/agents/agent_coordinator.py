"""
Agent Coordinator - Orchestrates the multi-agent resume building system
"""

from typing import Dict, Any, List, Optional
from .base_agent import AgentResponse
from .conversation_agent import ConversationAgent
from .resume_analyzer_agent import ResumeAnalyzerAgent
from .content_optimizer_agent import ContentOptimizerAgent
from .formatting_agent import FormattingAgent


class AgentCoordinator:
    """Coordinates the multi-agent resume building system"""
    
    def __init__(self):
        self.conversation_agent = ConversationAgent()
        self.analyzer_agent = ResumeAnalyzerAgent()
        self.optimizer_agent = ContentOptimizerAgent()
        self.formatting_agent = FormattingAgent()
        
        self.current_session = None
        self.session_data = {}
        self.resume_data = {}
        self.analysis_results = {}
        self.optimized_content = {}
        
    def start_new_session(self, session_id: str, target_role: str = "", industry: str = "") -> AgentResponse:
        """Start a new resume building session"""
        try:
            self.current_session = session_id
            self.session_data = {
                "session_id": session_id,
                "target_role": target_role,
                "industry": industry,
                "stage": "conversation",
                "resume_data": {},
                "conversation_history": []
            }
            
            # Initialize conversation
            response = self.conversation_agent.process({
                "user_input": "Hello, I'd like to build my resume",
                "session_data": self.session_data,
                "resume_data": {}
            })
            
            return AgentResponse(
                success=True,
                message=response.message,
                data={
                    "session_id": session_id,
                    "stage": "conversation",
                    "next_action": "continue_conversation"
                },
                next_action="continue_conversation",
                confidence=0.9
            )
            
        except Exception as e:
                return AgentResponse(
                success=False,
                message="Failed to start new session. Please try again.",
                confidence=0.0
            )
    
    def continue_conversation(self, session_id: str, user_input: str) -> AgentResponse:
        """Continue the conversation and gather resume information"""
        try:
            if self.current_session != session_id:
                return AgentResponse(
                    success=False,
                    message="Session not found. Please start a new session.",
                    confidence=0.0
                )
            
            # Update session data
            self.session_data["resume_data"] = self.resume_data
            
            # Process with conversation agent
            response = self.conversation_agent.process({
                "user_input": user_input,
                "session_data": self.session_data,
                "resume_data": self.resume_data
            })
            
            # Update resume data with any new information
            if response.data and "resume_data" in response.data:
                self.resume_data.update(response.data["resume_data"])
            
            # Check if conversation is complete
            if response.data and response.data.get("is_complete", False):
                # Move to analysis stage
                return self._transition_to_analysis()
            
            return response
            
        except Exception as e:
                return AgentResponse(
                success=False,
                message="Error processing your input. Please try again.",
                confidence=0.0
            )
    
    def _transition_to_analysis(self) -> AgentResponse:
        """Transition from conversation to analysis stage"""
        try:
            self.session_data["stage"] = "analysis"
            
            # Analyze the resume
            analysis_response = self.analyzer_agent.process({
                "resume_data": self.resume_data,
                "target_role": self.session_data.get("target_role", ""),
                "industry": self.session_data.get("industry", "")
            })
            
            if analysis_response.success:
                self.analysis_results = analysis_response.data
                
                # Move to optimization stage
                return self._transition_to_optimization()
            else:
                return analysis_response
                
        except Exception as e:
                return AgentResponse(
                success=False,
                message="Error analyzing resume. Please try again.",
                confidence=0.0
            )
    
    def _transition_to_optimization(self) -> AgentResponse:
        """Transition from analysis to optimization stage"""
        try:
            self.session_data["stage"] = "optimization"
            
            # Optimize the content
            optimization_response = self.optimizer_agent.process({
                "resume_data": self.resume_data,
                "target_role": self.session_data.get("target_role", ""),
                "industry": self.session_data.get("industry", ""),
                "analysis_results": self.analysis_results
            })
            
            if optimization_response.success:
                self.optimized_content = optimization_response.data
                
                return AgentResponse(
                    success=True,
                    message="Resume analysis and optimization completed! Your resume is ready for formatting.",
                    data={
                        "session_id": self.current_session,
                        "stage": "ready_for_formatting",
                        "resume_data": self.optimized_content,
                        "analysis_results": self.analysis_results
                    },
                    next_action="format_resume",
                    confidence=0.95
                )
            else:
                return optimization_response
                
        except Exception as e:
                return AgentResponse(
                success=False,
                message="Error optimizing resume content. Please try again.",
                confidence=0.0
            )
    
    def format_resume(self, session_id: str, output_format: str = "html") -> AgentResponse:
        """Format the resume in the requested format"""
        try:
            if self.current_session != session_id:
                return AgentResponse(
                    success=False,
                    message="Session not found. Please start a new session.",
                    confidence=0.0
                )
            
            if not self.optimized_content:
                return AgentResponse(
                    success=False,
                    message="No optimized content available. Please complete the conversation first.",
                    confidence=0.0
                )
            
            # Format the resume
            formatting_response = self.formatting_agent.process({
                "resume_data": self.optimized_content,
                "target_role": self.session_data.get("target_role", ""),
                "output_format": output_format
            })
            
            if formatting_response.success:
                return AgentResponse(
                    success=True,
                    message=f"Resume formatted successfully in {output_format.upper()} format!",
                    data={
                        "session_id": session_id,
                        "formatted_resume": formatting_response.data,
                        "download_ready": True
                    },
                    next_action="download_resume",
                    confidence=0.95
                )
            else:
                return formatting_response
                
        except Exception as e:
                return AgentResponse(
                success=False,
                message="Error formatting resume. Please try again.",
                confidence=0.0
            )
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a session"""
        if self.current_session != session_id:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "stage": self.session_data.get("stage", "unknown"),
            "target_role": self.session_data.get("target_role", ""),
            "industry": self.session_data.get("industry", ""),
            "resume_completeness": self._calculate_completeness(),
            "has_analysis": bool(self.analysis_results),
            "has_optimized_content": bool(self.optimized_content)
        }
    
    def _calculate_completeness(self) -> float:
        """Calculate how complete the resume data is"""
        required_fields = ['name', 'experience', 'education', 'skills']
        completed_fields = sum(1 for field in required_fields if self.resume_data.get(field))
        return (completed_fields / len(required_fields)) * 100
    
    def reset_session(self, session_id: str) -> AgentResponse:
        """Reset a session to start over"""
        if self.current_session == session_id:
            self.current_session = None
            self.session_data = {}
            self.resume_data = {}
            self.analysis_results = {}
            self.optimized_content = {}
            
            # Reset agent conversations
            self.conversation_agent.reset_conversation()
            
            return AgentResponse(
                success=True,
                message="Session reset successfully. You can start a new resume building process.",
                next_action="start_new_session",
                confidence=1.0
            )
        else:
            return AgentResponse(
                success=False,
                message="Session not found.",
                confidence=0.0
            )
    
    def get_available_agents(self) -> List[Dict[str, str]]:
        """Get list of available agents and their roles"""
        return [
            {
                "name": "ConversationAgent",
                "role": "Career Counselor & Resume Expert",
                "description": "Guides users through natural conversation to gather resume information"
            },
            {
                "name": "ResumeAnalyzerAgent", 
                "role": "Resume Analysis Expert",
                "description": "Analyzes resume content for gaps and improvements"
            },
            {
                "name": "ContentOptimizerAgent",
                "role": "Resume Content Strategist", 
                "description": "Optimizes resume content for maximum impact"
            },
            {
                "name": "FormattingAgent",
                "role": "Resume Formatting Specialist",
                "description": "Handles resume formatting and structure optimization"
            }
        ]
