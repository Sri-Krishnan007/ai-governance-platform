import logging
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Action, HistoryCase

logger = logging.getLogger("app.services.history_engine")

def get_historical_intelligence(action: Action, db: Session) -> dict:
    """Retrieve aggregate past case statistics and comments for similar intent patterns."""
    logger.info(f"Retrieving historical intelligence for Action {action.id} (Domain: {action.domain}, Action: {action.extracted_action}, Object: {action.extracted_object})")
    
    action_name = action.extracted_action.upper() if action.extracted_action else None
    object_name = action.extracted_object.lower() if action.extracted_object else None
    
    # 1. Match against pre-seeded guidelines aggregates first
    hist = None
    if action_name and object_name:
        hist = db.query(HistoryCase).filter(
            func.lower(HistoryCase.domain) == func.lower(action.domain),
            func.upper(HistoryCase.extracted_action) == action_name,
            func.lower(HistoryCase.extracted_object) == object_name
        ).first()
        
        # Fallback to match just action and object if domain specific aggregate is missing
        if not hist:
            hist = db.query(HistoryCase).filter(
                func.upper(HistoryCase.extracted_action) == action_name,
                func.lower(HistoryCase.extracted_object) == object_name
            ).first()

    # Default aggregates
    total_cases = 0
    approved_count = 0
    rejected_count = 0
    average_risk = 0.0
    
    if hist:
        total_cases = hist.total_cases
        approved_count = hist.approved_count
        rejected_count = hist.rejected_count
        average_risk = hist.average_risk
        logger.info(f"Matched seeded HistoryCase aggregate ID {hist.id}: total_cases={total_cases}")
        
    # 2. Query Similar past cases dynamically
    similar_cases_list = []
    reviewer_comments = []
    
    if action.extracted_action:
        # Find past completed cases matching same domain and action type
        past_actions = db.query(Action).filter(
            Action.domain == action.domain,
            Action.extracted_action == action.extracted_action,
            Action.id != action.id,  # Exclude current action
            Action.status.in_(["APPROVED", "REJECTED"])
        ).order_by(Action.created_at.desc()).limit(5).all()
        
        for act in past_actions:
            comments = None
            if act.governance_case:
                comments = act.governance_case.comments
                if comments:
                    reviewer_comments.append(comments)
                    
            similar_cases_list.append({
                "id": act.id,
                "natural_language_request": act.natural_language_request,
                "status": act.status,
                "risk_score": act.risk_score,
                "comments": comments
            })
            
        # If we didn't find any seeded HistoryCase aggregate, calculate it dynamically from past actions
        if not hist:
            dynamic_actions = db.query(Action).filter(
                Action.domain == action.domain,
                Action.extracted_action == action.extracted_action,
                Action.status.in_(["APPROVED", "REJECTED"])
            ).all()
            
            if dynamic_actions:
                total_cases = len(dynamic_actions)
                approved_count = sum(1 for a in dynamic_actions if a.status == "APPROVED")
                rejected_count = sum(1 for a in dynamic_actions if a.status == "REJECTED")
                average_risk = float(sum(a.risk_score for a in dynamic_actions) / total_cases)
                logger.info(f"Calculated HistoryCase dynamically: total_cases={total_cases}")

    # 3. Dynamic counts for Adaptive Learning (Phase 15)
    dynamic_approved = 0
    dynamic_rejected = 0
    if action.extracted_action:
        dynamic_approved = db.query(Action).filter(
            Action.domain == action.domain,
            Action.extracted_action == action.extracted_action,
            Action.id != action.id,
            Action.status.in_(["APPROVED", "EXECUTED"])
        ).count()
        
        dynamic_rejected = db.query(Action).filter(
            Action.domain == action.domain,
            Action.extracted_action == action.extracted_action,
            Action.id != action.id,
            Action.status == "REJECTED"
        ).count()
                
    # Calculate rates
    approval_rate = float(approved_count / total_cases) if total_cases > 0 else 1.0
    rejection_rate = float(rejected_count / total_cases) if total_cases > 0 else 0.0
    
    # Compile historical intelligence package
    history_data = {
        "total_cases": total_cases,
        "approval_rate": approval_rate,
        "rejection_rate": rejection_rate,
        "average_risk": average_risk,
        "comments": reviewer_comments,
        "similar_cases": similar_cases_list,
        "dynamic_approved": dynamic_approved,
        "dynamic_rejected": dynamic_rejected
    }
    
    logger.info(f"Historical Intelligence package compiled: approval_rate={approval_rate:.2f}, dyn_appr={dynamic_approved}, dyn_rej={dynamic_rejected}")
    return history_data
