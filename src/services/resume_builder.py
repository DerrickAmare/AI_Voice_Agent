import logging
from typing import Dict, Any, Optional
from datetime import datetime
from src.models.resume_models import Resume, WorkExperience, Education, PersonalInfo, Skill
from jinja2 import Template

logger = logging.getLogger(__name__)

class ResumeBuilder:
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load HTML templates for resume generation"""
        return {
            "html": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ personal_info.full_name }} - Resume</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .resume-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .name {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
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
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
            margin-bottom: 15px;
        }
        .work-item, .education-item {
            margin-bottom: 20px;
            padding-left: 20px;
            border-left: 3px solid #007acc;
        }
        .job-title {
            font-weight: bold;
            font-size: 1.2em;
            color: #333;
        }
        .company {
            font-weight: bold;
            color: #007acc;
        }
        .dates {
            color: #666;
            font-style: italic;
        }
        .responsibilities {
            margin-top: 10px;
        }
        .responsibilities ul {
            margin: 5px 0;
            padding-left: 20px;
        }
        .skills-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .skill-tag {
            background-color: #007acc;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9em;
        }
        .summary {
            font-style: italic;
            color: #555;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="resume-container">
        <div class="header">
            <div class="name">{{ personal_info.full_name or "Your Name" }}</div>
            <div class="contact-info">
                {% if personal_info.phone %}{{ personal_info.phone }} | {% endif %}
                {% if personal_info.email %}{{ personal_info.email }} | {% endif %}
                {% if personal_info.address %}{{ personal_info.address }}{% endif %}
            </div>
        </div>

        {% if personal_info.summary %}
        <div class="section">
            <div class="section-title">Professional Summary</div>
            <div class="summary">{{ personal_info.summary }}</div>
        </div>
        {% endif %}

        {% if work_experience %}
        <div class="section">
            <div class="section-title">Work Experience</div>
            {% for work in work_experience %}
            <div class="work-item">
                <div class="job-title">{{ work.job_title or "Job Title" }}</div>
                <div class="company">{{ work.company_name or "Company Name" }}</div>
                <div class="dates">
                    {% if work.start_date %}{{ work.start_date.strftime('%B %Y') }}{% endif %}
                    {% if work.end_date %} - {{ work.end_date.strftime('%B %Y') }}{% elif work.current_job %} - Present{% endif %}
                    {% if work.location %} | {{ work.location }}{% endif %}
                </div>
                {% if work.responsibilities %}
                <div class="responsibilities">
                    <ul>
                        {% for responsibility in work.responsibilities %}
                        <li>{{ responsibility }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}
                {% if work.achievements %}
                <div class="achievements">
                    <strong>Achievements:</strong>
                    <ul>
                        {% for achievement in work.achievements %}
                        <li>{{ achievement }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if education %}
        <div class="section">
            <div class="section-title">Education</div>
            {% for edu in education %}
            <div class="education-item">
                <div class="job-title">{{ edu.degree or "Degree" }}</div>
                <div class="company">{{ edu.institution_name or "Institution" }}</div>
                <div class="dates">
                    {% if edu.graduation_date %}{{ edu.graduation_date.strftime('%Y') }}{% endif %}
                    {% if edu.location %} | {{ edu.location }}{% endif %}
                </div>
                {% if edu.honors %}
                <div class="honors">
                    <strong>Honors:</strong> {{ edu.honors | join(', ') }}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if skills %}
        <div class="section">
            <div class="section-title">Skills</div>
            <div class="skills-list">
                {% for skill in skills %}
                <span class="skill-tag">{{ skill.name }}</span>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
            """,
            "text": """
{{ personal_info.full_name or "Your Name" }}
{% if personal_info.phone %}{{ personal_info.phone }}{% endif %}{% if personal_info.email %} | {{ personal_info.email }}{% endif %}{% if personal_info.address %} | {{ personal_info.address }}{% endif %}

{% if personal_info.summary %}
PROFESSIONAL SUMMARY
{{ personal_info.summary }}

{% endif %}
{% if work_experience %}
WORK EXPERIENCE

{% for work in work_experience %}
{{ work.job_title or "Job Title" }}
{{ work.company_name or "Company Name" }}
{% if work.start_date %}{{ work.start_date.strftime('%B %Y') }}{% endif %}{% if work.end_date %} - {{ work.end_date.strftime('%B %Y') }}{% elif work.current_job %} - Present{% endif %}{% if work.location %} | {{ work.location }}{% endif %}

{% if work.responsibilities %}
Responsibilities:
{% for responsibility in work.responsibilities %}
• {{ responsibility }}
{% endfor %}
{% endif %}

{% if work.achievements %}
Achievements:
{% for achievement in work.achievements %}
• {{ achievement }}
{% endfor %}
{% endif %}

{% endfor %}
{% endif %}
{% if education %}
EDUCATION

{% for edu in education %}
{{ edu.degree or "Degree" }}
{{ edu.institution_name or "Institution" }}
{% if edu.graduation_date %}{{ edu.graduation_date.strftime('%Y') }}{% endif %}{% if edu.location %} | {{ edu.location }}{% endif %}
{% if edu.honors %}
Honors: {{ edu.honors | join(', ') }}
{% endif %}

{% endfor %}
{% endif %}
{% if skills %}
SKILLS

{% for skill in skills %}{{ skill.name }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}
            """
        }
    
    def build_html_resume(self, resume: Resume) -> str:
        """Build HTML resume from resume data"""
        template = Template(self.templates["html"])
        return template.render(
            personal_info=resume.personal_info,
            work_experience=resume.work_experience,
            education=resume.education,
            skills=resume.skills
        )
    
    def build_text_resume(self, resume: Resume) -> str:
        """Build text resume from resume data"""
        template = Template(self.templates["text"])
        return template.render(
            personal_info=resume.personal_info,
            work_experience=resume.work_experience,
            education=resume.education,
            skills=resume.skills
        )
    
    def build_pdf_resume(self, resume: Resume, output_path: str) -> bool:
        """Build PDF resume from resume data"""
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            html_content = self.build_html_resume(resume)
            
            # Add PDF-specific CSS
            pdf_css = CSS(string='''
                @page {
                    size: A4;
                    margin: 1in;
                }
                body {
                    font-size: 12pt;
                }
                .name {
                    font-size: 24pt;
                }
                .section-title {
                    font-size: 14pt;
                }
            ''')
            
            HTML(string=html_content).write_pdf(output_path, stylesheets=[pdf_css])
            return True
            
        except ImportError:
            logger.error("WeasyPrint not available for PDF generation")
            return False
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return False
    
    def enhance_resume(self, resume: Resume) -> Resume:
        """Enhance resume with additional formatting and content"""
        enhanced_resume = resume.copy()
        
        # Enhance personal info
        if enhanced_resume.personal_info.summary:
            enhanced_resume.personal_info.summary = self._enhance_summary(
                enhanced_resume.personal_info.summary
            )
        
        # Enhance work experience
        for work in enhanced_resume.work_experience:
            if work.responsibilities:
                work.responsibilities = [
                    self._enhance_responsibility(resp) for resp in work.responsibilities
                ]
        
        # Enhance skills
        enhanced_resume.skills = self._categorize_skills(enhanced_resume.skills)
        
        return enhanced_resume
    
    def _enhance_summary(self, summary: str) -> str:
        """Enhance professional summary"""
        # Add action words and make it more professional
        action_words = ["experienced", "skilled", "dedicated", "results-driven", "detail-oriented"]
        
        if not any(word in summary.lower() for word in action_words):
            summary = f"Experienced {summary.lower()}"
        
        # Ensure it ends with a period
        if not summary.endswith('.'):
            summary += '.'
        
        return summary
    
    def _enhance_responsibility(self, responsibility: str) -> str:
        """Enhance job responsibility"""
        # Remove bullet points if present
        responsibility = responsibility.lstrip('•-* ')
        
        # Capitalize first letter
        if responsibility:
            responsibility = responsibility[0].upper() + responsibility[1:]
        
        # Ensure it ends with a period
        if not responsibility.endswith('.'):
            responsibility += '.'
        
        return responsibility
    
    def _categorize_skills(self, skills: list) -> list:
        """Categorize skills by type"""
        categorized_skills = []
        
        # Define skill categories
        categories = {
            "Technical": ["excel", "word", "powerpoint", "photoshop", "autocad", "solidworks", "python", "java"],
            "Manufacturing": ["welding", "machining", "assembly", "quality control", "safety", "cnc"],
            "Soft Skills": ["leadership", "communication", "teamwork", "problem solving", "time management"]
        }
        
        for skill in skills:
            skill_name_lower = skill.name.lower()
            category = "Other"
            
            for cat_name, cat_skills in categories.items():
                if any(cat_skill in skill_name_lower for cat_skill in cat_skills):
                    category = cat_name
                    break
            
            skill.category = category
            categorized_skills.append(skill)
        
        # Sort by category
        categorized_skills.sort(key=lambda x: x.category)
        
        return categorized_skills
    
    def generate_resume_insights(self, resume: Resume) -> Dict[str, Any]:
        """Generate insights about the resume"""
        insights = {
            "completeness_score": self._calculate_completeness_score(resume),
            "strengths": self._identify_strengths(resume),
            "improvements": self._suggest_improvements(resume),
            "ats_compatibility": self._check_ats_compatibility(resume)
        }
        
        return insights
    
    def _calculate_completeness_score(self, resume: Resume) -> int:
        """Calculate resume completeness score (0-100)"""
        score = 0
        total_checks = 0
        
        # Personal info (30 points)
        total_checks += 4
        if resume.personal_info.full_name:
            score += 10
        if resume.personal_info.phone:
            score += 5
        if resume.personal_info.email:
            score += 10
        if resume.personal_info.address:
            score += 5
        
        # Work experience (50 points)
        if resume.work_experience:
            total_checks += len(resume.work_experience) * 4
            for work in resume.work_experience:
                if work.company_name:
                    score += 5
                if work.job_title:
                    score += 5
                if work.start_date:
                    score += 2
                if work.responsibilities:
                    score += 3
        
        # Education (10 points)
        if resume.education:
            total_checks += len(resume.education) * 2
            for edu in resume.education:
                if edu.institution_name:
                    score += 3
                if edu.degree:
                    score += 2
        
        # Skills (10 points)
        if resume.skills:
            score += 10
            total_checks += 1
        
        return min(100, int((score / total_checks) * 100)) if total_checks > 0 else 0
    
    def _identify_strengths(self, resume: Resume) -> list:
        """Identify resume strengths"""
        strengths = []
        
        if len(resume.work_experience) >= 3:
            strengths.append("Extensive work experience")
        
        if any(work.achievements for work in resume.work_experience):
            strengths.append("Quantified achievements")
        
        if len(resume.skills) >= 5:
            strengths.append("Diverse skill set")
        
        if resume.personal_info.summary:
            strengths.append("Professional summary included")
        
        return strengths
    
    def _suggest_improvements(self, resume: Resume) -> list:
        """Suggest resume improvements"""
        improvements = []
        
        if not resume.personal_info.summary:
            improvements.append("Add a professional summary")
        
        if not any(work.achievements for work in resume.work_experience):
            improvements.append("Include specific achievements and results")
        
        if len(resume.skills) < 5:
            improvements.append("Add more relevant skills")
        
        if not any(work.current_job for work in resume.work_experience):
            improvements.append("Include current employment status")
        
        return improvements
    
    def _check_ats_compatibility(self, resume: Resume) -> Dict[str, bool]:
        """Check ATS (Applicant Tracking System) compatibility"""
        return {
            "has_contact_info": bool(resume.personal_info.phone and resume.personal_info.email),
            "has_work_experience": len(resume.work_experience) > 0,
            "has_skills": len(resume.skills) > 0,
            "has_dates": any(work.start_date for work in resume.work_experience),
            "has_responsibilities": any(work.responsibilities for work in resume.work_experience)
        }
