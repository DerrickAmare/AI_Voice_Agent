"""
Resume Analyzer Agent - Analyzes resume content for gaps and improvements
Enhanced with file processing capabilities for PDF/DOCX uploads
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
import logging
import io
import json

# File processing imports
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)

class ResumeAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing resume content and identifying gaps"""
    
    def __init__(self):
        system_prompt = """You are an expert resume analyst with deep knowledge of ATS systems, 
recruiter preferences, and industry standards. Your role is to analyze resume content and provide 
actionable insights for improvement.

ANALYSIS EXPERTISE:
- ATS (Applicant Tracking System) optimization
- Industry-specific resume standards
- Keyword optimization for job descriptions
- Content gaps and missing elements
- Format and structure recommendations
- Quantifiable achievement identification

ANALYSIS FRAMEWORK:
1. CONTENT COMPLETENESS: Check for all essential sections
2. KEYWORD OPTIMIZATION: Identify missing industry keywords
3. ACHIEVEMENT QUANTIFICATION: Find opportunities to add metrics
4. ATS COMPATIBILITY: Ensure proper formatting and structure
5. INDUSTRY ALIGNMENT: Match content to target role requirements
6. COMPETITIVE POSITIONING: Identify unique value propositions

ANALYSIS CRITERIA:
- Contact information completeness
- Professional summary quality
- Work experience depth and relevance
- Education and certification alignment
- Skills section optimization
- Achievement quantification
- Action verb usage
- Industry keyword presence
- ATS-friendly formatting

PROVIDE SPECIFIC, ACTIONABLE RECOMMENDATIONS:
- Identify exact gaps and missing elements
- Suggest specific improvements with examples
- Recommend industry-specific keywords
- Highlight opportunities for quantification
- Suggest better action verbs and phrasing
- Recommend additional sections if relevant

Your analysis should be thorough, specific, and immediately actionable."""

        super().__init__(
            name="ResumeAnalyzerAgent",
            role="Resume Analysis Expert",
            system_prompt=system_prompt
        )
        
    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Analyze resume content and provide recommendations"""
        try:
            resume_data = input_data.get('resume_data', {})
            target_role = input_data.get('target_role', '')
            industry = input_data.get('industry', '')
            
            # Perform comprehensive analysis
            analysis_results = self._analyze_resume(resume_data, target_role, industry)
            
            return AgentResponse(
                success=True,
                message="Resume analysis completed successfully",
                data=analysis_results,
                next_action="optimize_content",
                confidence=0.95
            )
            
        except Exception as e:
            logger.error(f"ResumeAnalyzerAgent error: {e}")
            return AgentResponse(
                success=False,
                message="Analysis encountered an error. Please try again.",
                confidence=0.0
            )
    
    def _analyze_resume(self, resume_data: Dict[str, Any], target_role: str, industry: str) -> Dict[str, Any]:
        """Perform comprehensive resume analysis"""
        
        analysis_prompt = f"""
Analyze this resume data for a {target_role} position in the {industry} industry:

RESUME DATA:
{resume_data}

TARGET ROLE: {target_role}
INDUSTRY: {industry}

Provide a comprehensive analysis including:

1. CONTENT GAPS:
   - Missing essential sections
   - Incomplete information
   - Areas needing more detail

2. KEYWORD OPTIMIZATION:
   - Missing industry keywords
   - ATS optimization opportunities
   - Skill alignment with target role

3. ACHIEVEMENT QUANTIFICATION:
   - Opportunities to add metrics
   - Quantifiable results to highlight
   - Impact statements to strengthen

4. CONTENT IMPROVEMENTS:
   - Action verb suggestions
   - Phrasing improvements
   - Structure recommendations

5. ATS COMPATIBILITY:
   - Formatting issues
   - Structure problems
   - Optimization opportunities

6. COMPETITIVE POSITIONING:
   - Unique value propositions
   - Differentiators to emphasize
   - Strengths to highlight

