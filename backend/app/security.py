import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.token_minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.secret_key, algorithm="HS256")


def create_oauth_state(user_id: int) -> str:
    """Signed, short-lived anti-forgery `state` for the TikTok authorization redirect."""
    exp = datetime.now(timezone.utc) + timedelta(minutes=10)
    return jwt.encode({"sub": str(user_id), "purpose": "tiktok_oauth", "nonce": os.urandom(8).hex(), "exp": exp},
                      settings.secret_key, algorithm="HS256")


def verify_oauth_state(state: str, user_id: int) -> bool:
    try:
        payload = jwt.decode(state, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return False
    return payload.get("purpose") == "tiktok_oauth" and payload.get("sub") == str(user_id)


def default_user(db: Session) -> User:
    """The single local user used when login is disabled. The '!' hash can never match a password."""
    email = settings.default_user_email.lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        try:
            user = User(email=email, name="Me", password_hash="!")
            db.add(user)
            db.commit()
        except IntegrityError:  # concurrent first requests
            db.rollback()
            user = db.query(User).filter(User.email == email).one()
    return user


def current_user(token: str | None = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    if not settings.auth_required:
        return default_user(db)
    err = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    if not token:
        raise err
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise err
    if user is None:
        raise err
    return user
