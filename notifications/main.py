"""Servicio de notificaciones en tiempo real: Redis Pub/Sub -> WebSocket."""
import asyncio
import os
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

clients: set[WebSocket] = set()


async def listen_redis():
    while True:  # reintenta si Redis se cae
        try:
            r = aioredis.from_url(os.environ["REDIS_URL"])
            pubsub = r.pubsub()
            await pubsub.subscribe("eventos")
            async for msg in pubsub.listen():
                if msg["type"] != "message":
                    continue
                text = msg["data"].decode()
                for ws in list(clients):
                    try:
                        await ws.send_text(text)
                    except Exception:
                        clients.discard(ws)
        except Exception:
            await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(listen_redis())
    yield
    task.cancel()


app = FastAPI(title="PhotoShare - Notifications", lifespan=lifespan)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()  # mantiene la conexión abierta
    except WebSocketDisconnect:
        clients.discard(ws)