Return your analysis in a structured format with specific, actionable recommendations.
"""
        
        analysis_text = self.call_openai(analysis_prompt)
        
        # Parse analysis into structured format
        return {
            "raw_analysis": analysis_text,
            "content_gaps": self._extract_content_gaps(resume_data),
            "keyword_suggestions": self._suggest_keywords(target_role, industry),
            "quantification_opportunities": self._find_quantification_opportunities(resume_data),
            "ats_score": self._calculate_ats_score(resume_data),
            "overall_score": self._calculate_overall_score(resume_data),
            "priority_improvements": self._get_priority_improvements(resume_data, target_role)
        }
    
    def _extract_content_gaps(self, resume_data: Dict[str, Any]) -> List[str]:
        """Identify missing content sections"""
        gaps = []
        required_sections = ['name', 'email', 'phone', 'experience', 'education', 'skills']
        
        for section in required_sections:
            if section not in resume_data or not resume_data[section]:
                gaps.append(f"Missing or incomplete {section} section")
        
        return gaps
    
    def _suggest_keywords(self, target_role: str, industry: str) -> List[str]:
        """Suggest relevant keywords for the target role and industry"""
        keyword_prompt = f"""
Suggest 10-15 important keywords for a {target_role} position in the {industry} industry.
Focus on:
- Technical skills
- Industry-specific terms
- Soft skills
- Tools and technologies
- Certifications

