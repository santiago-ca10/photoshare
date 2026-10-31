# 4. Referencia de la API

Base: `http://localhost:8080`. Las rutas protegidas exigen la cabecera `Authorization: Bearer <token>`.
Los errores devuelven `{"detail": "mensaje"}`.

## Auth (`/api/auth`)
| Método | Ruta | Auth | Cuerpo | Respuesta |
|---|---|---|---|---|
| POST | `/api/auth/register` | No | `{"username","password"}` | `201 {"token","username"}` |
| POST | `/api/auth/login` | No | `{"username","password"}` | `200 {"token","username"}` |
| GET | `/api/auth/me` | Sí | - | `200 {"id","username"}` |

Reglas: usuario de 3 a 30 caracteres (`A-Z a-z 0-9 _`); contraseña de 4 a 100.

## Fotos (`/api/photos`)
| Método | Ruta | Auth | Cuerpo | Respuesta |
|---|---|---|---|---|
| GET | `/api/photos/feed` | No | - | `{"served_by","cached","photos":[{id, filename, caption, username, created_at, likes, comments}]}` |
| POST | `/api/photos` | Sí | `multipart/form-data`: `file`, `caption` (≤ 200) | `201 {"id","filename","served_by"}` |
| DELETE | `/api/photos/{id}` | Sí (solo el autor) | - | `200 {"ok":true}` |

Formatos: JPG, PNG, GIF, WEBP. Tamaño máximo: 5 MB. El feed devuelve las 30 fotos más recientes.

## Social (`/api/social`)
| Método | Ruta | Auth | Cuerpo | Respuesta |
|---|---|---|---|---|
| POST | `/api/social/photos/{id}/like` | Sí | - | `{"liked","likes"}` (alterna) |
| GET | `/api/social/liked` | Sí | - | `{"photo_ids":[...]}` |
| GET | `/api/social/photos/{id}/comments` | No | - | `{"comments":[{id, text, username, created_at}]}` |
| POST | `/api/social/photos/{id}/comments` | Sí | `{"text"}` (1-300) | `201 {"ok":true}` |

## WebSocket
`ws://localhost:8080/ws`: solo recibe mensajes del servidor, con la forma:
```json
{"type": "photo | like | comment | delete", "user": "ana", "photo_id": 7, "liked": true}
```
(`liked` solo aparece en eventos `like`.)

## Códigos de error
| Código | Significado |
|---|---|
| 401 | Falta el token o es inválido/vencido |
| 403 | Intento de eliminar una foto ajena |
| 404 | La foto no existe |
| 409 | El nombre de usuario ya existe |
| 413 | Imagen mayor a 5 MB |
| 415 | Tipo de archivo no permitido |
| 422 | Datos con formato inválido |

## Ejemplo con curl
```bash
# Registrar y guardar el token
TOKEN=$(curl -s -X POST localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ana","password":"1234"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

# Subir foto
curl -X POST localhost:8080/api/photos -H "Authorization: Bearer $TOKEN" \
  -F "file=@foto.jpg" -F "caption=Mi primera foto"

# Ver feed y dar like
curl localhost:8080/api/photos/feed
curl -X POST localhost:8080/api/social/photos/1/like -H "Authorization: Bearer $TOKEN"
```
