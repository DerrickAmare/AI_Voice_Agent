#!/usr/bin/env python3
"""
Resume Parser Test Script

This script tests the resume parsing functionality including:
1. Parsing different resume formats
2. Extracting structured information
3. Identifying missing information
4. Displaying comprehensive results
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.resume_parser import ResumeParser
from models.resume_models import Resume, PersonalInfo, WorkExperience, Education, Skill

class ResumeParserTester:
    def __init__(self):
        self.parser = ResumeParser()
        self.test_results = []
    
    def run_all_tests(self):
        """Run all resume parsing tests"""
        print("=" * 60)
        print("🔍 RESUME PARSER TESTING SUITE")
        print("=" * 60)
        print()
        
        # Test different resume samples
        test_cases = [
            ("Complete Resume", self.get_complete_resume()),
            ("Incomplete Resume", self.get_incomplete_resume()),
            ("Poorly Formatted Resume", self.get_poorly_formatted_resume())
        ]
        
        for test_name, resume_text in test_cases:
            print(f"📄 Testing: {test_name}")
            print("-" * 50)
            self.test_resume_parsing(test_name, resume_text)
            print()
        
        # Summary
        self.print_test_summary()
    
    def test_resume_parsing(self, test_name: str, resume_text: str):
        """Test parsing a single resume"""
        try:
            # Parse the resume
            start_time = datetime.now()
            parsed_resume = self.parser.parse_text_resume(resume_text)
            parse_time = (datetime.now() - start_time).total_seconds()
            
            # Identify missing information
            missing_info = self.parser.identify_missing_information(parsed_resume)
            
            # Display results
            self.display_parsing_results(test_name, parsed_resume, missing_info, parse_time)
            
            # Store results for summary
            self.test_results.append({
                'name': test_name,
                'success': True,
                'parse_time': parse_time,
                'missing_count': len(missing_info)
            })
            
        except Exception as e:
            print(f"❌ Error parsing resume: {str(e)}")
            self.test_results.append({
                'name': test_name,
                'success': False,
                'error': str(e)
            })
    
    def display_parsing_results(self, test_name: str, resume: Resume, missing_info: list, parse_time: float):
        """Display detailed parsing results"""
        print(f"✅ Parsed in {parse_time:.3f} seconds")
        print()
        
        # Personal Information
        print("👤 PERSONAL INFORMATION:")
        pi = resume.personal_info
        self.print_field("Name", pi.full_name)
        self.print_field("Email", pi.email)
        self.print_field("Phone", pi.phone)
        self.print_field("Address", pi.address)
        print()
        
        # Work Experience
        print(f"💼 WORK EXPERIENCE ({len(resume.work_experience)} jobs found):")
        for i, work in enumerate(resume.work_experience, 1):
            print(f"  Job {i}:")
            self.print_field("    Company", work.company_name)
            self.print_field("    Title", work.job_title)
            self.print_field("    Start Date", work.start_date)
            self.print_field("    End Date", work.end_date if not work.current_job else "Current")
            self.print_field("    Responsibilities", f"{len(work.responsibilities)} items" if work.responsibilities else None)
        if not resume.work_experience:
            print("  ❌ No work experience found")
        print()
        
        # Education
        print(f"🎓 EDUCATION ({len(resume.education)} entries found):")
        for i, edu in enumerate(resume.education, 1):
            print(f"  Education {i}:")
            self.print_field("    Institution", edu.institution_name)
            self.print_field("    Degree", edu.degree)
            self.print_field("    Field", edu.field_of_study)
            self.print_field("    Graduation", edu.graduation_date)
        if not resume.education:
            print("  ❌ No education found")
        print()
        
        # Skills
        print(f"🛠️  SKILLS ({len(resume.skills)} skills found):")
        if resume.skills:
            skills_by_category = {}
            for skill in resume.skills:
                category = skill.category or "General"
                if category not in skills_by_category:
                    skills_by_category[category] = []
                skills_by_category[category].append(skill.name)
            
            for category, skills in skills_by_category.items():
                print(f"  {category}: {', '.join(skills)}")
        else:
            print("  ❌ No skills found")
        print()
        
        # Missing Information
        print("❌ MISSING INFORMATION:")
        if missing_info:
            for item in missing_info:
                print(f"  • {item}")
        else:
            print("  ✅ No critical information missing!")
        print()
    
    def print_field(self, label: str, value: Any):
        """Print a field with status indicator"""
        if value:
            print(f"  ✅ {label}: {value}")
        else:
            print(f"  ❌ {label}: Not found")
    
    def get_complete_resume(self) -> str:
        """Return a well-formatted complete resume"""
        return """
