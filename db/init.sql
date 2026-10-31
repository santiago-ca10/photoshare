CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS photos (
    id         SERIAL PRIMARY KEY,
    user_id    INT NOT NULL REFERENCES users(id),
    filename   TEXT NOT NULL,
    caption    TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- La clave primaria compuesta evita likes duplicados aunque dos
-- peticiones lleguen al mismo tiempo (control de concurrencia en la BD).
CREATE TABLE IF NOT EXISTS likes (
    user_id    INT NOT NULL REFERENCES users(id),
    photo_id   INT NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, photo_id)
);

CREATE TABLE IF NOT EXISTS comments (
    id         SERIAL PRIMARY KEY,
    photo_id   INT NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    user_id    INT NOT NULL REFERENCES users(id),
    text       TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_photos_created ON photos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_photo ON comments(photo_id);
