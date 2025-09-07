#!/usr/bin/env python3
"""
Debug Resume Parser Script

This script helps debug the resume parsing functionality by showing
step-by-step what the parser is doing and where it might be failing.
"""

import sys
import os
import re

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.resume_parser import ResumeParser
from models.resume_models import Resume

def debug_parser():
    """Debug the resume parser step by step"""
    parser = ResumeParser()
    
    # Simple test resume
    test_resume = """
JOHN SMITH
Email: john.smith@email.com
Phone: (555) 123-4567
Address: 123 Main Street, Anytown, CA 90210

EXPERIENCE

SOFTWARE ENGINEER
TechCorp Inc.
January 2020 - Present
• Developed web applications
• Led team of developers

EDUCATION

BACHELOR OF SCIENCE IN COMPUTER SCIENCE
University of California
Graduated: May 2018

SKILLS
Python, JavaScript, Leadership
    """.strip()
    
    print("🔍 DEBUGGING RESUME PARSER")
    print("=" * 50)
    print()
    
    print("📝 ORIGINAL RESUME TEXT:")
    print(test_resume)
    print()
    
    # Test text cleaning
    print("🧹 AFTER TEXT CLEANING:")
    cleaned_text = parser._clean_text(test_resume)
    print(cleaned_text)
    print()
    
    # Test pattern matching
    print("🔍 TESTING REGEX PATTERNS:")
    print()
    
    # Test name patterns
    print("👤 NAME PATTERNS:")
    for i, pattern in enumerate(parser.patterns["name"]):
        print(f"  Pattern {i+1}: {pattern}")
        matches = re.findall(pattern, test_resume, re.MULTILINE)
        print(f"  Matches: {matches}")
    print()
    
    # Test email patterns
    print("📧 EMAIL PATTERNS:")
    for i, pattern in enumerate(parser.patterns["email"]):
        print(f"  Pattern {i+1}: {pattern}")
        matches = re.findall(pattern, test_resume)
        print(f"  Matches: {matches}")
    print()
    
    # Test phone patterns
    print("📞 PHONE PATTERNS:")
    for i, pattern in enumerate(parser.patterns["phone"]):
        print(f"  Pattern {i+1}: {pattern}")
        matches = re.findall(pattern, test_resume)
        print(f"  Matches: {matches}")
    print()
    
    # Test section extraction
    print("📋 SECTION EXTRACTION:")
    work_section = parser._extract_section(test_resume, ["experience", "employment", "work history"])
    print(f"Work section found: {work_section is not None}")
    if work_section:
        print(f"Work section content: {work_section[:100]}...")
    
    education_section = parser._extract_section(test_resume, ["education", "academic"])
    print(f"Education section found: {education_section is not None}")
    if education_section:
        print(f"Education section content: {education_section[:100]}...")
    
    skills_section = parser._extract_section(test_resume, ["skills", "technical skills"])
    print(f"Skills section found: {skills_section is not None}")
    if skills_section:
        print(f"Skills section content: {skills_section[:100]}...")
    print()
    
    # Test full parsing
    print("🔄 FULL PARSING TEST:")
    try:
        parsed_resume = parser.parse_text_resume(test_resume)
        
        print(f"Personal Info:")
        print(f"  Name: {parsed_resume.personal_info.full_name}")
        print(f"  Email: {parsed_resume.personal_info.email}")
        print(f"  Phone: {parsed_resume.personal_info.phone}")
        print(f"  Address: {parsed_resume.personal_info.address}")
        
        print(f"Work Experience: {len(parsed_resume.work_experience)} jobs")
        for i, work in enumerate(parsed_resume.work_experience):
            print(f"  Job {i+1}: {work.company_name} - {work.job_title}")
        
        print(f"Education: {len(parsed_resume.education)} entries")
        for i, edu in enumerate(parsed_resume.education):
            print(f"  Education {i+1}: {edu.institution_name} - {edu.degree}")
        
        print(f"Skills: {len(parsed_resume.skills)} skills")
        for skill in parsed_resume.skills:
            print(f"  Skill: {skill.name}")
        
        # Test missing information detection
        missing_info = parser.identify_missing_information(parsed_resume)
        print(f"\nMissing Information ({len(missing_info)} items):")
        for item in missing_info:
            print(f"  • {item}")
            
    except Exception as e:
        print(f"❌ Error during parsing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_parser()
