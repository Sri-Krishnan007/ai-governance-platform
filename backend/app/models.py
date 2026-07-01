from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import datetime

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    role = relationship("Role", back_populates="users")
    actions = relationship("Action", back_populates="requester", foreign_keys="[Action.requester_id]")
    reviewed_cases = relationship("GovernanceCase", back_populates="reviewer")
    audit_logs = relationship("AuditLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    domain = Column(String(50), index=True, nullable=False)  # Finance, Healthcare, etc.
    description = Column(Text, nullable=True)
    rule_definition = Column(JSON, nullable=False)  # JSON criteria for validation
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    action_type = Column(String(50), nullable=False)  # DELETE, TRANSFER, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    domain = Column(String(50), index=True, nullable=False)
    natural_language_request = Column(Text, nullable=False)
    
    # LLM Intent Extraction outputs
    extracted_action = Column(String(50), nullable=True)
    extracted_object = Column(String(100), nullable=True)
    extracted_scope = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True)
    missing_info = Column(JSON, nullable=True)  # List of missing fields/parameters

    # Risk & Autonomy decision outputs
    risk_score = Column(Integer, nullable=True)  # 0 to 100
    autonomy_level = Column(String(50), nullable=True)  # AUTOMATIC, USER_CONFIRMATION, HUMAN_REVIEW
    status = Column(String(50), default="PENDING")  # PENDING, EXECUTED, REJECTED, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    requester = relationship("User", back_populates="actions", foreign_keys=[requester_id])
    risk_breakdown = relationship("RiskBreakdown", uselist=False, back_populates="action")
    governance_case = relationship("GovernanceCase", uselist=False, back_populates="action")
    clarification_questions = relationship("ClarificationQuestion", back_populates="action")
    audit_logs = relationship("AuditLog", back_populates="action")


class RiskBreakdown(Base):
    __tablename__ = "risk_breakdowns"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id", ondelete="CASCADE"), unique=True, nullable=False)
    reversibility_factor = Column(Float, default=0.0)
    scope_factor = Column(Float, default=0.0)
    domain_factor = Column(Float, default=0.0)
    policy_factor = Column(Float, default=0.0)
    confidence_factor = Column(Float, default=0.0)
    history_factor = Column(Float, default=0.0)
    
    # 9 Trust and Safety risk metrics
    negation = Column(Float, default=0.0)
    harmful_biasness = Column(Float, default=0.0)
    confabulation = Column(Float, default=0.0)
    integrity = Column(Float, default=1.0)
    abusive = Column(Float, default=0.0)
    privacy_enhanced = Column(Float, default=1.0)
    dangerous = Column(Float, default=0.0)
    violent = Column(Float, default=0.0)
    environmental_impacts = Column(Float, default=0.0)
    
    explanation = Column(Text, nullable=True)

    action = relationship("Action", back_populates="risk_breakdown")


class GovernanceCase(Base):
    __tablename__ = "governance_cases"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id", ondelete="CASCADE"), unique=True, nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="PENDING")  # PENDING, APPROVED, REJECTED, MODIFIED
    comments = Column(Text, nullable=True)
    conditions_applied = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    action = relationship("Action", back_populates="governance_case")
    reviewer = relationship("User", back_populates="reviewed_cases")
    audit_logs = relationship("AuditLog", back_populates="case")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("governance_cases.id"), nullable=True)
    event_type = Column(String(100), nullable=False)  # SUBMISSION, CONFIRMATION, REVIEW_APPROVAL, etc.
    details = Column(Text, nullable=False)
    ip_address = Column(String(50), nullable=True)

    user = relationship("User", back_populates="audit_logs")
    action = relationship("Action", back_populates="audit_logs")
    case = relationship("GovernanceCase", back_populates="audit_logs")


class HistoryCase(Base):
    __tablename__ = "history_cases"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(50), index=True, nullable=False)
    extracted_action = Column(String(50), index=True, nullable=False)
    extracted_object = Column(String(100), index=True, nullable=False)
    total_cases = Column(Integer, default=0)
    approved_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    average_risk = Column(Float, default=0.0)


class ClarificationQuestion(Base):
    __tablename__ = "clarification_questions"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id", ondelete="CASCADE"), nullable=False)
    parameter_name = Column(String(100), nullable=False)  # e.g., "record_count", "reason"
    question_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    action = relationship("Action", back_populates="clarification_questions")
    answer = relationship("ClarificationAnswer", uselist=False, back_populates="question")


class ClarificationAnswer(Base):
    __tablename__ = "clarification_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("clarification_questions.id", ondelete="CASCADE"), unique=True, nullable=False)
    answer_text = Column(Text, nullable=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    question = relationship("ClarificationQuestion", back_populates="answer")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(100), nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")
