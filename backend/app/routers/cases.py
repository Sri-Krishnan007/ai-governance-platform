import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import GovernanceCase, Action, User, AuditLog
from app.schemas import GovernanceCaseResponse, GovernanceCaseDetailResponse, GovernanceCaseReview, GovernanceExplanationResponse
from app.auth import get_current_user
from app.services.explainability import generate_case_explanation

logger = logging.getLogger("app.routers.cases")

router = APIRouter(
    prefix="/cases",
    tags=["Governance Cases"]
)

class CaseDecisionRequest(BaseModel):
    comments: Optional[str] = None
    conditions_applied: Optional[str] = None

@router.get("", response_model=List[GovernanceCaseResponse])
def get_cases(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all governance cases. Employees only see their own submitted cases."""
    logger.info(f"User '{current_user.username}' (Role: {current_user.role.name}) requesting governance cases")
    
    query = db.query(GovernanceCase).join(Action)
    
    # If user is Employee, restrict to cases they requested
    if current_user.role.name == "Employee":
        query = query.filter(Action.requester_id == current_user.id)
        
    # Optional status filter
    if status_filter:
        query = query.filter(GovernanceCase.status == status_filter.upper())
        
    cases = query.all()
    return cases

@router.get("/{case_id}", response_model=GovernanceCaseDetailResponse)
def get_case_by_id(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full details of a specific governance case by ID."""
    logger.info(f"User '{current_user.username}' fetching governance case ID {case_id}")
    
    case = db.query(GovernanceCase).filter(GovernanceCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Governance case not found")
        
    # Permission check: Employees can only view their own cases
    if current_user.role.name == "Employee" and case.action.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    return case

@router.post("/{case_id}/review", response_model=GovernanceCaseResponse)
def review_case(
    case_id: int,
    review_in: GovernanceCaseReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a reviewer decision (APPROVE/REJECT/MODIFY) for a pending case."""
    logger.info(f"Reviewer '{current_user.username}' submitting review for case ID {case_id}: status={review_in.status}")
    
    # Permission check: Only Reviewers and Admins can review cases
    if current_user.role.name not in ["Governance Reviewer", "Administrator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied. Only governance reviewers or administrators can review cases."
        )
        
    case = db.query(GovernanceCase).filter(GovernanceCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Governance case not found")
        
    if case.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Governance case has already been reviewed (Current Status: {case.status})"
        )
        
    action = case.action
    
    # Update Governance Case state
    case.status = review_in.status
    case.comments = review_in.comments
    case.conditions_applied = review_in.conditions_applied
    case.reviewer_id = current_user.id
    
    # Update associated Action status to match decision
    action.status = review_in.status
    
    # Write Audit Trail Log
    log_details = (
        f"Governance Case reviewed. Status set to: {review_in.status}. "
        f"Comments: {review_in.comments or 'None'}. "
        f"Conditions Applied: {review_in.conditions_applied or 'None'}."
    )
    audit_log = AuditLog(
        user_id=current_user.id,
        action_id=action.id,
        case_id=case.id,
        event_type=f"REVIEW_{review_in.status}",
        details=log_details
    )
    db.add(audit_log)
    
    try:
        db.commit()
        db.refresh(case)
        
        # Dispatch case resolved notification to requester employee
        try:
            from app.services.notification_engine import notify_employee_case_resolved
            notify_employee_case_resolved(db, case)
        except Exception as notify_err:
            logger.error(f"Failed to dispatch case resolved notification: {notify_err}")
            
        logger.info(f"Governance Case ID {case.id} reviewed successfully. Decision: {review_in.status}")
        return case
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to submit reviewer decision for Case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit reviewer decision"
        )

@router.post("/{case_id}/approve", response_model=GovernanceCaseResponse)
def approve_case(
    case_id: int,
    decision_in: CaseDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Directly approve a pending governance case. Reviewer/Admin only."""
    review_in = GovernanceCaseReview(
        status="APPROVED",
        comments=decision_in.comments,
        conditions_applied=decision_in.conditions_applied
    )
    return review_case(case_id, review_in, db, current_user)

@router.post("/{case_id}/reject", response_model=GovernanceCaseResponse)
def reject_case_direct(
    case_id: int,
    decision_in: CaseDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Directly reject a pending governance case. Reviewer/Admin only."""
    review_in = GovernanceCaseReview(
        status="REJECTED",
        comments=decision_in.comments,
        conditions_applied=decision_in.conditions_applied
    )
    return review_case(case_id, review_in, db, current_user)

@router.get("/{case_id}/explanation", response_model=GovernanceExplanationResponse)
def get_case_explanation(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed mathematical and policy explainability data for a specific case."""
    logger.info(f"User '{current_user.username}' requesting explanation for case ID {case_id}")
    
    case = db.query(GovernanceCase).filter(GovernanceCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Governance case not found")
        
    # Permission check: Employees can only view their own cases
    if current_user.role.name == "Employee" and case.action.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    return generate_case_explanation(case, db)
