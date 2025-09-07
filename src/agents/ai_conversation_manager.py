"""
AI Conversation Manager - OpenAI-powered phone conversation handler
Focused on comprehensive resume building through natural conversation
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent, AgentResponse

# Import OpenAI with new API
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except ImportError:
    # Fallback for older versions
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    client = None

logger = logging.getLogger(__name__)

class AIConversationManager(BaseAgent):
    """OpenAI-powered conversation manager for resume building phone calls"""
    
    def __init__(self):
        super().__init__(
            name="AIConversationManager",
            role="AI Resume Building Interviewer",
            system_prompt=""  # We'll use dynamic prompts
        )
        
        # OpenAI client is initialized globally
        pass
        
        self.conversation_state = {}
        self.resume_fields = {
            'personal_info': ['full_name', 'email', 'phone', 'address', 'city', 'state', 'zip_code'],
            'work_experience': ['employer', 'job_title', 'start_date', 'end_date', 'location', 'description'],
            'education': ['school_name', 'degree', 'field_of_study', 'graduation_date', 'location'],
            'skills': ['technical_skills', 'soft_skills', 'certifications'],
            'additional': ['languages', 'volunteer_work', 'achievements']
        }
        
        # Track conversation progress
        self.conversation_history = []
        self.extracted_data = {}
        self.employment_gaps = []
        self.conversation_complete = False
    
    def get_initial_prompt(self, user_name: str = None, existing_resume_text: str = None) -> str:
        """Generate initial conversation prompt"""
        base_prompt = f"""You are a professional resume builder assistant conducting a phone interview with {user_name if user_name else 'the caller'}. 

Your goal is to gather comprehensive information to build a complete professional resume. You need to be conversational, friendly, and thorough.

Key objectives:
1. Get complete work history with NO gaps - if there are gaps between jobs, ask what they did during that time
2. For each job: employer name, job title, location, start/end dates, key responsibilities
3. Education background
4. Skills and certifications
5. Any additional relevant experience

CRITICAL INSTRUCTIONS:
- Be prepared for users who may be reluctant to share information
- Ask follow-up questions and be persistent but polite
- If there are large gaps in employment (like 15+ years), specifically ask about other work they may have done in different fields
- Focus on ONE question at a time for phone conversation
- Keep responses conversational and under 2 sentences
- Use natural speech patterns appropriate for phone calls
- If you detect evasive answers, try different approaches (multiple choice, softer language)

EMPLOYMENT GAP STRATEGY:
- Break large time periods into smaller chunks (e.g., "What about between 1990 and 1995?")
- Suggest common industries: construction, manufacturing, retail, food service, healthcare, cleaning, security
- Ask about family responsibilities, education, health issues during gaps
- Be persistent but empathetic about sensitive periods

{f'Based on their existing resume: {existing_resume_text[:500]}...' if existing_resume_text else ''}

Start the conversation naturally and build rapport before diving into details.

