"""
Phone Conversation Agent - Specialized for phone-based resume building conversations
Handles adversarial users and employment gap detection
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent, AgentResponse
import logging
import re
from datetime import datetime, date

logger = logging.getLogger(__name__)

class PhoneConversationAgent(BaseAgent):
    """Agent specialized for phone conversations with focus on employment gaps and adversarial handling"""
    
    def __init__(self):
        system_prompt = """You are an expert phone interviewer specializing in employment history collection. 
Your goal is to build complete employment timelines, especially for users who may be evasive or adversarial.

CORE PRINCIPLES:
- Be warm, patient, and persistent
- Focus on employment timeline completion
- Detect and address employment gaps
- Handle adversarial/evasive responses professionally
- Use phone-appropriate language (conversational, not text-based)
- Ask one focused question at a time
- Break down large time periods into smaller chunks

CONVERSATION STRATEGY:
1. Start with basic info (name, current situation)
2. Build employment timeline chronologically
3. Identify and investigate gaps
4. Use industry suggestions for gap periods
5. Validate timeline consistency
6. Handle resistance with empathy

ADVERSARIAL HANDLING:
- Detect evasive responses ("I don't know", "Maybe", very short answers)
- Acknowledge concerns and explain purpose
- Use softer language when resistance detected
- Offer multiple choice options when stuck
- Build rapport before pushing for details

EMPLOYMENT GAP STRATEGIES:
- Break large gaps into smaller periods (e.g., 1977-2004 → 1977-1985, 1985-1995, etc.)
- Suggest common industries: construction, manufacturing, retail, food service, healthcare
- Ask about family responsibilities, education, health issues
- Validate with cross-references and consistency checks

