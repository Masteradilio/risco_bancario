"""Password policy and adaptive hashing."""

from __future__ import annotations

import re

import bcrypt


class PasswordPolicyError(ValueError):
    pass


def validate_password(password: str, *, username: str = "") -> None:
    failures: list[str] = []
    if not 12 <= len(password) <= 128 or len(password.encode()) > 72:
        failures.append("length")
    if not re.search(r"[A-Z]", password):
        failures.append("uppercase")
    if not re.search(r"[a-z]", password):
        failures.append("lowercase")
    if not re.search(r"\d", password):
        failures.append("digit")
    if not re.search(r"[^A-Za-z0-9]", password):
        failures.append("special")
    if username and username.casefold() in password.casefold():
        failures.append("username")
    if failures:
        raise PasswordPolicyError(f"Password policy failed: {', '.join(failures)}")


def hash_password(password: str, *, username: str = "") -> str:
    validate_password(password, username=username)
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bool(bcrypt.checkpw(password.encode(), password_hash.encode()))
    except ValueError:
        return False
