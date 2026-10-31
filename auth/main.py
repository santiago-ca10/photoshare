"""Servicio de autenticación: registro, login y datos del usuario."""
from fastapi import Depends, FastAPI, HTTPException
from psycopg2.errors import UniqueViolation
from pydantic import BaseModel, Field

from common.db import cursor
from common.security import current_user, hash_password, make_token, verify_password

app = FastAPI(title="PhotoShare - Auth")


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=4, max_length=100)


@app.post("/api/auth/register", status_code=201)
def register(c: Credentials):
    try:
        with cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                (c.username, hash_password(c.password)),
            )
            uid = cur.fetchone()["id"]
    except UniqueViolation:
        raise HTTPException(409, "Ese nombre de usuario ya existe")
    return {"token": make_token(uid, c.username), "username": c.username}


@app.post("/api/auth/login")
def login(c: Credentials):
    with cursor() as cur:
        cur.execute("SELECT id, password_hash FROM users WHERE username = %s", (c.username,))
        row = cur.fetchone()
    if not row or not verify_password(c.password, row["password_hash"]):
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    return {"token": make_token(row["id"], c.username), "username": c.username}


@app.get("/api/auth/me")
def me(user: dict = Depends(current_user)):
    return user