JOHN SMITH
Email: john.smith@email.com
Phone: (555) 123-4567
Address: 123 Main Street, Anytown, CA 90210

PROFESSIONAL EXPERIENCE

SENIOR SOFTWARE ENGINEER
TechCorp Inc.
January 2020 - Present
• Developed and maintained web applications using Python and JavaScript
• Led a team of 5 developers on multiple projects
• Implemented automated testing procedures that reduced bugs by 40%
• Collaborated with product managers to define technical requirements

SOFTWARE DEVELOPER
StartupXYZ LLC
June 2018 - December 2019
• Built REST APIs using Python Flask framework
• Designed and implemented database schemas using PostgreSQL
• Participated in code reviews and maintained coding standards
• Worked in agile development environment with 2-week sprints

EDUCATION

BACHELOR OF SCIENCE IN COMPUTER SCIENCE
University of California, Los Angeles
Graduated: May 2018
GPA: 3.7/4.0

SKILLS
Programming Languages: Python, JavaScript, Java, SQL
Web Technologies: HTML, CSS, React, Flask, Django
Databases: PostgreSQL, MySQL, MongoDB
Tools: Git, Docker, AWS, Jenkins
Soft Skills: Leadership, Communication, Problem Solving, Teamwork
        """.strip()
    
    def get_incomplete_resume(self) -> str:
        """Return a resume with missing information"""
        return """
JANE DOE
jane.doe@email.com

EXPERIENCE

MARKETING MANAGER
ABC Company
2019 - 2022
Managed marketing campaigns and social media presence

ASSISTANT MANAGER
XYZ Store
Helped with daily operations and customer service

EDUCATION

Business Administration
State University

SKILLS
Microsoft Office, Communication, Organization
        """.strip()
    
    def get_poorly_formatted_resume(self) -> str:
        """Return a poorly formatted resume to test parser robustness"""
        return """
mike johnson
email:mike.j@test.com phone:555.987.6543

work history:
TECHNICIAN at FACTORY CORP from 2020 to now
-operated machinery
-quality control checks
-safety procedures

HELPER at LOCAL SHOP 2018-2020
basic duties and cleaning

education: high school diploma 2018

skills: welding machining teamwork excel
        """.strip()
    
    def print_test_summary(self):
        """Print summary of all tests"""
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        successful_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        print(f"✅ Successful tests: {len(successful_tests)}")
        print(f"❌ Failed tests: {len(failed_tests)}")
        
        if successful_tests:
            avg_parse_time = sum(r['parse_time'] for r in successful_tests) / len(successful_tests)
            total_missing = sum(r['missing_count'] for r in successful_tests)
            print(f"⏱️  Average parse time: {avg_parse_time:.3f} seconds")
            print(f"📋 Total missing information items: {total_missing}")
        
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['error']}")
        
        print("\n🎯 RECOMMENDATIONS:")
        print("• Test with your own resume files by modifying the sample text")
        print("• Add PDF parsing capability for real file uploads")
        print("• Enhance regex patterns for better extraction accuracy")
        print("• Consider adding machine learning for improved parsing")

def main():
    """Main function to run the tests"""
    tester = ResumeParserTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
