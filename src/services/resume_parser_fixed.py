import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from src.models.resume_models import Resume, WorkExperience, Education, PersonalInfo, Skill

logger = logging.getLogger(__name__)

class ResumeParserFixed:
    def __init__(self):
        self.patterns = self._load_parsing_patterns()
    
    def _load_parsing_patterns(self) -> Dict[str, List[str]]:
        """Load regex patterns for parsing resume text"""
        return {
            "phone": [
                r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
                r'(\(\d{3}\)\s?\d{3}[-.\s]?\d{4})'
            ],
            "email": [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            "date": [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
                r'(\d{4})'
            ],
            "name": [
                r'^([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+)',
                r'Name:\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)'
            ],
            "address": [
                r'(\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd))',
                r'([A-Za-z0-9\s,.-]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)'
            ]
        }
    
    def parse_text_resume(self, text: str) -> Resume:
        """Parse a text-based resume"""
        resume = Resume()
        
        # Parse different sections (keep original text structure for better parsing)
        resume.personal_info = self._parse_personal_info(text)
        resume.work_experience = self._parse_work_experience(text)
        resume.education = self._parse_education(text)
        resume.skills = self._parse_skills(text)
        
        return resume
    
    def parse_pdf_resume(self, pdf_path: str) -> Resume:
        """Parse a PDF resume (placeholder for PDF parsing)"""
        logger.warning("PDF parsing not implemented yet")
        return Resume()
    
    def _parse_personal_info(self, text: str) -> PersonalInfo:
        """Parse personal information from resume text"""
        personal_info = PersonalInfo()
        
        # Extract name from first few lines
        lines = text.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if line and not any(keyword in line.lower() for keyword in ['email', 'phone', 'address', '@']):
                # Check if line looks like a name (2+ words, starts with capital)
                words = line.split()
                if len(words) >= 2 and all(word[0].isupper() for word in words if word):
                    personal_info.full_name = line
                    break
        
        # Extract phone number
        for pattern in self.patterns["phone"]:
            match = re.search(pattern, text)
            if match:
                personal_info.phone = match.group(1)
                break
        
        # Extract email
        for pattern in self.patterns["email"]:
            match = re.search(pattern, text)
            if match:
                personal_info.email = match.group(1)
                break
        
        # Extract address (look for address patterns)
        address_patterns = [
            r'Address:\s*([^\n]+)',
            r'(\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)[^\n]*)',
            r'([A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                personal_info.address = match.group(1).strip()
                break
        
        return personal_info
    
    def _parse_work_experience(self, text: str) -> List[WorkExperience]:
        """Parse work experience from resume text"""
        work_experiences = []
        
        # Find work experience section
        work_section = self._extract_section(text, ["experience", "employment", "work history", "professional experience"])
        
        if not work_section:
            return work_experiences
        
        # Split into individual jobs using better logic
        job_entries = self._split_job_entries_improved(work_section)
        
        for job_text in job_entries:
            work_exp = self._parse_single_job_improved(job_text)
            if work_exp.company_name or work_exp.job_title:
                work_experiences.append(work_exp)
        
        return work_experiences
    
    def _parse_education(self, text: str) -> List[Education]:
        """Parse education from resume text"""
        education_list = []
        
        # Find education section
        education_section = self._extract_section(text, ["education", "academic", "qualifications"])
        
        if not education_section:
            return education_list
        
        # Split into individual education entries
        education_entries = self._split_education_entries_improved(education_section)
        
        for edu_text in education_entries:
            education = self._parse_single_education_improved(edu_text)
            if education.institution_name or education.degree:
                education_list.append(education)
        
        return education_list
    
    def _parse_skills(self, text: str) -> List[Skill]:
        """Parse skills from resume text"""
        skills = []
        
        # Find skills section
        skills_section = self._extract_section(text, ["skills", "technical skills", "competencies", "abilities"])
        
        if skills_section:
            # Extract skills from dedicated section
            skill_text = skills_section.lower()
            
            # Split by common delimiters
            skill_items = re.split(r'[,\n•\-\*]', skill_text)
            
            for item in skill_items:
                item = item.strip()
                if item and len(item) > 1:
                    # Clean up the skill name
                    skill_name = re.sub(r'^[\s\-\*•]+', '', item).strip()
                    if skill_name and len(skill_name) > 1:
                        skill = Skill(name=skill_name.title())
                        skills.append(skill)
        
        # Also extract common skills from work experience
        common_skills = [
            "excel", "word", "powerpoint", "photoshop", "autocad", "solidworks",
            "welding", "machining", "assembly", "quality control", "safety",
            "leadership", "communication", "teamwork", "problem solving",
            "python", "java", "javascript", "sql", "html", "css", "react", "django"
        ]
        
        work_section = self._extract_section(text, ["experience", "employment"])
        if work_section:
            for skill_name in common_skills:
                if skill_name in work_section.lower():
                    # Check if skill already exists
                    existing_skill = next((s for s in skills if s.name.lower() == skill_name.lower()), None)
                    if not existing_skill:
                        skill = Skill(name=skill_name.title())
                        skills.append(skill)
        
        return skills
    
    def _extract_section(self, text: str, section_keywords: List[str]) -> Optional[str]:
        """Extract a specific section from resume text"""
        text_lower = text.lower()
        
        for keyword in section_keywords:
            # Look for section headers - improved pattern
            patterns = [
                rf'{keyword}[:\s]*\n(.*?)(?=\n[A-Z][A-Z\s]+[:\n]|$)',  # Until next section
                rf'{keyword}[:\s]*\n(.*?)(?=\n\n[A-Z]|$)',  # Until double newline + capital
                rf'{keyword}[:\s]*\n(.*?)(?=\n[A-Z]{{3,}}|$)'  # Until all caps word
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        return None
    
    def _split_job_entries_improved(self, work_section: str) -> List[str]:
        """Split work experience section into individual job entries"""
        lines = work_section.split('\n')
        entries = []
        current_entry = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line starts a new job entry
            # Look for patterns like job titles or company names
            if (line.isupper() and len(line) > 3) or \
               any(word in line.lower() for word in ["inc", "corp", "llc", "ltd", "company"]) or \
               any(word in line.lower() for word in ["manager", "engineer", "developer", "analyst", "supervisor", "technician"]):
                
                # Save previous entry if it exists
                if current_entry:
                    entries.append('\n'.join(current_entry))
                    current_entry = []
                
                current_entry.append(line)
            else:
                current_entry.append(line)
        
        # Add the last entry
        if current_entry:
            entries.append('\n'.join(current_entry))
        
        return entries
    
    def _split_education_entries_improved(self, education_section: str) -> List[str]:
        """Split education section into individual education entries"""
        lines = education_section.split('\n')
        entries = []
        current_entry = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line starts a new education entry
            if any(word in line.lower() for word in ["university", "college", "school", "institute"]) or \
               any(word in line.lower() for word in ["bachelor", "master", "associate", "certificate", "diploma"]):
                
                # Save previous entry if it exists
                if current_entry:
                    entries.append('\n'.join(current_entry))
                    current_entry = []
                
                current_entry.append(line)
            else:
                current_entry.append(line)
        
        # Add the last entry
        if current_entry:
            entries.append('\n'.join(current_entry))
        
        return entries
    
    def _parse_single_job_improved(self, job_text: str) -> WorkExperience:
        """Parse a single job entry with improved logic"""
        work_exp = WorkExperience()
        lines = job_text.split('\n')
        
        # Extract job title and company (usually first 1-2 lines)
        for i, line in enumerate(lines[:3]):
            line = line.strip()
            if not line:
                continue
                
            # Check if it's a company name (has company indicators)
            if any(word in line.lower() for word in ["
