import logging
from sqlalchemy.orm import Session
from app.models import Action, GovernanceCase

logger = logging.getLogger("app.services.decision_engine")

def determine_autonomy_level(risk_score: int) -> str:
    """Determine recommended action execution autonomy level based on calculated risk score."""
    if risk_score is None:
        return "HUMAN_REVIEW"
        
    if 0 <= risk_score <= 30:
        return "AUTOMATIC"
    elif 31 <= risk_score <= 60:
        return "USER_CONFIRMATION"
    elif 61 <= risk_score <= 100:
        return "HUMAN_REVIEW"
        
    return "HUMAN_REVIEW"

def process_autonomy_decision(action: Action, db: Session) -> str:
    """Evaluate recommended autonomy level and register Governance Cases for actions flagged for manual review."""
    logger.info(f"Processing autonomy decision rules for Action {action.id} (Risk Score: {action.risk_score})")
    
    autonomy_level = determine_autonomy_level(action.risk_score)
    action.autonomy_level = autonomy_level
    
    # If recommended action is HUMAN_REVIEW, register a governance case
    if autonomy_level == "HUMAN_REVIEW":
        existing_case = db.query(GovernanceCase).filter(GovernanceCase.action_id == action.id).first()
        if not existing_case:
            logger.warning(f"High risk action {action.id} flagged for human review. Registering new Governance Case...")
            gov_case = GovernanceCase(
                action_id=action.id,
                status="PENDING",
                comments=None,
                conditions_applied=None
            )
            db.add(gov_case)
            db.flush()
            logger.info(f"Governance Case registered successfully for Action {action.id}")
            
    return autonomy_level
