"""
Telephony service for outbound calling using Twilio
Integrated with Redis-based state management
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import phonenumbers
from phonenumbers import NumberParseException
import structlog

logger = structlog.get_logger()

class TelephonyService:
    """Service for managing Twilio telephony operations"""
    
    def __init__(self, account_sid: str = None, auth_token: str = None, phone_number: str = None):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = phone_number or os.getenv("TWILIO_PHONE_NUMBER")
        self.logger = logger.bind(service="telephony")
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            self.logger.warning("Twilio credentials not fully configured")
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                self.logger.info("Twilio client initialized", phone_number=self.phone_number)
            except Exception as e:
                self.logger.error("Failed to initialize Twilio client", error=str(e))
                self.client = None
    
    def validate_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """Validate and format phone number"""
        try:
            parsed = phonenumbers.parse(phone_number, "US")
            if phonenumbers.is_valid_number(parsed):
                formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                return {
                    "valid": True,
                    "formatted": formatted,
                    "country": phonenumbers.region_code_for_number(parsed)
                }
            else:
                return {"valid": False, "error": "Invalid phone number"}
        except NumberParseException as e:
            return {"valid": False, "error": str(e)}
    
    def initiate_call(self, to_number: str, webhook_url: str) -> Any:
        """Initiate an outbound call"""
        if not self.client:
            self.logger.warning("Twilio not configured - cannot initiate real call")
            # Return a mock call object for testing
            class MockCall:
                def __init__(self):
                    self.sid = f"demo_call_{to_number.replace('+', '')}"
                    self.status = "initiated"
            return MockCall()
        
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=webhook_url,
                method="POST",
                status_callback=webhook_url + "/status",
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                record=True,
                timeout=30,
                machine_detection="Enable"
            )
            
            self.logger.info("Call initiated", call_sid=call.sid, to_number=to_number)
            return call
            
        except Exception as e:
            self.logger.error("Failed to initiate call", to_number=to_number, error=str(e))
            raise
    
    def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """Get current status of a call"""
        if not self.client:
            return {
                "call_sid": call_sid,
                "status": "completed",
                "duration": "300",
                "demo_mode": True
            }
        
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "call_sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "start_time": call.start_time.isoformat() if call.start_time else None,
                "end_time": call.end_time.isoformat() if call.end_time else None,
                "price": call.price,
                "direction": call.direction
            }
        except Exception as e:
            self.logger.error("Failed to get call status", call_sid=call_sid, error=str(e))
            return {"error": str(e)}
    
    def generate_twiml_response(self, message: str, gather_input: bool = True, 
                              timeout: int = 10, action_url: str = None) -> str:
        """Generate TwiML response for phone conversation"""
        response = VoiceResponse()
        
        if gather_input and action_url:
            gather = response.gather(
                input='speech',
                timeout=timeout,
                action=action_url,
                method='POST'
            )
            gather.say(message, voice='alice', language='en-US')
            
            # If no input received, try again
            response.say("I didn't hear anything. Let me try again.", voice='alice')
        else:
            response.say(message, voice='alice', language='en-US')
            if not gather_input:
                response.hangup()
        
        return str(response)
    
    def send_sms_notification(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS notification"""
        if not self.client:
            self.logger.info("Demo SMS sent", to_number=phone_number, message=message[:50])
            return {"success": True, "demo_mode": True}
        
        try:
            sms = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=phone_number
            )
            
            self.logger.info("SMS sent", message_sid=sms.sid, to_number=phone_number)
            return {
                "success": True,
                "message_sid": sms.sid,
                "status": sms.status
            }
        except Exception as e:
            self.logger.error("Failed to send SMS", to_number=phone_number, error=str(e))
            return {"success": False, "error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Twilio service"""
        if not self.client:
            return {
                "status": "unhealthy",
                "error": "Twilio client not configured",
                "demo_mode": True
            }
        
        try:
            # Test by fetching account info
            account = self.client.api.accounts(self.account_sid).fetch()
            
            return {
                "status": "healthy",
                "account_sid": self.account_sid,
                "phone_number": self.phone_number,
                "account_status": account.status,
                "timestamp": str(datetime.now())
            }
        except Exception as e:
            self.logger.error("Twilio health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": str(datetime.now())
            }
    
    def is_available(self) -> bool:
        """Check if telephony service is available"""
        return self.client is not None
