# 6. Despliegue y pruebas

## Requisitos
Docker Engine y Docker Compose v2 (Docker Desktop en Windows y macOS). Puerto `8080` libre.

## Ejecución
```bash
docker compose up --build        # primera vez (1-2 minutos)
docker compose up -d             # en segundo plano
docker compose ps                # estado de los 8 contenedores
docker compose logs -f photos1 photos2
docker compose down              # apaga y conserva los datos
docker compose down -v           # apaga y BORRA base de datos y fotos
```
Aplicación: http://localhost:8080

## Contenedores
| Contenedor | Imagen | Puerto interno |
|---|---|---|
| nginx | `nginx:alpine` | 80 → publicado como 8080 |
| auth, photos1, photos2, social, notifications | construidas con `python:3.12-slim` | 8000 |
| db | `postgres:16` | 5432 |
| redis | `redis:7-alpine` | 6379 |

Los servicios se encuentran por nombre dentro de la red de Compose (`db`, `redis`, `auth`...), nunca por `localhost`.

## Plan de pruebas

> Cada prueba indica la **captura** sugerida (ver [`images/README.md`](images/README.md)).

### P1. Balanceo de carga
1. Con el feed abierto, recarga varias veces (F5).
2. **Esperado:** el indicador de la barra superior alterna entre `photos-1` y `photos-2`.
3. Alternativa por consola: `for i in 1 2 3 4; do curl -s localhost:8080/api/photos/feed | grep -o '"served_by":"[^"]*"'; done`
4. Captura: `03-balanceo-replicas.png`.

### P2. Caché del feed
1. Recarga: el indicador dice `· caché`.
2. Sube una foto o da un like: la siguiente carga dice `· BD` (la caché se invalidó) y luego vuelve a `· caché`.
3. Captura: `04-cache.png`.

### P3. Tolerancia a fallos de una réplica
```bash
docker compose stop photos1
# recargar el feed varias veces: siempre responde photos-2
docker compose start photos1
```
**Esperado:** el sistema sigue funcionando sin errores visibles. Capturas: `05-fallo-photos1.png` (terminal + navegador).

### P4. Tolerancia a la caída de Redis
```bash
docker compose stop redis
```
**Esperado:** el feed sigue cargando (siempre `· BD`); no llegan avisos en tiempo real. `docker compose start redis` lo restablece (el servicio de Notificaciones se reconecta solo). Captura: `06-fallo-redis.png`.

### P5. Tiempo real (WebSocket)
Abre dos navegadores (uno en modo incógnito) con usuarios distintos. Al subir, comentar, dar like o eliminar en uno, el otro recibe un aviso y su feed se actualiza. Captura: `07-tiempo-real.png`.

### P6. Concurrencia de likes
```bash
# 20 peticiones simultáneas del mismo usuario
for i in $(seq 1 20); do
  curl -s -X POST localhost:8080/api/social/photos/1/like -H "Authorization: Bearer $TOKEN" > /dev/null &
done; wait
docker compose exec db psql -U app -d photoshare -c "SELECT COUNT(*) FROM likes WHERE photo_id = 1;"
```
**Esperado:** el conteo es 0 o 1; nunca hay duplicados ni errores de integridad. Captura: `08-concurrencia.png`.

### P7. Autorización al eliminar
1. Con el usuario A, publica una foto. Con el usuario B comprueba que **no** aparece el icono 🗑 en esa foto.
2. Intento directo: `curl -X DELETE localhost:8080/api/photos/1 -H "Authorization: Bearer $TOKEN_B"` → `403`.
3. Elimina con el usuario A: la foto desaparece y también sus likes y comentarios.

### P8. Persistencia
`docker compose down` seguido de `docker compose up -d`: los usuarios y fotos siguen ahí. Con `down -v` quedan en cero.

### P9. Validaciones
- Subir un `.pdf` → `415`; imagen de más de 5 MB → `413`; dar like sin sesión → `401`; registrar usuario repetido → `409`.

## Solución de problemas
| Síntoma | Causa probable | Solución |
|---|---|---|
| `port is already allocated` | El puerto 8080 está en uso | Cambiar `"8080:80"` en `docker-compose.yml` |
| Las tablas no existen | El volumen `pgdata` ya existía con otro esquema | `docker compose down -v` y volver a levantar |
| Nginx no inicia (`host not found`) | Un servicio no arrancó | `docker compose logs <servicio>` |
| La imagen no se ve tras subirla | Volumen `uploads` sin permisos | `docker compose down -v` y reintentar |
| Sin avisos en tiempo real | Redis o Notificaciones caídos | `docker compose ps` y `docker compose logs notifications` |