Return as a simple list.
"""
        
        response = self.call_openai(keyword_prompt)
        # In production, parse this into a proper list
        return response.split('\n')[:15]
    
    def _find_quantification_opportunities(self, resume_data: Dict[str, Any]) -> List[str]:
        """Find opportunities to add quantifiable metrics"""
        opportunities = []
        
        # Check experience section for quantification opportunities
        experience = resume_data.get('experience', [])
        for exp in experience:
            if isinstance(exp, dict):
                responsibilities = exp.get('responsibilities', '')
                if responsibilities and not any(char.isdigit() for char in responsibilities):
                    opportunities.append(f"Add metrics to: {exp.get('title', 'Experience')}")
        
        return opportunities
    
    def _calculate_ats_score(self, resume_data: Dict[str, Any]) -> int:
        """Calculate ATS compatibility score (0-100)"""
        score = 0
        
        # Check for essential elements
        if resume_data.get('name'): score += 10
        if resume_data.get('email'): score += 10
        if resume_data.get('phone'): score += 10
        if resume_data.get('experience'): score += 20
        if resume_data.get('education'): score += 15
        if resume_data.get('skills'): score += 15
        
        # Check for good structure
        if len(resume_data.get('experience', [])) >= 2: score += 10
        if len(resume_data.get('skills', [])) >= 5: score += 10
        
        return min(score, 100)
    
    def _calculate_overall_score(self, resume_data: Dict[str, Any]) -> int:
        """Calculate overall resume quality score (0-100)"""
        ats_score = self._calculate_ats_score(resume_data)
        
        # Additional quality factors
        quality_bonus = 0
        if resume_data.get('summary'): quality_bonus += 5
        if resume_data.get('achievements'): quality_bonus += 5
        if resume_data.get('certifications'): quality_bonus += 5
        
        return min(ats_score + quality_bonus, 100)
    
    def _get_priority_improvements(self, resume_data: Dict[str, Any], target_role: str) -> List[str]:
        """Get priority improvements based on analysis"""
        improvements = []
        
        # High priority improvements
        if not resume_data.get('summary'):
            improvements.append("Add a professional summary tailored to the target role")
        
        if not resume_data.get('achievements'):
            improvements.append("Add a dedicated achievements section with quantifiable results")
        
        if len(resume_data.get('skills', [])) < 5:
            improvements.append("Expand skills section with industry-relevant competencies")
        
        return improvements[:5]  # Return top 5 priorities
    
    def process_uploaded_file(self, file_content: bytes, file_type: str) -> Dict[str, Any]:
        """Process uploaded resume file and return structured analysis with conversation hints"""
        try:
            # Extract text from file
            raw_text = self._extract_text_from_file(file_content, file_type)
            
            # Use AI to parse AND analyze in one step
            structured_data = self._ai_parse_and_analyze(raw_text)
            
            # Extract conversation hints for better phone interview
            hints = self._extract_conversation_hints(structured_data)
            structured_data["conversation_hints"] = hints
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            raise ValueError(f"Failed to process {file_type} file: {str(e)}")
    
    def _extract_conversation_hints(self, structured_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract hints from parsed resume to improve phone conversation"""
        hints = {
            "companies": [],
            "titles": [],
            "skills": [],
            "date_range": ""
        }
        
        try:
            # Extract company names
            work_experience = structured_data.get("work_experience", [])
            for job in work_experience:
                if isinstance(job, dict) and job.get("company"):
                    company = job["company"].strip()
                    if company and company not in hints["companies"]:
                        hints["companies"].append(company)
            
            # Extract job titles
            for job in work_experience:
                if isinstance(job, dict) and job.get("title"):
                    title = job["title"].strip()
                    if title and title not in hints["titles"]:
                        hints["titles"].append(title)
            
            # Extract skills
            skills = structured_data.get("skills", [])
            if isinstance(skills, list):
                hints["skills"] = [skill.strip() for skill in skills if skill and skill.strip()][:10]
            
            # Determine date range
            dates = []
            for job in work_experience:
                if isinstance(job, dict):
                    if job.get("start_date"):
                        try:
                            year = int(job["start_date"][:4])
                            dates.append(year)
                        except (ValueError, TypeError):
                            pass
                    if job.get("end_date") and job["end_date"] != "present":
                        try:
                            year = int(job["end_date"][:4])
                            dates.append(year)
                        except (ValueError, TypeError):
                            pass
            
            if dates:
                hints["date_range"] = f"{min(dates)}-{max(dates)}"
            
        except Exception as e:
            logger.error(f"Error extracting conversation hints: {e}")
        
        return hints
    
    def _extract_text_from_file(self, file_content: bytes, file_type: str) -> str:
        """Extract text from PDF, DOCX, or TXT files"""
        file_type = file_type.lower()
        
        if file_type == 'pdf':
            if not PDF_AVAILABLE:
                raise ValueError("PyPDF2 not installed. Cannot process PDF files.")
            return self._extract_pdf_text(file_content)
        elif file_type in ['docx', 'doc']:
            if not DOCX_AVAILABLE:
                raise ValueError("python-docx not installed. Cannot process DOCX files.")
            return self._extract_docx_text(file_content)
        elif file_type == 'txt':
            return file_content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            doc_file = io.BytesIO(file_content)
            doc = docx.Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    def _ai_parse_and_analyze(self, raw_text: str) -> Dict[str, Any]:
        """Use AI to parse resume text into structured data AND analyze it"""
        parse_prompt = f"""
Parse this resume text into structured JSON format and provide analysis:

RESUME TEXT:
{raw_text}

Return a valid JSON object with this exact structure:
{{
    "personal_info": {{
        "name": "",
        "email": "",
        "phone": "",
        "address": ""
    }},
    "work_experience": [
        {{
            "company": "",
            "title": "",
            "start_date": "",
            "end_date": "",
            "responsibilities": []
        }}
    ],
    "education": [
        {{
            "institution": "",
            "degree": "",
            "graduation_date": ""
        }}
    ],
    "skills": [],
    "summary": "",
    "analysis": {{
        "strengths": [],
        "gaps": [],
        "improvements": [],
        "ats_score": 85
    }}
}}

Extract all available information from the resume text and fill in the structure. For missing information, use empty strings or arrays. Ensure the JSON is valid and parseable.
"""
        
        try:
            response = self.call_openai(parse_prompt)
            
            # Try to parse JSON response
            try:
                parsed_data = json.loads(response)
                return parsed_data
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    parsed_data = json.loads(json_match.group())
                    return parsed_data
                else:
                    # Fallback: return basic structure with raw text
                    return {
                        "personal_info": {"name": "", "email": "", "phone": "", "address": ""},
                        "work_experience": [],
                        "education": [],
                        "skills": [],
                        "summary": "",
                        "raw_text": raw_text,
                        "analysis": {
                            "strengths": ["Resume uploaded successfully"],
                            "gaps": ["Needs manual review"],
                            "improvements": ["Review and enhance extracted data"],
                            "ats_score": 50
                        }
                    }
        except Exception as e:
            logger.error(f"Error in AI parsing: {e}")
            # Return basic structure with error info
            return {
                "personal_info": {"name": "", "email": "", "phone": "", "address": ""},
                "work_experience": [],
                "education": [],
                "skills": [],
                "summary": "",
                "raw_text": raw_text,
                "analysis": {
                    "strengths": [],
                    "gaps": ["AI parsing failed"],
                    "improvements": ["Manual review required"],
                    "ats_score": 30
                },
                "error": str(e)
            }
