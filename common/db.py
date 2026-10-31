"""Acceso a PostgreSQL con pool de conexiones."""
import os
import time
from contextlib import contextmanager

from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        for _ in range(30):  # espera a que la BD esté lista
            try:
                _pool = ThreadedConnectionPool(1, 10, os.environ["DB_URL"])
                break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("No se pudo conectar a PostgreSQL")
    return _pool


@contextmanager
def cursor():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)
