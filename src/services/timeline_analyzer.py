"""
Timeline Analyzer - Advanced employment gap detection and analysis
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmploymentPeriod:
    start_year: int
    end_year: Optional[int]
    company: Optional[str]
    job_title: Optional[str]
    industry: Optional[str]
    confidence: float
    source: str  # "extracted", "inferred", "user_confirmed"

@dataclass
class EmploymentGap:
    start_year: int
    end_year: int
    gap_size: int
    severity: str  # "minor", "moderate", "major", "critical"
    suggested_industries: List[str]
    follow_up_questions: List[str]
    resolved: bool = False
    resolution_notes: Optional[str] = None

class TimelineAnalyzer:
    """Advanced analyzer for employment timelines and gap detection"""
    
    def __init__(self):
        self.industry_categories = {
            "blue_collar": [
                "construction", "manufacturing", "warehouse", "assembly",
                "maintenance", "landscaping", "cleaning", "security"
            ],
            "service": [
                "retail", "food service", "hospitality", "customer service",
                "sales", "restaurant", "fast food"
            ],
            "healthcare": [
                "healthcare", "nursing", "medical", "hospital", "clinic"
            ],
            "transportation": [
                "transportation", "trucking", "delivery", "driving", "logistics"
            ],
            "office": [
                "office", "administrative", "clerical", "data entry", "reception"
            ]
        }
        
        self.common_gap_reasons = {
            "family": ["raising children", "family care", "maternity", "paternity"],
            "education": ["school", "college", "training", "certification"],
            "health": ["illness", "injury", "recovery", "disability"],
            "economic": ["layoff", "plant closure", "recession", "downsizing"],
            "personal": ["travel", "relocation", "personal reasons"]
        }
    
    def analyze_timeline(self, conversation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conversation data to build employment timeline"""
        try:
            # Extract employment periods
            periods = self._extract_employment_periods(conversation_data)
            
            # Detect gaps
            gaps = self._detect_gaps(periods)
            
            # Analyze gap severity and generate suggestions
            analyzed_gaps = [self._analyze_gap(gap, periods) for gap in gaps]
            
            # Generate overall timeline assessment
            assessment = self._assess_timeline_completeness(periods, analyzed_gaps)
            
            return {
                "employment_periods": [self._period_to_dict(p) for p in periods],
                "gaps": [self._gap_to_dict(g) for g in analyzed_gaps],
                "assessment": assessment,
                "recommendations": self._generate_recommendations(periods, analyzed_gaps)
            }
            
        except Exception as e:
            logger.error(f"Timeline analysis error: {e}")
            return {"error": str(e)}
    
    def _extract_employment_periods(self, conversation_data: List[Dict[str, Any]]) -> List[EmploymentPeriod]:
        """Extract employment periods from conversation data"""
        periods = []
        
        for entry in conversation_data:
            info = entry.get('info', {})
            
            # Extract years
            years = info.get('years_mentioned', [])
            if len(years) >= 1:
                start_year = min(years)
                end_year = max(years) if len(years) > 1 else None
                
                period = EmploymentPeriod(
                    start_year=start_year,
                    end_year=end_year,
                    company=info.get('company'),
                    job_title=info.get('job_title'),
                    industry=info.get('industry'),
                    confidence=self._calculate_confidence(info),
                    source="extracted"
                )
                periods.append(period)
        
        # Sort by start year
        periods.sort(key=lambda p: p.start_year)
        
        # Merge overlapping or adjacent periods
        return self._merge_periods(periods)
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted information"""
        score = 0.0
        
        if info.get('years_mentioned'):
            score += 0.4
        if info.get('company'):
            score += 0.3
        if info.get('job_title'):
            score += 0.2
        if info.get('industry'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _merge_periods(self, periods: List[EmploymentPeriod]) -> List[EmploymentPeriod]:
        """Merge overlapping or adjacent employment periods"""
        if not periods:
            return []
        
        merged = [periods[0]]
        
        for current in periods[1:]:
            last = merged[-1]
            
            # Check if periods should be merged
            if (last.end_year and current.start_year <= last.end_year + 1) or \
               (last.company and current.company and last.company == current.company):
                # Merge periods
                last.end_year = max(last.end_year or current.start_year, 
                                  current.end_year or current.start_year)
                last.confidence = max(last.confidence, current.confidence)
                
                # Update other fields if missing
                if not last.job_title and current.job_title:
                    last.job_title = current.job_title
                if not last.industry and current.industry:
                    last.industry = current.industry
            else:
                merged.append(current)
        
        return merged
    
    def _detect_gaps(self, periods: List[EmploymentPeriod]) -> List[EmploymentGap]:
        """Detect gaps in employment timeline"""
        gaps = []
        
        if len(periods) < 2:
            return gaps
        
        for i in range(len(periods) - 1):
            current_period = periods[i]
            next_period = periods[i + 1]
            
            # Determine end of current period
            current_end = current_period.end_year or current_period.start_year
            
            # Check for gap
            if next_period.start_year > current_end + 1:
                gap_size = next_period.start_year - current_end - 1
                
                gap = EmploymentGap(
                    start_year=current_end + 1,
                    end_year=next_period.start_year - 1,
                    gap_size=gap_size,
                    severity=self._determine_gap_severity(gap_size),
                    suggested_industries=[],
                    follow_up_questions=[]
                )
                gaps.append(gap)
        
        return gaps
    
    def _determine_gap_severity(self, gap_size: int) -> str:
        """Determine severity of employment gap"""
        if gap_size <= 1:
            return "minor"
        elif gap_size <= 3:
            return "moderate"
        elif gap_size <= 10:
            return "major"
        else:
            return "critical"
    
    def _analyze_gap(self, gap: EmploymentGap, periods: List[EmploymentPeriod]) -> EmploymentGap:
        """Analyze a gap and generate suggestions"""
        # Generate industry suggestions based on surrounding employment
        gap.suggested_industries = self._suggest_industries_for_gap(gap, periods)
        
        # Generate follow-up questions
        gap.follow_up_questions = self._generate_gap_questions(gap)
        
        return gap
    
    def _suggest_industries_for_gap(self, gap: EmploymentGap, periods: List[EmploymentPeriod]) -> List[str]:
        """Suggest likely industries for a gap period"""
        suggestions = []
        
        # Find periods before and after the gap
        before_period = None
        after_period = None
        
        for period in periods:
            if period.end_year and period.end_year < gap.start_year:
                before_period = period
            elif period.start_year > gap.end_year and not after_period:
                after_period = period
                break
        
        # Base suggestions on gap characteristics
        if gap.gap_size <= 2:
            # Short gaps - likely same industry or related
            if before_period and before_period.industry:
                suggestions.append(before_period.industry)
            if after_period and after_period.industry:
                suggestions.append(after_period.industry)
        
        # Add common industries based on gap size and era
        if gap.start_year < 1990:
            # Older gaps - more traditional industries
            suggestions.extend(["manufacturing", "construction", "retail"])
        else:
            # More recent gaps - broader range
            suggestions.extend(["retail", "food service", "healthcare", "warehouse"])
        
        # Remove duplicates and limit
        return list(dict.fromkeys(suggestions))[:6]
    
    def _generate_gap_questions(self, gap: EmploymentGap) -> List[str]:
        """Generate targeted questions for a gap"""
        questions = []
        
        if gap.severity == "critical":
            # Large gaps need breaking down
            mid_year = gap.start_year + (gap.gap_size // 2)
            questions.append(f"That's a long period from {gap.start_year} to {gap.end_year}. Let's break it down - what were you doing around {mid_year}?")
            questions.append(f"Were you perhaps working in construction, manufacturing, or retail during the {gap.start_year}s?")
        elif gap.severity == "major":
            # Medium gaps - direct but gentle
            questions.append(f"What about between {gap.start_year} and {gap.end_year}? Were you working anywhere during that time?")
            questions.append(f"Did you have any jobs, even part-time or temporary, between {gap.start_year} and {gap.end_year}?")
        else:
            # Smaller gaps - more direct
            questions.append(f"What were you doing between {gap.start_year} and {gap.end_year}?")
        
        # Add industry-specific questions
        if gap.suggested_industries:
            industries = ", ".join(gap.suggested_industries[:3])
            questions.append(f"Were you perhaps working in {industries} during that time?")
        
        return questions
    
    def _assess_timeline_completeness(self, periods: List[EmploymentPeriod], gaps: List[EmploymentGap]) -> Dict[str, Any]:
        """Assess overall timeline completeness"""
        total_years = 0
        covered_years = 0
        
        if periods:
            earliest = min(p.start_year for p in periods)
            latest = max(p.end_year or p.start_year for p in periods)
            total_years = latest - earliest + 1
            
            # Calculate covered years
            for period in periods:
                period_years = (period.end_year or period.start_year) - period.start_year + 1
                covered_years += period_years
        
        # Calculate gap statistics
        total_gap_years = sum(g.gap_size for g in gaps)
        critical_gaps = len([g for g in gaps if g.severity == "critical"])
        major_gaps = len([g for g in gaps if g.severity == "major"])
        
        # Overall completeness score
        completeness = covered_years / total_years if total_years > 0 else 0
        
        return {
            "total_timeline_years": total_years,
            "covered_years": covered_years,
            "gap_years": total_gap_years,
            "completeness_score": completeness,
            "total_gaps": len(gaps),
            "critical_gaps": critical_gaps,
            "major_gaps": major_gaps,
            "needs_attention": critical_gaps > 0 or major_gaps > 2
        }
    
    def _generate_recommendations(self, periods: List[EmploymentPeriod], gaps: List[EmploymentGap]) -> List[str]:
        """Generate recommendations for improving timeline"""
        recommendations = []
        
        # Gap-based recommendations
        critical_gaps = [g for g in gaps if g.severity == "critical"]
        if critical_gaps:
            recommendations.append("Focus on resolving large employment gaps by breaking them into smaller periods")
        
        major_gaps = [g for g in gaps if g.severity == "major"]
        if len(major_gaps) > 2:
            recommendations.append("Multiple significant gaps detected - prioritize the most recent ones")
        
        # Period-based recommendations
        low_confidence_periods = [p for p in periods if p.confidence < 0.5]
        if low_confidence_periods:
            recommendations.append("Gather more details for employment periods with limited information")
        
        # Timeline span recommendations
        if periods:
            span = max(p.end_year or p.start_year for p in periods) - min(p.start_year for p in periods)
            if span > 30:
                recommendations.append("Long employment history - focus on most recent 20-25 years")
        
        return recommendations
    
    def _period_to_dict(self, period: EmploymentPeriod) -> Dict[str, Any]:
        """Convert EmploymentPeriod to dictionary"""
        return {
            "start_year": period.start_year,
            "end_year": period.end_year,
            "company": period.company,
            "job_title": period.job_title,
            "industry": period.industry,
            "confidence": period.confidence,
            "source": period.source
        }
    
    def _gap_to_dict(self, gap: EmploymentGap) -> Dict[str, Any]:
        """Convert EmploymentGap to dictionary"""
        return {
            "start_year": gap.start_year,
            "end_year": gap.end_year,
            "gap_size": gap.gap_size,
            "severity": gap.severity,
            "suggested_industries": gap.suggested_industries,
            "follow_up_questions": gap.follow_up_questions,
            "resolved": gap.resolved,
            "resolution_notes": gap.resolution_notes
        }
    
    def identify_priority_gaps(self, gaps: List[EmploymentGap]) -> List[EmploymentGap]:
        """Identify which gaps should be prioritized for resolution"""
        # Sort by severity and size
        priority_order = {"critical": 4, "major": 3, "moderate": 2, "minor": 1}
        
        return sorted(gaps, 
                     key=lambda g: (priority_order.get(g.severity, 0), g.gap_size), 
                     reverse=True)
    
    def suggest_conversation_strategy(self, timeline_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest conversation strategy based on timeline analysis"""
        gaps = timeline_analysis.get("gaps", [])
        assessment = timeline_analysis.get("assessment", {})
        
        strategy = {
            "approach": "standard",
            "focus_areas": [],
            "conversation_tips": [],
            "expected_difficulty": "normal"
        }
        
        # Determine approach based on gaps
        critical_gaps = [g for g in gaps if g.get("severity") == "critical"]
        if critical_gaps:
            strategy["approach"] = "gap_focused"
            strategy["focus_areas"].append("large_employment_gaps")
            strategy["conversation_tips"].append("Break large gaps into smaller periods")
            strategy["expected_difficulty"] = "high"
        
        # Add specific tips
        if assessment.get("completeness_score", 0) < 0.5:
            strategy["conversation_tips"].append("Timeline is incomplete - gather basic employment history first")
        
        if len(gaps) > 5:
            strategy["conversation_tips"].append("Many gaps detected - focus on the largest ones first")
            strategy["expected_difficulty"] = "high"
        
        return strategy
