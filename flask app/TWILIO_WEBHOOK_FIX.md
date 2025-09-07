# Twilio Webhook 404 Fix - Step by Step Guide

This guide fixes the **HTTP 404** errors you're getting from Twilio webhooks, which cause **Error 11200 (HTTP retrieval failure)** and the "we're sorry, an application error has occurred" IVR.

## The Problem

Your current FastAPI app doesn't have routes that match the exact paths Twilio is calling:
- `/api/calls/webhook/call_b7b44f018f2b` (TwiML webhook)
- `/api/calls/webhook/call_b7b44f018f2b/status` (Status callback)

## The Solution

Use the simple Flask app with exact webhook endpoints that Twilio expects.

## Step-by-Step Fix

### 1. Start the Flask Webhook Server

```bash
# In your project directory
python twilio_webhook_app.py
```

You should see:
```
🚀 Starting Twilio webhook server...
📡 Endpoints available:
   POST /api/calls/webhook/<call_id> - Main call webhook
   POST /api/calls/webhook/<call_id>/status - Status callback
   GET /health - Health check
   GET /test - Test endpoint

🔗 After starting, run: ngrok http 5000
📋 Then update your Twilio call URLs to use the ngrok HTTPS URL
```

### 2. Start ngrok (in a new terminal)

```bash
ngrok http 5000
```

Copy the **HTTPS** URL (e.g., `https://abcd1234.ngrok-free.app`)

### 3. Test the Webhook Endpoints

```bash
python test_webhook_endpoints.py https://abcd1234.ngrok-free.app
```

You should see all tests pass (✅).

### 4. Create a Twilio Call with Proper URLs

```bash
python setup_twilio_call.py https://abcd1234.ngrok-free.app +1234567890
```

Replace:
- `https://abcd1234.ngrok-free.app` with your actual ngrok URL
- `+1234567890` with the phone number you want to call

### 5. Manual Testing (Alternative)

If you prefer to test manually with curl:

```bash
# Test the main webhook endpoint
curl -X POST https://abcd1234.ngrok-free.app/api/calls/webhook/test -i

# Test the status callback endpoint  
curl -X POST https://abcd1234.ngrok-free.app/api/calls/webhook/test/status -i
```

Both should return **200 OK**.

## What This Fixes

✅ **404 Errors**: Flask routes match Twilio's exact URL patterns  
✅ **Error 11200**: Webhook returns valid TwiML (200 OK)  
✅ **Warning 15003**: Status callbacks return 200 quickly  
✅ **IVR Error**: No more "application error has occurred"  

## Key Differences from Your Current Setup

| Current (FastAPI) | Fixed (Flask) |
|-------------------|---------------|
| Complex routing | Simple exact matches |
| Async handlers | Synchronous (Twilio doesn't need async) |
| Multiple endpoints | Just the two Twilio needs |
| 404 on missing routes | Always returns 200 |

## Files Created

- `twilio_webhook_app.py` - Simple Flask app with proper webhook endpoints
- `test_webhook_endpoints.py` - Test script to verify endpoints work
- `setup_twilio_call.py` - Script to create Twilio calls with correct URLs
- `TWILIO_WEBHOOK_FIX.md` - This guide

## Next Steps

1. **Test the fix**: Follow the steps above
2. **Verify the call works**: You should receive the call without errors
3. **Integrate back**: Once working, you can integrate these endpoints into your main FastAPI app
4. **Update your main app**: Add these exact routes to your FastAPI app

## Troubleshooting

**Still getting 404?**
- Check that ngrok URL is HTTPS (not HTTP)
- Verify Flask app is running on port 5000
- Make sure ngrok is pointing to port 5000

**Call not connecting?**
- Verify your Twilio phone number is correct
- Check that the target number is verified (for trial accounts)
- Ensure you have sufficient Twilio credits

**Webhook not receiving data?**
- Check Flask app logs for incoming requests
- Verify the ngrok URL is accessible from the internet
- Test with the curl commands above
