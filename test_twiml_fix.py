#!/usr/bin/env python3
"""
Test and fix TwiML generation issues causing Twilio error 1210
"""

import requests
import xml.etree.ElementTree as ET
from twilio.twiml.voice_response import VoiceResponse

def test_twiml_generation():
    """Test TwiML generation to identify issues"""
    print("🔧 Testing TwiML Generation")
    print("=" * 40)
    
    # Test 1: Basic TwiML structure
    print("1️⃣ Testing basic TwiML structure...")
    try:
        response = VoiceResponse()
        response.say("Hello, this is a test.", voice='alice', language='en-US')
        twiml_str = str(response)
        print(f"✅ Basic TwiML: {twiml_str}")
        
        # Validate XML
        ET.fromstring(twiml_str)
        print("✅ XML validation passed")
    except Exception as e:
        print(f"❌ Basic TwiML failed: {e}")
    
    # Test 2: Gather with speech
    print("\n2️⃣ Testing Gather with speech...")
    try:
        response = VoiceResponse()
        gather = response.gather(
            input='speech',
            timeout=10,
            speechTimeout='auto',
            action="/api/calls/webhook/test123/gather",
            method='POST',
            language='en-US'
        )
        gather.say("Please tell me about your work experience.", voice='alice', language='en-US')
        response.say("I didn't hear anything.", voice='alice')
        response.hangup()
        
        twiml_str = str(response)
        print(f"✅ Gather TwiML: {twiml_str}")
        
        # Validate XML
        ET.fromstring(twiml_str)
        print("✅ Gather XML validation passed")
    except Exception as e:
        print(f"❌ Gather TwiML failed: {e}")
    
    # Test 3: Complex nested structure
    print("\n3️⃣ Testing complex nested structure...")
    try:
        response = VoiceResponse()
        
        # First gather
        gather1 = response.gather(
            input='speech',
            timeout=10,
            speechTimeout='auto',
            action="/api/calls/webhook/test123/gather",
            method='POST',
            language='en-US'
        )
        gather1.say("What is your current job?", voice='alice', language='en-US')
        
        # Fallback message
        response.say("I didn't hear anything. Let me try again.", voice='alice')
        
        # Second gather
        gather2 = response.gather(
            input='speech',
            timeout=8,
            speechTimeout='auto',
            action="/api/calls/webhook/test123/gather",
            method='POST',
            language='en-US'
        )
        gather2.say("Can you tell me about your work?", voice='alice', language='en-US')
        
        # Final fallback
        response.say("Thank you for your time. Goodbye.", voice='alice')
        response.hangup()
        
        twiml_str = str(response)
        print(f"✅ Complex TwiML generated successfully")
        print(f"Length: {len(twiml_str)} characters")
        
        # Validate XML
        ET.fromstring(twiml_str)
        print("✅ Complex XML validation passed")
        
        # Check for common issues
        if twiml_str.startswith('<?xml'):
            print("✅ Proper XML declaration")
        else:
            print("⚠️ Missing XML declaration")
            
        if '<Response>' in twiml_str and '</Response>' in twiml_str:
            print("✅ Proper Response tags")
        else:
            print("❌ Missing Response tags")
            
    except Exception as e:
        print(f"❌ Complex TwiML failed: {e}")

def test_webhook_endpoints():
    """Test actual webhook endpoints"""
    print("\n🌐 Testing Webhook Endpoints")
    print("=" * 40)
    
    base_url = "http://localhost:8000"  # Assuming local testing
    
    # Test TwiML test endpoint
    print("1️⃣ Testing TwiML test endpoint...")
    try:
        response = requests.get(f"{base_url}/api/test-twiml/test123", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            # Validate XML
            ET.fromstring(response.text)
            print("✅ Endpoint XML validation passed")
        else:
            print(f"❌ Endpoint returned {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Server not running - start with 'python main.py'")
    except Exception as e:
        print(f"❌ Endpoint test failed: {e}")

def validate_twiml_response(twiml_string):
    """Validate TwiML response for common issues"""
    print(f"\n🔍 Validating TwiML Response")
    print("=" * 40)
    
    issues = []
    
    # Check for XML declaration
    if not twiml_string.strip().startswith('<?xml'):
        issues.append("Missing XML declaration")
    
    # Check for Response root element
    if '<Response>' not in twiml_string or '</Response>' not in twiml_string:
        issues.append("Missing Response root element")
    
    # Check for unclosed tags
    try:
        ET.fromstring(twiml_string)
    except ET.ParseError as e:
        issues.append(f"XML Parse Error: {e}")
    
    # Check for invalid characters
    invalid_chars = ['&', '<', '>', '"', "'"]
    for char in invalid_chars:
        if char in twiml_string and f'&{char};' not in twiml_string:
            # Check if it's properly escaped
            if char == '&' and '&amp;' not in twiml_string:
                issues.append(f"Unescaped character: {char}")
            elif char in ['<', '>'] and ('&lt;' not in twiml_string and '&gt;' not in twiml_string):
                # These might be valid XML tags, so check context
                pass
    
    # Check for extra content before XML
    lines = twiml_string.split('\n')
    if lines and not lines[0].strip().startswith('<?xml'):
        first_non_empty = next((line for line in lines if line.strip()), "")
        if first_non_empty and not first_non_empty.strip().startswith('<?xml'):
            issues.append("Content before XML declaration")
    
    if issues:
        print("❌ TwiML Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ TwiML validation passed")
    
    return len(issues) == 0

if __name__ == "__main__":
    print("🔧 TwiML Error 1210 Diagnostic Tool")
    print("=" * 50)
    
    # Test TwiML generation
    test_twiml_generation()
    
    # Test webhook endpoints
    test_webhook_endpoints()
    
    print("\n" + "=" * 50)
    print("🎯 Recommendations:")
    print("1. Ensure all TwiML responses have proper XML headers")
    print("2. Always wrap content in <Response> tags")
    print("3. Validate XML before sending to Twilio")
    print("4. Set Content-Type: application/xml header")
    print("5. Handle exceptions gracefully with fallback TwiML")
