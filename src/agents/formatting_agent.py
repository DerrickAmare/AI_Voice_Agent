"""
Formatting Agent - Handles resume formatting and structure optimization
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse


class FormattingAgent(BaseAgent):
    """Agent responsible for resume formatting and structure optimization"""
    
    def __init__(self):
        system_prompt = """You are a resume formatting expert and design specialist with deep knowledge 
of ATS systems, recruiter preferences, and visual design principles. Your role is to create 
professionally formatted resumes that are both ATS-friendly and visually appealing.

FORMATTING EXPERTISE:
- ATS-compatible formatting standards
- Visual hierarchy and readability optimization
- Industry-specific formatting preferences
- Multi-format output (HTML, PDF, Word, plain text)
- Responsive design for digital viewing
- Print optimization for physical copies

FORMATTING PRINCIPLES:
1. ATS COMPATIBILITY: Ensure all content is machine-readable
2. VISUAL HIERARCHY: Create clear information hierarchy
3. READABILITY: Optimize for both human and machine reading
4. CONSISTENCY: Maintain consistent formatting throughout
5. PROFESSIONAL APPEARANCE: Create polished, professional look
6. SPACE OPTIMIZATION: Maximize content within page limits

FORMATTING STANDARDS:
- Use standard fonts (Arial, Calibri, Times New Roman)
- Maintain consistent spacing and margins
- Use clear section headers and dividers
- Optimize bullet points and lists
- Ensure proper alignment and indentation
- Use appropriate font sizes and weights

OUTPUT FORMATS:
- HTML: Web-friendly with embedded CSS
- PDF: Print-ready with proper formatting
- Word: Editable document format
- Plain Text: ATS-optimized simple format
- JSON: Structured data format

