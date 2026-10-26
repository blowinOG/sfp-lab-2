from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.audit.service import write_event
from app.core.deps import get_current_user
from app.core.jwt import create_access_token
from app.core.passwords import (
    WeakPasswordError,
    hash_password,
    validate_policy,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


@router.post("/register", response_model=TokenResponse)
def register(payload: Credentials, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    try:
        validate_policy(payload.password, user_inputs=[payload.email])
    except WeakPasswordError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    ip, ua = _client_meta(request)
    write_event(db, "user.created", actor_id=user.id, ip=ip, user_agent=ua, metadata={"email": user.email})

    return TokenResponse(access_token=create_access_token(sub=user.email))


@router.post("/login", response_model=TokenResponse)
def login(payload: Credentials, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    ip, ua = _client_meta(request)
    user = db.query(User).filter(User.email == payload.email).one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        write_event(db, "user.login.failure", ip=ip, user_agent=ua, metadata={"email": payload.email})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        write_event(db, "user.login.failure", actor_id=user.id, ip=ip, user_agent=ua,
                    metadata={"email": payload.email, "reason": "inactive"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    write_event(db, "user.login.success", actor_id=user.id, ip=ip, user_agent=ua)
    return TokenResponse(access_token=create_access_token(sub=user.email))


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(id=user.id, email=user.email, is_admin=user.is_admin)