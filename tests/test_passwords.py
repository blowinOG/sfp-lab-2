import pytest

from app.core.passwords import (
    WeakPasswordError,
    hash_password,
    validate_policy,
    verify_password,
)


def test_weak_password_rejected():
    with pytest.raises(WeakPasswordError):
        validate_policy("short", user_inputs=["x"])


def test_strong_password_accepted(strong_password):
    validate_policy(strong_password, user_inputs=["a@example.com"])


def test_hash_and_verify(strong_password):
    h = hash_password(strong_password)
    assert verify_password(strong_password, h) is True
    assert verify_password("wrong-password", h) is False