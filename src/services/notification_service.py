"""
Notification Service - Call anticipation and user communication
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
from .telephony_service import TelephonyService

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications to prepare users for calls"""
    
    def __init__(self):
        self.telephony_service = TelephonyService()
        self.notification_templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load notification message templates"""
        return {
            "call_scheduled": """
Hello {name}! This is a friendly reminder that you have a resume building call scheduled for {time}. 
We'll help you create a professional resume by discussing your work experience. 
The call should take about 5-10 minutes. Reply STOP to cancel.
            """.strip(),
            
            "call_imminent": """
Hi {name}! Your resume building call will begin in about 15 minutes. 
Please be ready to discuss your work history. We're here to help! 
Reply STOP to cancel.
            """.strip(),
            
            "call_starting": """
Hello {name}! We're about to call you now for your resume building session. 
Please answer when your phone rings. This will only take a few minutes.
            """.strip(),
            
            "call_missed": """
Hi {name}, we tried to reach you for your resume building call but couldn't connect. 
We'll try again later. Reply READY when you're available.
            """.strip(),
            
            "call_completed": """
Thank you {name}! Your resume building call is complete. 
Your professional resume will be available shortly. 
We appreciate your time!
            """.strip(),
            
            "call_rescheduled": """
Hi {name}, your resume building call has been rescheduled to {new_time}. 
We'll send another reminder before we call. Reply STOP to cancel.
            """.strip()
        }
    
    def schedule_call_notifications(self, phone_number: str, name: str, 
                                  call_time: datetime, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Schedule all notifications for a call"""
        try:
            notifications_scheduled = []
            
            # Schedule advance notification (24 hours before)
            advance_time = call_time - timedelta(hours=24)
            if advance_time > datetime.now():
                advance_result = self._schedule_notification(
                    phone_number, name, advance_time, "call_scheduled", 
                    {"time": call_time.strftime("%B %d at %I:%M %p")}
                )
                notifications_scheduled.append(advance_result)
            
            # Schedule imminent notification (15 minutes before)
            imminent_time = call_time - timedelta(minutes=15)
            if imminent_time > datetime.now():
                imminent_result = self._schedule_notification(
                    phone_number, name, imminent_time, "call_imminent", {}
                )
                notifications_scheduled.append(imminent_result)
            
            # Schedule starting notification (at call time)
            starting_result = self._schedule_notification(
                phone_number, name, call_time, "call_starting", {}
            )
            notifications_scheduled.append(starting_result)
            
            return {
                "success": True,
                "notifications_scheduled": len(notifications_scheduled),
                "details": notifications_scheduled
            }
            
        except Exception as e:
            logger.error(f"Error scheduling notifications: {e}")
            return {"success": False, "error": str(e)}
    
    def _schedule_notification(self, phone_number: str, name: str, 
                             send_time: datetime, template_key: str, 
                             template_vars: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a single notification"""
        try:
            # In a real implementation, this would use a job scheduler like Celery
            # For now, we'll simulate scheduling
            
            message = self.notification_templates[template_key].format(
                name=name or "there",
                **template_vars
            )
            
            # If send time is now or past, send immediately
            if send_time <= datetime.now():
                return self.send_immediate_notification(phone_number, message)
            
            # Otherwise, log that it would be scheduled
            logger.info(f"Would schedule SMS to {phone_number} at {send_time}: {message[:50]}...")
            
            return {
                "success": True,
                "scheduled_for": send_time.isoformat(),
                "message_preview": message[:50] + "...",
                "type": template_key
            }
            
        except Exception as e:
            logger.error(f"Error scheduling notification: {e}")
            return {"success": False, "error": str(e)}
    
    def send_immediate_notification(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send notification immediately"""
        try:
            result = self.telephony_service.send_sms_notification(phone_number, message)
            
            if result.get("success"):
                logger.info(f"Notification sent to {phone_number}")
                return {
                    "success": True,
                    "message_sid": result.get("message_sid"),
                    "sent_at": datetime.now().isoformat()
                }
            else:
                logger.error(f"Failed to send notification: {result.get('error')}")
                return {"success": False, "error": result.get("error")}
                
        except Exception as e:
            logger.error(f"Error sending immediate notification: {e}")
            return {"success": False, "error": str(e)}
    
    def notify_call_scheduled(self, phone_number: str, name: str, call_time: datetime) -> Dict[str, Any]:
        """Send call scheduled notification"""
        template_vars = {
            "time": call_time.strftime("%B %d at %I:%M %p")
        }
        
        message = self.notification_templates["call_scheduled"].format(
            name=name or "there",
            **template_vars
        )
        
        return self.send_immediate_notification(phone_number, message)
    
    def notify_call_imminent(self, phone_number: str, name: str) -> Dict[str, Any]:
        """Send call imminent notification (15 minutes before)"""
        message = self.notification_templates["call_imminent"].format(
            name=name or "there"
        )
        
        return self.send_immediate_notification(phone_number, message)
    
    def notify_call_starting(self, phone_number: str, name: str) -> Dict[str, Any]:
        """Send call starting notification"""
        message = self.notification_templates["call_starting"].format(
            name=name or "there"
        )
        
        return self.send_immediate_notification(phone_number, message)
    
    def notify_call_missed(self, phone_number: str, name: str, reason: str = None) -> Dict[str, Any]:
        """Send call missed notification"""
        message = self.notification_templates["call_missed"].format(
            name=name or "there"
        )
        
        return self.send_immediate_notification(phone_number, message)
    
    def notify_call_completed(self, phone_number: str, name: str, 
                            completion_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send call completed notification"""
        message = self.notification_templates["call_completed"].format(
            name=name or "there"
        )
        
        return self.send_immediate_notification(phone_number, message)
    
    def notify_call_rescheduled(self, phone_number: str, name: str, 
                              new_call_time: datetime) -> Dict[str, Any]:
        """Send call rescheduled notification"""
        template_vars = {
            "new_time": new_call_time.strftime("%B %d at %I:%M %p")
        }
        
        message = self.notification_templates["call_rescheduled"].format(
            name=name or "there",
            **template_vars
        )
        
        return self.send_immediate_notification(phone_number, message)
    
    def handle_user_response(self, phone_number: str, response_text: str) -> Dict[str, Any]:
        """Handle user responses to notifications"""
        response_lower = response_text.lower().strip()
        
        if response_lower in ["stop", "cancel", "unsubscribe"]:
            return self._handle_stop_request(phone_number)
        elif response_lower in ["ready", "ok", "yes"]:
            return self._handle_ready_response(phone_number)
        elif response_lower in ["reschedule", "later", "not now"]:
            return self._handle_reschedule_request(phone_number)
        else:
            return self._handle_unknown_response(phone_number, response_text)
    
    def _handle_stop_request(self, phone_number: str) -> Dict[str, Any]:
        """Handle stop/cancel requests"""
        try:
            # In a real implementation, this would:
            # 1. Remove phone number from call queue
            # 2. Cancel scheduled notifications
            # 3. Update database records
            
            confirmation_message = "Your resume building call has been cancelled. You will not receive further messages."
            result = self.send_immediate_notification(phone_number, confirmation_message)
            
            return {
                "action": "cancelled",
                "phone_number": phone_number,
                "notification_sent": result.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"Error handling stop request: {e}")
            return {"action": "error", "error": str(e)}
    
    def _handle_ready_response(self, phone_number: str) -> Dict[str, Any]:
        """Handle ready responses"""
        try:
            # In a real implementation, this would:
            # 1. Mark user as ready in database
            # 2. Potentially prioritize their call
            # 3. Send confirmation
            
            confirmation_message = "Great! We'll call you shortly for your resume building session."
            result = self.send_immediate_notification(phone_number, confirmation_message)
            
            return {
                "action": "ready_confirmed",
                "phone_number": phone_number,
                "notification_sent": result.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"Error handling ready response: {e}")
            return {"action": "error", "error": str(e)}
    
    def _handle_reschedule_request(self, phone_number: str) -> Dict[str, Any]:
        """Handle reschedule requests"""
        try:
            # In a real implementation, this would:
            # 1. Move call to later time slot
            # 2. Update database
            # 3. Send new scheduled time
            
            response_message = "We'll reschedule your call for later today. You'll receive a new notification with the time."
            result = self.send_immediate_notification(phone_number, response_message)
            
            return {
                "action": "reschedule_requested",
                "phone_number": phone_number,
                "notification_sent": result.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"Error handling reschedule request: {e}")
            return {"action": "error", "error": str(e)}
    
    def _handle_unknown_response(self, phone_number: str, response_text: str) -> Dict[str, Any]:
        """Handle unknown responses"""
        try:
            help_message = "Reply STOP to cancel, READY when available, or RESCHEDULE to change time."
            result = self.send_immediate_notification(phone_number, help_message)
            
            return {
                "action": "help_sent",
                "phone_number": phone_number,
                "original_response": response_text,
                "notification_sent": result.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"Error handling unknown response: {e}")
            return {"action": "error", "error": str(e)}
    
    def get_notification_history(self, phone_number: str) -> List[Dict[str, Any]]:
        """Get notification history for a phone number"""
        # In a real implementation, this would query the database
        # For now, return empty list
        return []
    
    def cancel_scheduled_notifications(self, phone_number: str) -> Dict[str, Any]:
        """Cancel all scheduled notifications for a phone number"""
        try:
            # In a real implementation, this would:
            # 1. Query scheduled notifications
            # 2. Cancel them in the job scheduler
            # 3. Update database
            
            logger.info(f"Would cancel scheduled notifications for {phone_number}")
            
            return {
                "success": True,
                "cancelled_count": 0,  # Would be actual count
                "phone_number": phone_number
            }
            
        except Exception as e:
            logger.error(f"Error cancelling notifications: {e}")
            return {"success": False, "error": str(e)}
    
    def get_notification_preferences(self, phone_number: str) -> Dict[str, Any]:
        """Get notification preferences for a user"""
        # Default preferences - in real implementation, would come from database
        return {
            "phone_number": phone_number,
            "sms_enabled": True,
            "advance_notice_hours": 24,
            "reminder_minutes": 15,
            "timezone": "America/Chicago"
        }
    
    def update_notification_preferences(self, phone_number: str, 
                                      preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update notification preferences for a user"""
        try:
            # In a real implementation, this would update the database
            logger.info(f"Would update preferences for {phone_number}: {preferences}")
            
            return {
                "success": True,
                "phone_number": phone_number,
                "updated_preferences": preferences
            }
            
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return {"success": False, "error": str(e)}