PHONE CONVERSATION STYLE:
- Use natural speech patterns
- Include verbal acknowledgments ("I see", "That makes sense")
- Use pauses and transitions appropriately
- Speak clearly and at appropriate pace
- Confirm understanding frequently"""

        super().__init__(
            name="PhoneConversationAgent",
            role="Phone Employment Interviewer",
            system_prompt=system_prompt
        )
        
        self.conversation_stage = "greeting"
        self.employment_timeline = []
        self.identified_gaps = []
        self.adversarial_flags = []
        self.current_gap_focus = None
        self.industry_suggestions = [
            "construction", "manufacturing", "retail", "food service", 
            "healthcare", "cleaning", "security", "transportation",
            "warehouse", "assembly", "maintenance", "landscaping"
        ]
    
    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process phone conversation input"""
        try:
            user_input = input_data.get('user_input', '').strip()
            call_metadata = input_data.get('call_metadata', {})
            
            # Detect adversarial behavior
            adversarial_score = self._detect_adversarial_behavior(user_input)
            if adversarial_score > 3:
                self.adversarial_flags.append({
                    "timestamp": datetime.now().isoformat(),
                    "input": user_input,
                    "score": adversarial_score
                })
            
            # Extract employment information
            extracted_info = self._extract_employment_info(user_input)
            if extracted_info:
                self._update_employment_timeline(extracted_info)
            
            # Detect employment gaps
            gaps = self._detect_employment_gaps()
            if gaps:
                self.identified_gaps.extend(gaps)
            
            # Generate appropriate response
            response_text = self._generate_phone_response(user_input, call_metadata)
            
            # Determine completion status
            completion_score = self._calculate_completion_score()
            is_complete = completion_score > 0.8
            
            return AgentResponse(
                success=True,
                message=response_text,
                data={
                    "employment_timeline": self.employment_timeline,
                    "identified_gaps": self.identified_gaps,
                    "adversarial_score": len(self.adversarial_flags),
                    "completion_score": completion_score,
                    "conversation_stage": self.conversation_stage,
                    "is_complete": is_complete
                },
                next_action="continue_conversation" if not is_complete else "complete_call",
                confidence=max(0.3, 1.0 - (adversarial_score / 10))
            )
            
        except Exception as e:
            logger.error(f"PhoneConversationAgent error: {e}")
            return AgentResponse(
                success=False,
                message="I'm sorry, I didn't catch that. Could you repeat what you said?",
                confidence=0.1
            )
    
    def _detect_adversarial_behavior(self, user_input: str) -> int:
        """Detect adversarial/evasive behavior (0-10 scale)"""
        score = 0
        user_input_lower = user_input.lower()
        
        # Very short responses
        if len(user_input.split()) <= 2:
            score += 2
        
        # Evasive phrases
        evasive_phrases = [
            "i don't know", "maybe", "i guess", "whatever", 
            "i don't remember", "not sure", "don't care"
        ]
        for phrase in evasive_phrases:
            if phrase in user_input_lower:
                score += 2
                break
        
        # Hostile language
        hostile_words = ["no", "stop", "leave me alone", "annoying", "stupid"]
        for word in hostile_words:
            if word in user_input_lower:
                score += 3
                break
        
        # Contradictory information (basic check)
        if any(word in user_input_lower for word in ["actually", "wait", "i mean"]):
            score += 1
        
        # Repeated same response pattern
        if hasattr(self, 'last_responses'):
            if user_input in self.last_responses[-3:]:
                score += 2
        else:
            self.last_responses = []
        
        self.last_responses.append(user_input)
        if len(self.last_responses) > 5:
            self.last_responses.pop(0)
        
        return min(score, 10)
    
    def _extract_employment_info(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Extract employment information from user input"""
        info = {}
        
        # Extract years
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, user_input)
        if years:
            info['years_mentioned'] = [int(y) for y in re.findall(r'\b(19|20)\d{2}\b', user_input)]
        
        # Extract company names (basic heuristic)
        company_indicators = ['worked at', 'job at', 'employed by', 'company called']
        for indicator in company_indicators:
            if indicator in user_input.lower():
                # Try to extract company name after indicator
                parts = user_input.lower().split(indicator)
                if len(parts) > 1:
                    potential_company = parts[1].split()[0:3]  # Take next few words
                    info['company'] = ' '.join(potential_company).strip('.,')
        
        # Extract job titles
        job_keywords = [
            'manager', 'supervisor', 'worker', 'operator', 'technician',
            'assistant', 'clerk', 'driver', 'mechanic', 'welder',
            'assembler', 'inspector', 'foreman', 'lead'
        ]
        for keyword in job_keywords:
            if keyword in user_input.lower():
                info['job_title'] = keyword
                break
        
        # Extract industries
        for industry in self.industry_suggestions:
            if industry in user_input.lower():
                info['industry'] = industry
                break
        
        return info if info else None
    
    def _update_employment_timeline(self, info: Dict[str, Any]):
        """Update employment timeline with new information"""
        # Simple timeline update - in production, this would be more sophisticated
        timeline_entry = {
            "timestamp": datetime.now().isoformat(),
            "info": info
        }
        self.employment_timeline.append(timeline_entry)
    
    def _detect_employment_gaps(self) -> List[Dict[str, Any]]:
        """Detect gaps in employment timeline"""
        gaps = []
        
        # Extract all years mentioned
        all_years = []
        for entry in self.employment_timeline:
            if 'years_mentioned' in entry['info']:
                all_years.extend(entry['info']['years_mentioned'])
        
        if len(all_years) >= 2:
            all_years = sorted(set(all_years))
            
            # Look for gaps larger than 2 years
            for i in range(len(all_years) - 1):
                gap_size = all_years[i + 1] - all_years[i]
                if gap_size > 2:
                    gaps.append({
                        "start_year": all_years[i],
                        "end_year": all_years[i + 1],
                        "gap_size": gap_size,
                        "resolved": False
                    })
        
        return gaps
    
    def _generate_phone_response(self, user_input: str, call_metadata: Dict[str, Any]) -> str:
        """Generate appropriate phone response"""
        # Check if we're dealing with adversarial behavior
        recent_adversarial = len([f for f in self.adversarial_flags if 
                                datetime.fromisoformat(f['timestamp']) > 
                                datetime.now().replace(microsecond=0).replace(second=0)]) > 0
        
        # Build context for AI response
        context = f"""
Current conversation stage: {self.conversation_stage}
User input: "{user_input}"
Employment timeline entries: {len(self.employment_timeline)}
Identified gaps: {len(self.identified_gaps)}
Adversarial flags: {len(self.adversarial_flags)}
Recent adversarial behavior: {recent_adversarial}

Employment gaps to address: {self.identified_gaps}

Generate a phone-appropriate response that:
1. Acknowledges what they said
2. Asks the next logical question for employment timeline
3. If gaps exist, focus on resolving them
4. If adversarial behavior detected, use softer approach
5. Keep it conversational and phone-friendly
6. Use industry suggestions if needed: {self.industry_suggestions}

Response should be 1-2 sentences maximum for phone conversation.
"""
        
        # Get AI response
        ai_response = self.call_openai(context)
        
        # Post-process for phone conversation
        return self._make_phone_friendly(ai_response)
    
    def _make_phone_friendly(self, text: str) -> str:
        """Make text more suitable for phone conversation"""
        # Remove text-specific formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Remove italics
        
        # Add natural speech patterns
        if not any(phrase in text.lower() for phrase in ['i see', 'okay', 'alright', 'that makes sense']):
            acknowledgments = ['I see.', 'Okay.', 'That makes sense.', 'Alright.']
            import random
            text = f"{random.choice(acknowledgments)} {text}"
        
        # Ensure it ends appropriately
        if not text.endswith(('?', '.', '!')):
            text += '.'
        
        return text
    
    def _calculate_completion_score(self) -> float:
        """Calculate how complete the employment timeline is"""
        score = 0.0
        
        # Basic information gathered
        if self.employment_timeline:
            score += 0.3
        
        # Multiple employment entries
        if len(self.employment_timeline) >= 3:
            score += 0.2
        
        # Gaps identified and addressed
        total_gaps = len(self.identified_gaps)
        resolved_gaps = len([g for g in self.identified_gaps if g.get('resolved', False)])
        if total_gaps > 0:
            score += 0.3 * (resolved_gaps / total_gaps)
        else:
            score += 0.3  # No gaps is good
        
        # Low adversarial behavior
        if len(self.adversarial_flags) < 3:
            score += 0.2
        
        return min(score, 1.0)
    
    def detect_employment_gaps(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Public method to detect employment gaps"""
        return self._detect_employment_gaps()
    
    def handle_adversarial_responses(self, response: str) -> Dict[str, Any]:
        """Public method to handle adversarial responses"""
        score = self._detect_adversarial_behavior(response)
        return {
            "adversarial_score": score,
            "is_adversarial": score > 3,
            "suggested_approach": "softer" if score > 3 else "normal"
        }
    
    def ask_targeted_followups(self, gap_period: Dict[str, Any]) -> str:
        """Generate targeted follow-up questions for employment gaps"""
        start_year = gap_period.get('start_year')
        end_year = gap_period.get('end_year')
        gap_size = gap_period.get('gap_size', 0)
        
        if gap_size > 10:
            # Large gap - break it down
            mid_year = start_year + (gap_size // 2)
            return f"That's quite a long period from {start_year} to {end_year}. Let's break it down. What were you doing around {mid_year}?"
        else:
            # Smaller gap - direct question with industry suggestions
            industries = ", ".join(self.industry_suggestions[:4])
            return f"What about between {start_year} and {end_year}? Were you perhaps working in {industries}, or something else?"
    
    def validate_employment_timeline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate employment timeline for consistency"""
        issues = []
        
        # Check for overlapping employment
        years_mentioned = []
        for entry in self.employment_timeline:
            if 'years_mentioned' in entry['info']:
                years_mentioned.extend(entry['info']['years_mentioned'])
        
        # Check for reasonable timeline
        if years_mentioned:
            min_year = min(years_mentioned)
            max_year = max(years_mentioned)
            current_year = datetime.now().year
            
            if min_year < 1950:
                issues.append("Employment start date seems too early")
            if max_year > current_year:
                issues.append("Employment date in the future")
            if max_year - min_year > 50:
                issues.append("Employment span seems unusually long")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "timeline_span": max_year - min_year if years_mentioned else 0
        }
    
    def generate_industry_suggestions(self, gap_period: Dict[str, Any]) -> List[str]:
        """Generate industry suggestions for a gap period"""
        # Could be enhanced with demographic data, location, etc.
        return self.industry_suggestions[:6]  # Return top 6 suggestions
