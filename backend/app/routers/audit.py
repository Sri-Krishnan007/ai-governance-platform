import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, User
from app.schemas import AuditLogResponse
from app.auth import get_current_user, RoleChecker

logger = logging.getLogger("app.routers.audit")

router = APIRouter(
    prefix="/audit",
    tags=["Audit Logging"]
)

@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["Administrator"]))
):
    """Retrieve all system audit logs. Administrator only."""
    logger.info(f"Admin '{current_user.username}' requesting system audit logs")
    
    query = db.query(AuditLog)
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type.upper())
        
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
        
    # Order by timestamp descending (newest first)
    logs = query.order_by(AuditLog.timestamp.desc()).all()
    return logs
