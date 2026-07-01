import logging
from sqlalchemy.orm import Session
from app.models import GovernanceCase, Policy
from app.schemas import (
    GovernanceExplanationResponse,
    GovernanceExplanationFactor,
    GovernanceExplanationPolicy
)
from app.services.policy_engine import evaluate_policies, parse_context_variables
from app.services.history_engine import get_historical_intelligence

logger = logging.getLogger("app.services.explainability")

def get_friendly_decision(autonomy_level: str) -> str:
    mapping = {
        "AUTOMATIC": "Automatic Execution",
        "USER_CONFIRMATION": "User Confirmation",
        "HUMAN_REVIEW": "Human Governance Review"
    }
    return mapping.get(autonomy_level, "Human Governance Review")

def generate_case_explanation(case: GovernanceCase, db: Session) -> GovernanceExplanationResponse:
    """
    Generate detailed mathematical breakdown and factor explanations for a governance case decision.
    """
    action = case.action
    rb = action.risk_breakdown
    
    if not rb:
        # Fallback if risk breakdown doesn't exist for some reason
        logger.warning(f"Risk breakdown missing for Action ID {action.id}")
        return GovernanceExplanationResponse(
            case_id=case.id,
            action_text=action.natural_language_request,
            matched_policies=[],
            risk_factors=[],
            adaptive_offset=0.0,
            final_risk=action.risk_score or 0,
            decision=get_friendly_decision(action.autonomy_level)
        )
    
    # 1. Fetch matched policies and violations
    policy_results = evaluate_policies(action, db)
    matched_names = policy_results.get("matched_policies", [])
    
    matched_db_policies = db.query(Policy).filter(
        Policy.name.in_(matched_names),
        Policy.is_active == True
    ).all() if matched_names else []
    
    # Calculate policy-specific contributions
    total_policy_boost = 0
    policy_boosts = []
    for policy in matched_db_policies:
        boost = 50 if policy.severity == "CRITICAL" else 30 if policy.severity == "HIGH" else 15 if policy.severity == "MEDIUM" else 5
        total_policy_boost += boost
        policy_boosts.append((policy, boost))
        
    total_policy_points = rb.policy_factor * 25
    matched_policies_explanation = []
    
    for policy, boost in policy_boosts:
        # Proportional contribution to final score
        contrib = (boost / total_policy_boost) * total_policy_points if total_policy_boost > 0 else 0.0
        matched_policies_explanation.append(
            GovernanceExplanationPolicy(
                name=policy.name,
                severity=policy.severity,
                boost=boost,
                contribution=round(contrib, 2)
            )
        )
        
    # 2. Get history engine variables for Adaptive Learning offset
    history_pkg = get_historical_intelligence(action, db)
    dynamic_approved = history_pkg.get("dynamic_approved", 0)
    dynamic_rejected = history_pkg.get("dynamic_rejected", 0)
    adaptive_offset = -min(dynamic_approved * 5, 20) + min(dynamic_rejected * 10, 30)
    
    # 3. Build factors breakdown list
    context_vars = parse_context_variables(action)
    
    # Domain Risk Factor description details
    domain_desc = f"Assigned multiplier for domain: {action.domain}"
    
    # Reversibility impact description details
    rev_desc = f"Irreversibility rating for operations of type: {action.extracted_action or 'N/A'}"
    
    # Scope exposure description details
    if action.extracted_action == "TRANSFER":
        scope_desc = f"Exposure score based on transfer amount (Rs. {context_vars.get('amount', 0):,})"
    elif action.extracted_action in ["DELETE", "UPDATE"]:
        scope_desc = f"Exposure score based on affected record count ({context_vars.get('records', 0):,} records)"
    else:
        scope_desc = "Scope exposure assessment of evaluated target parameters"
        
    # Policy Violations description details
    p_desc = f"Security & privacy policy exceptions triggered ({len(matched_names)} matches)"
    
    # Confidence description details
    c_desc = f"Ambiguity factor derived from LLM confidence ({round((action.confidence or 1.0)*100)}%)"
    
    # History description details
    h_desc = f"Rejection trends based on historical frequency matching: {history_pkg.get('total_cases', 0)} cases"
    
    # Safety description details
    negation_risk = rb.negation if rb.negation is not None else 0.0
    bias_risk = rb.harmful_biasness if rb.harmful_biasness is not None else 0.0
    confabulation_risk = rb.confabulation if rb.confabulation is not None else 0.0
    integrity_risk = float(max(1.0 - (rb.integrity if rb.integrity is not None else 1.0), 0.0))
    abusive_risk = rb.abusive if rb.abusive is not None else 0.0
    privacy_risk = float(max(1.0 - (rb.privacy_enhanced if rb.privacy_enhanced is not None else 1.0), 0.0))
    dangerous_risk = rb.dangerous if rb.dangerous is not None else 0.0
    violent_risk = rb.violent if rb.violent is not None else 0.0
    environmental_risk = rb.environmental_impacts if rb.environmental_impacts is not None else 0.0
    
    safety_factor = float(max(
        negation_risk, bias_risk, confabulation_risk, integrity_risk, abusive_risk, privacy_risk, dangerous_risk, violent_risk, environmental_risk
    ))
    
    safety_issues = []
    if dangerous_risk > 0.3: safety_issues.append("dangerous intent")
    if violent_risk > 0.3: safety_issues.append("violent language")
    if abusive_risk > 0.3: safety_issues.append("toxic content")
    if privacy_risk > 0.3: safety_issues.append("privacy risk")
    if integrity_risk > 0.3: safety_issues.append("integrity risk")
    if bias_risk > 0.3: safety_issues.append("harmful bias")
    if confabulation_risk > 0.3: safety_issues.append("confabulation")
    if negation_risk > 0.3: safety_issues.append("negation mismatch")
    if environmental_risk > 0.3: safety_issues.append("environmental impact")
    
    if safety_issues:
        s_desc = f"NIST safety exceptions flagged: {', '.join(safety_issues)}"
    else:
        s_desc = "No safety compliance exceptions triggered"
    
    factors = [
        GovernanceExplanationFactor(
            name="Domain Risk",
            score=round(rb.domain_factor * 100, 1),
            weight=15.0,
            contribution=round(rb.domain_factor * 15, 2),
            description=domain_desc
        ),
        GovernanceExplanationFactor(
            name="Reversibility Impact",
            score=round(rb.reversibility_factor * 100, 1),
            weight=15.0,
            contribution=round(rb.reversibility_factor * 15, 2),
            description=rev_desc
        ),
        GovernanceExplanationFactor(
            name="Scope Exposure",
            score=round(rb.scope_factor * 100, 1),
            weight=20.0,
            contribution=round(rb.scope_factor * 20, 2),
            description=scope_desc
        ),
        GovernanceExplanationFactor(
            name="Policy Violations",
            score=round(rb.policy_factor * 100, 1),
            weight=25.0,
            contribution=round(rb.policy_factor * 25, 2),
            description=p_desc
        ),
        GovernanceExplanationFactor(
            name="AI Confidence Mismatch",
            score=round(rb.confidence_factor * 100, 1),
            weight=10.0,
            contribution=round(rb.confidence_factor * 10, 2),
            description=c_desc
        ),
        GovernanceExplanationFactor(
            name="Historical Rejections",
            score=round(rb.history_factor * 100, 1),
            weight=15.0,
            contribution=round(rb.history_factor * 15, 2),
            description=h_desc
        ),
        GovernanceExplanationFactor(
            name="Safety & Trust Compliance",
            score=round(safety_factor * 100, 1),
            weight=20.0,
            contribution=round(safety_factor * 20, 2),
            description=s_desc
        )
    ]
    
    return GovernanceExplanationResponse(
        case_id=case.id,
        action_text=action.natural_language_request,
        matched_policies=matched_policies_explanation,
        risk_factors=factors,
        adaptive_offset=float(adaptive_offset),
        final_risk=action.risk_score or 0,
        decision=get_friendly_decision(action.autonomy_level)
    )
