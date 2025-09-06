from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    VOLUNTEER = "volunteer"

class EducationLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    CERTIFICATE = "certificate"
    DIPLOMA = "diploma"
    GED = "ged"

class WorkExperience(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    current_job: bool = False
    location: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    responsibilities: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    skills_used: List[str] = Field(default_factory=list)
    salary: Optional[str] = None
    supervisor_name: Optional[str] = None
    reason_for_leaving: Optional[str] = None
    promotions: List[str] = Field(default_factory=list)
    team_size: Optional[int] = None
    projects: List[str] = Field(default_factory=list)

class Education(BaseModel):
    institution_name: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    graduation_date: Optional[date] = None
    gpa: Optional[float] = None
    location: Optional[str] = None
    honors: List[str] = Field(default_factory=list)
    relevant_coursework: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

class Skill(BaseModel):
    name: str
    category: Optional[str] = None  # technical, soft, language, etc.
    proficiency_level: Optional[str] = None  # beginner, intermediate, advanced, expert
    years_experience: Optional[int] = None
    certifications: List[str] = Field(default_factory=list)

class PersonalInfo(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    summary: Optional[str] = None

class Resume(BaseModel):
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    additional_info: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ConversationState(BaseModel):
    current_section: Optional[str] = None  # personal_info, work_experience, education, skills
    current_work_index: Optional[int] = None
    current_education_index: Optional[int] = None
    missing_fields: List[str] = Field(default_factory=list)
    completed_sections: List[str] = Field(default_factory=list)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    resume_data: Resume = Field(default_factory=Resume)
    is_complete: bool = False

class QuestionContext(BaseModel):
    field_name: str
    field_type: str
    current_value: Optional[Any] = None
    is_required: bool = True
    follow_up_questions: List[str] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