Begin the conversation now:"""
        return base_prompt
    
    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process phone conversation input using OpenAI"""
        try:
            user_input = input_data.get('user_input', '').strip()
            call_metadata = input_data.get('call_metadata', {})
            call_id = call_metadata.get('call_id', 'unknown')
            
            # Initialize conversation if first interaction
            if not self.conversation_history:
                user_name = call_metadata.get('user_name')
                existing_resume = call_metadata.get('existing_resume_text')
                initial_prompt = self.get_initial_prompt(user_name, existing_resume)
                
                # Get initial AI response
                ai_response = self._get_ai_response([
                    {"role": "system", "content": initial_prompt}
                ])
                
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                
                return AgentResponse(
                    success=True,
                    message=ai_response,
                    data={
                        "conversation_stage": "greeting",
                        "extracted_data": self.extracted_data,
                        "employment_gaps": self.employment_gaps,
                        "is_complete": False,
                        "conversation_state": self.conversation_state
                    },
                    next_action="continue_conversation",
                    confidence=0.9
                )
            
            # Process user response
            return self.process_response(call_id, user_input)
            
        except Exception as e:
            logger.error(f"AIConversationManager error: {e}")
            return AgentResponse(
                success=False,
                message="I'm sorry, I'm having trouble processing that. Could you please repeat what you said?",
                confidence=0.1
            )
    
    def process_response(self, call_id: str, user_input: str) -> AgentResponse:
        """Process user response and generate AI reply"""
        try:
            # Add user input to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Get conversation context
            context = self.get_conversation_context(call_id)
            
            # Build messages for OpenAI
            messages = [
                {"role": "system", "content": context}
            ] + self.conversation_history[-10:]  # Keep last 10 exchanges for context
            
            # Get AI response
            ai_response = self._get_ai_response(messages)
            
            # Add AI response to history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Extract and store resume information
            self.extract_resume_data(call_id, user_input, ai_response)
            
            # Check if conversation is complete
            is_complete = self._check_conversation_complete(ai_response)
            
            # Detect employment gaps
            self._detect_employment_gaps()
            
            return AgentResponse(
                success=True,
                message=ai_response,
                data={
                    "conversation_stage": self._determine_conversation_stage(),
                    "extracted_data": self.extracted_data,
                    "employment_gaps": self.employment_gaps,
                    "is_complete": is_complete,
                    "conversation_state": {
                        "history_length": len(self.conversation_history),
                        "data_completeness": self._calculate_data_completeness()
                    },
                    "employment_timeline": self._build_employment_timeline()
                },
                next_action="complete_call" if is_complete else "continue_conversation",
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return AgentResponse(
                success=False,
                message="I'm sorry, I didn't catch that. Could you repeat what you said?",
                confidence=0.1
            )
    
    def get_conversation_context(self, call_id: str) -> str:
        """Get dynamic conversation context based on current state"""
        gaps_info = ""
        if self.employment_gaps:
            gaps_info = f"\nIMPORTANT: There are employment gaps that need to be addressed: {self.employment_gaps}"
        
        data_summary = ""
        if self.extracted_data:
            data_summary = f"\nData collected so far: {json.dumps(self.extracted_data, indent=2)}"
        
        return f"""Continue the resume building conversation. Focus on:
        1. Getting complete work history with specific details (employer, job title, dates, location, responsibilities)
        2. Identifying and filling employment gaps - be persistent but polite
        3. Collecting education and skills information
        4. Being conversational and phone-friendly (1-2 sentences max)
        5. Ask ONE focused question at a time
        
        CONVERSATION RULES:
        - If user is evasive, try softer approach or multiple choice questions
        - For large time gaps, break them into smaller periods
        - Suggest common industries if they're stuck: construction, manufacturing, retail, food service, healthcare
        - Use natural speech patterns: "I see", "That makes sense", "Okay"
        - Keep responses under 2 sentences for phone conversation
        
        {gaps_info}
        {data_summary}
        
        If you have gathered comprehensive work history, education, and skills, end with: "Thank you! I have all the information I need to build your resume."
        """
    
    def _get_ai_response(self, messages: List[Dict[str, str]]) -> str:
        """Get response from OpenAI API"""
        try:
            if client:
                # Use new OpenAI API (v1.0+)
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=150,  # Keep responses short for phone
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            else:
                # Fallback to old API
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=150,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "I'm sorry, I'm having trouble processing that. Could you please repeat what you said?"
    
    def extract_resume_data(self, call_id: str, user_input: str, ai_response: str):
        """Extract structured resume data from conversation using OpenAI"""
        extraction_prompt = f"""
        Extract resume information from this conversation segment and return as JSON:
        
        User: {user_input}
        Assistant: {ai_response}
        
        Extract any of these fields that are mentioned:
        - employer_name
        - job_title  
        - start_date (format as YYYY or MM/YYYY)
        - end_date (format as YYYY or MM/YYYY)
        - job_location
        - job_description
        - school_name
        - degree
        - graduation_date
        - skills
        - phone_number
        - email
        - address
        - full_name
        
        Return as JSON with only the fields that were mentioned. Use null for missing fields.
        Be very precise - only extract information that was explicitly stated.
        """
        
        try:
            if client:
                # Use new OpenAI API (v1.0+)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": extraction_prompt}],
                    max_tokens=200,
                    temperature=0
                )
                extracted_json = response.choices[0].message.content.strip()
            else:
                # Fallback to old API
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": extraction_prompt}],
                    max_tokens=200,
                    temperature=0
                )
                extracted_json = response.choices[0].message.content.strip()
            
            # Clean up JSON response (remove markdown formatting if present)
            if extracted_json.startswith("```json"):
                extracted_json = extracted_json.replace("```json", "").replace("```", "").strip()
            
            extracted_data = json.loads(extracted_json)
            
            # Merge with existing data
            for field, value in extracted_data.items():
                if value and value != "null":
                    if field not in self.extracted_data:
                        self.extracted_data[field] = []
                    
                    # Avoid duplicates
                    if value not in self.extracted_data[field]:
                        self.extracted_data[field].append({
                            "value": value,
                            "timestamp": datetime.now().isoformat(),
                            "confidence": 0.8
                        })
            
        except Exception as e:
            logger.error(f"Data extraction error: {e}")
    
    def _detect_employment_gaps(self):
        """Detect employment gaps from extracted data"""
        if 'start_date' not in self.extracted_data or 'end_date' not in self.extracted_data:
            return
        
        # Extract years from dates
        start_years = []
        end_years = []
        
        for date_entry in self.extracted_data.get('start_date', []):
            try:
                year = int(date_entry['value'].split('/')[0] if '/' in date_entry['value'] else date_entry['value'])
                start_years.append(year)
            except:
                continue
        
        for date_entry in self.extracted_data.get('end_date', []):
            try:
                year = int(date_entry['value'].split('/')[0] if '/' in date_entry['value'] else date_entry['value'])
                end_years.append(year)
            except:
                continue
        
        # Find gaps
        all_years = sorted(set(start_years + end_years))
        
        if len(all_years) >= 2:
            for i in range(len(all_years) - 1):
                gap_size = all_years[i + 1] - all_years[i]
                if gap_size > 2:  # Gap larger than 2 years
                    gap = {
                        "start_year": all_years[i],
                        "end_year": all_years[i + 1],
                        "gap_size": gap_size,
                        "resolved": False
                    }
                    
                    # Check if this gap already exists
                    gap_exists = any(
                        g["start_year"] == gap["start_year"] and g["end_year"] == gap["end_year"]
                        for g in self.employment_gaps
                    )
                    
                    if not gap_exists:
                        self.employment_gaps.append(gap)
    
    def _check_conversation_complete(self, ai_response: str) -> bool:
        """Check if conversation is complete based on AI response"""
        completion_phrases = [
            "thank you! i have all the information",
            "i have all the information i need",
            "that completes our interview",
            "we have everything we need"
        ]
        
        return any(phrase in ai_response.lower() for phrase in completion_phrases)
    
    def _determine_conversation_stage(self) -> str:
        """Determine current conversation stage"""
        if len(self.conversation_history) <= 2:
            return "greeting"
        elif not self.extracted_data.get('employer_name'):
            return "work_history"
        elif self.employment_gaps and not all(g.get('resolved') for g in self.employment_gaps):
            return "gap_resolution"
        elif not self.extracted_data.get('school_name'):
            return "education"
        elif not self.extracted_data.get('skills'):
            return "skills"
        else:
            return "completion"
    
    def _calculate_data_completeness(self) -> float:
        """Calculate how complete the resume data is"""
        required_fields = ['employer_name', 'job_title', 'start_date', 'end_date']
        optional_fields = ['school_name', 'degree', 'skills']
        
        score = 0.0
        
        # Required fields (70% of score)
        for field in required_fields:
            if field in self.extracted_data and self.extracted_data[field]:
                score += 0.175  # 70% / 4 fields
        
        # Optional fields (30% of score)
        for field in optional_fields:
            if field in self.extracted_data and self.extracted_data[field]:
                score += 0.1  # 30% / 3 fields
        
        return min(score, 1.0)
    
    def _build_employment_timeline(self) -> List[Dict[str, Any]]:
        """Build employment timeline from extracted data"""
        timeline = []
        
        employers = self.extracted_data.get('employer_name', [])
        titles = self.extracted_data.get('job_title', [])
        start_dates = self.extracted_data.get('start_date', [])
        end_dates = self.extracted_data.get('end_date', [])
        
        # Simple matching - in production, this would be more sophisticated
        max_entries = max(len(employers), len(titles), len(start_dates), len(end_dates))
        
        for i in range(max_entries):
            entry = {
                "employer": employers[i]['value'] if i < len(employers) else None,
                "title": titles[i]['value'] if i < len(titles) else None,
                "start_date": start_dates[i]['value'] if i < len(start_dates) else None,
                "end_date": end_dates[i]['value'] if i < len(end_dates) else None,
                "timestamp": datetime.now().isoformat()
            }
            
            if any(entry.values()):  # Only add if has some data
                timeline.append(entry)
        
        return timeline
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of conversation for debugging"""
        return {
            "total_exchanges": len(self.conversation_history),
            "extracted_fields": list(self.extracted_data.keys()),
            "employment_gaps": len(self.employment_gaps),
            "data_completeness": self._calculate_data_completeness(),
            "conversation_stage": self._determine_conversation_stage(),
            "is_complete": self.conversation_complete
        }
