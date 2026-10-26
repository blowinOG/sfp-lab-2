import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Переменные окружения ДО импорта приложения
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test_jwt_secret_abcdefghijklmnop")
os.environ.setdefault("PASSWORD_PEPPER", "test_pepper_abcdefghijklmnop")
os.environ.setdefault("PASSWORD_MIN_LENGTH", "12")

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Патчим SessionLocal, чтобы GraphQL-контекст ходил в тестовую БД
    import app.graphql.context as ctx
    original = ctx.SessionLocal
    ctx.SessionLocal = TestingSessionLocal

    with TestClient(app) as c:
        yield c

    ctx.SessionLocal = original
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def strong_password():
    return "Correct-Horse-Battery-Staple-9!"


@pytest.fixture()
def registered_user(client, strong_password):
    resp = client.post("/auth/register", json={"email": "a@example.com", "password": strong_password})
    assert resp.status_code == 200, resp.text
    return {"email": "a@example.com", "password": strong_password, "token": resp.json()["access_token"]}