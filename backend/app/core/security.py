"""Password hashing and opaque token helpers."""

import hashlib
import hmac
import secrets
from functools import lru_cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings


@lru_cache
def _hasher() -> PasswordHasher:
    if get_settings().password_hash_profile == "fast-test":
        # Only for automated tests: keeps seeding fast. Rejected in production by config validation.
        return PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1)
    return PasswordHasher()  # argon2id with library-recommended parameters


@lru_cache
def _dummy_hash() -> str:
    return _hasher().hash(secrets.token_hex(16))


def hash_password(password: str) -> str:
    return _hasher().hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    """Constant-shape verification: unknown accounts still pay the hashing cost."""
    try:
        return _hasher().verify(password_hash or _dummy_hash(), password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher().check_needs_rehash(password_hash)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def tokens_match(token: str, digest: str) -> bool:
    return hmac.compare_digest(token_digest(token), digest)


def identifier_digest(school_id: str, login_id: str) -> str:
    return hashlib.sha256(f"{school_id}:{login_id}".encode()).hexdigest()
