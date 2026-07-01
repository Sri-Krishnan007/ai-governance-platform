import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Action, User, ClarificationQuestion, ClarificationAnswer, RiskBreakdown, AuditLog
from app.schemas import (
    ActionSubmit, ActionResponse, ActionConfirm, ActionReject,
    ClarificationQuestionResponse, ClarificationAnswerSubmit, ClarificationAnswerResponse
)
from app.auth import get_current_user
from app.services.llm import extract_intent
from app.services.policy_engine import evaluate_policies
from app.services.history_engine import get_historical_intelligence
from app.services.risk_engine import calculate_risk
from app.services.decision_engine import process_autonomy_decision

logger = logging.getLogger("app.routers.actions")

router = APIRouter(
    prefix="/actions",
    tags=["Actions"]
)

# Friendly mapping for common missing fields
QUESTION_TEMPLATES = {
    "source_account": "What is the source account number for this transfer?",
    "destination_account": "What is the destination/recipient account number for this transfer?",
    "amount": "What is the exact amount you wish to transfer?",
    "reason_for_deletion": "What is the business justification/reason for deleting these records?",
    "affected_records": "How many database records will be affected by this operation?",
    "reason": "Please provide the justification or reason for this request.",
    "target_record": "Which specific record(s) should be updated?",
    "new_value": "What is the new value to be applied?",
    "rollback_plan": "What is the rollback/recovery plan if this destructive action fails?",
    "environment": "Is this action targeted for Production or a Test/Development environment?",
    "reversibility": "Can this action be reversed or undone after execution?"
}

