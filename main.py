"""
Voice AI Resume Builder - Main Application
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import route modules
from src.api.routes import conversation, resume, voice, agents

# Create FastAPI app
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

# Include API routes
app.include_router(conversation.router, prefix="/api/conversation", tags=["conversation"])
app.include_router(resume.router, prefix="/api/resume", tags=["resume"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """Serve the main application page"""
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "voice_service_available": False,  # Will be updated when voice service is properly initialized
        "active_sessions": 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
