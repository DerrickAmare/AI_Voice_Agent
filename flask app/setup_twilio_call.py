#!/usr/bin/env python3
"""
Script to set up a Twilio call with the correct webhook URLs
This fixes the 404 errors by using the proper Flask webhook endpoints
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_twilio_call(ngrok_url, to_number, from_number=None):
    """Set up a Twilio call with proper webhook URLs"""
    
    # Get Twilio credentials
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        print("❌ Missing Twilio credentials in .env file")
        print("Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
        return None
    
    # Use provided from_number or get from environment
    if not from_number:
        from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not from_number:
        print("❌ Missing Twilio phone number")
        print("Please set TWILIO_PHONE_NUMBER in .env file or provide from_number parameter")
        return None
    
    # Remove trailing slash from ngrok URL
    base_url = ngrok_url.rstrip('/')
    
    # Generate a unique call ID
    import uuid
    call_id = f"call_{uuid.uuid4().hex[:12]}"
    
    # Set up webhook URLs
    webhook_url = f"{base_url}/api/calls/webhook/{call_id}"
    status_callback_url = f"{base_url}/api/calls/webhook/{call_id}/status"
    
    print("🚀 Setting up Twilio call with proper webhook URLs")
    print("=" * 60)
    print(f"📞 To: {to_number}")
    print(f"📞 From: {from_number}")
    print(f"🔗 Webhook URL: {webhook_url}")
    print(f"📊 Status Callback: {status_callback_url}")
    print("")
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Create the call
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url=webhook_url,
            method="POST",
            status_callback=status_callback_url,
            status_callback_method="POST",
            status_callback_event=["initiated", "ringing", "answered", "completed"]
        )
        
        print(f"✅ Call created successfully!")
        print(f"📋 Call SID: {call.sid}")
        print(f"🆔 Call ID: {call_id}")
        print("")
        print("📱 The call should now work without 404 errors!")
        print("🎯 Check your phone - you should receive the call shortly.")
        
        return {
            "call_sid": call.sid,
            "call_id": call_id,
            "webhook_url": webhook_url,
            "status_callback_url": status_callback_url
        }
        
    except Exception as e:
        print(f"❌ Error creating call: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python setup_twilio_call.py <ngrok_url> <to_phone_number> [from_phone_number]")
        print("")
        print("Examples:")
        print("  python setup_twilio_call.py https://abcd1234.ngrok-free.app +1234567890")
        print("  python setup_twilio_call.py https://abcd1234.ngrok-free.app +1234567890 +0987654321")
        print("")
        print("Make sure to:")
        print("1. Start the Flask webhook server: python twilio_webhook_app.py")
        print("2. Start ngrok: ngrok http 5000")
        print("3. Use the HTTPS ngrok URL (not HTTP)")
        sys.exit(1)
    
    ngrok_url = sys.argv[1]
    to_number = sys.argv[2]
    from_number = sys.argv[3] if len(sys.argv) > 3 else None
    
    setup_twilio_call(ngrok_url, to_number, from_number)