@router.post("/evaluate", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
async def evaluate_action(
    action_in: ActionSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a natural language request under a domain to evaluate risk and autonomy."""
    logger.info(f"User '{current_user.username}' submitted action request in domain '{action_in.domain}': {action_in.natural_language_request}")
    
    # 1. LLM Intent Extraction (Phase 6)
    try:
        extracted = await extract_intent(action_in.natural_language_request)
    except Exception as e:
        logger.error(f"Error during intent extraction: {e}")
        extracted = {
            "extracted_action": None,
            "extracted_object": None,
            "extracted_scope": None,
            "confidence": 0.0,
            "missing_info": []
        }
        
    missing_fields = extracted.get("missing_info", [])
    has_missing_info = len(missing_fields) > 0
    
    # If missing parameters exist, status is AWAITING_CLARIFICATION
    status_value = "AWAITING_CLARIFICATION" if has_missing_info else "PENDING"
    autonomy_value = "USER_CONFIRMATION" if has_missing_info else "AUTOMATIC"
    
    new_action = Action(
        requester_id=current_user.id,
        domain=action_in.domain,
        natural_language_request=action_in.natural_language_request,
        extracted_action=extracted.get("extracted_action"),
        extracted_object=extracted.get("extracted_object"),
        extracted_scope=extracted.get("extracted_scope"),
        confidence=extracted.get("confidence", 0.0),
        missing_info=missing_fields,
        risk_score=0,
        autonomy_level=autonomy_value,
        status=status_value
    )
    
    try:
        db.add(new_action)
        db.commit()
        db.refresh(new_action)
        logger.info(f"Action {new_action.id} saved successfully with status '{status_value}'")
        
        # Write initial submission audit log
        log_sub = AuditLog(
            user_id=current_user.id,
            action_id=new_action.id,
            event_type="SUBMISSION",
            details=f"User '{current_user.username}' submitted request: '{new_action.natural_language_request}' under domain '{new_action.domain}'"
        )
        db.add(log_sub)
        db.commit()
        
        # Initialize dynamic fields for response serialization
        matched = []
        violations_list = []
        history_pkg = None
        
        # 2. Clarification Engine: Create questions if missing information exists
        if has_missing_info:
            logger.info(f"Action {new_action.id} has missing fields: {missing_fields}. Generating questions...")
            for field in missing_fields:
                question_text = QUESTION_TEMPLATES.get(
                    field, 
                    f"Please clarify the following missing detail: {field.replace('_', ' ')}."
                )
                question = ClarificationQuestion(
                    action_id=new_action.id,
                    parameter_name=field,
                    question_text=question_text
                )
                db.add(question)
                
            log_clar = AuditLog(
                user_id=current_user.id,
                action_id=new_action.id,
                event_type="CLARIFICATION_PENDING",
                details=f"Action ID {new_action.id} flagged for clarification on missing parameters: {missing_fields}"
            )
            db.add(log_clar)
            db.commit()
            db.refresh(new_action)  # Load relationship
        else:
            # 3. Policy Engine: Evaluate policies if action is PENDING (complete context)
            policy_results = evaluate_policies(new_action, db, safety_eval=extracted.get("safety_eval"))
            
            # 4. History Engine: Query past case summaries
            history_pkg = get_historical_intelligence(new_action, db)
            
            # 5. Risk Scoring Engine: Calculate multi-vector risk and save breakdown
            risk_results = calculate_risk(new_action, policy_results, history_pkg, db, safety_eval=extracted.get("safety_eval"))
            new_action.risk_score = risk_results["risk_score"]
            
            rb = RiskBreakdown(
                action_id=new_action.id,
                reversibility_factor=risk_results["reversibility_factor"],
                scope_factor=risk_results["scope_factor"],
                domain_factor=risk_results["domain_factor"],
                policy_factor=risk_results["policy_factor"],
                confidence_factor=risk_results["confidence_factor"],
                history_factor=risk_results["history_factor"],
                # Safety evaluation factors
                negation=risk_results.get("negation", 0.0),
                harmful_biasness=risk_results.get("harmful_biasness", 0.0),
                confabulation=risk_results.get("confabulation", 0.0),
                integrity=risk_results.get("integrity", 1.0),
                abusive=risk_results.get("abusive", 0.0),
                privacy_enhanced=risk_results.get("privacy_enhanced", 1.0),
                dangerous=risk_results.get("dangerous", 0.0),
                violent=risk_results.get("violent", 0.0),
                environmental_impacts=risk_results.get("environmental_impacts", 0.0),
                explanation=risk_results["explanation"]
            )
            db.add(rb)
            db.flush()
            
            # 6. Autonomy Decision Engine: Resolve recommended autonomy execution level and register cases
            process_autonomy_decision(new_action, db)
            
            # Hook Audit Trail according to calculated autonomy
            if new_action.autonomy_level == "AUTOMATIC":
                new_action.status = "APPROVED"  # Auto-executed/approved
                log_dec = AuditLog(
                    user_id=current_user.id,
                    action_id=new_action.id,
                    event_type="AUTOMATIC_APPROVAL",
                    details=f"Action ID {new_action.id} approved automatically. Risk Score: {new_action.risk_score}. Recommended autonomy: AUTOMATIC."
                )
            elif new_action.autonomy_level == "USER_CONFIRMATION":
                log_dec = AuditLog(
                    user_id=current_user.id,
                    action_id=new_action.id,
                    event_type="USER_CONFIRMATION_PENDING",
                    details=f"Action ID {new_action.id} flagged for user confirmation. Risk Score: {new_action.risk_score}."
                )
            else:  # HUMAN_REVIEW
                log_dec = AuditLog(
                    user_id=current_user.id,
                    action_id=new_action.id,
                    event_type="HUMAN_REVIEW_PENDING",
                    details=f"Action ID {new_action.id} flagged for reviewer approval. Spawning Governance Case. Risk Score: {new_action.risk_score}."
                )
            db.add(log_dec)
            db.commit()
            db.refresh(new_action)
            
            # Dispatch notifications
            from app.services.notification_engine import (
                notify_employee_confirmation_required,
                notify_reviewers_new_case,
                notify_admins_policy_violation
            )
            if new_action.autonomy_level == "USER_CONFIRMATION":
                notify_employee_confirmation_required(db, new_action)
            elif new_action.autonomy_level == "HUMAN_REVIEW":
                if new_action.governance_case:
                    notify_reviewers_new_case(db, new_action.governance_case)
                    
            if policy_results.get("matched_policies"):
                notify_admins_policy_violation(db, new_action, policy_results)
            
            matched = policy_results["matched_policies"]
            violations_list = policy_results["violations"]
            
        # Attach transient properties dynamically for Pydantic serialization
        new_action.matched_policies = matched
        new_action.violations = violations_list
        new_action.history_intelligence = history_pkg
        return new_action
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving action, policies, risk, and autonomy decision: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate/save action request"
        )

@router.post("/confirm", response_model=ActionResponse)
def confirm_action(
    confirm_in: ActionConfirm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Confirm a pending action evaluation matching USER_CONFIRMATION autonomy rules."""
    logger.info(f"User '{current_user.username}' confirming action ID {confirm_in.action_id}")
    
    action = db.query(Action).filter(Action.id == confirm_in.action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
        
    # Access check: Employees can only confirm their own requests
    if current_user.role.name == "Employee" and action.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    if action.status != "PENDING" or action.autonomy_level != "USER_CONFIRMATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Action cannot be confirmed. Status is '{action.status}' and autonomy is '{action.autonomy_level}'."
        )
        
    action.status = "APPROVED"
    
    log_confirm = AuditLog(
        user_id=current_user.id,
        action_id=action.id,
        event_type="CONFIRMATION",
        details=f"User '{current_user.username}' confirmed action ID {action.id}. Recommended autonomy: USER_CONFIRMATION."
    )
    db.add(log_confirm)
    
    try:
        db.commit()
        db.refresh(action)
        logger.info(f"Action ID {action.id} successfully confirmed by user '{current_user.username}'")
        
        # Load transient properties
        policy_results = evaluate_policies(action, db)
        action.matched_policies = policy_results["matched_policies"]
        action.violations = policy_results["violations"]
        action.history_intelligence = get_historical_intelligence(action, db)
        return action
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to confirm action ID {action.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm action request"
        )

@router.post("/reject", response_model=ActionResponse)
def reject_action(
    reject_in: ActionReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a pending action evaluation matching USER_CONFIRMATION autonomy rules."""
    logger.info(f"User '{current_user.username}' rejecting action ID {reject_in.action_id}")
    
    action = db.query(Action).filter(Action.id == reject_in.action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
        
    # Access check: Employees can only reject their own requests
    if current_user.role.name == "Employee" and action.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    if action.status != "PENDING" or action.autonomy_level != "USER_CONFIRMATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Action cannot be rejected. Status is '{action.status}' and autonomy is '{action.autonomy_level}'."
        )
        
    action.status = "REJECTED"
    
    log_reject = AuditLog(
        user_id=current_user.id,
        action_id=action.id,
        event_type="USER_REJECTION",
        details=f"User '{current_user.username}' rejected action ID {action.id} manually. Recommended autonomy: USER_CONFIRMATION."
    )
    db.add(log_reject)
    
    try:
        db.commit()
        db.refresh(action)
        logger.info(f"Action ID {action.id} successfully rejected by user '{current_user.username}'")
        
        # Load transient properties
        policy_results = evaluate_policies(action, db)
        action.matched_policies = policy_results["matched_policies"]
        action.violations = policy_results["violations"]
        action.history_intelligence = get_historical_intelligence(action, db)
        return action
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reject action ID {action.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject action request"
        )

@router.get("/{action_id}/clarifications", response_model=List[ClarificationQuestionResponse])
def get_clarifications(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve pending clarification questions for a given action."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
        
    # Check if the user is the owner or an administrator/reviewer
    if action.requester_id != current_user.id and current_user.role.name not in ["Governance Reviewer", "Administrator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    questions = db.query(ClarificationQuestion).filter(ClarificationQuestion.action_id == action_id).all()
    return questions

@router.post("/questions/{question_id}/answer", response_model=ClarificationAnswerResponse, status_code=status.HTTP_201_CREATED)
def answer_question(
    question_id: int,
    answer_in: ClarificationAnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an answer to a clarification question."""
    logger.info(f"User '{current_user.username}' submitting answer for question ID {question_id}")
    
    question = db.query(ClarificationQuestion).filter(ClarificationQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clarification question not found")
        
    # Check if the user is the owner of the action
    action = question.action
    if action.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Only the requester can answer clarification questions.")
        
    # Check if already answered
    existing_answer = db.query(ClarificationAnswer).filter(ClarificationAnswer.question_id == question_id).first()
    if existing_answer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question has already been answered")
        
    new_answer = ClarificationAnswer(
        question_id=question_id,
        answer_text=answer_in.answer_text
    )
    
    try:
        db.add(new_answer)
        db.commit()
        db.refresh(new_answer)
        
        # Log response submission event in Audit log
        log_ans = AuditLog(
            user_id=current_user.id,
            action_id=action.id,
            event_type="CLARIFICATION_RESPONSE",
            details=f"User '{current_user.username}' answered question ID {question_id}: '{new_answer.answer_text}'"
        )
        db.add(log_ans)
        db.commit()
        
        # Check if all questions for this action are now answered
        total_questions = db.query(ClarificationQuestion).filter(ClarificationQuestion.action_id == action.id).count()
        answered_questions = db.query(ClarificationAnswer).join(ClarificationQuestion).filter(ClarificationQuestion.action_id == action.id).count()
        
        if total_questions == answered_questions:
            logger.info(f"All clarification questions for Action {action.id} have been answered. Updating status to 'PENDING'.")
            action.status = "PENDING"
            
            # Update scope to append answers so policy engine has full context
            answers_list = db.query(ClarificationQuestion).filter(ClarificationQuestion.action_id == action.id).all()
            context_summary = []
            for q in answers_list:
                ans_text = q.answer.answer_text if q.answer else (answer_in.answer_text if q.id == question_id else "")
                if ans_text:
                    context_summary.append(f"{q.parameter_name}: {ans_text}")
            
            action.extracted_scope = f"{action.extracted_scope or ''} | Context: {', '.join(context_summary)}"
            db.commit()
            
            # Re-evaluate policies
            policy_results = evaluate_policies(action, db)
            
            # Query history aggregates
            history_pkg = get_historical_intelligence(action, db)
            
            # Calculate Risk score and save breakdown record
            risk_results = calculate_risk(action, policy_results, history_pkg, db)
            action.risk_score = risk_results["risk_score"]
            
            # Look up or create RiskBreakdown
            rb = db.query(RiskBreakdown).filter(RiskBreakdown.action_id == action.id).first()
            if not rb:
                rb = RiskBreakdown(action_id=action.id)
                db.add(rb)
                
            rb.reversibility_factor = risk_results["reversibility_factor"]
            rb.scope_factor = risk_results["scope_factor"]
            rb.domain_factor = risk_results["domain_factor"]
            rb.policy_factor = risk_results["policy_factor"]
            rb.confidence_factor = risk_results["confidence_factor"]
            rb.history_factor = risk_results["history_factor"]
            
            # Save/Update safety metrics
            rb.negation = risk_results.get("negation", 0.0)
            rb.harmful_biasness = risk_results.get("harmful_biasness", 0.0)
            rb.confabulation = risk_results.get("confabulation", 0.0)
            rb.integrity = risk_results.get("integrity", 1.0)
            rb.abusive = risk_results.get("abusive", 0.0)
            rb.privacy_enhanced = risk_results.get("privacy_enhanced", 1.0)
            rb.dangerous = risk_results.get("dangerous", 0.0)
            rb.violent = risk_results.get("violent", 0.0)
            rb.environmental_impacts = risk_results.get("environmental_impacts", 0.0)
            
            rb.explanation = risk_results["explanation"]
            
            # Autonomy Decision Engine: Resolve recommended autonomy execution level and register cases
            process_autonomy_decision(action, db)
            
            # Hook Audit Trail according to calculated autonomy
            if action.autonomy_level == "AUTOMATIC":
                action.status = "APPROVED"  # Auto-executed/approved
                log_dec = AuditLog(
                    user_id=current_user.id,
                    action_id=action.id,
                    event_type="AUTOMATIC_APPROVAL",
                    details=f"Action ID {action.id} approved automatically after clarifications. Risk Score: {action.risk_score}."
                )
            elif action.autonomy_level == "USER_CONFIRMATION":
                log_dec = AuditLog(
                    user_id=current_user.id,
                    action_id=action.id,
                    event_type="USER_CONFIRMATION_PENDING",
                    details=f"Action ID {action.id} flagged for user confirmation after clarifications. Risk Score: {action.risk_score}."
                )
            else:  # HUMAN_REVIEW
                log_dec = AuditLog(
                    user_id=current_user.id,
                    action_id=action.id,
                    event_type="HUMAN_REVIEW_PENDING",
                    details=f"Action ID {action.id} flagged for reviewer approval after clarifications. Governance Case registered. Risk Score: {action.risk_score}."
                )
            db.add(log_dec)
            db.commit()
            db.refresh(action)
            
            # Dispatch notifications after clarification responses are resolved
            from app.services.notification_engine import (
                notify_employee_confirmation_required,
                notify_reviewers_new_case,
                notify_admins_policy_violation
            )
            if action.autonomy_level == "USER_CONFIRMATION":
                notify_employee_confirmation_required(db, action)
            elif action.autonomy_level == "HUMAN_REVIEW":
                if action.governance_case:
                    notify_reviewers_new_case(db, action.governance_case)
                    
            if policy_results.get("matched_policies"):
                notify_admins_policy_violation(db, action, policy_results)
            
        return new_answer
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving answer, policies, risk, and autonomy decision: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit answer"
        )

@router.get("/{action_id}", response_model=ActionResponse)
def get_action_by_id(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full details of a specific action request by ID."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
        
    # Check if user is owner or has reviewer/admin roles
    if action.requester_id != current_user.id and current_user.role.name not in ["Governance Reviewer", "Administrator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    # Run policy evaluation dynamically so matched_policies and violations are loaded in response
    policy_results = evaluate_policies(action, db)
    action.matched_policies = policy_results["matched_policies"]
    action.violations = policy_results["violations"]
    
    # Run historical engine lookup dynamically
    action.history_intelligence = get_historical_intelligence(action, db)
    return action
