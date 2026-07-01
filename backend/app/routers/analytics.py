from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.database import get_db
from app.models import Action, GovernanceCase, User, Notification, AuditLog
from app.auth import get_current_user

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

@router.get("", response_model=Dict[str, Any])
def get_governance_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes KPIs and chart datasets for the Governance Analytics Dashboard.
    """
    try:
        # 1. Gather all actions and cases
        total_actions = db.query(Action).count()
        
        # Calculate Average Risk
        avg_risk_row = db.query(func.avg(Action.risk_score)).first()
        avg_risk = round(float(avg_risk_row[0]), 1) if avg_risk_row and avg_risk_row[0] is not None else 0.0
        
        # Calculate Review Time (avg hours to resolve case)
        resolved_cases = db.query(GovernanceCase).filter(GovernanceCase.status.in_(["APPROVED", "REJECTED", "MODIFIED"])).all()
        avg_review_hours = 0.0
        if resolved_cases:
            total_seconds = 0.0
            valid_cases = 0
            for case in resolved_cases:
                if case.updated_at and case.created_at:
                    total_seconds += (case.updated_at - case.created_at).total_seconds()
                    valid_cases += 1
            if valid_cases > 0:
                avg_review_hours = round((total_seconds / valid_cases) / 3600.0, 1)

        # Autonomy Rates
        auto_approved = db.query(Action).filter(Action.autonomy_level == "AUTOMATIC").count()
        escalated = db.query(Action).filter(Action.autonomy_level == "HUMAN_REVIEW").count()
        
        auto_approval_rate = round((auto_approved / total_actions) * 100, 1) if total_actions > 0 else 0.0
        escalation_rate = round((escalated / total_actions) * 100, 1) if total_actions > 0 else 0.0

        # KPIs dict
        kpis = {
            "total_requests": total_actions,
            "average_risk": avg_risk,
            "review_time_hours": avg_review_hours,
            "auto_approval_rate": auto_approval_rate,
            "escalation_rate": escalation_rate
        }

        # 2. Risk Distribution
        low_risk = db.query(Action).filter(Action.risk_score >= 0, Action.risk_score <= 30).count()
        med_risk = db.query(Action).filter(Action.risk_score >= 31, Action.risk_score <= 60).count()
        high_risk = db.query(Action).filter(Action.risk_score >= 61, Action.risk_score <= 80).count()
        crit_risk = db.query(Action).filter(Action.risk_score >= 81, Action.risk_score <= 100).count()
        
        risk_distribution = {
            "Low (0-30)": low_risk,
            "Medium (31-60)": med_risk,
            "High (61-80)": high_risk,
            "Critical (81-100)": crit_risk
        }

        # 3. Policy Violations
        # Parse policy names from admin notifications
        policy_notes = db.query(Notification).filter(Notification.notification_type == "POLICY_VIOLATIONS").all()
        policy_violations = {}
        for note in policy_notes:
            # title is f"Policy Violation: {policy_name}"
            policy_name = note.title.replace("Policy Violation: ", "").strip()
            policy_violations[policy_name] = policy_violations.get(policy_name, 0) + 1

        # 4. Process all actions for daily series, monthly stats, and confidence
        today = datetime.utcnow().date()
        date_series = [today - timedelta(days=i) for i in range(6, -1, -1)]
        
        all_actions = db.query(Action).all()
        
        # Pre-populate map for last 7 days daily series
        daily_data = {d.strftime("%Y-%m-%d"): {"approved": 0, "rejected": 0, "confidences": []} for d in date_series}
        
        # Pre-populate map for monthly statistics
        monthly_map = {}
        
        for act in all_actions:
            if act.created_at:
                # Group by month
                month_key = act.created_at.strftime("%Y-%m")
                if month_key not in monthly_map:
                    monthly_map[month_key] = {"total": 0, "approved": 0, "rejected": 0}
                monthly_map[month_key]["total"] += 1
                if act.status == "APPROVED":
                    monthly_map[month_key]["approved"] += 1
                elif act.status in ["REJECTED", "MODIFIED"]:
                    monthly_map[month_key]["rejected"] += 1
                
                # Group by day for last 7 days
                date_key = act.created_at.strftime("%Y-%m-%d")
                if date_key in daily_data:
                    if act.status == "APPROVED":
                        daily_data[date_key]["approved"] += 1
                    elif act.status in ["REJECTED", "MODIFIED"]:
                        daily_data[date_key]["rejected"] += 1
                    if act.confidence is not None:
                        daily_data[date_key]["confidences"].append(float(act.confidence))

        # Build Approval Trends & LLM Confidence Trend
        approval_trends = []
        llm_confidence_trend = []
        for d in date_series:
            date_str_key = d.strftime("%Y-%m-%d")
            date_display = d.strftime("%b %d")
            
            day_info = daily_data[date_str_key]
            approval_trends.append({
                "date": date_display,
                "approved": day_info["approved"],
                "rejected": day_info["rejected"]
            })
            
            confs = day_info["confidences"]
            avg_conf = round(sum(confs) / len(confs), 2) if confs else 1.0
            llm_confidence_trend.append({
                "date": date_display,
                "confidence": avg_conf
            })

        # 5. Department-wise Risk (Domain-wise)
        domains = ["Finance", "Healthcare", "HR", "Legal", "Manufacturing"]
        department_risk = []
        for dom in domains:
            avg_dom_risk_row = db.query(func.avg(Action.risk_score)).filter(Action.domain == dom).first()
            avg_dom_risk = round(float(avg_dom_risk_row[0]), 1) if avg_dom_risk_row and avg_dom_risk_row[0] is not None else 0.0
            department_risk.append({
                "department": dom,
                "average_risk": avg_dom_risk
            })

        # 6. Build Monthly Statistics List
        monthly_statistics = []
        for month_key in sorted(monthly_map.keys()):
            try:
                dt = datetime.strptime(month_key, "%Y-%m")
                month_name = dt.strftime("%b %Y")
            except Exception:
                month_name = month_key
                
            monthly_statistics.append({
                "month": month_name,
                "total": monthly_map[month_key]["total"],
                "approved": monthly_map[month_key]["approved"],
                "rejected": monthly_map[month_key]["rejected"]
            })
            
        if not monthly_statistics:
            monthly_statistics.append({
                "month": today.strftime("%b %Y"),
                "total": 0,
                "approved": 0,
                "rejected": 0
            })

        # 7. Reviewer Performance
        reviewer_perf_rows = db.query(
            User.username,
            func.count(GovernanceCase.id).label('resolved_count')
        ).join(GovernanceCase, GovernanceCase.reviewer_id == User.id)\
         .filter(GovernanceCase.status.in_(["APPROVED", "REJECTED", "MODIFIED"]))\
         .group_by(User.username).order_by('resolved_count').all()
         
        reviewer_performance = []
        for row in reviewer_perf_rows:
            reviewer_performance.append({
                "reviewer": row.username,
                "resolved_cases": row.resolved_count
            })

        return {
            "kpis": kpis,
            "risk_distribution": risk_distribution,
            "policy_violations": policy_violations,
            "approval_trends": approval_trends,
            "department_risk": department_risk,
            "monthly_statistics": monthly_statistics,
            "reviewer_performance": reviewer_performance,
            "llm_confidence_trend": llm_confidence_trend
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing governance analytics: {str(e)}"
        )
