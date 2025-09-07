#!/usr/bin/env python3
"""
Enhanced Resume Parser Test Script

This script tests the resume parsing functionality with both embedded samples
and external resume files, including:
1. Parsing different resume formats
2. Extracting structured information
3. Identifying missing information
4. Loading resume files from sample_resumes directory
5. Displaying comprehensive results
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import glob

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.resume_parser import ResumeParser
from models.resume_models import Resume, PersonalInfo, WorkExperience, Education, Skill

class EnhancedResumeParserTester:
    def __init__(self):
        self.parser = ResumeParser()
        self.test_results = []
        self.sample_resumes_dir = "sample_resumes"
    
    def run_all_tests(self):
        """Run all resume parsing tests"""
        print("=" * 70)
        print("🔍 ENHANCED RESUME PARSER TESTING SUITE")
        print("=" * 70)
        print()
        
        # Test embedded samples
        print("📋 TESTING EMBEDDED SAMPLES")
        print("=" * 40)
        embedded_test_cases = [
            ("Complete Resume (Embedded)", self.get_complete_resume()),
            ("Incomplete Resume (Embedded)", self.get_incomplete_resume()),
            ("Poorly Formatted Resume (Embedded)", self.get_poorly_formatted_resume())
        ]
        
        for test_name, resume_text in embedded_test_cases:
            print(f"📄 Testing: {test_name}")
            print("-" * 50)
            self.test_resume_parsing(test_name, resume_text)
            print()
        
        # Test file-based samples
        print("\n📁 TESTING FILE-BASED SAMPLES")
        print("=" * 40)
        self.test_file_based_resumes()
        
        # Summary
        self.print_test_summary()
    
    def test_file_based_resumes(self):
        """Test resumes loaded from files"""
        if not os.path.exists(self.sample_resumes_dir):
            print(f"❌ Sample resumes directory '{self.sample_resumes_dir}' not found")
            return
        
        # Find all text files in sample_resumes directory
        resume_files = glob.glob(os.path.join(self.sample_resumes_dir, "*.txt"))
        
        if not resume_files:
            print(f"❌ No .txt files found in '{self.sample_resumes_dir}' directory")
            return
        
        for file_path in resume_files:
            file_name = os.path.basename(file_path)
            print(f"📄 Testing: {file_name}")
            print("-" * 50)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    resume_text = f.read()
                
                self.test_resume_parsing(f"File: {file_name}", resume_text)
                
            except Exception as e:
                print(f"❌ Error reading file {file_name}: {str(e)}")
                self.test_results.append({
                    'name': f"File: {file_name}",
                    'success': False,
                    'error': f"File read error: {str(e)}"
                })
            
            print()
    
    def test_resume_parsing(self, test_name: str, resume_text: str):
        """Test parsing a single resume"""
        try:
            # Show original text preview
            print("📝 ORIGINAL TEXT PREVIEW:")
            preview_lines = resume_text.strip().split('\n')[:5]
            for line in preview_lines:
                print(f"   {line}")
            if len(resume_text.strip().split('\n')) > 5:
                print("   ...")
            print()
            
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
                'missing_count': len(missing_info),
                'sections_found': self.count_sections_found(parsed_resume)
            })
            
        except Exception as e:
            print(f"❌ Error parsing resume: {str(e)}")
            self.test_results.append({
                'name': test_name,
                'success': False,
                'error': str(e)
            })
    
    def count_sections_found(self, resume: Resume) -> Dict[str, int]:
        """Count how many items were found in each section"""
        return {
            'personal_info_fields': sum([
                1 for field in [resume.personal_info.full_name, resume.personal_info.email, 
                               resume.personal_info.phone, resume.personal_info.address] 
                if field
            ]),
            'work_experience': len(resume.work_experience),
            'education': len(resume.education),
            'skills': len(resume.skills)
        }
    
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
            self.print_field("    Location", work.location)
            self.print_field("    Employment Type", work.employment_type)
            if work.responsibilities:
                print(f"    ✅ Responsibilities: {len(work.responsibilities)} items")
                for resp in work.responsibilities[:2]:  # Show first 2
                    print(f"      • {resp}")
                if len(work.responsibilities) > 2:
                    print(f"      ... and {len(work.responsibilities) - 2} more")
            else:
                print(f"    ❌ Responsibilities: Not found")
        if not resume.work_experience:
            print("  ❌ No work experience found")
        print()
        
        # Education
        print(f"🎓 EDUCATION ({len(resume.education)} entries found):")
        for i, edu in enumerate(resume.education, 1):
            print(f"  Education {i}:")
            self.print_field("    Institution", edu.institution_name)
            self.print_field("    Degree", edu.degree)
            self.print_field("    Field of Study", edu.field_of_study)
            self.print_field("    Graduation Date", edu.graduation_date)
            self.print_field("    GPA", edu.gpa)
            self.print_field("    Location", edu.location)
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
        
        # Missing Information Analysis
        print("❌ MISSING INFORMATION ANALYSIS:")
        if missing_info:
            # Categorize missing information
            personal_missing = [item for item in missing_info if any(keyword in item.lower() for keyword in ['name', 'phone', 'email', 'address'])]
            work_missing = [item for item in missing_info if any(keyword in item.lower() for keyword in ['company', 'job', 'start date', 'end date', 'responsibilities'])]
            education_missing = [item for item in missing_info if any(keyword in item.lower() for keyword in ['institution', 'degree', 'graduation'])]
            other_missing = [item for item in missing_info if item not in personal_missing + work_missing + education_missing]
            
            if personal_missing:
                print("  👤 Personal Information:")
                for item in personal_missing:
                    print(f"    • {item}")
            
            if work_missing:
                print("  💼 Work Experience:")
                for item in work_missing:
                    print(f"    • {item}")
            
            if education_missing:
                print("  🎓 Education:")
                for item in education_missing:
                    print(f"    • {item}")
            
            if other_missing:
                print("  📋 Other:")
                for item in other_missing:
                    print(f"    • {item}")
            
            print(f"\n  📊 Total missing items: {len(missing_info)}")
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
        print("=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        successful_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        print(f"✅ Successful tests: {len(successful_tests)}")
        print(f"❌ Failed tests: {len(failed_tests)}")
        
        if successful_tests:
            avg_parse_time = sum(r['parse_time'] for r in successful_tests) / len(successful_tests)
            total_missing = sum(r['missing_count'] for r in successful_tests)
            
            print(f"⏱️  Average parse time: {avg_parse_time:.3f} seconds")
            print(f"📋 Total missing information items: {total_missing}")
            
            # Section analysis
            print("\n📊 SECTION DETECTION ANALYSIS:")
            for test in successful_tests:
                if 'sections_found' in test:
                    sections = test['sections_found']
                    print(f"  {test['name']}:")
                    print(f"    Personal Info: {sections['personal_info_fields']}/4 fields")
                    print(f"    Work Experience: {sections['work_experience']} jobs")
                    print(f"    Education: {sections['education']} entries")
                    print(f"    Skills: {sections['skills']} skills")
        
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['error']}")
        
        print("\n🎯 RECOMMENDATIONS:")
        print("• Replace sample files in 'sample_resumes/' with your own resume files")
        print("• Test with different resume formats (PDF support coming soon)")
        print("• Enhance regex patterns for better extraction accuracy")
        print("• Consider adding machine learning for improved parsing")
        print("• Add more comprehensive skill detection patterns")
        
        print("\n📁 HOW TO ADD YOUR OWN RESUMES:")
        print("1. Save your resume as a .txt file in the 'sample_resumes/' directory")
        print("2. Run this script again to test your resume")
        print("3. Review the missing information output to improve your resume")

def main():
    """Main function to run the tests"""
    tester = EnhancedResumeParserTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
