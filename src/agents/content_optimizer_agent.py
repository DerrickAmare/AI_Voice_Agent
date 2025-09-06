"""
Content Optimizer Agent - Optimizes resume content for maximum impact
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse


class ContentOptimizerAgent(BaseAgent):
    """Agent responsible for optimizing resume content for maximum impact"""
    
    def __init__(self):
        system_prompt = """You are a master resume writer and content strategist with expertise in 
creating compelling, ATS-optimized resumes that get results. Your role is to transform basic resume 
information into powerful, impact-driven content.

OPTIMIZATION EXPERTISE:
- Action verb optimization and variety
- Quantifiable achievement enhancement
- ATS keyword integration
- Impact statement creation
- Industry-specific language adaptation
- Power word selection and placement
- Bullet point optimization
- Professional summary crafting

CONTENT TRANSFORMATION PRINCIPLES:
1. QUANTIFY EVERYTHING: Add numbers, percentages, and metrics wherever possible
2. USE STRONG ACTION VERBS: Start bullet points with powerful, specific verbs
3. SHOW IMPACT: Focus on results and outcomes, not just responsibilities
4. OPTIMIZE FOR ATS: Integrate relevant keywords naturally
5. CREATE COMPELLING NARRATIVES: Tell stories of success and achievement
6. MAINTAIN CONSISTENCY: Use consistent formatting and language throughout

OPTIMIZATION TECHNIQUES:
- Transform responsibilities into achievements
- Add context and scale to accomplishments
- Use industry-specific terminology
- Create compelling professional summaries
- Optimize bullet points for readability and impact
- Enhance skill descriptions with context
- Add quantifiable results to all experiences

CONTENT ENHANCEMENT STRATEGIES:
- Before/After transformations with explanations
- Multiple versions for different audiences
- ATS optimization while maintaining readability
- Industry-specific customization
- Keyword density optimization
- Impact statement creation

