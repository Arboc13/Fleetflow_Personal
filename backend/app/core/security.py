import datetime as dt

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

# bcrypt password hashing (NFR-1). pwdlib replaces the deprecated passlib,
# which relies on the stdlib `crypt` module removed in Python 3.13.
_password_hash = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _password_hash.verify(password, hashed)


def create_access_token(
    subject: str, role: str, expires_minutes: int | None = None
) -> str:
    expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
