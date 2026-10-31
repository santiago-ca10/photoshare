# Imágenes y capturas

## Incluido (listo para usar)
Cada imagen viene en **SVG** (vectorial, para GitHub/web) y **PNG** (para Word, PDF y presentaciones).

| Imagen | Qué muestra |
|---|---|
| `arquitectura` | Vista general: capas, servicios, datos y Docker |
| `flujo-registro` | Registro e inicio de sesión (JWT) |
| `flujo-subir-foto` | Subida de foto, caché y aviso en vivo |
| `flujo-feed` | Feed con caché Redis y consulta a PostgreSQL |
| `flujo-like` | Like y control de concurrencia |
| `flujo-eliminar` | Eliminación de una foto propia |
| `flujo-tiempo-real` | Eventos por Redis Pub/Sub y WebSocket |
| `flujo-caida-replica` | Tolerancia a fallos: cae photos-1 y responde photos-2 |

## Capturas opcionales de la aplicación en ejecución
Son evidencia de las pruebas (no son de arquitectura); útiles para el informe y el video, pero no obligatorias.


Guárdalas en esta carpeta con estos nombres y úsalas en el informe PDF y en el video.
Consejo: usa el navegador a pantalla completa (o 1280 px de ancho), tema claro y la ventana de terminal con letra grande.

| Archivo | Qué debe verse | Cuándo tomarla |
|---|---|---|
| `01-login.png` | Pantalla de entrada (pestañas Entrar / Crear cuenta) | Antes de iniciar sesión |
| `02-feed.png` | Feed con 4 o más fotos, likes, comentarios y la barra superior | Después de subir varias fotos |
| `03-balanceo-replicas.png` | Dos capturas juntas de la barra superior: una con `photos-1` y otra con `photos-2` | Recargando el feed (P1) |
| `04-cache.png` | Indicador `· caché` y luego `· BD` tras un cambio | Prueba P2 |
| `05-fallo-photos1.png` | Terminal con `docker compose stop photos1` y el navegador funcionando con `photos-2` | Prueba P3 |
| `06-fallo-redis.png` | Terminal con `docker compose stop redis` y el feed cargando en `· BD` | Prueba P4 |
| `07-tiempo-real.png` | Dos navegadores lado a lado, uno con el aviso emergente | Prueba P5 |
| `08-concurrencia.png` | Terminal con los 20 `curl` y el `COUNT(*)` resultante | Prueba P6 |
| `09-subir-foto.png` | Panel de subida con vista previa de la imagen | Antes de publicar |
| `10-eliminar.png` | Diálogo de confirmación "¿Eliminar esta foto?" | Al pulsar 🗑 |
| `11-docker-ps.png` | Salida de `docker compose ps` con los 8 contenedores | Con el sistema arriba |
| `12-base-de-datos.png` | Salida de `psql` con las tablas o un `SELECT` | Cualquier momento |
| `13-arquitectura-html.png` | La página `docs/arquitectura.html` en el navegador | Para el informe |

## Cómo incluirlas en la documentación
```markdown
![Feed de PhotoShare](images/02-feed.png)
```
