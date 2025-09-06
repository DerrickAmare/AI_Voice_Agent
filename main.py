import logging
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import tempfile
import json

from src.services.voice_service import VoiceService
from src.services.conversation_engine import ConversationEngine
from src.services.resume_parser import ResumeParser
from src.services.resume_builder import ResumeBuilder
from src.services.agent_service import AgentService
from src.models.resume_models import Resume

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice AI Resume Builder", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
voice_service = VoiceService()
conversation_engine = ConversationEngine()
resume_parser = ResumeParser()
resume_builder = ResumeBuilder()
agent_service = AgentService()

# Global state (in production, use a proper database)
conversation_sessions = {}

class ConversationRequest(BaseModel):
    session_id: str
    user_input: str

class ConversationResponse(BaseModel):
    session_id: str
    response: str
    is_complete: bool
    resume_data: Optional[Dict[str, Any]] = None

class VoiceRequest(BaseModel):
    session_id: str
    text: str

class VoiceSessionRequest(BaseModel):
    session_id: str

class VoiceResponse(BaseModel):
    session_id: str
    success: bool
    message: str

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """Serve the main application page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Voice AI Resume Builder</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                text-align: center;
                color: white;
                margin-bottom: 40px;
            }
            .header h1 {
                font-size: 3em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
            }
            .main-content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 40px;
        }
            .card {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                transition: transform 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
            }
            .card h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.8em;
            }
            .card p {
                color: #666;
                line-height: 1.6;
                margin-bottom: 20px;
            }
            .btn {
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 25px;
                font-size: 1.1em;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                margin: 10px 5px;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 40px;
            }
            .feature {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                color: white;
                text-align: center;
            }
            .feature h3 {
                margin-bottom: 10px;
                font-size: 1.3em;
            }
            .conversation-area {
                background: white;
                border-radius: 15px;
                padding: 30px;
                margin-top: 30px;
                display: none;
            }
            .conversation-area.active {
                display: block;
            }
            .message {
                margin: 15px 0;
                padding: 15px;
                border-radius: 10px;
                max-width: 80%;
            }
            .ai-message {
                background: #e3f2fd;
                margin-right: auto;
            }
            .user-message {
                background: #f3e5f5;
                margin-left: auto;
            }
            .input-area {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            .input-area input {
                flex: 1;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 25px;
                font-size: 1em;
            }
            .input-area button {
                padding: 15px 25px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
            }
            .voice-controls {
                display: flex;
                gap: 10px;
                margin: 20px 0;
            }
            .voice-btn {
                padding: 15px;
                border-radius: 50%;
                border: none;
                cursor: pointer;
                font-size: 1.2em;
                transition: all 0.3s ease;
            }
            .listen-btn {
                background: #4caf50;
                color: white;
            }
            .speak-btn {
                background: #2196f3;
                color: white;
            }
            .voice-btn:hover {
                transform: scale(1.1);
            }
            .voice-btn.active {
                animation: pulse 1s infinite;
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎤 Voice AI Resume Builder</h1>
                <p>Transform your work experience into a professional resume through natural conversation</p>
            </div>

            <div class="main-content">
                <div class="card">
                    <h2>🚀 Start Fresh</h2>
                    <p>Begin building your resume from scratch. Our AI will guide you through a conversation to capture all your work experience, skills, and achievements.</p>
                    <button class="btn" onclick="startNewConversation()">Start New Resume</button>
                </div>

                <div class="card">
                    <h2>📄 Upload Existing Resume</h2>
                    <p>Already have a partial resume? Upload it and we'll help you fill in the missing details through our intelligent conversation system.</p>
                    <input type="file" id="resumeFile" accept=".txt,.pdf" style="margin: 10px 0;">
                    <button class="btn" onclick="uploadResume()">Upload & Enhance</button>
                </div>
            </div>

            <div class="features">
                <div class="feature">
                    <h3>🎯 Smart Questions</h3>
                    <p>AI asks targeted questions to uncover hidden experience</p>
                </div>
                <div class="feature">
                    <h3>🗣️ Voice Interface</h3>
                    <p>Natural conversation through speech recognition</p>
                </div>
                <div class="feature">
                    <h3>📊 Professional Output</h3>
                    <p>Generate polished resumes in multiple formats</p>
                </div>
                <div class="feature">
                    <h3>🔍 Missing Details</h3>
                    <p>Identifies and fills gaps in work history</p>
                </div>
            </div>

            <div class="conversation-area" id="conversationArea">
                <h2>Conversation</h2>
                <div class="voice-controls">
                    <button class="voice-btn listen-btn" id="listenBtn" onclick="toggleListening()">🎤</button>
                    <button class="voice-btn speak-btn" id="speakBtn" onclick="speakLastMessage()">🔊</button>
                </div>
                <div id="messages"></div>
                <div class="input-area">
                    <input type="text" id="userInput" placeholder="Type your response here..." onkeypress="handleKeyPress(event)">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>

        <script>
            let currentSessionId = null;
            let isListening = false;
            let lastAIMessage = '';

            function startNewConversation() {
                currentSessionId = 'session_' + Date.now();
                document.getElementById('conversationArea').classList.add('active');
                document.getElementById('messages').innerHTML = '';
                
                // Start conversation
                fetch('/api/conversation/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({session_id: currentSessionId})
                })
                .then(response => response.json())
                .then(data => {
                    addMessage(data.response, 'ai');
                    lastAIMessage = data.response;
                });
            }

            function uploadResume() {
                const fileInput = document.getElementById('resumeFile');
                const file = fileInput.files[0];
                
                if (!file) {
                    alert('Please select a file');
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);

                fetch('/api/resume/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        currentSessionId = data.session_id;
                        document.getElementById('conversationArea').classList.add('active');
                        document.getElementById('messages').innerHTML = '';
                        addMessage(data.message, 'ai');
                        lastAIMessage = data.message;
                    } else {
                        alert('Error uploading resume: ' + data.message);
                    }
                });
            }

            function sendMessage() {
                const input = document.getElementById('userInput');
                const message = input.value.trim();
                
                if (!message || !currentSessionId) return;

                addMessage(message, 'user');
                input.value = '';

                fetch('/api/conversation/continue', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        user_input: message
                    })
                })
                .then(response => response.json())
                .then(data => {
                    addMessage(data.response, 'ai');
                    lastAIMessage = data.response;
                    
                    if (data.is_complete) {
                        showResumeOptions(data.resume_data);
                    }
                });
            }

            function addMessage(text, sender) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}-message`;
                messageDiv.textContent = text;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }

            function toggleListening() {
                const btn = document.getElementById('listenBtn');
                
                if (isListening) {
                    // Stop listening
                    fetch('/api/voice/stop-listening', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({session_id: currentSessionId})
                    });
                    btn.classList.remove('active');
                    isListening = false;
                } else {
                    // Start listening
                    fetch('/api/voice/start-listening', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({session_id: currentSessionId})
                    });
                    btn.classList.add('active');
                    isListening = true;
                }
            }

            function speakLastMessage() {
                if (lastAIMessage) {
                    fetch('/api/voice/speak', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            session_id: currentSessionId,
                            text: lastAIMessage
                        })
                    });
                }
            }

            function showResumeOptions(resumeData) {
                const messagesDiv = document.getElementById('messages');
                const optionsDiv = document.createElement('div');
                optionsDiv.className = 'message ai-message';
                optionsDiv.innerHTML = `
                    <h3>Resume Complete! 🎉</h3>
                    <p>Your resume has been generated. Choose a format:</p>
                    <button class="btn" onclick="downloadResume('html')">Download HTML</button>
                    <button class="btn" onclick="downloadResume('pdf')">Download PDF</button>
                    <button class="btn" onclick="downloadResume('text')">Download Text</button>
                `;
                messagesDiv.appendChild(optionsDiv);
            }

            function downloadResume(format) {
                if (!currentSessionId) return;

                fetch(`/api/resume/download/${format}?session_id=${currentSessionId}`)
                .then(response => {
                    if (response.ok) {
                        return response.blob();
                    }
                    throw new Error('Download failed');
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `resume.${format}`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                })
                .catch(error => {
                    alert('Error downloading resume: ' + error.message);
                });
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/conversation/start")
async def start_conversation(request: Dict[str, str]):
    """Start a new conversation session"""
    session_id = request["session_id"]
    
    try:
        # Initialize conversation
        response = conversation_engine.start_conversation()
        conversation_sessions[session_id] = {
            "engine": conversation_engine,
            "resume": conversation_engine.get_resume()
        }
        
        return {"session_id": session_id, "response": response, "is_complete": False}
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversation/continue")
async def continue_conversation(request: ConversationRequest):
    """Continue an existing conversation"""
    session_id = request.session_id
    
    if session_id not in conversation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = conversation_sessions[session_id]
        engine = session["engine"]
        
        response, is_complete = engine.process_response(request.user_input)
        
        # Update session
        session["resume"] = engine.get_resume()
        
        result = {
            "session_id": session_id,
            "response": response,
            "is_complete": is_complete
        }
        
        if is_complete:
            result["resume_data"] = session["resume"].dict()
        
        return result
    except Exception as e:
        logger.error(f"Error continuing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse an existing resume"""
    try:
        # Read file content
        content = await file.read()
        
        if file.filename.endswith('.txt'):
            text_content = content.decode('utf-8')
        else:
            # For PDF files, you would need additional processing
            raise HTTPException(status_code=400, detail="PDF parsing not implemented yet")
        
        # Parse resume
        parsed_resume = resume_parser.parse_text_resume(text_content)
        
        # Start conversation with existing resume
        session_id = f"session_{len(conversation_sessions)}_{file.filename}"
        conversation_engine.start_conversation(parsed_resume)
        
        conversation_sessions[session_id] = {
            "engine": conversation_engine,
            "resume": parsed_resume
        }
        
        # Get first question
        response = conversation_engine._get_next_question()
        
        return {
            "success": True,
            "session_id": session_id,
            "message": response
        }
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/speak")
async def speak_text(request: VoiceRequest):
    """Convert text to speech"""
    try:
        voice_service.speak_async(request.text)
        return {"session_id": request.session_id, "success": True, "message": "Speaking"}
    except Exception as e:
        logger.error(f"Error with TTS: {e}")
        return {"session_id": request.session_id, "success": False, "message": str(e)}