Your goal is to transform basic information into compelling, results-driven content that 
stands out to both ATS systems and human recruiters."""

        super().__init__(
            name="ContentOptimizerAgent",
            role="Resume Content Strategist",
            system_prompt=system_prompt
        )
        
    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Optimize resume content for maximum impact"""
        try:
            resume_data = input_data.get('resume_data', {})
            target_role = input_data.get('target_role', '')
            industry = input_data.get('industry', '')
            analysis_results = input_data.get('analysis_results', {})
            
            # Optimize each section of the resume
            optimized_content = self._optimize_resume_content(
                resume_data, target_role, industry, analysis_results
            )
            
            return AgentResponse(
                success=True,
                message="Content optimization completed successfully",
                data=optimized_content,
                next_action="format_resume",
                confidence=0.9
            )
            
        except Exception as e:
                return AgentResponse(
                success=False,
                message="Content optimization encountered an error. Please try again.",
                confidence=0.0
            )
    
    def _optimize_resume_content(self, resume_data: Dict[str, Any], target_role: str, 
                                industry: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize all sections of the resume"""
        
        optimized = {}
        
        # Optimize professional summary
        if resume_data.get('summary') or resume_data.get('experience'):
            optimized['summary'] = self._optimize_summary(resume_data, target_role, industry)
        
        # Optimize work experience
        if resume_data.get('experience'):
            optimized['experience'] = self._optimize_experience(resume_data['experience'], target_role, industry)
        
        # Optimize skills section
        if resume_data.get('skills'):
            optimized['skills'] = self._optimize_skills(resume_data['skills'], target_role, industry)
        
        # Optimize education
        if resume_data.get('education'):
            optimized['education'] = self._optimize_education(resume_data['education'])
        
        # Add achievements section if missing
        if not resume_data.get('achievements') and resume_data.get('experience'):
            optimized['achievements'] = self._extract_achievements(resume_data['experience'])
        
        # Preserve basic information
        for field in ['name', 'email', 'phone', 'location', 'linkedin', 'website']:
            if resume_data.get(field):
                optimized[field] = resume_data[field]
        
        return optimized
    
    def _optimize_summary(self, resume_data: Dict[str, Any], target_role: str, industry: str) -> str:
        """Create an optimized professional summary"""
        
        summary_prompt = f"""
Create a compelling professional summary for a {target_role} position in the {industry} industry.

RESUME DATA:
{resume_data}

Requirements:
- 3-4 sentences maximum
- Include years of experience
- Highlight key skills and achievements
- Use industry-specific keywords
- Show value proposition
- Quantify achievements where possible
- Tailor to target role

Make it compelling and ATS-optimized while remaining human-readable.
"""
        
        return self.call_openai(summary_prompt)
    
    def _optimize_experience(self, experience: List[Dict[str, Any]], target_role: str, industry: str) -> List[Dict[str, Any]]:
        """Optimize work experience descriptions"""
        
        optimized_experience = []
        
        for exp in experience:
            if isinstance(exp, dict):
                optimized_exp = exp.copy()
                
                # Optimize job description
                if exp.get('description') or exp.get('responsibilities'):
                    optimized_exp['description'] = self._optimize_job_description(
                        exp, target_role, industry
                    )
                
                # Optimize achievements
                if exp.get('achievements'):
                    optimized_exp['achievements'] = self._optimize_achievements(
                        exp['achievements'], target_role, industry
                    )
                
                optimized_experience.append(optimized_exp)
        
        return optimized_experience
    
    def _optimize_job_description(self, experience: Dict[str, Any], target_role: str, industry: str) -> str:
        """Optimize individual job description"""
        
        desc_prompt = f"""
Transform this job experience into compelling, ATS-optimized content for a {target_role} role in {industry}:

EXPERIENCE:
{experience}

Requirements:
- Start each bullet point with a strong action verb
- Add quantifiable results and metrics
- Use industry-specific keywords
- Focus on achievements, not just responsibilities
- Show impact and results
- Keep each bullet point concise but impactful
- 3-5 bullet points maximum

Transform the description to be more compelling and results-focused.
"""
        
        return self.call_openai(desc_prompt)
    
    def _optimize_skills(self, skills: List[str], target_role: str, industry: str) -> List[str]:
        """Optimize skills section with context and categorization"""
        
        skills_prompt = f"""
Optimize and categorize these skills for a {target_role} position in the {industry} industry:

SKILLS: {skills}

Requirements:
- Categorize into Technical Skills, Soft Skills, Tools & Technologies
- Add context where helpful
- Include industry-relevant keywords
- Prioritize most important skills first
- Remove redundant or irrelevant skills
- Add missing skills that are relevant to the role

Return as categorized lists with clear headings.
"""
        
        response = self.call_openai(skills_prompt)
        # In production, parse this into structured categories
        return [response]  # Simplified for now
    
    def _optimize_education(self, education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize education section"""
        
        optimized_education = []
        
        for edu in education:
            if isinstance(edu, dict):
                optimized_edu = edu.copy()
                
                # Add relevant coursework or achievements if missing
                if not edu.get('relevant_coursework') and not edu.get('gpa'):
                    optimized_edu['note'] = "Relevant coursework and academic achievements"
                
                optimized_education.append(optimized_edu)
        
        return optimized_education
    
    def _extract_achievements(self, experience: List[Dict[str, Any]]) -> List[str]:
        """Extract and optimize key achievements from experience"""
        
        achievements_prompt = f"""
Extract and optimize the top 5-7 key achievements from this work experience:

EXPERIENCE: {experience}

Requirements:
- Focus on quantifiable results
- Use strong action verbs
- Show impact and scale
- Make them compelling and specific
- Prioritize most impressive achievements
- Format as bullet points

Return as a list of optimized achievement statements.
"""
        
        response = self.call_openai(achievements_prompt)
        # In production, parse this into a proper list
        return [response]  # Simplified for now
    
    def _optimize_achievements(self, achievements: List[str], target_role: str, industry: str) -> List[str]:
        """Optimize existing achievements"""
        
        achievements_prompt = f"""
Optimize these achievements for a {target_role} position in the {industry} industry:

ACHIEVEMENTS: {achievements}

Requirements:
- Add quantifiable metrics where possible
- Use stronger action verbs
- Show greater impact and scale
- Use industry-specific language
- Make them more compelling
- Ensure they align with target role

Return optimized achievement statements.
"""
        
        response = self.call_openai(achievements_prompt)
        # In production, parse this into a proper list
        return [response]  # Simplified for now
