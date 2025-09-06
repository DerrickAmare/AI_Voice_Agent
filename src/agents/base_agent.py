"""
Base Agent Class for AI Resume Builder
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import openai
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentResponse:
    """Standard response format for all agents"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    next_action: Optional[str] = None
    confidence: float = 0.0

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        # Initialize OpenAI client with error handling
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        
        if api_key and api_key != 'your_openai_api_key_here':
            try:
                # Try different configurations
                if 'ysk-proj-' in api_key:
                    # Handle project-specific keys
                    self.client = openai.OpenAI(
                        api_key=api_key,
                        base_url=base_url
                    )
                else:
                    # Standard OpenAI key
                    self.client = openai.OpenAI(api_key=api_key)
                
                # Test the client with a simple call
                test_response = self.client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{'role': 'user', 'content': 'test'}],
                    max_tokens=1
                )
                        
            except Exception as e:
                        self.client = None
        else:
            self.client = None
            self.conversation_history = []
        
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        
    def get_messages(self, user_input: str) -> List[Dict[str, str]]:
        """Get formatted messages for OpenAI API"""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history[-10:])  # Keep last 10 messages
        messages.append({"role": "user", "content": user_input})
        return messages
    
    def call_openai(self, user_input: str, model: str = "gpt-4") -> str:
        """Make API call to OpenAI"""
        if not self.client:
            return self._get_fallback_response(user_input)
        
        try:
            messages = self.get_messages(user_input)
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
                return self._get_fallback_response(user_input)
    
    def _get_fallback_response(self, user_input: str) -> str:
        """Get fallback response when OpenAI is not available"""
        return f"I'm currently in demo mode. In a full setup, I would process: '{user_input[:100]}...'"
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process input and return response"""
        pass
    
    def log_interaction(self, input_data: Dict[str, Any], response: AgentResponse):
        """Log agent interaction"""
        logger.info(f"{self.name} processed: {input_data.get('type', 'unknown')} -> {response.success}")
        
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
