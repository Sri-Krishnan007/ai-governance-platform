import re
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Policy, User
from app.auth import get_current_user, RoleChecker

router = APIRouter(
    prefix="/policies",
    tags=["policies"]
)

# Pydantic schemas for Policy CRUD
class PolicyRuleDefinition(BaseModel):
    category: str = "General"
    condition_type: str = "domain_specific"
    operator: str = ""
    threshold_value: int = 0
    regulation: str = ""

class PolicyBase(BaseModel):
    name: str
    domain: str
    description: str = ""
    action_type: str = "ALL"
    severity: str = "MEDIUM"
    rule_definition: PolicyRuleDefinition
    is_active: bool = True

class PolicyResponse(PolicyBase):
    id: int
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[PolicyResponse])
def get_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all policies in the platform (accessible to all authenticated users)."""
    return db.query(Policy).all()

@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    policy_in: PolicyBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["Administrator"]))
):
    """Manually register a new policy rule (Administrator only)."""
    # Check duplicate
    existing = db.query(Policy).filter(Policy.name == policy_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy name '{policy_in.name}' already exists"
        )
    
    policy = Policy(
        name=policy_in.name,
        domain=policy_in.domain,
        description=policy_in.description,
        action_type=policy_in.action_type,
        severity=policy_in.severity.upper(),
        rule_definition=policy_in.rule_definition.model_dump(),
        is_active=policy_in.is_active
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

@router.put("/{id}", response_model=PolicyResponse)
def update_policy(
    id: int,
    policy_in: PolicyBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["Administrator"]))
):
    """Modify an existing policy rule (Administrator only)."""
    policy = db.query(Policy).filter(Policy.id == id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
        
    policy.name = policy_in.name
    policy.domain = policy_in.domain
    policy.description = policy_in.description
    policy.action_type = policy_in.action_type
    policy.severity = policy_in.severity.upper()
    policy.rule_definition = policy_in.rule_definition.model_dump()
    policy.is_active = policy_in.is_active
    
    db.commit()
    db.refresh(policy)
    return policy

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["Administrator"]))
):
    """Delete a policy rule (Administrator only)."""
    policy = db.query(Policy).filter(Policy.id == id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    db.delete(policy)
    db.commit()
    return None

@router.post("/upload", response_model=List[PolicyResponse])
async def upload_policies_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["Administrator"]))
):
    """
    Accepts a .txt policy file, parses policy declarations, saves them in the DB,
    and returns the list of newly created policies (Administrator only).
    """
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt files are supported for policy uploads"
        )
        
    contents = await file.read()
    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = contents.decode("latin1")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to decode text file. Ensure it is UTF-8 or ASCII."
            )
            
    # Extract domain from filename helper
    filename_lower = file.filename.lower()
    inferred_domain = "ALL"
    for d in ["finance", "healthcare", "hr", "legal", "manufacturing"]:
        if d in filename_lower:
            inferred_domain = "HR" if d == "hr" else d.capitalize()
            break
            
    # Parse blocks
    # Support policy separation only by explicit [POLICY] indicators or horizontal divider lines
    blocks = re.split(r'\[POLICY\]|--{3,}|=={3,}', text)
    parsed_policies = []
    
    for block in blocks:
        block_clean = block.strip()
        if not block_clean:
            continue
            
        # Check if structured block (contains colon key-value pairs)
        lines = [l.strip() for l in block_clean.split("\n") if l.strip()]
        has_keys = any(":" in line and line.split(":", 1)[0].strip().lower() in ["name", "domain", "condition", "severity"] for line in lines)
        
        if has_keys:
            fields = {}
            for line in lines:
                if ":" in line:
                    k, v = line.split(":", 1)
                    fields[k.strip().lower()] = v.strip()
            
            name = fields.get("name")
            if not name:
                continue # name is required for structured blocks
                
            domain = fields.get("domain", inferred_domain)
            action_type = fields.get("action type", fields.get("action_type", "ALL"))
            severity = fields.get("severity", "MEDIUM").upper()
            description = fields.get("description", "")
            condition_str = fields.get("condition", "always").lower()
            
            # Map condition
            rule_def = {"category": "Compliance", "condition_type": "domain_specific", "operator": "", "threshold_value": 0, "regulation": ""}
            if "amount >" in condition_str:
                match = re.findall(r'\d+', condition_str)
                if match:
                    rule_def["condition_type"] = "threshold"
                    rule_def["operator"] = ">"
                    rule_def["threshold_value"] = int(match[0])
            elif "records >" in condition_str:
                match = re.findall(r'\d+', condition_str)
                if match:
                    rule_def["condition_type"] = "bulk_threshold"
                    rule_def["operator"] = ">"
                    rule_def["threshold_value"] = int(match[0])
            elif "environment" in condition_str and "production" in condition_str:
                rule_def["condition_type"] = "production_check"
                
            parsed_policies.append({
                "name": name,
                "domain": domain,
                "description": description,
                "action_type": action_type,
                "severity": severity,
                "rule_definition": rule_def
            })
        else:
            # Unstructured block fallback (treat entire file/block as one policy)
            # Find first line for name
            name_cand = lines[0] if lines else "Unnamed Policy"
            # Sanitize name
            name_cand = name_cand.replace("#", "").replace("*", "").strip()[:50]
            
            # Inferred severity from text keywords
            inferred_severity = "MEDIUM"
            text_lower = block_clean.lower()
            if "critical" in text_lower:
                inferred_severity = "CRITICAL"
            elif "high" in text_lower:
                inferred_severity = "HIGH"
            elif "low" in text_lower:
                inferred_severity = "LOW"
                
            # Check if any action type keywords match
            inferred_action = "ALL"
            for a in ["delete", "transfer", "update", "create", "read"]:
                if a in text_lower:
                    inferred_action = a.upper()
                    break
                    
            rule_def = {"category": "Operational", "condition_type": "domain_specific", "operator": "", "threshold_value": 0, "regulation": ""}
            
            # Simple number extraction fallback for thresholds
            if "amount" in text_lower or "transfer" in text_lower:
                match = re.findall(r'\d+', text_lower)
                if match:
                    rule_def["condition_type"] = "threshold"
                    rule_def["operator"] = ">"
                    rule_def["threshold_value"] = int(match[0])
            elif "records" in text_lower or "rows" in text_lower:
                match = re.findall(r'\d+', text_lower)
                if match:
                    rule_def["condition_type"] = "bulk_threshold"
                    rule_def["operator"] = ">"
                    rule_def["threshold_value"] = int(match[0])
            elif "production" in text_lower:
                rule_def["condition_type"] = "production_check"
                
            parsed_policies.append({
                "name": f"{name_cand} ({os.path.basename(file.filename)})",
                "domain": inferred_domain,
                "description": block_clean,
                "action_type": inferred_action,
                "severity": inferred_severity,
                "rule_definition": rule_def
            })
            
    # Save newly created policies into DB
    created_policies = []
    for p_info in parsed_policies:
        # Avoid duplicate name collision by suffixing if duplicate exists
        base_name = p_info["name"]
        counter = 1
        name = base_name
        while db.query(Policy).filter(Policy.name == name).first() is not None:
            name = f"{base_name} ({counter})"
            counter += 1
            
        policy = Policy(
            name=name,
            domain=p_info["domain"],
            description=p_info["description"],
            action_type=p_info["action_type"],
            severity=p_info["severity"],
            rule_definition=p_info["rule_definition"],
            is_active=True
        )
        db.add(policy)
        created_policies.append(policy)
        
    db.commit()
    for cp in created_policies:
        db.refresh(cp)
        
    return created_policies
