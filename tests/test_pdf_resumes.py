#!/usr/bin/env python3
"""
Test PDF Resume Parsing

This script specifically tests the PDF resume files in the sample_resumes folder.
"""

import sys
import os
from datetime import datetime
import glob

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.resume_parser import ResumeParser
from models.resume_models import Resume

def test_pdf_resumes():
    """Test all PDF files in the sample_resumes folder"""
    parser = ResumeParser()
    
    print("🔍 PDF RESUME PARSER TESTING")
    print("=" * 60)
    print()
    
    # Find all PDF files in sample_resumes directory
    pdf_files = glob.glob("sample_resumes/*.pdf")
    
    if not pdf_files:
        print("❌ No PDF files found in sample_resumes directory")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files to test:")
    for pdf_file in pdf_files:
        print(f"  • {os.path.basename(pdf_file)}")
    print()
    
    test_results = []
    
    for pdf_file in pdf_files:
        file_name = os.path.basename(pdf_file)
        print(f"📄 TESTING: {file_name}")
        print("-" * 50)
        
        try:
            # Parse the PDF resume
            start_time = datetime.now()
            parsed_resume = parser.parse_resume_file(pdf_file)
            parse_time = (datetime.now() - start_time).total_seconds()
            
            # Identify missing information
            missing_info = parser.identify_missing_information(parsed_resume)
            
            print(f"✅ Parsed in {parse_time:.3f} seconds")
            print()
            
            # Display results
            display_parsing_results(file_name, parsed_resume, missing_info)
            
            # Store results
            test_results.append({
                'file': file_name,
                'success': True,
                'parse_time': parse_time,
                'missing_count': len(missing_info),
                'sections_found': count_sections_found(parsed_resume)
            })
            
        except Exception as e:
            print(f"❌ Error parsing {file_name}: {str(e)}")
            test_results.append({
                'file': file_name,
                'success': False,
                'error': str(e)
            })
        
        print()
        print("=" * 60)
        print()
    
    # Print summary
    print_test_summary(test_results)

def display_parsing_results(file_name: str, resume: Resume, missing_info: list):
    """Display detailed parsing results"""
    
    # Personal Information
    print("👤 PERSONAL INFORMATION:")
    pi = resume.personal_info
    print_field("Name", pi.full_name)
    print_field("Email", pi.email)
    print_field("Phone", pi.phone)
    print_field("Address", pi.address)
    print()
    
    # Work Experience
    print(f"💼 WORK EXPERIENCE ({len(resume.work_experience)} jobs found):")
    if resume.work_experience:
        for i, work in enumerate(resume.work_experience, 1):
            print(f"  Job {i}:")
            print_field("    Company", work.company_name)
            print_field("    Title", work.job_title)
            print_field("    Start Date", work.start_date)
            print_field("    End Date", work.end_date if not work.current_job else "Current")
            print_field("    Location", work.location)
            if work.responsibilities:
                print(f"    ✅ Responsibilities: {len(work.responsibilities)} items")
                for resp in work.responsibilities[:2]:  # Show first 2
                    print(f"      • {resp}")
                if len(work.responsibilities) > 2:
                    print(f"      ... and {len(work.responsibilities) - 2} more")
            else:
                print(f"    ❌ Responsibilities: Not found")
    else:
        print("  ❌ No work experience found")
    print()
    
    # Education
    print(f"🎓 EDUCATION ({len(resume.education)} entries found):")
    if resume.education:
        for i, edu in enumerate(resume.education, 1):
            print(f"  Education {i}:")
            print_field("    Institution", edu.institution_name)
            print_field("    Degree", edu.degree)
            print_field("    Field of Study", edu.field_of_study)
            print_field("    Graduation Date", edu.graduation_date)
            print_field("    GPA", edu.gpa)
    else:
        print("  ❌ No education found")
    print()
    
    # Skills
    print(f"🛠️ SKILLS ({len(resume.skills)} skills found):")
    if resume.skills:
        skill_names = [skill.name for skill in resume.skills]
        print(f"  ✅ Skills detected: {', '.join(skill_names)}")
    else:
        print("  ❌ No skills found")
    print()
    
    # Missing Information
    print(f"❌ MISSING INFORMATION ({len(missing_info)} items):")
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
    else:
        print("  ✅ No critical information missing!")

def print_field(label: str, value):
    """Print a field with status indicator"""
    if value:
        print(f"  ✅ {label}: {value}")
    else:
        print(f"  ❌ {label}: Not found")

def count_sections_found(resume: Resume) -> dict:
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

def print_test_summary(test_results: list):
    """Print summary of all tests"""
    print("📊 PDF PARSING TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in test_results if r['success']]
    failed_tests = [r for r in test_results if not r['success']]
    
    print(f"✅ Successful PDF parses: {len(successful_tests)}")
    print(f"❌ Failed PDF parses: {len(failed_tests)}")
    
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
                print(f"  {test['file']}:")
                print(f"    Personal Info: {sections['personal_info_fields']}/4 fields")
                print(f"    Work Experience: {sections['work_experience']} jobs")
                print(f"    Education: {sections['education']} entries")
                print(f"    Skills: {sections['skills']} skills")
    
    if failed_tests:
        print("\n❌ FAILED PDF PARSES:")
        for test in failed_tests:
            print(f"  • {test['file']}: {test['error']}")
    
    print("\n🎯 PDF PARSING INSIGHTS:")
    print("• PDF text extraction quality varies by document")
    print("• Some formatting may be lost during PDF-to-text conversion")
    print("• Complex layouts may require manual review")
    print("• Consider providing text versions for best results")

if __name__ == "__main__":
    test_pdf_resumes()
