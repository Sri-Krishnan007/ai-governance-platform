import logging
from sqlalchemy.orm import Session
from app.models import Notification, User, Role, Action, GovernanceCase

logger = logging.getLogger("app.services.notification_engine")

def dispatch_notification(db: Session, user_id: int, title: str, message: str, notification_type: str) -> Notification:
    """
    Core function to save a database notification and log simulated integrations.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"Cannot dispatch notification: User ID {user_id} not found")
        return None
        
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        read=False
    )
    db.add(notification)
    try:
        db.commit()
        db.refresh(notification)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit notification database transaction: {e}")
        return None
    
    logger.info(f"Database notification saved for user '{user.username}' (ID: {user_id}) type={notification_type}")
    
    # Simulated Integrations (Phase 19 Future Integrations Requirements)
    # Log simulated dispatches to Email, Teams, and Slack
    logger.info(f"[SIMULATED EMAIL DISPATCH] Sent to {user.email}: '{title}' - {message}")
    logger.info(f"[SIMULATED SLACK DISPATCH] Dispatched to Slack user @{user.username} channel: '{title}' - {message}")
    logger.info(f"[SIMULATED MS TEAMS DISPATCH] Dispatched to Microsoft Teams card for @{user.username}: '{title}' - {message}")
    
    return notification

def notify_employee_confirmation_required(db: Session, action: Action):
    """
    Alerts the requester employee that their action requires user confirmation.
    """
    title = "Confirmation Required: Action Pending"
    message = (
        f"Your action request in domain '{action.domain}' ('{action.natural_language_request}') "
        f"requires confirmation before execution. Calculated Risk Score: {action.risk_score}/100."
    )
    dispatch_notification(db, action.requester_id, title, message, "CONFIRMATION_REQUIRED")

def notify_employee_case_resolved(db: Session, case: GovernanceCase):
    """
    Alerts the requester employee that their case has been reviewed.
    """
    action = case.action
    title = f"Governance Case Decision: {case.status}"
    message = (
        f"Your governance case (ID: {case.id}) for action '{action.natural_language_request}' "
        f"has been resolved with decision: {case.status}. Reviewer comments: '{case.comments or 'None'}'."
    )
    # Check if there are applied conditions to append to message
    if case.conditions_applied:
        message += f" Applied conditions: {case.conditions_applied}"
        
    notification_type = "CASE_APPROVED" if case.status == "APPROVED" else "CASE_REJECTED"
    dispatch_notification(db, action.requester_id, title, message, notification_type)

def notify_reviewers_new_case(db: Session, case: GovernanceCase):
    """
    Alerts all Governance Reviewers and Administrators that a new case is pending review.
    Handles escalation alerts if the risk score is very high (>80) or if a critical policy was matched.
    """
    action = case.action
    
    # Query all users who are Reviewers or Admins
    reviewers = db.query(User).join(Role).filter(Role.name.in_(["Governance Reviewer", "Administrator"])).all()
    
    # Check if this case should be escalated
    is_escalated = (action.risk_score or 0) > 80
    
    # Also escalate if a CRITICAL policy matched
    # Let's inspect matched policies dynamically by evaluating (already saved on case evaluation)
    # Since we evaluate policies, let's look at risk score boost or policy severity in DB
    # If risk_score > 80 or autonomy level is human review and risk breakdown policy factor is critical, escalate
    if action.risk_breakdown and action.risk_breakdown.policy_factor >= 0.5: # Boost was >= 50 (CRITICAL)
        is_escalated = True
        
    for rev in reviewers:
        if is_escalated:
            title = f"ESCALATED Case: Case ID {case.id}"
            message = (
                f"URGENT: High risk case ID {case.id} in domain '{action.domain}' has been escalated! "
                f"Calculated Risk Score: {action.risk_score}/100. Request: '{action.natural_language_request}'"
            )
            dispatch_notification(db, rev.id, title, message, "ESCALATED_CASE")
        else:
            title = f"New Governance Case: Case ID {case.id}"
            message = (
                f"A new pending governance case (ID: {case.id}) in domain '{action.domain}' requires review. "
                f"Calculated Risk: {action.risk_score}/100. Request: '{action.natural_language_request}'"
            )
            dispatch_notification(db, rev.id, title, message, "NEW_CASE")

def notify_admins_policy_violation(db: Session, action: Action, policy_results: dict):
    """
    Alerts all Administrators of policy violations and security alerts.
    """
    admins = db.query(User).join(Role).filter(Role.name == "Administrator").all()
    matched_policies = policy_results.get("matched_policies", [])
    violations = policy_results.get("violations", [])
    severity = policy_results.get("severity", "LOW")
    
    for admin in admins:
        # Notify about general policy violations
        for idx, policy_name in enumerate(matched_policies):
            desc = violations[idx] if idx < len(violations) else ""
            title = f"Policy Violation: {policy_name}"
            message = (
                f"Action ID {action.id} requested by User {action.requester_id} triggered policy violation: "
                f"'{policy_name}' - {desc}."
            )
            dispatch_notification(db, admin.id, title, message, "POLICY_VIOLATIONS")
            
        # Notify security alert if severity is HIGH or CRITICAL
        if severity in ["HIGH", "CRITICAL"]:
            title = f"Security Alert: {severity} Violation Detected"
            message = (
                f"Security violation detected in Action ID {action.id}! "
                f"Calculated Risk: {action.risk_score or 0}/100. Highest Severity Matched: {severity}."
            )
            dispatch_notification(db, admin.id, title, message, "SECURITY_ALERTS")
