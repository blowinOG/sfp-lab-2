from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from zxcvbn import zxcvbn

from app.config import settings

# Параметры Argon2id по рекомендациям OWASP (минимум для интерактивного логина)
_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


class WeakPasswordError(Exception):
    """Пароль не удовлетворяет политике."""


def _apply_pepper(password: str) -> str:
    return password + settings.password_pepper


def hash_password(password: str) -> str:
    return _hasher.hash(_apply_pepper(password))


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, _apply_pepper(password))
    except (VerifyMismatchError, InvalidHashError):
        return False


def validate_policy(password: str, user_inputs: list[str] | None = None) -> None:
    if len(password) < settings.password_min_length:
        raise WeakPasswordError(
            f"Пароль должен быть не короче {settings.password_min_length} символов"
        )
    result = zxcvbn(password, user_inputs=user_inputs or [])
    if result["score"] < 3:
        raise WeakPasswordError(
            "Пароль слишком слабый (оценка zxcvbn ниже 3 из 4)"
        )