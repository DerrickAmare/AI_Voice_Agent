"""
Conversation Agent - Handles natural conversation flow for resume building
"""

from typing import Dict, Any
from .base_agent import BaseAgent, AgentResponse
import logging

logger = logging.getLogger(__name__)

class ConversationAgent(BaseAgent):
    """Agent responsible for natural conversation flow and information gathering"""
    
    def __init__(self):
        system_prompt = """You are a professional career counselor and resume expert with 15+ years of experience. 
Your role is to guide users through building their resume through natural, engaging conversation.

CORE PRINCIPLES:
- Be warm, encouraging, and professional
- Ask one focused question at a time
- Dig deeper when you sense there's more to uncover
- Help users articulate their achievements in quantifiable terms
- Guide them to think about skills they might have overlooked
- Make the process feel like a friendly consultation, not an interrogation

CONVERSATION FLOW:
1. Start with basic information (name, contact, target role)
2. Work experience (current and previous roles)
3. Education and certifications
4. Skills and competencies
5. Achievements and accomplishments
6. Additional sections (projects, volunteer work, etc.)

QUESTIONING STRATEGY:
- Use follow-up questions to get specific details
- Ask for metrics, numbers, and quantifiable results
- Help users identify transferable skills
- Encourage storytelling about challenges overcome
- Ask about leadership, teamwork, and problem-solving examples

RESPONSE FORMAT:
- Keep responses conversational and encouraging
- Acknowledge what they've shared before asking the next question
- Provide gentle guidance when they seem stuck
- Celebrate their achievements and help them see their value

Remember: Your goal is to help them create a compelling resume by drawing out their best stories and achievements through natural conversation."""

        super().__init__(
            name="ConversationAgent",
            role="Career Counselor & Resume Expert",
            system_prompt=system_prompt
        )
        
        self.conversation_stage = "greeting"
        self.resume_data = {}
        self.current_section = None
        
    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process conversation input and determine next steps"""
        try:
            user_input = input_data.get('user_input', '')
            session_data = input_data.get('session_data', {})
            
            # Update resume data with any new information
            if 'resume_data' in input_data:
                self.resume_data.update(input_data['resume_data'])
            
            # Determine conversation stage
            self._update_conversation_stage(user_input, session_data)
            
            # Generate response based on current stage
            response_text = self._generate_stage_response(user_input, session_data)
            
            # Determine if conversation is complete
            is_complete = self._is_conversation_complete()
            
            # Add to conversation history
            self.add_to_history("user", user_input)
            self.add_to_history("assistant", response_text)
            
            return AgentResponse(
                success=True,
                message=response_text,
                data={
                    "conversation_stage": self.conversation_stage,
                    "resume_data": self.resume_data,
                    "is_complete": is_complete,
                    "next_section": self._get_next_section()
                },
                next_action="continue_conversation" if not is_complete else "analyze_resume",
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"ConversationAgent error: {e}")
            return AgentResponse(
                success=False,
                message="I apologize, but I encountered an error. Let's continue with your resume.",
                confidence=0.0
            )
    
    def _update_conversation_stage(self, user_input: str, session_data: Dict[str, Any]):
        """Update the current conversation stage based on progress"""
        if not self.resume_data:
            self.conversation_stage = "greeting"
        elif 'name' not in self.resume_data:
            self.conversation_stage = "basic_info"
        elif 'experience' not in self.resume_data or len(self.resume_data.get('experience', [])) == 0:
            self.conversation_stage = "experience"
        elif 'education' not in self.resume_data:
            self.conversation_stage = "education"
        elif 'skills' not in self.resume_data:
            self.conversation_stage = "skills"
        elif 'achievements' not in self.resume_data:
            self.conversation_stage = "achievements"
        else:
            self.conversation_stage = "completion"
    
    def _generate_stage_response(self, user_input: str, session_data: Dict[str, Any]) -> str:
        """Generate response based on current conversation stage"""
        
        # Add context about current stage and resume data
        context = f"""
Current conversation stage: {self.conversation_stage}
Current resume data: {self.resume_data}
User input: {user_input}

Based on this context, provide an appropriate response that:
1. Acknowledges what they've shared
2. Asks the next logical question
3. Guides them toward completing their resume
4. Maintains a warm, professional tone
"""
        
        return self.call_openai(context)
    
    def _is_conversation_complete(self) -> bool:
        """Determine if the conversation has gathered enough information"""
        required_sections = ['name', 'experience', 'education', 'skills']
        return all(section in self.resume_data for section in required_sections)
    
    def _get_next_section(self) -> str:
        """Get the next section to focus on"""
        if 'name' not in self.resume_data:
            return "basic_info"
        elif 'experience' not in self.resume_data:
            return "experience"
        elif 'education' not in self.resume_data:
            return "education"
        elif 'skills' not in self.resume_data:
            return "skills"
        else:
            return "completion"
    
    def extract_information(self, user_input: str) -> Dict[str, Any]:
        """Extract structured information from user input"""
        extraction_prompt = f"""
Extract resume information from this user input: "{user_input}"

Return a JSON object with any relevant information found. Possible fields:
- name, email, phone, location
- job_title, company, dates, responsibilities, achievements
- degree, school, graduation_date, gpa
- skills, certifications, languages
- projects, volunteer_work

Only include fields where you found clear information. Return empty object {{}} if no clear information found.
"""
        
        try:
            response = self.call_openai(extraction_prompt)
            # In a real implementation, you'd parse the JSON response
            # For now, we'll do basic keyword extraction
            extracted = {}
            
            # Simple keyword-based extraction (in production, use more sophisticated NLP)
            if any(word in user_input.lower() for word in ['worked', 'job', 'position', 'role']):
                extracted['has_experience'] = True
            if any(word in user_input.lower() for word in ['degree', 'university', 'college', 'graduated']):
                extracted['has_education'] = True
            if any(word in user_input.lower() for word in ['skill', 'proficient', 'experienced', 'expert']):
                extracted['has_skills'] = True
                
            return extracted
        except Exception as e:
            logger.error(f"Information extraction error: {e}")
            return {}
