from datetime import datetime, timedelta, timezone
import jwt
from flask import current_app


def create_jwt(user_id: int, role: str) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)

    expires_minutes = current_app.config.get("JWT_EXPIRES_MINUTES", 60)
    secret = current_app.config.get("JWT_SECRET_KEY", "change-me-in-env")

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token: str) -> dict:
    """Decode and validate a JWT token."""
    secret = current_app.config.get("JWT_SECRET_KEY", "change-me-in-env")
    return jwt.decode(token, secret, algorithms=["HS256"])