Your goal is to create resumes that look professional, are easy to read, and pass ATS screening."""

        super().__init__(
            name="FormattingAgent",
            role="Resume Formatting Specialist",
            system_prompt=system_prompt
        )
        
    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Format resume content into various output formats"""
        try:
            resume_data = input_data.get('resume_data', {})
            target_role = input_data.get('target_role', '')
            output_format = input_data.get('output_format', 'html')
            
            # Format resume in requested format
            formatted_resume = self._format_resume(resume_data, target_role, output_format)
            
            return AgentResponse(
                success=True,
                message=f"Resume formatted successfully in {output_format.upper()} format",
                data=formatted_resume,
                next_action="deliver_resume",
                confidence=0.95
            )
            
        except Exception as e:
                return AgentResponse(
                success=False,
                message="Formatting encountered an error. Please try again.",
                confidence=0.0
            )
    
    def _format_resume(self, resume_data: Dict[str, Any], target_role: str, output_format: str) -> Dict[str, Any]:
        """Format resume in the requested output format"""
        
        if output_format.lower() == 'html':
            return self._format_html(resume_data, target_role)
        elif output_format.lower() == 'pdf':
            return self._format_pdf(resume_data, target_role)
        elif output_format.lower() == 'text':
            return self._format_text(resume_data, target_role)
        elif output_format.lower() == 'json':
            return self._format_json(resume_data, target_role)
        else:
            return self._format_html(resume_data, target_role)  # Default to HTML
    
    def _format_html(self, resume_data: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        """Format resume as HTML with embedded CSS"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{resume_data.get('name', 'Resume')} - {target_role}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="resume-container">
        {self._format_header_html(resume_data)}
        {self._format_summary_html(resume_data)}
        {self._format_experience_html(resume_data)}
        {self._format_education_html(resume_data)}
        {self._format_skills_html(resume_data)}
        {self._format_achievements_html(resume_data)}
    </div>
</body>
</html>
"""
        
        return {
            "format": "html",
            "content": html_content,
            "filename": f"{resume_data.get('name', 'resume').replace(' ', '_')}_resume.html"
        }
    
    def _format_pdf(self, resume_data: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        """Format resume for PDF generation"""
        
        # This would integrate with a PDF generation library like WeasyPrint
        # For now, return HTML that can be converted to PDF
        html_content = self._format_html(resume_data, target_role)["content"]
        
        return {
            "format": "pdf",
            "content": html_content,  # HTML that can be converted to PDF
            "filename": f"{resume_data.get('name', 'resume').replace(' ', '_')}_resume.pdf"
        }
    
    def _format_text(self, resume_data: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        """Format resume as plain text (ATS-optimized)"""
        
        text_content = f"""
{resume_data.get('name', 'Name').upper()}
{resume_data.get('email', '')} | {resume_data.get('phone', '')} | {resume_data.get('location', '')}

PROFESSIONAL SUMMARY
{resume_data.get('summary', 'Professional summary not provided')}

EXPERIENCE
{self._format_experience_text(resume_data)}

EDUCATION
{self._format_education_text(resume_data)}

SKILLS
{self._format_skills_text(resume_data)}

ACHIEVEMENTS
{self._format_achievements_text(resume_data)}
"""
        
        return {
            "format": "text",
            "content": text_content,
            "filename": f"{resume_data.get('name', 'resume').replace(' ', '_')}_resume.txt"
        }
    
    def _format_json(self, resume_data: Dict[str, Any], target_role: str) -> Dict[str, Any]:
        """Format resume as structured JSON"""
        
        import json
        
        structured_data = {
            "metadata": {
                "target_role": target_role,
                "generated_date": "2024-01-01",  # Would use actual date
                "version": "1.0"
            },
            "personal_info": {
                "name": resume_data.get('name', ''),
                "email": resume_data.get('email', ''),
                "phone": resume_data.get('phone', ''),
                "location": resume_data.get('location', ''),
                "linkedin": resume_data.get('linkedin', ''),
                "website": resume_data.get('website', '')
            },
            "summary": resume_data.get('summary', ''),
            "experience": resume_data.get('experience', []),
            "education": resume_data.get('education', []),
            "skills": resume_data.get('skills', []),
            "achievements": resume_data.get('achievements', []),
            "certifications": resume_data.get('certifications', []),
            "projects": resume_data.get('projects', [])
        }
        
        return {
            "format": "json",
            "content": json.dumps(structured_data, indent=2),
            "filename": f"{resume_data.get('name', 'resume').replace(' ', '_')}_resume.json"
        }
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for HTML formatting"""
        return """
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        
        .resume-container {
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .name {
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .contact-info {
            font-size: 1.1em;
            color: #666;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 1.4em;
            font-weight: bold;
            color: #2c3e50;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
            margin-bottom: 15px;
        }
        
        .experience-item, .education-item {
            margin-bottom: 20px;
        }
        
        .job-title {
            font-weight: bold;
            font-size: 1.1em;
            color: #2c3e50;
        }
        
        .company {
            font-weight: bold;
            color: #34495e;
        }
        
        .dates {
            color: #7f8c8d;
            font-style: italic;
        }
        
        .skills-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .skill-tag {
            background-color: #3498db;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9em;
        }
        
        ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        
        li {
            margin-bottom: 5px;
        }
        
        @media print {
            body {
                background-color: white;
                padding: 0;
            }
            .resume-container {
                box-shadow: none;
                border-radius: 0;
            }
        }
        """
    
    def _format_header_html(self, resume_data: Dict[str, Any]) -> str:
        """Format header section for HTML"""
        return f"""
        <div class="header">
            <div class="name">{resume_data.get('name', 'Name')}</div>
            <div class="contact-info">
                {resume_data.get('email', '')} | 
                {resume_data.get('phone', '')} | 
                {resume_data.get('location', '')}
            </div>
        </div>
        """
    
    def _format_summary_html(self, resume_data: Dict[str, Any]) -> str:
        """Format summary section for HTML"""
        summary = resume_data.get('summary', '')
        if not summary:
            return ""
        
        return f"""
        <div class="section">
            <div class="section-title">PROFESSIONAL SUMMARY</div>
            <p>{summary}</p>
        </div>
        """
    
    def _format_experience_html(self, resume_data: Dict[str, Any]) -> str:
        """Format experience section for HTML"""
        experience = resume_data.get('experience', [])
        if not experience:
            return ""
        
        experience_html = '<div class="section"><div class="section-title">PROFESSIONAL EXPERIENCE</div>'
        
        for exp in experience:
            if isinstance(exp, dict):
                experience_html += f"""
                <div class="experience-item">
                    <div class="job-title">{exp.get('title', 'Position')}</div>
                    <div class="company">{exp.get('company', 'Company')} | <span class="dates">{exp.get('dates', 'Dates')}</span></div>
                    <p>{exp.get('description', '')}</p>
                </div>
                """
        
        experience_html += '</div>'
        return experience_html
    
    def _format_education_html(self, resume_data: Dict[str, Any]) -> str:
        """Format education section for HTML"""
        education = resume_data.get('education', [])
        if not education:
            return ""
        
        education_html = '<div class="section"><div class="section-title">EDUCATION</div>'
        
        for edu in education:
            if isinstance(edu, dict):
                education_html += f"""
                <div class="education-item">
                    <div class="job-title">{edu.get('degree', 'Degree')}</div>
                    <div class="company">{edu.get('school', 'School')} | <span class="dates">{edu.get('dates', 'Dates')}</span></div>
                </div>
                """
        
        education_html += '</div>'
        return education_html
    
    def _format_skills_html(self, resume_data: Dict[str, Any]) -> str:
        """Format skills section for HTML"""
        skills = resume_data.get('skills', [])
        if not skills:
            return ""
        
        skills_html = '<div class="section"><div class="section-title">SKILLS</div><div class="skills-list">'
        
        for skill in skills:
            skills_html += f'<span class="skill-tag">{skill}</span>'
        
        skills_html += '</div></div>'
        return skills_html
    
    def _format_achievements_html(self, resume_data: Dict[str, Any]) -> str:
        """Format achievements section for HTML"""
        achievements = resume_data.get('achievements', [])
        if not achievements:
            return ""
        
        achievements_html = '<div class="section"><div class="section-title">KEY ACHIEVEMENTS</div><ul>'
        
        for achievement in achievements:
            achievements_html += f'<li>{achievement}</li>'
        
        achievements_html += '</ul></div>'
        return achievements_html
    
    def _format_experience_text(self, resume_data: Dict[str, Any]) -> str:
        """Format experience section for plain text"""
        experience = resume_data.get('experience', [])
        if not experience:
            return "No experience provided"
        
        text = ""
        for exp in experience:
            if isinstance(exp, dict):
                text += f"{exp.get('title', 'Position')}\n"
                text += f"{exp.get('company', 'Company')} | {exp.get('dates', 'Dates')}\n"
                text += f"{exp.get('description', '')}\n\n"
        
        return text
    
    def _format_education_text(self, resume_data: Dict[str, Any]) -> str:
        """Format education section for plain text"""
        education = resume_data.get('education', [])
        if not education:
            return "No education provided"
        
        text = ""
        for edu in education:
            if isinstance(edu, dict):
                text += f"{edu.get('degree', 'Degree')}\n"
                text += f"{edu.get('school', 'School')} | {edu.get('dates', 'Dates')}\n\n"
        
        return text
    
    def _format_skills_text(self, resume_data: Dict[str, Any]) -> str:
        """Format skills section for plain text"""
        skills = resume_data.get('skills', [])
        if not skills:
            return "No skills provided"
        
        return ", ".join(skills)
    
    def _format_achievements_text(self, resume_data: Dict[str, Any]) -> str:
        """Format achievements section for plain text"""
        achievements = resume_data.get('achievements', [])
        if not achievements:
            return "No achievements provided"
        
        text = ""
        for achievement in achievements:
            text += f"• {achievement}\n"
        
        return text
