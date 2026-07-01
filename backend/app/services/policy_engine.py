import re
import logging
from sqlalchemy.orm import Session
from app.models import Action, Policy

logger = logging.getLogger("app.services.policy_engine")

def parse_context_variables(action: Action) -> dict:
    """Regex-based parser to extract numeric amounts, record count, and target environments from natural request and context."""
    text = f"{action.natural_language_request} {action.extracted_scope or ''}"
    
    # 1. Parse Financial Amount
    amount = 0
    # Match symbols like ₹, $, Rs., INR followed by numbers with commas, e.g. ₹50,000 or Rs. 10,000
    amount_match = re.search(r'(?:₹|\$|\brs\b\.?|\binr\b)\s*([\d,]+(?:\.\d+)?)', text, re.IGNORECASE)
    if not amount_match:
        # Match numbers followed by currency words, e.g. 50000 rupees
        amount_match = re.search(r'([\d,]+(?:\.\d+)?)\s*(?:\brupees\b|\binr\b|\bdollars\b|\busd\b|\bbucks\b)', text, re.IGNORECASE)
    if amount_match:
        try:
            amount = int(amount_match.group(1).replace(',', '').split('.')[0])
        except ValueError:
            pass
            
    # 2. Parse Record Count
    records = 0
    # Match "affected_records: 1500" or "delete 1500 records" or "delete 1200 rows"
    records_match = re.search(r'(?:affected_records|records|rows|items)\s*[:=]?\s*(\d+)', text, re.IGNORECASE)
    if not records_match:
        records_match = re.search(r'(\d+)\s+(?:[a-zA-Z]+\s+)?(?:records|rows|items|customers|users|patients)', text, re.IGNORECASE)
    if records_match:
        try:
            records = int(records_match.group(1))
        except ValueError:
            pass
            
    # 3. Parse target environment
    environment = "Testing"  # Default fallback
    if re.search(r'\b(production|prod|live)\b', text, re.IGNORECASE):
        environment = "Production"
    elif re.search(r'\b(testing|test|dev|development|staging)\b', text, re.IGNORECASE):
        environment = "Testing"
        
    logger.info(f"Parsed context variables for Action {action.id}: amount={amount}, records={records}, environment={environment}")
    return {"amount": amount, "records": records, "environment": environment}

