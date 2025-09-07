#!/usr/bin/env python3
"""
Simple Resume Parser Test Script

This script demonstrates the resume parsing functionality with a focus on
showing what information is detected vs missing.
"""

import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.resume_parser import ResumeParser
from models.resume_models import Resume

def test_resume_parsing():
    """Test resume parsing with clear examples"""
    parser = ResumeParser()
    
    print("🔍 RESUME PARSER TESTING")
    print("=" * 60)
    print()
    
    # Test cases with different levels of completeness
    test_cases = [
        {
            "name": "Complete Professional Resume",
            "text": """SARAH JOHNSON
Email: sarah.johnson@email.com
Phone: (555) 987-6543
Address: 456 Oak Avenue, Springfield, IL 62701

EXPERIENCE

SENIOR MARKETING MANAGER
Digital Solutions Inc.
March 2021 - Present
• Developed comprehensive digital marketing campaigns
• Managed team of 6 marketing specialists
• Implemented marketing automation tools

MARKETING SPECIALIST
TechStart Company
June 2018 - February 2021
• Created social media content
• Designed email marketing campaigns
• Conducted market research

EDUCATION

BACHELOR OF SCIENCE IN MARKETING
University of Illinois at Springfield
Graduated: May 2015

SKILLS
Google Analytics, HubSpot, Salesforce, Leadership, Communication"""
        },
        {
            "name": "Incomplete Resume (Missing Info)",
            "text": """MICHAEL RODRIGUEZ
mike.rodriguez@gmail.com

EXPERIENCE

WAREHOUSE SUPERVISOR
ABC Logistics
2020 - 2023
Supervised warehouse operations

FORKLIFT OPERATOR
XYZ Distribution
Operated forklifts and moved materials

EDUCATION

High School Diploma
Central High School

SKILLS
Forklift operation, teamwork"""
        },
        {
            "name": "Minimal Resume (Lots Missing)",
            "text": """john doe
john@email.com

worked at factory
did some stuff

went to school"""
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📄 TEST {i}: {test_case['name']}")
        print("-" * 50)
        
        try:
            # Parse the resume
            start_time = datetime.now()
            parsed_resume = parser.parse_text_resume(test_case['text'])
            parse_time = (datetime.now() - start_time).total_seconds()
            
            print(f"✅ Parsed in {parse_time:.3f} seconds")
            print()
            
            # Show what was extracted
            print("📋 EXTRACTED INFORMATION:")
            
            # Personal Info
            pi = parsed_resume.personal_info
            print("👤 Personal Information:")
            print(f"  Name: {'✅ ' + pi.full_name if pi.full_name else '❌ Not found'}")
            print(f"  Email: {'✅ ' + pi.email if pi.email else '❌ Not found'}")
            print(f"  Phone: {'✅ ' + pi.phone if pi.phone else '❌ Not found'}")
            print(f"  Address: {'✅ ' + pi.address if pi.address else '❌ Not found'}")
            print()
            
            # Work Experience
            print(f"💼 Work Experience: {len(parsed_resume.work_experience)} jobs found")
            if parsed_resume.work_experience:
                for j, work in enumerate(parsed_resume.work_experience, 1):
                    print(f"  Job {j}:")
                    print(f"    Company: {'✅ ' + work.company_name if work.company_name else '❌ Not found'}")
                    print(f"    Title: {'✅ ' + work.job_title if work.job_title else '❌ Not found'}")
                    print(f"    Start Date: {'✅ ' + str(work.start_date) if work.start_date else '❌ Not found'}")
                    print(f"    Responsibilities: {'✅ ' + str(len(work.responsibilities)) + ' items' if work.responsibilities else '❌ Not found'}")
            else:
                print("  ❌ No work experience detected")
            print()
            
            # Education
            print(f"🎓 Education: {len(parsed_resume.education)} entries found")
            if parsed_resume.education:
                for j, edu in enumerate(parsed_resume.education, 1):
                    print(f"  Education {j}:")
                    print(f"    Institution: {'✅ ' + edu.institution_name if edu.institution_name else '❌ Not found'}")
                    print(f"    Degree: {'✅ ' + edu.degree if edu.degree else '❌ Not found'}")
                    print(f"    Graduation: {'✅ ' + str(edu.graduation_date) if edu.graduation_date else '❌ Not found'}")
            else:
                print("  ❌ No education detected")
            print()
            
            # Skills
            print(f"🛠️ Skills: {len(parsed_resume.skills)} skills found")
            if parsed_resume.skills:
                skill_names = [skill.name for skill in parsed_resume.skills]
                print(f"  ✅ Skills detected: {', '.join(skill_names)}")
            else:
                print("  ❌ No skills detected")
            print()
            
            # Missing Information Analysis
            missing_info = parser.identify_missing_information(parsed_resume)
            print(f"❌ MISSING INFORMATION ({len(missing_info)} items):")
            if missing_info:
                for item in missing_info:
                    print(f"  • {item}")
            else:
                print("  ✅ No critical information missing!")
            
            print()
            print("=" * 60)
            print()
            
        except Exception as e:
            print(f"❌ Error parsing resume: {str(e)}")
            print()
    
    print("🎯 SUMMARY:")
    print("This test demonstrates:")
    print("• How the parser extracts different types of information")
    print("• What information is successfully detected vs. missing")
    print("• The parser's ability to handle different resume formats")
    print("• Missing information detection for resume improvement")
    print()
    print("📁 TO TEST YOUR OWN RESUME:")
    print("1. Save your resume as a .txt file in the 'sample_resumes/' directory")
    print("2. Run 'python test_resume_parser_with_files.py' to test it")
    print("3. Review the missing information output to improve your resume")

if __name__ == "__main__":
    test_resume_parsing()