@app.post("/api/voice/start-listening")
async def start_listening(request: VoiceSessionRequest):
    """Start voice listening"""
    try:
        # In a real implementation, you would handle voice input here
        return {"session_id": request.session_id, "success": True, "message": "Listening started"}
    except Exception as e:
        logger.error(f"Error starting listening: {e}")
        return {"session_id": request.session_id, "success": False, "message": str(e)}

@app.post("/api/voice/stop-listening")
async def stop_listening(request: VoiceSessionRequest):
    """Stop voice listening"""
    try:
        # In a real implementation, you would handle stopping voice input here
        return {"session_id": request.session_id, "success": True, "message": "Listening stopped"}
    except Exception as e:
        logger.error(f"Error stopping listening: {e}")
        return {"session_id": request.session_id, "success": False, "message": str(e)}

@app.get("/api/resume/download/{format}")
async def download_resume(format: str, session_id: str):
    """Download resume in specified format"""
    if session_id not in conversation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = conversation_sessions[session_id]
        resume = session["resume"]
        
        if format == "html":
            content = resume_builder.build_html_resume(resume)
            return HTMLResponse(content=content)
        elif format == "text":
            content = resume_builder.build_text_resume(resume)
            return {"content": content}
        elif format == "pdf":
            # Generate PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                success = resume_builder.build_pdf_resume(resume, tmp_file.name)
                if success:
                    return FileResponse(tmp_file.name, filename="resume.pdf")
                else:
                    raise HTTPException(status_code=500, detail="PDF generation failed")
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
    except Exception as e:
        logger.error(f"Error downloading resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "voice_service_available": voice_service.is_available(),
        "active_sessions": len(conversation_sessions)
    }



