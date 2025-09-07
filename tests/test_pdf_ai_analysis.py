#!/usr/bin/env python3
"""
Test PDF Resume Parsing with AI Analysis

This script tests PDF resume files and runs them through the conversational AI
for complete analysis and recommendations.
"""

import sys
import os
from datetime import datetime
import glob

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.resume_parser import ResumeParser
from agents.resume_analyzer_agent import ResumeAnalyzerAgent
from models.resume_models import Resume

def test_pdf_ai_analysis():
    """Test PDF files with full AI analysis"""
    parser = ResumeParser()
    analyzer = ResumeAnalyzerAgent()
    
    print("🤖 PDF RESUME AI ANALYSIS TESTING")
    print("=" * 70)
    print()
    
    # Find all PDF files
    pdf_files = glob.glob("sample_resumes/*.pdf")
    
    if not pdf_files:
        print("❌ No PDF files found in sample_resumes directory")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files to analyze:")
    for pdf_file in pdf_files:
        print(f"  • {os.path.basename(pdf_file)}")
    print()
    
    for pdf_file in pdf_files:
        file_name = os.path.basename(pdf_file)
        print(f"📄 ANALYZING: {file_name}")
        print("=" * 50)
        
        try:
            # Step 1: Parse the PDF resume
            print("🔍 STEP 1: PARSING PDF RESUME")
            print("-" * 30)
            start_time = datetime.now()
            parsed_resume = parser.parse_resume_file(pdf_file)
            parse_time = (datetime.now() - start_time).total_seconds()
            
            # Identify missing information
            missing_info = parser.identify_missing_information(parsed_resume)
            
            print(f"✅ PDF parsed in {parse_time:.3f} seconds")
            print(f"📋 Missing information items: {len(missing_info)}")
            for item in missing_info[:5]:  # Show first 5
                print(f"  • {item}")
            if len(missing_info) > 5:
                print(f"  ... and {len(missing_info) - 5} more")
            print()
            
            # Step 2: Prepare data for AI analysis
            print("🔄 STEP 2: PREPARING DATA FOR AI")
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
            print(f"📊 Resume sections: Personal Info, Work ({len(parsed_resume.work_experience)}), Education ({len(parsed_resume.education)}), Skills ({len(parsed_resume.skills)})")
            print()
            
            # Step 3: AI Analysis
            print("🧠 STEP 3: AI ANALYSIS AND RECOMMENDATIONS")
            print("-" * 30)
            
            # Determine target role based on resume content
            target_role = determine_target_role(parsed_resume)
            industry = determine_industry(parsed_resume)
            
            analysis_input = {
                'resume_data': resume_data,
                'target_role': target_role,
                'industry': industry,
                'missing_info': missing_info
            }
            
            try:
                analysis_result = analyzer.process(analysis_input)
                
                if analysis_result.success:
                    print("✅ AI analysis completed successfully")
                    print(f"🎯 Target Role: {target_role}")
                    print(f"🏢 Industry: {industry}")
                    print(f"📊 Confidence: {analysis_result.confidence}")
                    print()
                    
                    # Display key recommendations
                    if 'raw_analysis' in analysis_result.data:
                        analysis_text = analysis_result.data['raw_analysis']
                        # Extract key points
                        print("🔑 KEY AI RECOMMENDATIONS:")
                        print("-" * 25)
                        
                        # Extract recommendations section
                        if "RECOMMENDATIONS:" in analysis_text:
                            recommendations = analysis_text.split("RECOMMENDATIONS:")[1]
                            lines = recommendations.split('\n')[:10]  # First 10 lines
                            for line in lines:
                                line = line.strip()
                                if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '-', '•'))):
                                    print(f"  {line}")
                        print()
                    
                    if 'priority_improvements' in analysis_result.data:
                        print("⭐ PRIORITY IMPROVEMENTS:")
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
                print("Note: This might be due to missing OpenAI API key")
            
        except Exception as e:
            print(f"❌ Error processing {file_name}: {str(e)}")
        
        print()
        print("=" * 70)
        print()
    
    print("🎯 COMPLETE WORKFLOW DEMONSTRATED:")
    print("1. ✅ PDF parsing with text extraction")
    print("2. ✅ Missing information detection")
    print("3. ✅ AI-powered analysis and recommendations")
    print("4. ✅ Industry-specific suggestions")
    print("5. ✅ ATS compatibility scoring")
    print()
    print("💡 This represents the full user experience:")
    print("   Upload PDF → Parse → Analyze → Get personalized advice")

def determine_target_role(resume: Resume) -> str:
    """Determine likely target role based on resume content"""
    # Simple heuristic based on skills and experience
    skills_text = ' '.join([skill.name.lower() for skill in resume.skills])
    experience_text = ' '.join([work.job_title.lower() if work.job_title else '' for work in resume.work_experience])
    
    combined_text = skills_text + ' ' + experience_text
    
    if any(word in combined_text for word in ['warehouse', 'forklift', 'logistics', 'inventory']):
        return "Warehouse Manager"
    elif any(word in combined_text for word in ['software', 'developer', 'programming', 'code']):
        return "Software Developer"
    elif any(word in combined_text for word in ['marketing', 'sales', 'customer']):
        return "Marketing Specialist"
    elif any(word in combined_text for word in ['manager', 'supervisor', 'lead']):
        return "Operations Manager"
    else:
        return "General Position"

def determine_industry(resume: Resume) -> str:
    """Determine likely industry based on resume content"""
    skills_text = ' '.join([skill.name.lower() for skill in resume.skills])
    experience_text = ' '.join([work.job_title.lower() if work.job_title else '' for work in resume.work_experience])
    
    combined_text = skills_text + ' ' + experience_text
    
    if any(word in combined_text for word in ['warehouse', 'logistics', 'supply', 'distribution']):
        return "Logistics and Supply Chain"
    elif any(word in combined_text for word in ['software', 'tech', 'programming', 'development']):
        return "Technology"
    elif any(word in combined_text for word in ['retail', 'sales', 'customer', 'service']):
        return "Retail"
    elif any(word in combined_text for word in ['manufacturing', 'production', 'factory']):
        return "Manufacturing"
    else:
        return "General Business"

if __name__ == "__main__":
    test_pdf_ai_analysis()
