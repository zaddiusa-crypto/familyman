import os
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    sub: str
    role: str
    lodge_id: str
    exp: int
    iat: int
    type: str = "access"
    jti: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def load_private_key() -> bytes:
    return settings.JWT_PRIVATE_KEY.encode()


def load_public_key() -> bytes:
    return settings.JWT_PUBLIC_KEY.encode()


def create_access_token(
    subject: str,
    role: str,
    lodge_id: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str]:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    iat = datetime.now(UTC)
    jti = os.urandom(16).hex()

    claims = {
        "sub": subject,
        "role": role,
        "lodge_id": lodge_id,
        "exp": int(expire.timestamp()),
        "iat": int(iat.timestamp()),
        "type": "access",
        "jti": jti,
    }
    if extra_claims:
        claims.update(extra_claims)

    private_key = load_private_key()
    encoded = jwt.encode(claims, private_key, algorithm=settings.JWT_ALGORITHM)
    return encoded, jti


def create_refresh_token(subject: str, role: str, lodge_id: str) -> tuple[str, str]:
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    iat = datetime.now(UTC)
    jti = os.urandom(16).hex()

    claims = {
        "sub": subject,
        "role": role,
        "lodge_id": lodge_id,
        "exp": int(expire.timestamp()),
        "iat": int(iat.timestamp()),
        "type": "refresh",
        "jti": jti,
    }

    private_key = load_private_key()
    encoded = jwt.encode(claims, private_key, algorithm=settings.JWT_ALGORITHM)
    return encoded, jti


def create_token_pair(user_id: str, role: str, lodge_id: str) -> TokenPair:
    access_token, access_jti = create_access_token(user_id, role, lodge_id)
    refresh_token, refresh_jti = create_refresh_token(user_id, role, lodge_id)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def decode_token(token: str) -> TokenPayload:
    try:
        public_key = load_public_key()
        payload = jwt.decode(token, public_key, algorithms=[settings.JWT_ALGORITHM])
        return TokenPayload(**payload)
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")


def decode_token_unsafe(token: str) -> dict:
    try:
        public_key = load_public_key()
        return jwt.decode(token, public_key, algorithms=[settings.JWT_ALGORITHM], options={"verify_exp": False})
    except JWTError:
        return {}


def generate_rsa_keys() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem.decode(), public_pem.decode()
