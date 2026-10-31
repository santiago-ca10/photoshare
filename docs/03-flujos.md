# 3. Flujos del sistema

Versión en imagen (para Word/PDF): [`images/`](images/) contiene un `flujo-*.png` por cada flujo.

| Flujo | Imagen |
|---|---|
| Registro | ![registro](images/flujo-registro.png) |
| Subir foto | ![subir](images/flujo-subir-foto.png) |
| Feed | ![feed](images/flujo-feed.png) |
| Like | ![like](images/flujo-like.png) |
| Eliminar | ![eliminar](images/flujo-eliminar.png) |
| Tiempo real | ![tiempo real](images/flujo-tiempo-real.png) |
| Caída de réplica | ![caida](images/flujo-caida-replica.png) |

Los diagramas se renderizan automáticamente en GitHub, GitLab y VS Code (extensión Markdown Mermaid).

## 3.1 Registro e inicio de sesión
```mermaid
sequenceDiagram
  actor U as Navegador
  participant N as Nginx
  participant A as Auth
  participant P as PostgreSQL
  U->>N: POST /api/auth/register {usuario, contraseña}
  N->>A: enruta
  A->>A: PBKDF2 (hash + sal)
  A->>P: INSERT INTO users
  P-->>A: id (o error de usuario duplicado)
  A-->>U: 201 {token JWT, username}
  Note over U: guarda el token y lo envía como Bearer
```

## 3.2 Subir una foto
```mermaid
sequenceDiagram
  actor U as Navegador
  participant N as Nginx
  participant F as Fotos (réplica 1 o 2)
  participant V as Volumen uploads
  participant P as PostgreSQL
  participant R as Redis
  participant W as Notificaciones
  U->>N: POST /api/photos (multipart + JWT)
  N->>F: round-robin
  F->>F: valida JWT, tipo MIME y tamaño (≤ 5 MB)
  F->>V: guarda archivo con nombre UUID
  F->>P: INSERT INTO photos
  F->>R: DEL feed (invalida caché)
  F->>R: PUBLISH eventos {type: photo}
  F-->>U: 201 {id, filename, served_by}
  R-->>W: evento
  W-->>U: WebSocket a los demás navegadores
```

## 3.3 Ver el feed (con caché)
```mermaid
sequenceDiagram
  actor U as Navegador
  participant N as Nginx
  participant F as Fotos
  participant R as Redis
  participant P as PostgreSQL
  U->>N: GET /api/photos/feed
  N->>F: round-robin
  F->>R: GET feed
  alt acierto de caché
    R-->>F: JSON del feed
    F-->>U: {served_by, cached: true, photos}
  else fallo de caché
    F->>P: SELECT (fotos + likes + comentarios)
    P-->>F: filas
    F->>R: SETEX feed 30 s
    F-->>U: {served_by, cached: false, photos}
  end
  U->>N: GET /uploads/<archivo> (Nginx lo sirve del volumen)
```

## 3.4 Dar like (concurrencia)
```mermaid
sequenceDiagram
  actor U as Navegador
  participant N as Nginx
  participant S as Social
  participant P as PostgreSQL
  participant R as Redis
  U->>N: POST /api/social/photos/{id}/like
  N->>S: enruta
  S->>S: valida JWT
  S->>P: INSERT likes ON CONFLICT DO NOTHING
  alt filas insertadas = 1
    Note over S: like nuevo
  else ya existía
    S->>P: DELETE (quita el like)
  end
  S->>P: SELECT COUNT(*)
  S->>R: DEL feed + PUBLISH eventos
  S-->>U: {liked, likes}
```

## 3.5 Eliminar una foto
```mermaid
sequenceDiagram
  actor U as Navegador
  participant N as Nginx
  participant F as Fotos
  participant P as PostgreSQL
  participant V as Volumen
  participant R as Redis
  U->>N: DELETE /api/photos/{id} (JWT)
  N->>F: round-robin
  F->>P: SELECT user_id, filename
  alt no es el autor
    F-->>U: 403
  else es el autor
    F->>P: DELETE photos (likes y comentarios en cascada)
    F->>V: elimina el archivo
    F->>R: DEL feed + PUBLISH {type: delete}
    F-->>U: 200
  end
```

## 3.6 Avisos en tiempo real
```mermaid
sequenceDiagram
  actor U1 as Navegador de Ana
  actor U2 as Navegador de Luis
  participant W as Notificaciones
  participant R as Redis
  participant F as Fotos / Social
  U1->>W: WebSocket /ws (conexión abierta)
  U2->>W: WebSocket /ws (conexión abierta)
  W->>R: SUBSCRIBE eventos
  F->>R: PUBLISH {type, user, photo_id}
  R-->>W: mensaje
  W-->>U1: reenvía el evento
  W-->>U2: reenvía el evento
  Note over U1,U2: el cliente ignora los eventos propios, muestra un aviso y recarga el feed
```

## 3.7 Caída de una réplica
```mermaid
sequenceDiagram
  actor U as Navegador
  participant N as Nginx
  participant F1 as photos1 (caída)
  participant F2 as photos2
  U->>N: GET /api/photos/feed
  N->>F1: intenta
  F1--xN: sin respuesta (conexión rechazada)
  Note over N: marca photos1 como caída durante 10 s
  N->>F2: reintenta
  F2-->>U: respuesta normal (served_by: photos-2)
```