def evaluate_policies(action: Action, db: Session, safety_eval: dict = None) -> dict:
    """Evaluate active database policies and dynamic trust/safety policies against the action request details and context."""
    logger.info(f"Evaluating policies for Action {action.id} (Domain: {action.domain}, ActionType: {action.extracted_action})")
    
    # If the action has missing parameters and is awaiting clarification, we skip evaluation until resolved
    if action.status == "AWAITING_CLARIFICATION":
        return {
            "matched_policies": [],
            "violations": [],
            "severity": "LOW",
            "recommended_action": "Clarification Required",
            "risk_score_boost": 0
        }

    # Fetch all enabled policies
    policies = db.query(Policy).filter(Policy.is_active == True).all()
    
    matched_policies = []
    violations = []
    max_severity = "LOW"
    risk_score_boost = 0
    
    context_vars = parse_context_variables(action)
    
    # Mapping of severity order to resolve the maximum severity violation
    severity_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    
    for policy in policies:
        # Check if the policy applies to this action's domain and type
        domain_matches = (policy.domain == "ALL") or (policy.domain == action.domain)
        action_matches = (policy.action_type == "ALL") or (policy.action_type == action.extracted_action)
        
        if not (domain_matches and action_matches):
            continue
            
        rule = policy.rule_definition
        condition_type = rule.get("condition_type")
        triggered = False
        
        # Condition checks
        if condition_type == "threshold":
            threshold_val = rule.get("threshold_value", 0)
            if context_vars["amount"] > threshold_val:
                triggered = True
                
        elif condition_type == "bulk_threshold":
            threshold_val = rule.get("threshold_value", 0)
            if context_vars["records"] > threshold_val:
                triggered = True
                
        elif condition_type == "production_check":
            if context_vars["environment"] == "Production":
                triggered = True
                
        elif condition_type == "domain_specific":
            # Always triggers if the domain and action type match
            triggered = True
            
        if triggered:
            logger.warning(f"Action {action.id} triggered policy violation: {policy.name} ({policy.severity})")
            matched_policies.append(policy.name)
            violations.append(policy.description)
            
            # Keep track of highest severity
            if severity_rank.get(policy.severity, 0) > severity_rank.get(max_severity, 0):
                max_severity = policy.severity
                
            # Accumulate risk weight/boost
            if policy.severity == "CRITICAL":
                risk_score_boost += 50
            elif policy.severity == "HIGH":
                risk_score_boost += 30
            elif policy.severity == "MEDIUM":
                risk_score_boost += 15
            else:
                risk_score_boost += 5
                
    # 2. Evaluate Dynamic AI Safety and Trustworthiness Policies (NIST AI RMF)
    safety_data = safety_eval or {}
    if not safety_data:
        # Try loading from database RiskBreakdown
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
            logger.warning(f"Could not load safety_data from db: {e}")
            
    if safety_data:
        # Negation Check (contradictory commands)
        if safety_data.get("negation", 0.0) > 0.5:
            matched_policies.append("Contradictory Instruction Check")
            violations.append("The request contains negation commands or contradictory instructions.")
            risk_score_boost += 15
            if severity_rank["MEDIUM"] > severity_rank.get(max_severity, 0):
                max_severity = "MEDIUM"
                
        # Harmful Bias Check
        if safety_data.get("harmful_biasness", 0.0) > 0.5:
            matched_policies.append("Fair AI and Anti-Bias Guardrail")
            violations.append("Harmful bias, stereotypes, or discriminatory language detected in request.")
            risk_score_boost += 30
            if severity_rank["HIGH"] > severity_rank.get(max_severity, 0):
                max_severity = "HIGH"
                
        # Confabulation Check
        if safety_data.get("confabulation", 0.0) > 0.5:
            matched_policies.append("Reliable AI Groundedness Check")
            violations.append("The request carries a high risk of confabulation or hallucinated information.")
            risk_score_boost += 15
            if severity_rank["MEDIUM"] > severity_rank.get(max_severity, 0):
                max_severity = "MEDIUM"
                
        # Integrity Check (integrity < 0.5 represents low integrity, hence high risk)
        if safety_data.get("integrity", 1.0) < 0.5:
            matched_policies.append("Information Integrity Safeguard")
            violations.append("The action attempts to modify, corrupt, or falsify historical logs or system data.")
            risk_score_boost += 30
            if severity_rank["HIGH"] > severity_rank.get(max_severity, 0):
                max_severity = "HIGH"
                
        # Abusive Check
        if safety_data.get("abusive", 0.0) > 0.5:
            matched_policies.append("Toxic and Abusive Language Guardrail")
            violations.append("Abusive, toxic, or offensive content detected in the input request.")
            risk_score_boost += 30
            if severity_rank["HIGH"] > severity_rank.get(max_severity, 0):
                max_severity = "HIGH"
                
        # Privacy Check (privacy_enhanced < 0.5 represents low privacy enhancement, hence high risk)
        if safety_data.get("privacy_enhanced", 1.0) < 0.5:
            matched_policies.append("Data Privacy Protection Safeguard")
            violations.append("Request risks exposing or leaking sensitive personal information (PII/confidential records).")
            risk_score_boost += 30
            if severity_rank["HIGH"] > severity_rank.get(max_severity, 0):
                max_severity = "HIGH"
                
        # Dangerous Check
        if safety_data.get("dangerous", 0.0) > 0.5:
            matched_policies.append("Unsafe and Dangerous Action Guardrail")
            violations.append("The request attempts dangerous system execution, unauthorized exploits, or high-risk operations.")
            risk_score_boost += 50
            if severity_rank["CRITICAL"] > severity_rank.get(max_severity, 0):
                max_severity = "CRITICAL"
                
        # Violent Check
        if safety_data.get("violent", 0.0) > 0.5:
            matched_policies.append("Violent and Threatening Content Guardrail")
            violations.append("The request contains violent or threatening language.")
            risk_score_boost += 50
            if severity_rank["CRITICAL"] > severity_rank.get(max_severity, 0):
                max_severity = "CRITICAL"
                
        # Environmental Check
        if safety_data.get("environmental_impacts", 0.0) > 0.5:
            matched_policies.append("Green Computing and Carbon Safeguard")
            violations.append("Request demands excessive or unoptimized computational footprint with potential environmental impact.")
            risk_score_boost += 15
            if severity_rank["MEDIUM"] > severity_rank.get(max_severity, 0):
                max_severity = "MEDIUM"

    # Cap risk score boost at 100
    risk_score_boost = min(risk_score_boost, 100)
    
    # Autonomy level recommendation based on highest severity matched
    if max_severity == "CRITICAL":
        recommended_action = "HUMAN_REVIEW"
    elif max_severity in ["HIGH", "MEDIUM"]:
        recommended_action = "USER_CONFIRMATION"
    else:
        recommended_action = "AUTOMATIC"
        
    return {
        "matched_policies": matched_policies,
        "violations": violations,
        "severity": max_severity,
        "recommended_action": recommended_action,
        "risk_score_boost": risk_score_boost
    }
