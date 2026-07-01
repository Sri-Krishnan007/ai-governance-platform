import logging
from sqlalchemy.orm import Session
from app.models import Role, User
from app.auth import get_password_hash

logger = logging.getLogger("app.seed")

from sqlalchemy import text

def seed_database(db: Session):
    """Seed roles and default users into the database."""
    logger.info("Starting database seeding...")
    
    # 0. Dynamic migration check for the 9 safety factors
    logger.info("Running safety factors column migrations check...")
    columns = [
        ("negation", "DOUBLE PRECISION DEFAULT 0.0"),
        ("harmful_biasness", "DOUBLE PRECISION DEFAULT 0.0"),
        ("confabulation", "DOUBLE PRECISION DEFAULT 0.0"),
        ("integrity", "DOUBLE PRECISION DEFAULT 1.0"),
        ("abusive", "DOUBLE PRECISION DEFAULT 0.0"),
        ("privacy_enhanced", "DOUBLE PRECISION DEFAULT 1.0"),
        ("dangerous", "DOUBLE PRECISION DEFAULT 0.0"),
        ("violent", "DOUBLE PRECISION DEFAULT 0.0"),
        ("environmental_impacts", "DOUBLE PRECISION DEFAULT 0.0")
    ]
    for col_name, col_type in columns:
        try:
            db.execute(text(f"ALTER TABLE risk_breakdowns ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to add column {col_name} via DDL: {e}. It might already exist or using a different dialect.")
            
    # 1. Seed Roles
    default_roles = [
        {"name": "Employee", "description": "Default role for submitting AI-generated actions"},
        {"name": "Governance Reviewer", "description": "Reviewer responsible for approving/rejecting high-risk actions"},
        {"name": "Administrator", "description": "Full administrator permissions"}
    ]
    
    db_roles = {}
    for role_info in default_roles:
        role = db.query(Role).filter(Role.name == role_info["name"]).first()
        if not role:
            role = Role(name=role_info["name"], description=role_info["description"])
            db.add(role)
            db.flush()  # Generate ID
            logger.info(f"Seeded role: {role_info['name']}")
        db_roles[role_info["name"]] = role

    # 2. Seed Default Users
    default_users = [
        {
            "username": "admin",
            "email": "admin@enterprise.com",
            "password": "adminpassword",
            "role_name": "Administrator"
        },
        {
            "username": "reviewer",
            "email": "reviewer@enterprise.com",
            "password": "reviewerpassword",
            "role_name": "Governance Reviewer"
        },
        {
            "username": "employee",
            "email": "employee@enterprise.com",
            "password": "employeepassword",
            "role_name": "Employee"
        }
    ]

    for user_info in default_users:
        user = db.query(User).filter(User.username == user_info["username"]).first()
        if not user:
            role = db_roles.get(user_info["role_name"])
            if not role:
                logger.error(f"Cannot seed user {user_info['username']}: Role {user_info['role_name']} not found")
                continue
                
            hashed_pwd = get_password_hash(user_info["password"])
            user = User(
                username=user_info["username"],
                email=user_info["email"],
                hashed_password=hashed_pwd,
                role_id=role.id,
                is_active=True
            )
            db.add(user)
            logger.info(f"Seeded user: {user_info['username']} ({user_info['role_name']})")

    # 3. Seed Policies
    from app.models import Policy
    default_policies = [
        {
            "name": "Finance Limit Safeguard",
            "domain": "Finance",
            "description": "Requires confirmation for financial transfers exceeding Rs. 50,000.",
            "action_type": "TRANSFER",
            "severity": "HIGH",
            "rule_definition": {
                "category": "Financial",
                "condition_type": "threshold",
                "operator": ">",
                "threshold_value": 50000,
                "regulation": "PCI DSS"
            }
        },
        {
            "name": "Healthcare Patient Deletion Restrictor",
            "domain": "Healthcare",
            "description": "Multi-reviewer human review mandated for delete patient record requests.",
            "action_type": "DELETE",
            "severity": "CRITICAL",
            "rule_definition": {
                "category": "Privacy",
                "condition_type": "domain_specific",
                "regulation": "HIPAA"
            }
        },
        {
            "name": "Bulk Deletion Guardrail",
            "domain": "ALL",
            "description": "Requires additional verification for bulk record deletions (exceeding 1000 items).",
            "action_type": "DELETE",
            "severity": "HIGH",
            "rule_definition": {
                "category": "Operational",
                "condition_type": "bulk_threshold",
                "operator": ">",
                "threshold_value": 1000
            }
        },
        {
            "name": "Production Change Safeguard",
            "domain": "ALL",
            "description": "Safety confirmation required for destructive actions running directly on production servers.",
            "action_type": "DELETE",
            "severity": "MEDIUM",
            "rule_definition": {
                "category": "Security",
                "condition_type": "production_check"
            }
        }
    ]

    for policy_info in default_policies:
        policy = db.query(Policy).filter(Policy.name == policy_info["name"]).first()
        if not policy:
            policy = Policy(
                name=policy_info["name"],
                domain=policy_info["domain"],
                description=policy_info["description"],
                action_type=policy_info["action_type"],
                severity=policy_info["severity"],
                rule_definition=policy_info["rule_definition"],
                is_active=True
            )
            db.add(policy)
            logger.info(f"Seeded policy: {policy_info['name']}")

    # 4. Seed HistoryCase aggregates
    from app.models import HistoryCase
    default_history = [
        {
            "domain": "Finance",
            "extracted_action": "TRANSFER",
            "extracted_object": "rupees",
            "total_cases": 12,
            "approved_count": 10,
            "rejected_count": 2,
            "average_risk": 25.0
        },
        {
            "domain": "Healthcare",
            "extracted_action": "DELETE",
            "extracted_object": "patient record",
            "total_cases": 6,
            "approved_count": 1,
            "rejected_count": 5,
            "average_risk": 75.0
        }
    ]
    
    for hist_info in default_history:
        hist = db.query(HistoryCase).filter(
            HistoryCase.domain == hist_info["domain"],
            HistoryCase.extracted_action == hist_info["extracted_action"],
            HistoryCase.extracted_object == hist_info["extracted_object"]
        ).first()
        if not hist:
            hist = HistoryCase(
                domain=hist_info["domain"],
                extracted_action=hist_info["extracted_action"],
                extracted_object=hist_info["extracted_object"],
                total_cases=hist_info["total_cases"],
                approved_count=hist_info["approved_count"],
                rejected_count=hist_info["rejected_count"],
                average_risk=hist_info["average_risk"]
            )
            db.add(hist)
            logger.info(f"Seeded history case summary for {hist_info['domain']} {hist_info['extracted_action']}")

    # 5. Seed actual past actions and governance cases for "similar cases" queries
    from app.models import Action, GovernanceCase
    
    employee_user = db.query(User).filter(User.username == "employee").first()
    emp_id = employee_user.id if employee_user else 1
    
    reviewer_user = db.query(User).filter(User.username == "reviewer").first()
    rev_id = reviewer_user.id if reviewer_user else None
    
    past_cases = [
        {
            "natural_request": "Transfer 10,000 rupees to savings account",
            "domain": "Finance",
            "extracted_action": "TRANSFER",
            "extracted_object": "rupees",
            "extracted_scope": "10,000 rupees to savings",
            "risk_score": 10,
            "autonomy_level": "AUTOMATIC",
            "status": "APPROVED",
            "comments": "Approved. Request is below the threshold guidelines.",
            "conditions_applied": "None"
        },
        {
            "natural_request": "Transfer 80,000 rupees to personal fund",
            "domain": "Finance",
            "extracted_action": "TRANSFER",
            "extracted_object": "rupees",
            "extracted_scope": "80,000 rupees to personal fund",
            "risk_score": 40,
            "autonomy_level": "USER_CONFIRMATION",
            "status": "REJECTED",
            "comments": "Rejected: Transfer exceeds limits without multi-signer verification.",
            "conditions_applied": "None"
        },
        {
            "natural_request": "Delete patient medical history chart ID 109",
            "domain": "Healthcare",
            "extracted_action": "DELETE",
            "extracted_object": "patient record",
            "extracted_scope": "chart ID 109",
            "risk_score": 60,
            "autonomy_level": "HUMAN_REVIEW",
            "status": "REJECTED",
            "comments": "Rejected: HIPAA compliance restricts deletion of records less than 7 years old.",
            "conditions_applied": "None"
        }
    ]
    
    for case_info in past_cases:
        action_exists = db.query(Action).filter(
            Action.natural_language_request == case_info["natural_request"]
        ).first()
        if not action_exists:
            past_action = Action(
                requester_id=emp_id,
                domain=case_info["domain"],
                natural_language_request=case_info["natural_request"],
                extracted_action=case_info["extracted_action"],
                extracted_object=case_info["extracted_object"],
                extracted_scope=case_info["extracted_scope"],
                confidence=0.98,
                risk_score=case_info["risk_score"],
                autonomy_level=case_info["autonomy_level"],
                status=case_info["status"]
            )
            db.add(past_action)
            db.flush()
            
            gov_case = GovernanceCase(
                action_id=past_action.id,
                reviewer_id=rev_id,
                status=case_info["status"],
                comments=case_info["comments"],
                conditions_applied=case_info["conditions_applied"]
            )
            db.add(gov_case)
            logger.info(f"Seeded past case: '{case_info['natural_request']}' ({case_info['status']})")

    try:
        db.commit()
        logger.info("Database seeding completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit seeding to database: {e}")
        raise e
