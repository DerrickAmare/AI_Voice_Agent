#!/usr/bin/env python3
"""
Simple Flask app for Twilio webhooks
Fixes the 404 errors by providing exact endpoints Twilio expects
"""

from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

# TwiML webhook for the live call
@app.route("/api/calls/webhook/<call_id>", methods=["POST"])
def call_webhook(call_id):
    """Handle incoming call webhook from Twilio"""
    print(f"📞 Call webhook received for call_id: {call_id}")
    print(f"📋 Form data: {request.form.to_dict()}")
    
    # Create TwiML response
    vr = VoiceResponse()
    vr.say("Hi Michael, I am calling to talk to you about your registration with Labor Up and learn more about you. Would you be open to a quick chat?")
    
    # You can add <Gather> here if you want to collect digits or speech
    # gather = vr.gather(
    #     input='speech',
    #     timeout=10,
    #     action=f"/api/calls/webhook/{call_id}/gather"
    # )
    
    response_xml = str(vr)
    print(f"📤 Sending TwiML response: {response_xml}")
    
    return Response(response_xml, status=200, mimetype="text/xml")

# Status callback (Twilio posts call state changes here). Must return 200 quickly.
@app.route("/api/calls/webhook/<call_id>/status", methods=["POST"])
def call_status(call_id):
    """Handle call status updates from Twilio"""
    print(f"📊 Status callback received for call_id: {call_id}")
    print(f"📋 Status data: {request.form.to_dict()}")
    
    # Just acknowledge - no body needed, just return 200
    return ("", 200)

# Optional: Add a simple health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "twilio-webhook-app"}, 200

# Optional: Add a test endpoint to verify the server is running
@app.route("/test", methods=["GET"])
def test_endpoint():
    """Test endpoint to verify server is running"""
    return {"message": "Twilio webhook server is running!", "endpoints": [
        "/api/calls/webhook/<call_id> (POST)",
        "/api/calls/webhook/<call_id>/status (POST)",
        "/health (GET)",
        "/test (GET)"
    ]}, 200

if __name__ == "__main__":
    print("🚀 Starting Twilio webhook server...")
    print("📡 Endpoints available:")
    print("   POST /api/calls/webhook/<call_id> - Main call webhook")
    print("   POST /api/calls/webhook/<call_id>/status - Status callback")
    print("   GET /health - Health check")
    print("   GET /test - Test endpoint")
    print("")
    print("🔗 After starting, run: ngrok http 5000")
    print("📋 Then update your Twilio call URLs to use the ngrok HTTPS URL")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
