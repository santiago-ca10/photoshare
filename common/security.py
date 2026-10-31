"""Contraseñas (PBKDF2) y tokens JWT compartidos por los servicios."""
import hashlib
import hmac
import os
import secrets
import time

import jwt
from fastapi import Header, HTTPException

SECRET = os.environ.get("JWT_SECRET", "dev-secret")


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    salt, _ = stored.split("$")
    return hmac.compare_digest(hash_password(password, salt), stored)


def make_token(user_id: int, username: str) -> str:
    payload = {"sub": str(user_id), "username": username, "exp": int(time.time()) + 86400}
    return jwt.encode(payload, SECRET, algorithm="HS256")


def current_user(authorization: str = Header(default="")) -> dict:
    """Dependencia de FastAPI: valida el token Bearer sin consultar a otro servicio."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Inicia sesión para continuar")
    try:
        data = jwt.decode(authorization[7:], SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Sesión inválida o vencida")
    return {"id": int(data["sub"]), "username": data["username"]}
