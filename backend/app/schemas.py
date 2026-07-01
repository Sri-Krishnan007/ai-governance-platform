from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ----------------- ROLE SCHEMAS -----------------
class RoleBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int

    class Config:
        from_attributes = True


# ----------------- USER SCHEMAS -----------------
class UserBase(BaseModel):
    username: str = Field(..., max_length=100)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role_id: int

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    role_id: int
    is_active: bool
    created_at: datetime
    role: Optional[RoleResponse] = None

    class Config:
        from_attributes = True


# ----------------- TOKEN SCHEMAS -----------------
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ----------------- POLICY SCHEMAS -----------------
class PolicyBase(BaseModel):
    name: str = Field(..., max_length=100)
    domain: str = Field(..., max_length=50)
    description: Optional[str] = None
    rule_definition: Dict[str, Any]
    severity: str = Field(..., max_length=20)
    action_type: str = Field(..., max_length=50)
    is_active: bool = True

class PolicyCreate(PolicyBase):
    pass

class PolicyResponse(PolicyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------- RISK BREAKDOWN SCHEMAS -----------------
class RiskBreakdownBase(BaseModel):
    reversibility_factor: float
    scope_factor: float
    domain_factor: float
    policy_factor: float
    confidence_factor: float
    history_factor: float
    
    # 9 Trust and Safety metrics
    negation: Optional[float] = 0.0
    harmful_biasness: Optional[float] = 0.0
    confabulation: Optional[float] = 0.0
    integrity: Optional[float] = 1.0
    abusive: Optional[float] = 0.0
    privacy_enhanced: Optional[float] = 1.0
    dangerous: Optional[float] = 0.0
    violent: Optional[float] = 0.0
    environmental_impacts: Optional[float] = 0.0
    
    explanation: Optional[str] = None

class RiskBreakdownResponse(RiskBreakdownBase):
    id: int
    action_id: int

    class Config:
        from_attributes = True


# ----------------- CLARIFICATION SCHEMAS -----------------
class ClarificationAnswerSubmit(BaseModel):
    answer_text: str

class ClarificationAnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: str
    answered_at: datetime

    class Config:
        from_attributes = True

class ClarificationQuestionBase(BaseModel):
    parameter_name: str
    question_text: str

class ClarificationQuestionResponse(ClarificationQuestionBase):
    id: int
    action_id: int
    created_at: datetime
    answer: Optional[ClarificationAnswerResponse] = None

    class Config:
        from_attributes = True



# ----------------- GOVERNANCE CASE SCHEMAS -----------------
class GovernanceCaseBase(BaseModel):
    status: str
    comments: Optional[str] = None
    conditions_applied: Optional[str] = None

class GovernanceCaseReview(BaseModel):
    status: str = Field(..., pattern="^(APPROVED|REJECTED|MODIFIED)$")
    comments: Optional[str] = None
    conditions_applied: Optional[str] = None

class GovernanceCaseResponse(GovernanceCaseBase):
    id: int
    action_id: int
    reviewer_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----------------- HISTORICAL SCHEMAS -----------------
class SimilarCaseResponse(BaseModel):
    id: int
    natural_language_request: str
    status: str
    risk_score: int
    comments: Optional[str] = None

    class Config:
        from_attributes = True

class HistoryIntelligenceResponse(BaseModel):
    total_cases: int
    approval_rate: float
    rejection_rate: float
    average_risk: float
    comments: List[str] = []
    similar_cases: List[SimilarCaseResponse] = []

    class Config:
        from_attributes = True


# ----------------- ACTION SCHEMAS -----------------
class ActionBase(BaseModel):
    domain: str = Field(..., max_length=50)
    natural_language_request: str

class ActionSubmit(ActionBase):
    pass

class ActionResponse(ActionBase):
    id: int
    requester_id: int
    extracted_action: Optional[str] = None
    extracted_object: Optional[str] = None
    extracted_scope: Optional[str] = None
    confidence: Optional[float] = None
    missing_info: Optional[List[str]] = None
    risk_score: Optional[int] = None
    autonomy_level: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    risk_breakdown: Optional[RiskBreakdownResponse] = None
    governance_case: Optional[GovernanceCaseResponse] = None
    clarification_questions: List[ClarificationQuestionResponse] = []
    
    # Policy Engine evaluation fields (dynamic)
    matched_policies: List[str] = []
    violations: List[str] = []

    # Historical Intelligence (dynamic)
    history_intelligence: Optional[HistoryIntelligenceResponse] = None

    class Config:
        from_attributes = True


class GovernanceCaseDetailResponse(GovernanceCaseResponse):
    action: Optional[ActionResponse] = None


# ----------------- AUDIT LOG SCHEMAS -----------------
class AuditLogBase(BaseModel):
    event_type: str
    details: str
    ip_address: Optional[str] = None

class AuditLogResponse(AuditLogBase):
    id: int
    timestamp: datetime
    user_id: Optional[int] = None
    action_id: Optional[int] = None
    case_id: Optional[int] = None
    
    user: Optional[UserResponse] = None
    action: Optional[ActionResponse] = None

    class Config:
        from_attributes = True


# ----------------- HISTORY CASE SCHEMAS -----------------
class HistoryCaseBase(BaseModel):
    domain: str
    extracted_action: str
    extracted_object: str
    total_cases: int
    approved_count: int
    rejected_count: int
    average_risk: float

class HistoryCaseResponse(HistoryCaseBase):
    id: int

    class Config:
        from_attributes = True


# ----------------- ACTIONS CONFIRM/REJECT SCHEMAS -----------------
class ActionConfirm(BaseModel):
    action_id: int

class ActionReject(BaseModel):
    action_id: int


# ----------------- EXPLAINABILITY SCHEMAS -----------------
class GovernanceExplanationFactor(BaseModel):
    name: str
    score: float
    weight: float
    contribution: float
    description: str

class GovernanceExplanationPolicy(BaseModel):
    name: str
    severity: str
    boost: int
    contribution: float

class GovernanceExplanationResponse(BaseModel):
    case_id: int
    action_text: str
    matched_policies: List[GovernanceExplanationPolicy]
    risk_factors: List[GovernanceExplanationFactor]
    adaptive_offset: float
    final_risk: int
    decision: str


# ----------------- NOTIFICATION SCHEMAS -----------------
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


