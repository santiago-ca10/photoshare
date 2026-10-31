"""Redis: caché del feed y publicación de eventos (Pub/Sub).
Si Redis falla, el sistema sigue funcionando sin caché (degradación elegante)."""
import json
import os

import redis

_r = redis.from_url(os.environ["REDIS_URL"], socket_timeout=2)

FEED_KEY = "feed"
FEED_TTL = 30  # segundos


def cache_get(key):
    try:
        return _r.get(key)
    except Exception:
        return None


def cache_set(key, value, ttl=FEED_TTL):
    try:
        _r.setex(key, ttl, value)
    except Exception:
        pass


def invalidate_feed():
    try:
        _r.delete(FEED_KEY)
    except Exception:
        pass


def publish(event: dict):
    try:
        _r.publish("eventos", json.dumps(event))
    except Exception:
        pass
