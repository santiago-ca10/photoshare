"""Servicio de fotos (se ejecuta en 2 réplicas detrás de Nginx)."""
import json
import os
import socket
import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile

from common.db import cursor
from common.events import FEED_KEY, cache_get, cache_set, invalidate_feed, publish
from common.security import current_user

app = FastAPI(title="PhotoShare - Photos")

UPLOADS = "/data/uploads"
MAX_BYTES = 5 * 1024 * 1024
EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}
REPLICA = os.environ.get("REPLICA_NAME", socket.gethostname())

os.makedirs(UPLOADS, exist_ok=True)

FEED_SQL = """
SELECT p.id, p.filename, p.caption, u.username, p.created_at::text AS created_at,
       (SELECT COUNT(*) FROM likes    l WHERE l.photo_id = p.id) AS likes,
       (SELECT COUNT(*) FROM comments c WHERE c.photo_id = p.id) AS comments
FROM photos p JOIN users u ON u.id = p.user_id
ORDER BY p.id DESC LIMIT 30
"""


@app.get("/api/photos/feed")
def feed():
    cached = cache_get(FEED_KEY)
    if cached:
        return {"served_by": REPLICA, "cached": True, "photos": json.loads(cached)}
    with cursor() as cur:
        cur.execute(FEED_SQL)
        photos = cur.fetchall()
    cache_set(FEED_KEY, json.dumps(photos))
    return {"served_by": REPLICA, "cached": False, "photos": photos}


@app.post("/api/photos", status_code=201)
def upload(
    file: UploadFile = File(...),
    caption: str = Form(default="", max_length=200),
    user: dict = Depends(current_user),
):
    if file.content_type not in EXT:
        raise HTTPException(415, "Solo se aceptan imágenes JPG, PNG, GIF o WEBP")
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "La imagen supera los 5 MB")

    filename = uuid.uuid4().hex + EXT[file.content_type]
    with open(os.path.join(UPLOADS, filename), "wb") as f:
        f.write(data)

    with cursor() as cur:
        cur.execute(
            "INSERT INTO photos (user_id, filename, caption) VALUES (%s, %s, %s) RETURNING id",
            (user["id"], filename, caption.strip()),
        )
        photo_id = cur.fetchone()["id"]

    invalidate_feed()
    publish({"type": "photo", "user": user["username"], "photo_id": photo_id})
    return {"id": photo_id, "filename": filename, "served_by": REPLICA}


@app.delete("/api/photos/{photo_id}")
def delete_photo(photo_id: int, user: dict = Depends(current_user)):
    """Elimina una foto propia. Los likes y comentarios se borran en cascada (FK)."""
    with cursor() as cur:
        cur.execute("SELECT user_id, filename FROM photos WHERE id = %s", (photo_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "La foto no existe")
        if row["user_id"] != user["id"]:
            raise HTTPException(403, "Solo puedes eliminar tus propias fotos")
        cur.execute("DELETE FROM photos WHERE id = %s", (photo_id,))
    try:  # el volumen es compartido, así que cualquier réplica puede borrar el archivo
        os.remove(os.path.join(UPLOADS, row["filename"]))
    except FileNotFoundError:
        pass
    invalidate_feed()
    publish({"type": "delete", "user": user["username"], "photo_id": photo_id})
    return {"ok": True, "served_by": REPLICA}
