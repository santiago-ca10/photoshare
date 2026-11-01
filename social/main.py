"""Servicio social: likes y comentarios."""
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from common.db import cursor
from common.events import invalidate_feed, publish
from common.security import current_user

app = FastAPI(title="PhotoShare - Social")


class CommentIn(BaseModel):
    text: str = Field(min_length=1, max_length=300)

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El comentario no puede estar vacío")
        return value


def _photo_exists(cur, photo_id: int):
    cur.execute("SELECT 1 FROM photos WHERE id = %s", (photo_id,))
    if not cur.fetchone():
        raise HTTPException(404, "La foto no existe")


@app.post("/api/social/photos/{photo_id}/like")
def toggle_like(photo_id: int, user: dict = Depends(current_user)):
    """Alterna el like. La clave primaria (user_id, photo_id) hace la operación
    segura aunque lleguen dos peticiones simultáneas del mismo usuario."""
    with cursor() as cur:
        _photo_exists(cur, photo_id)
        cur.execute(
            "INSERT INTO likes (user_id, photo_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user["id"], photo_id),
        )
        liked = cur.rowcount == 1
        if not liked:
            cur.execute("DELETE FROM likes WHERE user_id = %s AND photo_id = %s", (user["id"], photo_id))
        cur.execute("SELECT COUNT(*) AS n FROM likes WHERE photo_id = %s", (photo_id,))
        total = cur.fetchone()["n"]

    invalidate_feed()
    publish({"type": "like", "user": user["username"], "photo_id": photo_id, "liked": liked})
    return {"liked": liked, "likes": total}


@app.get("/api/social/liked")
def my_likes(user: dict = Depends(current_user)):
    with cursor() as cur:
        cur.execute("SELECT photo_id FROM likes WHERE user_id = %s", (user["id"],))
        return {"photo_ids": [r["photo_id"] for r in cur.fetchall()]}


@app.get("/api/social/photos/{photo_id}/comments")
def list_comments(photo_id: int):
    with cursor() as cur:
        _photo_exists(cur, photo_id)
        cur.execute(
            """SELECT c.id, c.text, u.username, c.created_at::text AS created_at
               FROM comments c JOIN users u ON u.id = c.user_id
               WHERE c.photo_id = %s ORDER BY c.id""",
            (photo_id,),
        )
        return {"comments": cur.fetchall()}


@app.post("/api/social/photos/{photo_id}/comments", status_code=201)
def add_comment(photo_id: int, body: CommentIn, user: dict = Depends(current_user)):
    with cursor() as cur:
        _photo_exists(cur, photo_id)
        cur.execute(
            "INSERT INTO comments (photo_id, user_id, text) VALUES (%s, %s, %s)",
            (photo_id, user["id"], body.text.strip()),
        )
    invalidate_feed()
    publish({"type": "comment", "user": user["username"], "photo_id": photo_id})
    return {"ok": True}
