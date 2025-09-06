import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from src.models.resume_models import (
    ConversationState, Resume, WorkExperience, Education, 
    PersonalInfo, Skill, QuestionContext
)


class ConversationEngine:
    def __init__(self):
        self.state = ConversationState()
        self.question_templates = self._load_question_templates()
        self.extraction_patterns = self._load_extraction_patterns()
    
    def _load_question_templates(self) -> Dict[str, List[str]]:
        """Load question templates for different resume sections"""
        return {
            "personal_info": [
                "Let's start with some basic information. What's your full name?",
                "What's your phone number?",
                "What's your email address?",
                "Where are you located? Please include city and state.",
                "Do you have a LinkedIn profile or personal website?",
                "Can you tell me a brief summary about yourself and your career goals?"
            ],
            "work_experience": [
                "Let's talk about your work experience. What's the name of the company you worked for?",
                "What was your job title at {company}?",
                "When did you start working at {company}?",
                "Are you still working at {company}, or when did you leave?",
                "Where was {company} located?",
                "What were your main responsibilities at {company}?",
                "What achievements are you most proud of at {company}?",
                "What skills did you use in this role?",
                "Did you receive any promotions while at {company}?",
                "What was the size of your team?",
                "What projects did you work on?",
                "Why did you leave {company}?",
                "Who was your supervisor at {company}?"
            ],
            "education": [
                "Let's talk about your education. What schools did you attend?",
                "What degree or certification did you earn at {institution}?",
                "What was your field of study at {institution}?",
                "When did you start at {institution}?",
                "When did you graduate from {institution}?",
                "Where was {institution} located?",
                "Did you receive any honors or awards?",
                "What was your GPA?",
                "What relevant coursework did you complete?",
                "Did you earn any certifications?"
            ],
            "skills": [
                "What technical skills do you have?",
                "What software or tools are you proficient with?",
                "What languages do you speak?",
                "What soft skills would you say are your strengths?",
                "How many years of experience do you have with {skill}?",
                "Do you have any certifications for {skill}?"
            ]
        }
    
    def _load_extraction_patterns(self) -> Dict[str, List[str]]:
        """Load regex patterns for extracting information from responses"""
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
            "years": [
                r'(\d+)\s*years?',
                r'(\d+)\s*yr'
            ]
        }
    
    def start_conversation(self, existing_resume: Optional[Resume] = None) -> str:
        """Start a new conversation"""
        if existing_resume:
            self.state.resume_data = existing_resume
            self._analyze_existing_resume()
        
        self.state.current_section = "personal_info"
        return self._get_next_question()
    
    def process_response(self, user_input: str) -> Tuple[str, bool]:
        """Process user response and return next question and completion status"""
        # Add to conversation history
        self.state.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "section": self.state.current_section
        })
        
        # Extract information from response
        extracted_data = self._extract_information(user_input)
        
        # Update resume data
        self._update_resume_data(extracted_data)
        
        # Determine next question
        next_question = self._get_next_question()
        
        # Check if conversation is complete
        is_complete = self._is_conversation_complete()
        
        return next_question, is_complete
    
    def _analyze_existing_resume(self):
        """Analyze existing resume to identify missing information"""
        resume = self.state.resume_data
        
        # Check personal info
        if not resume.personal_info.full_name:
            self.state.missing_fields.append("personal_info.full_name")
        if not resume.personal_info.phone:
            self.state.missing_fields.append("personal_info.phone")
        if not resume.personal_info.email:
            self.state.missing_fields.append("personal_info.email")
        
        # Check work experience
        for i, work in enumerate(resume.work_experience):
            if not work.company_name:
                self.state.missing_fields.append(f"work_experience.{i}.company_name")
            if not work.job_title:
                self.state.missing_fields.append(f"work_experience.{i}.job_title")
            if not work.start_date:
                self.state.missing_fields.append(f"work_experience.{i}.start_date")
    
    def _extract_information(self, user_input: str) -> Dict[str, Any]:
        """Extract structured information from user input"""
        extracted = {}
        
        # Extract phone numbers
        for pattern in self.extraction_patterns["phone"]:
            match = re.search(pattern, user_input)
            if match:
                extracted["phone"] = match.group(1)
                break
        
        # Extract email addresses
        for pattern in self.extraction_patterns["email"]:
            match = re.search(pattern, user_input)
            if match:
                extracted["email"] = match.group(1)
                break
        
        # Extract dates
        for pattern in self.extraction_patterns["date"]:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                extracted["date"] = match.group(1)
                break
        
        # Extract years of experience
        for pattern in self.extraction_patterns["years"]:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                extracted["years"] = int(match.group(1))
                break
        
        # Extract other information based on context
        if self.state.current_section == "work_experience":
            extracted.update(self._extract_work_info(user_input))
        elif self.state.current_section == "education":
            extracted.update(self._extract_education_info(user_input))
        elif self.state.current_section == "skills":
            extracted.update(self._extract_skills_info(user_input))
        else:
            extracted.update(self._extract_personal_info(user_input))
        
        return extracted
    
    def _extract_work_info(self, user_input: str) -> Dict[str, Any]:
        """Extract work experience information"""
        info = {}
        
        # Company names (capitalize first letter of each word)
        if "company" in user_input.lower() or any(word in user_input.lower() for word in ["inc", "corp", "llc", "ltd"]):
            # Simple heuristic - take the first capitalized word sequence
            words = user_input.split()
            for i, word in enumerate(words):
                if word[0].isupper() and len(word) > 2:
                    company_words = [word]
                    for j in range(i + 1, len(words)):
                        if words[j][0].isupper() or words[j].lower() in ["inc", "corp", "llc", "ltd"]:
                            company_words.append(words[j])
                        else:
                            break
                    info["company_name"] = " ".join(company_words)
                    break
        
        # Job titles
        title_keywords = ["manager", "supervisor", "technician", "operator", "assistant", "specialist", "coordinator"]
        for keyword in title_keywords:
            if keyword in user_input.lower():
                # Extract the phrase containing the keyword
                words = user_input.split()
                for i, word in enumerate(words):
                    if keyword in word.lower():
                        start = max(0, i - 2)
                        end = min(len(words), i + 3)
                        info["job_title"] = " ".join(words[start:end])
                        break
                break
        
        return info
    
    def _extract_education_info(self, user_input: str) -> Dict[str, Any]:
        """Extract education information"""
        info = {}
        
        # Institution names
        school_keywords = ["university", "college", "school", "institute", "academy"]
        for keyword in school_keywords:
            if keyword in user_input.lower():
                words = user_input.split()
                for i, word in enumerate(words):
                    if keyword in word.lower():
                        start = max(0, i - 2)
                        end = min(len(words), i + 2)
                        info["institution_name"] = " ".join(words[start:end])
                        break
                break
        
        # Degrees
        degree_keywords = ["bachelor", "master", "associate", "certificate", "diploma", "degree"]
        for keyword in degree_keywords:
            if keyword in user_input.lower():
                info["degree"] = keyword.title()
                break
        
        return info
    
    def _extract_skills_info(self, user_input: str) -> Dict[str, Any]:
        """Extract skills information"""
        info = {}
        
        # Common skills
        skills = []
        skill_keywords = [
            "excel", "word", "powerpoint", "photoshop", "autocad", "solidworks",
            "welding", "machining", "assembly", "quality control", "safety",
            "leadership", "communication", "teamwork", "problem solving",
            "python", "java", "javascript", "sql", "html", "css"
        ]
        
        for keyword in skill_keywords:
            if keyword in user_input.lower():
                skills.append(keyword.title())
        
        if skills:
            info["skills"] = skills
        
        return info
    
    def _extract_personal_info(self, user_input: str) -> Dict[str, Any]:
        """Extract personal information"""
        info = {}
        
        # Full name - improved extraction
        if "name" in user_input.lower():
            # Look for "My name is" or "I am" patterns
            name_patterns = [
                r'my name is ([a-zA-Z\s]+)',
                r'i am ([a-zA-Z\s]+)',
                r'name is ([a-zA-Z\s]+)',
                r'call me ([a-zA-Z\s]+)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, user_input.lower())
                if match:
                    name = match.group(1).strip().title()
                    if len(name.split()) >= 2:  # At least first and last name
                        info["full_name"] = name
                        break
        
        # If no pattern match, try simple heuristic for names
        if "full_name" not in info:
            words = user_input.split()
            if len(words) >= 2:
                # Check if first two words look like names (start with capital letters)
                if words[0][0].isupper() and words[1][0].isupper():
                    info["full_name"] = f"{words[0]} {words[1]}"
        
        # Location - improved extraction
        location_keywords = ["live in", "located in", "from", "address", "detroit", "michigan", "chicago", "illinois"]
        if any(keyword in user_input.lower() for keyword in location_keywords):
            info["address"] = user_input
        
        return info
    
    def _update_resume_data(self, extracted_data: Dict[str, Any]):
        """Update resume data with extracted information"""
        if self.state.current_section == "personal_info":
            self._update_personal_info(extracted_data)
        elif self.state.current_section == "work_experience":
            self._update_work_experience(extracted_data)
        elif self.state.current_section == "education":
            self._update_education(extracted_data)
        elif self.state.current_section == "skills":
            self._update_skills(extracted_data)
    
    def _update_personal_info(self, data: Dict[str, Any]):
        """Update personal information"""
        if "full_name" in data:
            self.state.resume_data.personal_info.full_name = data["full_name"]
        if "phone" in data:
            self.state.resume_data.personal_info.phone = data["phone"]
        if "email" in data:
            self.state.resume_data.personal_info.email = data["email"]
        if "address" in data:
            self.state.resume_data.personal_info.address = data["address"]
    
    def _update_work_experience(self, data: Dict[str, Any]):
        """Update work experience"""
        if self.state.current_work_index is None:
            # Create new work experience entry
            work_exp = WorkExperience()
            self.state.resume_data.work_experience.append(work_exp)
            self.state.current_work_index = len(self.state.resume_data.work_experience) - 1
        
        work_exp = self.state.resume_data.work_experience[self.state.current_work_index]
        
        if "company_name" in data:
            work_exp.company_name = data["company_name"]
        if "job_title" in data:
            work_exp.job_title = data["job_title"]
        if "date" in data:
            # Try to parse date
            try:
                work_exp.start_date = datetime.strptime(data["date"], "%m/%d/%Y").date()
            except:
                pass
    
    def _update_education(self, data: Dict[str, Any]):
        """Update education information"""
        if self.state.current_education_index is None:
            # Create new education entry
            education = Education()
            self.state.resume_data.education.append(education)
            self.state.current_education_index = len(self.state.resume_data.education) - 1
        
        education = self.state.resume_data.education[self.state.current_education_index]
        
        if "institution_name" in data:
            education.institution_name = data["institution_name"]
        if "degree" in data:
            education.degree = data["degree"]
    
    def _update_skills(self, data: Dict[str, Any]):
        """Update skills information"""
        if "skills" in data:
            for skill_name in data["skills"]:
                # Check if skill already exists
                existing_skill = next((s for s in self.state.resume_data.skills if s.name.lower() == skill_name.lower()), None)
                if not existing_skill:
                    skill = Skill(name=skill_name)
                    self.state.resume_data.skills.append(skill)
    
    def _get_next_question(self) -> str:
        """Get the next question to ask"""
        if self.state.current_section == "personal_info":
            return self._get_personal_info_question()
        elif self.state.current_section == "work_experience":
            return self._get_work_experience_question()
        elif self.state.current_section == "education":
            return self._get_education_question()
        elif self.state.current_section == "skills":
            return self._get_skills_question()
        else:
            return "Is there anything else you'd like to add to your resume?"
    
    def _get_personal_info_question(self) -> str:
        """Get next personal info question"""
        questions = self.question_templates["personal_info"]
        
        if not self.state.resume_data.personal_info.full_name:
            return questions[0]
        elif not self.state.resume_data.personal_info.phone:
            return questions[1]
        elif not self.state.resume_data.personal_info.email:
            return questions[2]
        elif not self.state.resume_data.personal_info.address:
            return questions[3]
        else:
            # Move to work experience
            self.state.current_section = "work_experience"
            return self._get_work_experience_question()
    
    def _get_work_experience_question(self) -> str:
        """Get next work experience question"""
        questions = self.question_templates["work_experience"]
        
        if self.state.current_work_index is None:
            return questions[0]
        
        work_exp = self.state.resume_data.work_experience[self.state.current_work_index]
        
        if not work_exp.company_name:
            return questions[0]
        elif not work_exp.job_title:
            return questions[1].format(company=work_exp.company_name)
        elif not work_exp.start_date:
            return questions[2].format(company=work_exp.company_name)
        else:
            # Ask about more details or move to next section
            if len(work_exp.responsibilities) == 0:
                return questions[5].format(company=work_exp.company_name)
            else:
                # Move to education
                self.state.current_section = "education"
                return self._get_education_question()
    
    def _get_education_question(self) -> str:
        """Get next education question"""
        questions = self.question_templates["education"]
        
        if self.state.current_education_index is None:
            return questions[0]
        
        education = self.state.resume_data.education[self.state.current_education_index]
        
        if not education.institution_name:
            return questions[0]
        elif not education.degree:
            return questions[1].format(institution=education.institution_name)
        else:
            # Move to skills
            self.state.current_section = "skills"
            return self._get_skills_question()
    
    def _get_skills_question(self) -> str:
        """Get next skills question"""
        questions = self.question_templates["skills"]
        
        if len(self.state.resume_data.skills) == 0:
            return questions[0]
        else:
            return "Great! I think we have enough information. Let me generate your resume."
    
    def _is_conversation_complete(self) -> bool:
        """Check if conversation is complete"""
        # Basic completion criteria
        has_personal_info = (
            self.state.resume_data.personal_info.full_name and
            self.state.resume_data.personal_info.phone and
            self.state.resume_data.personal_info.email
        )
        
        has_work_experience = len(self.state.resume_data.work_experience) > 0
        
        return has_personal_info and has_work_experience
    
    def get_resume(self) -> Resume:
        """Get the current resume data"""
        return self.state.resume_data
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        return {
            "total_exchanges": len(self.state.conversation_history),
            "completed_sections": self.state.completed_sections,
            "missing_fields": self.state.missing_fields,
            "is_complete": self.state.is_complete
        }
