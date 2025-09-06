"""
Analytics Service - Call metrics, success tracking, and reporting
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from ..models.database_models import get_db, User, Call, ResumeData, EmploymentGap, CallQueue

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for tracking call metrics and generating reports"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.cache_duration = timedelta(minutes=15)
    
    def get_call_metrics(self, start_date: Optional[date] = None, 
                        end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get comprehensive call metrics"""
        try:
            db = next(get_db())
            
            # Default to last 30 days if no dates provided
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Basic call statistics
            total_calls = db.query(Call).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1)
            ).count()
            
            completed_calls = db.query(Call).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1),
                Call.status == "completed"
            ).count()
            
            failed_calls = db.query(Call).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1),
                Call.status.in_(["failed", "no-answer", "busy"])
            ).count()
            
            # Success rates
            success_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0
            
            # Average call duration
            avg_duration = db.query(func.avg(Call.duration)).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1),
                Call.status == "completed",
                Call.duration.isnot(None)
            ).scalar() or 0
            
            # Completion scores
            avg_completion_score = db.query(func.avg(Call.completion_score)).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1),
                Call.completion_score.isnot(None)
            ).scalar() or 0
            
            # Adversarial behavior metrics
            high_adversarial_calls = db.query(Call).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1),
                Call.adversarial_score >= 5
            ).count()
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "call_volume": {
                    "total_calls": total_calls,
                    "completed_calls": completed_calls,
                    "failed_calls": failed_calls,
                    "success_rate": round(success_rate, 2)
                },
                "call_quality": {
                    "average_duration_seconds": round(avg_duration, 1),
                    "average_completion_score": round(avg_completion_score, 3),
                    "high_adversarial_calls": high_adversarial_calls,
                    "adversarial_rate": round((high_adversarial_calls / total_calls * 100), 2) if total_calls > 0 else 0
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating call metrics: {e}")
            return {"error": str(e)}
    
    def get_queue_performance(self) -> Dict[str, Any]:
        """Get call queue performance metrics"""
        try:
            db = next(get_db())
            
            # Queue statistics
            pending_calls = db.query(CallQueue).filter(CallQueue.status == "pending").count()
            processing_calls = db.query(CallQueue).filter(CallQueue.status == "processing").count()
            completed_calls = db.query(CallQueue).filter(CallQueue.status == "completed").count()
            failed_calls = db.query(CallQueue).filter(CallQueue.status == "failed").count()
            
            total_queued = pending_calls + processing_calls + completed_calls + failed_calls
            
            # Average processing time for completed calls
            avg_processing_time = db.query(
                func.avg(
                    func.extract('epoch', CallQueue.processed_at - CallQueue.created_at)
                )
            ).filter(
                CallQueue.status == "completed",
                CallQueue.processed_at.isnot(None)
            ).scalar() or 0
            
            # Retry statistics
            high_retry_calls = db.query(CallQueue).filter(CallQueue.attempts >= 2).count()
            
            return {
                "queue_status": {
                    "pending": pending_calls,
                    "processing": processing_calls,
                    "completed": completed_calls,
                    "failed": failed_calls,
                    "total": total_queued
                },
                "performance": {
                    "average_processing_time_seconds": round(avg_processing_time, 1),
                    "completion_rate": round((completed_calls / total_queued * 100), 2) if total_queued > 0 else 0,
                    "high_retry_calls": high_retry_calls,
                    "retry_rate": round((high_retry_calls / total_queued * 100), 2) if total_queued > 0 else 0
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating queue performance: {e}")
            return {"error": str(e)}
    
    def get_resume_completion_stats(self, start_date: Optional[date] = None, 
                                   end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get resume completion statistics"""
        try:
            db = next(get_db())
            
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Resume data collection stats
            total_resume_entries = db.query(ResumeData).filter(
                ResumeData.created_at >= start_date,
                ResumeData.created_at <= end_date + timedelta(days=1)
            ).count()
            
            # Group by field type
            field_stats = db.query(
                ResumeData.field_name,
                func.count(ResumeData.id).label('count'),
                func.avg(ResumeData.confidence_score).label('avg_confidence')
            ).filter(
                ResumeData.created_at >= start_date,
                ResumeData.created_at <= end_date + timedelta(days=1)
            ).group_by(ResumeData.field_name).all()
            
            # Employment gap statistics
            total_gaps = db.query(EmploymentGap).filter(
                EmploymentGap.created_at >= start_date,
                EmploymentGap.created_at <= end_date + timedelta(days=1)
            ).count()
            
            resolved_gaps = db.query(EmploymentGap).filter(
                EmploymentGap.created_at >= start_date,
                EmploymentGap.created_at <= end_date + timedelta(days=1),
                EmploymentGap.resolved == True
            ).count()
            
            # Users with complete timelines
            users_with_data = db.query(func.count(func.distinct(ResumeData.user_id))).filter(
                ResumeData.created_at >= start_date,
                ResumeData.created_at <= end_date + timedelta(days=1)
            ).scalar() or 0
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "resume_data": {
                    "total_entries": total_resume_entries,
                    "users_with_data": users_with_data,
                    "field_breakdown": [
                        {
                            "field_name": field_name,
                            "count": count,
                            "average_confidence": round(avg_confidence, 3)
                        }
                        for field_name, count, avg_confidence in field_stats
                    ]
                },
                "employment_gaps": {
                    "total_gaps": total_gaps,
                    "resolved_gaps": resolved_gaps,
                    "resolution_rate": round((resolved_gaps / total_gaps * 100), 2) if total_gaps > 0 else 0
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating resume completion stats: {e}")
            return {"error": str(e)}
    
    def get_adversarial_behavior_analysis(self, start_date: Optional[date] = None, 
                                        end_date: Optional[date] = None) -> Dict[str, Any]:
        """Analyze adversarial behavior patterns"""
        try:
            db = next(get_db())
            
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Adversarial score distribution
            score_distribution = db.query(
                Call.adversarial_score,
                func.count(Call.id).label('count')
            ).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1),
                Call.adversarial_score.isnot(None)
            ).group_by(Call.adversarial_score).all()
            
            # High adversarial calls analysis
            high_adversarial_calls = db.query(Call).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1),
                Call.adversarial_score >= 5
            ).all()
            
            # Correlation with completion scores
            adversarial_completion_correlation = db.query(
                func.avg(Call.completion_score).label('avg_completion'),
                func.count(Call.id).label('count')
            ).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1),
                Call.adversarial_score >= 5,
                Call.completion_score.isnot(None)
            ).first()
            
            normal_completion_correlation = db.query(
                func.avg(Call.completion_score).label('avg_completion'),
                func.count(Call.id).label('count')
            ).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1),
                Call.adversarial_score < 5,
                Call.completion_score.isnot(None)
            ).first()
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "score_distribution": [
                    {"score": score, "count": count}
                    for score, count in score_distribution
                ],
                "high_adversarial_analysis": {
                    "total_high_adversarial": len(high_adversarial_calls),
                    "average_completion_score": round(adversarial_completion_correlation.avg_completion or 0, 3),
                    "call_count": adversarial_completion_correlation.count
                },
                "comparison": {
                    "normal_calls_avg_completion": round(normal_completion_correlation.avg_completion or 0, 3),
                    "normal_calls_count": normal_completion_correlation.count,
                    "completion_score_impact": round(
                        (normal_completion_correlation.avg_completion or 0) - 
                        (adversarial_completion_correlation.avg_completion or 0), 3
                    )
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating adversarial behavior analysis: {e}")
            return {"error": str(e)}
    
    def get_daily_call_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get daily call trends over specified period"""
        try:
            db = next(get_db())
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Daily call counts
            daily_stats = db.query(
                func.date(Call.created_at).label('call_date'),
                func.count(Call.id).label('total_calls'),
                func.sum(func.case([(Call.status == 'completed', 1)], else_=0)).label('completed_calls'),
                func.avg(Call.duration).label('avg_duration'),
                func.avg(Call.completion_score).label('avg_completion_score')
            ).filter(
                Call.created_at >= start_date,
                Call.created_at <= end_date + timedelta(days=1)
            ).group_by(func.date(Call.created_at)).order_by(func.date(Call.created_at)).all()
            
            # Calculate trends
            trends = []
            for stat in daily_stats:
                success_rate = (stat.completed_calls / stat.total_calls * 100) if stat.total_calls > 0 else 0
                trends.append({
                    "date": stat.call_date.isoformat(),
                    "total_calls": stat.total_calls,
                    "completed_calls": stat.completed_calls,
                    "success_rate": round(success_rate, 2),
                    "average_duration": round(stat.avg_duration or 0, 1),
                    "average_completion_score": round(stat.avg_completion_score or 0, 3)
                })
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "daily_trends": trends,
                "summary": {
                    "total_days_with_calls": len(trends),
                    "peak_day": max(trends, key=lambda x: x["total_calls"]) if trends else None,
                    "best_success_rate_day": max(trends, key=lambda x: x["success_rate"]) if trends else None
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating daily call trends: {e}")
            return {"error": str(e)}
    
    def get_user_engagement_metrics(self) -> Dict[str, Any]:
        """Get user engagement and retention metrics"""
        try:
            db = next(get_db())
            
            # Total users
            total_users = db.query(User).count()
            
            # Users with calls
            users_with_calls = db.query(func.count(func.distinct(Call.user_id))).scalar() or 0
            
            # Users with completed calls
            users_with_completed_calls = db.query(
                func.count(func.distinct(Call.user_id))
            ).filter(Call.status == "completed").scalar() or 0
            
            # Users with resume data
            users_with_resume_data = db.query(
                func.count(func.distinct(ResumeData.user_id))
            ).scalar() or 0
            
            # Repeat users (multiple calls)
            repeat_users = db.query(Call.user_id).group_by(Call.user_id).having(
                func.count(Call.id) > 1
            ).count()
            
            return {
                "user_base": {
                    "total_users": total_users,
                    "users_with_calls": users_with_calls,
                    "users_with_completed_calls": users_with_completed_calls,
                    "users_with_resume_data": users_with_resume_data
                },
                "engagement_rates": {
                    "call_participation_rate": round((users_with_calls / total_users * 100), 2) if total_users > 0 else 0,
                    "call_completion_rate": round((users_with_completed_calls / users_with_calls * 100), 2) if users_with_calls > 0 else 0,
                    "data_collection_rate": round((users_with_resume_data / users_with_completed_calls * 100), 2) if users_with_completed_calls > 0 else 0,
                    "repeat_user_rate": round((repeat_users / total_users * 100), 2) if total_users > 0 else 0
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating user engagement metrics: {e}")
            return {"error": str(e)}
    
    def generate_comprehensive_report(self, start_date: Optional[date] = None, 
                                    end_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            report = {
                "report_info": {
                    "generated_at": datetime.now().isoformat(),
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "report_type": "comprehensive_analytics"
                },
                "call_metrics": self.get_call_metrics(start_date, end_date),
                "queue_performance": self.get_queue_performance(),
                "resume_completion": self.get_resume_completion_stats(start_date, end_date),
                "adversarial_analysis": self.get_adversarial_behavior_analysis(start_date, end_date),
                "user_engagement": self.get_user_engagement_metrics(),
                "daily_trends": self.get_daily_call_trends(30)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {"error": str(e)}
    
    def get_system_health_metrics(self) -> Dict[str, Any]:
        """Get system health and performance metrics"""
        try:
            db = next(get_db())
            
            # Recent system activity
            recent_calls = db.query(Call).filter(
                Call.created_at >= datetime.now() - timedelta(hours=24)
            ).count()
            
            recent_queue_items = db.query(CallQueue).filter(
                CallQueue.created_at >= datetime.now() - timedelta(hours=24)
            ).count()
            
            # System status indicators
            stuck_processing = db.query(CallQueue).filter(
                CallQueue.status == "processing",
                CallQueue.processed_at < datetime.now() - timedelta(hours=2)
            ).count()
            
            return {
                "system_activity": {
                    "calls_last_24h": recent_calls,
                    "queue_items_last_24h": recent_queue_items,
                    "stuck_processing_calls": stuck_processing
                },
                "health_indicators": {
                    "system_responsive": stuck_processing == 0,
                    "recent_activity": recent_calls > 0 or recent_queue_items > 0,
                    "queue_healthy": stuck_processing < 5
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating system health metrics: {e}")
            return {"error": str(e)}
