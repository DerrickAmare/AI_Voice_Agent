"""
Resume API routes
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from typing import Dict, Any
import tempfile

from src.services.resume_parser import ResumeParser
from src.services.resume_builder import ResumeBuilder

router = APIRouter()

# Initialize services
resume_parser = ResumeParser()
resume_builder = ResumeBuilder()

# Global state (in production, use a proper database)
conversation_sessions = {}

@router.post("/upload")
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
        from src.services.conversation_engine import ConversationEngine
        conversation_engine = ConversationEngine()
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{format}")
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
        raise HTTPException(status_code=500, detail=str(e))
