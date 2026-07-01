import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.logging_config import setup_logging
from app.database import check_db_connection, SessionLocal
from app.seed import seed_database

# Initialize logging before FastAPI app
setup_logging()
logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Enterprise AI Governance Platform API...")
    
    # Run database seeding on startup
    if SessionLocal:
        db = SessionLocal()
        try:
            seed_database(db)
        except Exception as e:
            logger.error(f"Failed to seed database during startup: {e}")
        finally:
            db.close()
            
    yield
    logger.info("Shutting down Enterprise AI Governance Platform API...")

from app.routers import auth, actions, cases, audit, history, notifications, analytics, policies
from app.auth import get_current_user, RoleChecker
from app.schemas import UserResponse, UserCreate, TokenResponse
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models import User
from sqlalchemy.orm import Session
from app.database import get_db
from typing import List

app = FastAPI(
    title="Enterprise AI Governance Platform API",
    description="API for evaluating AI actions, managing risk, enforcing policies, and human governance cases.",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def root_register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Root-level register shortcut (Phase 16)."""
    from app.routers.auth import register
    return register(user_in, db)

@app.post("/login", response_model=TokenResponse)
def root_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Root-level login shortcut (Phase 16)."""
    from app.routers.auth import login
    return login(form_data, db)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(actions.router)
app.include_router(cases.router)
app.include_router(audit.router)
app.include_router(history.router)
app.include_router(notifications.router)
app.include_router(analytics.router)
app.include_router(policies.router)

@app.get("/health")
def health_check():
    db_connected = check_db_connection()
    status = "healthy" if db_connected else "unhealthy"
    return {
        "status": status,
        "database": "connected" if db_connected else "disconnected"
    }

@app.get("/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve the current authenticated user's profile."""
    return current_user

@app.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["Administrator"]))
):
    """Retrieve all user accounts (Administrator only)."""
    return db.query(User).all()

