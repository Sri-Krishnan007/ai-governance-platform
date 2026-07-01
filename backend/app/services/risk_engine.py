import logging
from sqlalchemy.orm import Session
from app.models import Action
from app.services.policy_engine import parse_context_variables

logger = logging.getLogger("app.services.risk_engine")

def calculate_risk(action: Action, policy_results: dict, history_results: dict, db: Session, safety_eval: dict = None) -> dict:
    """Calculate overall risk score (0-100) and seven-dimensional risk factors breakdown with Safety Compliance and Adaptive Learning."""
    logger.info(f"Computing risk score breakdown for Action {action.id}...")
    
    # 1. Domain Factor
    domain_factor = 0.3
    domain_lower = action.domain.lower() if action.domain else ""
    if "healthcare" in domain_lower:
        domain_factor = 1.0
    elif "finance" in domain_lower:
        domain_factor = 0.8
    elif "legal" in domain_lower:
        domain_factor = 0.7
    elif "hr" in domain_lower or "human" in domain_lower:
        domain_factor = 0.5
        
    # 2. Reversibility Factor
    reversibility_factor = 0.2
    action_type = action.extracted_action.upper() if action.extracted_action else ""
    if action_type == "DELETE":
        reversibility_factor = 1.0  # Destructive & irreversible
    elif action_type == "TRANSFER":
        reversibility_factor = 0.9  # Irreversible cash outlays
    elif action_type == "UPDATE":
        reversibility_factor = 0.5  # Partially reversible (overwrites values)
    elif action_type == "CREATE":
        reversibility_factor = 0.3  # Easy to delete
    elif action_type == "READ":
        reversibility_factor = 0.1  # Completely safe
        
    # 3. Scope Factor
    scope_factor = 0.2
    context_vars = parse_context_variables(action)
    if action_type == "TRANSFER":
        amount = context_vars.get("amount", 0)
        scope_factor = float(min(amount / 200000.0, 1.0))
    elif action_type in ["DELETE", "UPDATE"]:
        records = context_vars.get("records", 0)
        scope_factor = float(min(records / 2000.0, 1.0))
        
    # 4. Policy Factor
    policy_boost = policy_results.get("risk_score_boost", 0)
    policy_factor = float(min(policy_boost / 100.0, 1.0))
    
    # 5. Confidence Factor
    confidence = action.confidence if action.confidence is not None else 1.0
    confidence_factor = float(max(1.0 - confidence, 0.0))
    
    # 6. History Factor
    history_factor = 0.3  # Default fallback if no prior cases
    total_cases = history_results.get("total_cases", 0)
    if total_cases > 0:
        history_factor = float(history_results.get("rejection_rate", 0.0))
        
    # 7. Safety & NIST Trust Compliance Factor
    safety_data = safety_eval or {}
    if not safety_data and action.id:
        from app.models import RiskBreakdown
        try:
            rb = db.query(RiskBreakdown).filter(RiskBreakdown.action_id == action.id).first()
            if rb:
                safety_data = {
                    "negation": rb.negation,
                    "harmful_biasness": rb.harmful_biasness,
                    "confabulation": rb.confabulation,
                    "integrity": rb.integrity,
                    "abusive": rb.abusive,
                    "privacy_enhanced": rb.privacy_enhanced,
                    "dangerous": rb.dangerous,
                    "violent": rb.violent,
                    "environmental_impacts": rb.environmental_impacts
                }
        except Exception as e:
            logger.warning(f"Could not load risk breakdown for safety data fallback: {e}")
            
    negation = float(safety_data.get("negation", 0.0))
    harmful_biasness = float(safety_data.get("harmful_biasness", 0.0))
    confabulation = float(safety_data.get("confabulation", 0.0))
    integrity = float(safety_data.get("integrity", 1.0))
    abusive = float(safety_data.get("abusive", 0.0))
    privacy_enhanced = float(safety_data.get("privacy_enhanced", 1.0))
    dangerous = float(safety_data.get("dangerous", 0.0))
    violent = float(safety_data.get("violent", 0.0))
    environmental_impacts = float(safety_data.get("environmental_impacts", 0.0))
    
    negation_risk = negation
    bias_risk = harmful_biasness
    confabulation_risk = confabulation
    integrity_risk = float(max(1.0 - integrity, 0.0))
    abusive_risk = abusive
    privacy_risk = float(max(1.0 - privacy_enhanced, 0.0))
    dangerous_risk = dangerous
    violent_risk = violent
    environmental_risk = environmental_impacts
    
    safety_factor = float(max(
        negation_risk,
        bias_risk,
        confabulation_risk,
        integrity_risk,
        abusive_risk,
        privacy_risk,
        dangerous_risk,
        violent_risk,
        environmental_risk
    ))
        
    # Base Weighted calculation (weights sum to 100)
    raw_score = (
        (domain_factor * 15) +
        (reversibility_factor * 15) +
        (scope_factor * 20) +
        (policy_factor * 25) +
        (confidence_factor * 10) +
        (history_factor * 15)
    )
    
    # Safety Compliance risk boost (up to 20 additional points, capped at 100)
    safety_boost = safety_factor * 20
    raw_score += safety_boost
    
    # Adaptive Learning Adjustment (Phase 15)
    dynamic_approved = history_results.get("dynamic_approved", 0)
    dynamic_rejected = history_results.get("dynamic_rejected", 0)
    
    # Repeated approvals -> Reduce risk (-5 per case, capped at -20)
    # Repeated rejections -> Increase risk (+10 per case, capped at +30)
    adaptive_offset = -min(dynamic_approved * 5, 20) + min(dynamic_rejected * 10, 30)
    raw_score += adaptive_offset
    
    risk_score = int(round(raw_score))
    risk_score = max(0, min(risk_score, 100))
    
    # Determine the driving factor for natural explanation
    factors = {
        "domain rules": domain_factor,
        "action irreversibility": reversibility_factor,
        "affected scope size": scope_factor,
        "policy violations": policy_factor,
        "intent confidence mismatch": confidence_factor,
        "historical rejection trends": history_factor,
        "safety compliance violations": safety_factor
    }
    highest_driver = max(factors, key=factors.get)
    
    explanation = f"Risk score is {risk_score}/100. The primary risk driver is {highest_driver}."
    if adaptive_offset < 0:
        explanation += f" Adaptive learning offset: Risk decreased by {abs(adaptive_offset)} due to repeated approvals."
    elif adaptive_offset > 0:
        explanation += f" Adaptive learning offset: Risk increased by {adaptive_offset} due to repeated rejections."
        
    if policy_results.get("violations"):
        explanation += f" Critical alerts: {policy_results['violations'][0]}"
        
    # If safety risk is significant, mention the sub-safety details in the explanation
    if safety_factor > 0.3:
        unsafe_items = []
        if negation_risk > 0.3: unsafe_items.append(f"negation risk ({int(negation_risk*100)}%)")
        if bias_risk > 0.3: unsafe_items.append(f"harmful bias ({int(bias_risk*100)}%)")
        if confabulation_risk > 0.3: unsafe_items.append(f"confabulation risk ({int(confabulation_risk*100)}%)")
        if integrity_risk > 0.3: unsafe_items.append(f"integrity violation risk ({int(integrity_risk*100)}%)")
        if abusive_risk > 0.3: unsafe_items.append(f"toxic/abusive content ({int(abusive_risk*100)}%)")
        if privacy_risk > 0.3: unsafe_items.append(f"privacy risk ({int(privacy_risk*100)}%)")
        if dangerous_risk > 0.3: unsafe_items.append(f"dangerous instructions ({int(dangerous_risk*100)}%)")
        if violent_risk > 0.3: unsafe_items.append(f"violent content ({int(violent_risk*100)}%)")
        if environmental_risk > 0.3: unsafe_items.append(f"high environmental footprint ({int(environmental_risk*100)}%)")
        
        if unsafe_items:
            explanation += f" Safety warnings raised: {', '.join(unsafe_items)}."
        
    breakdown = {
        "reversibility_factor": reversibility_factor,
        "scope_factor": scope_factor,
        "domain_factor": domain_factor,
        "policy_factor": policy_factor,
        "confidence_factor": confidence_factor,
        "history_factor": history_factor,
        "safety_factor": safety_factor,
        
        # Individual safety scores
        "negation": negation,
        "harmful_biasness": harmful_biasness,
        "confabulation": confabulation,
        "integrity": integrity,
        "abusive": abusive,
        "privacy_enhanced": privacy_enhanced,
        "dangerous": dangerous,
        "violent": violent,
        "environmental_impacts": environmental_impacts,
        
        "explanation": explanation,
        "risk_score": risk_score
    }
    
    logger.info(f"Risk calculation completed with adaptive adjustment (offset={adaptive_offset}): score={risk_score}, driver={highest_driver}")
    return breakdown