# Agent System Endpoints
@app.post("/api/agents/start")
async def start_agent_conversation(request: Dict[str, str]):
    """Start a new agent-powered conversation session"""
    session_id = request.get("session_id", f"agent_session_{len(conversation_sessions)}")
    target_role = request.get("target_role", "")
    industry = request.get("industry", "")
    
    try:
        result = agent_service.start_conversation(session_id, target_role, industry)
        return result
    except Exception as e:
        logger.error(f"Error starting agent conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/continue")
async def continue_agent_conversation(request: ConversationRequest):
    """Continue an agent-powered conversation"""
    session_id = request.session_id
    user_input = request.user_input
    
    try:
        result = agent_service.continue_conversation(session_id, user_input)
        return result
    except Exception as e:
        logger.error(f"Error continuing agent conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/format")
async def format_resume_with_agents(request: Dict[str, str]):
    """Format resume using the agent system"""
    session_id = request.get("session_id")
    output_format = request.get("format", "html")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    try:
        result = agent_service.format_resume(session_id, output_format)
        return result
    except Exception as e:
        logger.error(f"Error formatting resume with agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/status/{session_id}")
async def get_agent_session_status(session_id: str):
    """Get the status of an agent session"""
    try:
        result = agent_service.get_session_status(session_id)
        return result
    except Exception as e:
        logger.error(f"Error getting agent session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/info")
async def get_agent_info():
    """Get information about available agents"""
    try:
        result = agent_service.get_available_agents()
        return result
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agents/session/{session_id}")
async def reset_agent_session(session_id: str):
    """Reset an agent session"""
    try:
        result = agent_service.reset_session(session_id)
        return result
    except Exception as e:
        logger.error(f"Error resetting agent session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
