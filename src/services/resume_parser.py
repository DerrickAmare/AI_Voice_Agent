import re
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from src.models.resume_models import Resume, WorkExperience, Education, PersonalInfo, Skill


class ResumeParser:
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
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'Name:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ],
            "address": [
                r'(\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd))',
                r'([A-Za-z0-9\s,.-]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)'
            ]
        }
    
    def parse_text_resume(self, text: str) -> Resume:
        """Parse a text-based resume"""
        resume = Resume()
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Parse different sections
        resume.personal_info = self._parse_personal_info(text)
        resume.work_experience = self._parse_work_experience(text)
        resume.education = self._parse_education(text)
        resume.skills = self._parse_skills(text)
        
        return resume
    
    def parse_pdf_resume(self, pdf_path: str) -> Resume:
        """Parse a PDF resume (placeholder for PDF parsing)"""
        # This would require additional libraries like PyPDF2 or pdfplumber
        # For now, return empty resume
        return Resume()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize resume text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?@()-]', '', text)
        
        return text.strip()
    
    def _parse_personal_info(self, text: str) -> PersonalInfo:
        """Parse personal information from resume text"""
        personal_info = PersonalInfo()
        
        # Extract name (usually at the top)
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            name_match = re.search(self.patterns["name"][0], line)
            if name_match:
                personal_info.full_name = name_match.group(1)
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
        
        # Extract address
        for pattern in self.patterns["address"]:
            match = re.search(pattern, text)
            if match:
                personal_info.address = match.group(1)
                break
        
        return personal_info
    
    def _parse_work_experience(self, text: str) -> List[WorkExperience]:
        """Parse work experience from resume text"""
        work_experiences = []
        
        # Find work experience section
        work_section = self._extract_section(text, ["experience", "employment", "work history", "professional experience"])
        
        if not work_section:
            return work_experiences
        
        # Split into individual jobs
        job_entries = self._split_job_entries(work_section)
        
        for job_text in job_entries:
            work_exp = self._parse_single_job(job_text)
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
        education_entries = self._split_education_entries(education_section)
        
        for edu_text in education_entries:
            education = self._parse_single_education(edu_text)
            if education.institution_name or education.degree:
                education_list.append(education)
        
        return education_list
    
    def _parse_skills(self, text: str) -> List[Skill]:
        """Parse skills from resume text"""
        skills = []
        
        # Find skills section
        skills_section = self._extract_section(text, ["skills", "technical skills", "competencies", "abilities"])
        
        if not skills_section:
            return skills
        
        # Extract skills from text
        skill_text = skills_section.lower()
        
        # Common skills to look for
        common_skills = [
            "excel", "word", "powerpoint", "photoshop", "autocad", "solidworks",
            "welding", "machining", "assembly", "quality control", "safety",
            "leadership", "communication", "teamwork", "problem solving",
            "python", "java", "javascript", "sql", "html", "css"
        ]
        
        for skill_name in common_skills:
            if skill_name in skill_text:
                skill = Skill(name=skill_name.title())
                skills.append(skill)
        
        # Also extract skills mentioned in work experience
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
            # Look for section headers
            pattern = rf'{keyword}[:\s]*\n(.*?)(?=\n[A-Z][A-Z\s]+:|$)'
            match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _split_job_entries(self, work_section: str) -> List[str]:
        """Split work experience section into individual job entries"""
        # Simple heuristic: split on common job separators
        separators = [
            r'\n(?=[A-Z][a-z]+.*\d{4})',  # New line followed by capitalized word and year
            r'\n(?=\d{4})',  # New line followed by year
            r'\n(?=[A-Z][A-Z\s]+)',  # New line followed by all caps (company name)
        ]
        
        entries = [work_section]
        for separator in separators:
            new_entries = []
            for entry in entries:
                parts = re.split(separator, entry)
                new_entries.extend(parts)
            entries = new_entries
        
        # Filter out empty entries
        return [entry.strip() for entry in entries if entry.strip()]
    
    def _split_education_entries(self, education_section: str) -> List[str]:
        """Split education section into individual education entries"""
        # Similar to job entries but for education
        separators = [
            r'\n(?=[A-Z][a-z]+.*\d{4})',
            r'\n(?=\d{4})',
            r'\n(?=[A-Z][A-Z\s]+)',
        ]
        
        entries = [education_section]
        for separator in separators:
            new_entries = []
            for entry in entries:
                parts = re.split(separator, entry)
                new_entries.extend(parts)
            entries = new_entries
        
        return [entry.strip() for entry in entries if entry.strip()]
    
    def _parse_single_job(self, job_text: str) -> WorkExperience:
        """Parse a single job entry"""
        work_exp = WorkExperience()
        
        lines = job_text.split('\n')
        
        # Extract company name (usually first line or in all caps)
        for line in lines:
            if line.isupper() and len(line) > 3:
                work_exp.company_name = line.title()
                break
            elif any(word in line.lower() for word in ["inc", "corp", "llc", "ltd", "company"]):
                work_exp.company_name = line.strip()
                break
        
        # Extract job title (usually near company name)
        for line in lines:
            if any(word in line.lower() for word in ["manager", "supervisor", "technician", "operator", "assistant"]):
                work_exp.job_title = line.strip()
                break
        
        # Extract dates
        for line in lines:
            for pattern in self.patterns["date"]:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(1)
                        if len(date_str) == 4:  # Just year
                            work_exp.start_date = datetime.strptime(date_str, "%Y").date()
                        else:
                            work_exp.start_date = datetime.strptime(date_str, "%m/%d/%Y").date()
                        break
                    except:
                        continue
        
        # Extract responsibilities (bullet points or sentences)
        responsibilities = []
        for line in lines:
            if line.strip().startswith(('•', '-', '*')) or 'responsible' in line.lower():
                responsibilities.append(line.strip())
        
        work_exp.responsibilities = responsibilities
        
        return work_exp
    
    def _parse_single_education(self, edu_text: str) -> Education:
        """Parse a single education entry"""
        education = Education()
        
        lines = edu_text.split('\n')
        
        # Extract institution name
        for line in lines:
            if any(word in line.lower() for word in ["university", "college", "school", "institute"]):
                education.institution_name = line.strip()
                break
        
        # Extract degree
        for line in lines:
            if any(word in line.lower() for word in ["bachelor", "master", "associate", "certificate", "diploma"]):
                education.degree = line.strip()
                break
        
        # Extract dates
        for line in lines:
            for pattern in self.patterns["date"]:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(1)
                        if len(date_str) == 4:  # Just year
                            education.graduation_date = datetime.strptime(date_str, "%Y").date()
                        break
                    except:
                        continue
        
        return education
    
    def identify_missing_information(self, resume: Resume) -> List[str]:
        """Identify missing information in a resume"""
        missing = []
        
        # Check personal info
        if not resume.personal_info.full_name:
            missing.append("Full name")
        if not resume.personal_info.phone:
            missing.append("Phone number")
        if not resume.personal_info.email:
            missing.append("Email address")
        if not resume.personal_info.address:
            missing.append("Address")
        
        # Check work experience
        for i, work in enumerate(resume.work_experience):
            if not work.company_name:
                missing.append(f"Company name for job {i+1}")
            if not work.job_title:
                missing.append(f"Job title for job {i+1}")
            if not work.start_date:
                missing.append(f"Start date for job {i+1}")
            if not work.end_date and not work.current_job:
                missing.append(f"End date for job {i+1}")
            if not work.responsibilities:
                missing.append(f"Responsibilities for job {i+1}")
        
        # Check education
        for i, edu in enumerate(resume.education):
            if not edu.institution_name:
                missing.append(f"Institution name for education {i+1}")
            if not edu.degree:
                missing.append(f"Degree for education {i+1}")
        
        # Check skills
        if not resume.skills:
            missing.append("Skills")
        
        return missing
