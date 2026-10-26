from sqlalchemy.orm import Session

from app.core.jwt import decode_token
from app.db.session import SessionLocal
from app.models.user import User


def get_context_value(request, data=None) -> dict:
    """Собирает контекст для каждого GraphQL-запроса.

    Возвращает dict с request, db (SQLAlchemy session) и user (если токен валидный).
    """
    db: Session = SessionLocal()
    user: User | None = None

    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        try:
            payload = decode_token(token)
            if payload.get("typ") == "access":
                user = db.query(User).filter(User.email == payload.get("sub")).one_or_none()
                if user is not None and not user.is_active:
                    user = None
        except ValueError:
            user = None

    return {"request": request, "db": db, "user": user}