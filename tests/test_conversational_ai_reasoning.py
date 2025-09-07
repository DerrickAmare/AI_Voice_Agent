#!/usr/bin/env python3
"""
Test Conversational AI Reasoning After Resume Parsing

This script tests the complete workflow:
1. Parse resume and identify missing information
2. Feed parsed data to ResumeAnalyzerAgent for AI reasoning
3. Test conversational responses and recommendations
"""

import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.resume_parser import ResumeParser
from agents.resume_analyzer_agent import ResumeAnalyzerAgent
from models.resume_models import Resume

def test_ai_reasoning():
    """Test the AI's conversational reasoning after resume parsing"""
    parser = ResumeParser()
    analyzer = ResumeAnalyzerAgent()
    
    print("🤖 TESTING CONVERSATIONAL AI REASONING")
    print("=" * 60)
    print()
    
    # Test resume with missing information
    test_resume = """MICHAEL RODRIGUEZ
mike.rodriguez@gmail.com

EXPERIENCE

WAREHOUSE SUPERVISOR
ABC Logistics
2020 - 2023
Supervised warehouse operations and managed inventory

FORKLIFT OPERATOR
XYZ Distribution
2018 - 2020
Operated forklifts and moved materials

EDUCATION

High School Diploma
Central High School
2018

SKILLS
Forklift operation, inventory management, teamwork"""
    
    print("📄 TESTING RESUME:")
    print("-" * 30)
    print(test_resume)
    print()
    
    # Step 1: Parse the resume
    print("🔍 STEP 1: PARSING RESUME")
    print("-" * 30)
    parsed_resume = parser.parse_text_resume(test_resume)
    missing_info = parser.identify_missing_information(parsed_resume)
    
    print(f"✅ Parsing completed")
    print(f"📋 Missing information items: {len(missing_info)}")
    for item in missing_info:
        print(f"  • {item}")
    print()
    
    # Step 2: Convert parsed resume to dict for AI analysis
    print("🔄 STEP 2: PREPARING DATA FOR AI ANALYSIS")
    print("-" * 30)
    
    resume_data = {
        'personal_info': {
            'name': parsed_resume.personal_info.full_name,
            'email': parsed_resume.personal_info.email,
            'phone': parsed_resume.personal_info.phone,
            'address': parsed_resume.personal_info.address
        },
        'work_experience': [
            {
                'company': work.company_name,
                'title': work.job_title,
                'start_date': str(work.start_date) if work.start_date else None,
                'end_date': str(work.end_date) if work.end_date else None,
                'responsibilities': work.responsibilities
            } for work in parsed_resume.work_experience
        ],
        'education': [
            {
                'institution': edu.institution_name,
                'degree': edu.degree,
                'graduation_date': str(edu.graduation_date) if edu.graduation_date else None
            } for edu in parsed_resume.education
        ],
        'skills': [skill.name for skill in parsed_resume.skills],
        'missing_information': missing_info
    }
    
    print(f"✅ Data prepared for AI analysis")
    print(f"📊 Resume data structure created with {len(resume_data)} main sections")
    print()
    
    # Step 3: Feed to AI for analysis and reasoning
    print("🧠 STEP 3: AI ANALYSIS AND REASONING")
    print("-" * 30)
    
    try:
        analysis_input = {
            'resume_data': resume_data,
            'target_role': 'Warehouse Manager',
            'industry': 'Logistics and Supply Chain',
            'missing_info': missing_info
        }
        
        # Get AI analysis
        analysis_result = analyzer.process(analysis_input)
        
        if analysis_result.success:
            print("✅ AI analysis completed successfully")
            print(f"🎯 Confidence: {analysis_result.confidence}")
            print()
            
            # Display AI reasoning and recommendations
            print("🤖 AI REASONING AND RECOMMENDATIONS:")
            print("-" * 40)
            
            if 'raw_analysis' in analysis_result.data:
                print("📝 Detailed Analysis:")
                print(analysis_result.data['raw_analysis'])
                print()
            
            if 'content_gaps' in analysis_result.data:
                print("🔍 Content Gaps Identified:")
                for gap in analysis_result.data['content_gaps']:
                    print(f"  • {gap}")
                print()
            
            if 'keyword_suggestions' in analysis_result.data:
                print("🔑 Keyword Suggestions:")
                for keyword in analysis_result.data['keyword_suggestions'][:10]:  # Show first 10
                    print(f"  • {keyword.strip()}")
                print()
            
            if 'priority_improvements' in analysis_result.data:
                print("⭐ Priority Improvements:")
                for improvement in analysis_result.data['priority_improvements']:
                    print(f"  • {improvement}")
                print()
            
            if 'ats_score' in analysis_result.data:
                print(f"📊 ATS Compatibility Score: {analysis_result.data['ats_score']}/100")
            
            if 'overall_score' in analysis_result.data:
                print(f"🎯 Overall Resume Score: {analysis_result.data['overall_score']}/100")
            
        else:
            print(f"❌ AI analysis failed: {analysis_result.message}")
    
    except Exception as e:
        print(f"❌ Error during AI analysis: {str(e)}")
        print("Note: This might be due to missing OpenAI API key or network issues")
    
    print()
    print("=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    print()
    print("This test demonstrates the complete workflow:")
    print("1. ✅ Resume parsing and missing information detection")
    print("2. ✅ Data preparation for AI analysis")
    print("3. 🤖 AI-powered conversational reasoning and recommendations")
    print()
    print("The AI provides:")
    print("• Detailed analysis of resume content")
    print("• Specific improvement recommendations")
    print("• Industry-specific keyword suggestions")
    print("• ATS compatibility scoring")
    print("• Priority action items")
    print()
    print("💡 This simulates what users would experience during a phone conversation")
    print("   where the AI analyzes their resume and provides personalized advice.")

def test_multiple_scenarios():
    """Test AI reasoning with different resume scenarios"""
    parser = ResumeParser()
    analyzer = ResumeAnalyzerAgent()
    
    print("\n" + "=" * 60)
    print("🔄 TESTING MULTIPLE SCENARIOS")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Entry Level Resume",
            "target_role": "Customer Service Representative",
            "industry": "Retail",
            "resume": """JANE SMITH
jane.smith@email.com
(555) 123-4567

EDUCATION
Bachelor of Arts in Communications
State University
Graduated: 2023

SKILLS
Communication, Microsoft Office, Customer Service"""
        },
        {
            "name": "Technical Resume",
            "target_role": "Software Developer",
            "industry": "Technology",
            "resume": """ALEX JOHNSON
alex.j@techmail.com

EXPERIENCE
JUNIOR DEVELOPER
Tech Startup
2022 - Present
Built web applications using JavaScript and Python

EDUCATION
Computer Science Degree
Tech University
2022

SKILLS
Python, JavaScript, HTML, CSS, Git"""
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 SCENARIO {i}: {scenario['name']}")
        print("-" * 40)
        
        # Parse resume
        parsed_resume = parser.parse_text_resume(scenario['resume'])
        missing_info = parser.identify_missing_information(parsed_resume)
        
        print(f"Target Role: {scenario['target_role']}")
        print(f"Industry: {scenario['industry']}")
        print(f"Missing Items: {len(missing_info)}")
        
        # Quick analysis without full AI call (to avoid API limits)
        print("Key Missing Information:")
        for item in missing_info[:5]:  # Show first 5
            print(f"  • {item}")
        
        print(f"✅ Scenario {i} analysis ready for AI processing")

if __name__ == "__main__":
    test_ai_reasoning()
    test_multiple_scenarios()
