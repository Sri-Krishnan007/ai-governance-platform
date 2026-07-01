import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import HistoryCase, User
from app.schemas import HistoryCaseResponse
from app.auth import get_current_user

logger = logging.getLogger("app.routers.history")

router = APIRouter(
    prefix="/history",
    tags=["History"]
)

@router.get("", response_model=List[HistoryCaseResponse])
def get_history_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all historical guideline and action aggregates (Phase 16)."""
    logger.info(f"User '{current_user.username}' requesting historical aggregates list")
    
    cases = db.query(HistoryCase).order_by(HistoryCase.id.asc()).all()
    return cases
