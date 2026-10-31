# 1. Conceptos básicos

## ¿Qué es un sistema distribuido?
Un conjunto de computadores (o procesos) **independientes** que se comunican por una red y se presentan al usuario como **un solo sistema coherente**. En PhotoShare, cada servicio corre en su propio contenedor y el usuario solo ve una aplicación web.

## Conceptos clave y dónde aparecen en PhotoShare

| Concepto | Definición | En PhotoShare |
|---|---|---|
| **Transparencia** | El usuario no sabe cuántos servidores hay ni cuál lo atiende | Nginx oculta las réplicas; la interfaz sólo habla con `localhost:8080` |
| **Escalabilidad horizontal** | Atender más carga agregando más instancias | Servicio de Fotos en 2 réplicas (`photos1`, `photos2`) |
| **Balanceo de carga** | Repartir las peticiones entre instancias | Nginx `upstream` con round-robin |
| **Tolerancia a fallos** | Seguir funcionando aunque falle un componente | Si cae una réplica, Nginx usa la otra; si cae Redis, el feed funciona sin caché |
| **Replicación** | Varias copias del mismo servicio o dato | Réplicas del servicio de Fotos |
| **Concurrencia** | Varias operaciones simultáneas sobre un mismo recurso | Likes simultáneos protegidos por clave primaria `(user_id, photo_id)` |
| **Caché** | Guardar resultados costosos para responder rápido | Feed en Redis (TTL 30 s e invalidación al cambiar datos) |
| **Mensajería Pub/Sub** | Los servicios publican eventos y otros se suscriben | Canal `eventos` de Redis → servicio de Notificaciones |
| **Tiempo real** | El servidor empuja datos al cliente sin que este pregunte | WebSocket `/ws` |
| **Microservicios** | Aplicación dividida en servicios pequeños e independientes | `auth`, `photos`, `social`, `notifications` |

## Protocolos de comunicación
- **TCP/IP:** base de todo el tráfico (conexiones confiables entre navegador, Nginx, servicios, PostgreSQL y Redis).
- **HTTP/REST:** peticiones y respuestas JSON entre navegador y servicios (verbos GET, POST, DELETE).
- **WebSocket:** canal bidireccional persistente sobre HTTP para avisos en vivo.
- **Protocolos propios de las bases de datos:** PostgreSQL (SQL) y Redis (comandos y Pub/Sub).

## Teorema CAP
En presencia de una partición de red, un sistema debe elegir entre **consistencia** y **disponibilidad**.
- PhotoShare usa una única base de datos PostgreSQL como fuente de verdad: favorece **consistencia** en likes, comentarios y usuarios.
- El feed en caché es **eventualmente consistente** (puede estar desactualizado hasta 30 s, aunque se invalida en cada cambio).
- Si Redis falla, se prioriza la **disponibilidad**: el sistema sigue respondiendo sin caché.

## Concurrencia: ¿qué pasa si dos usuarios dan like a la vez?
Cada like es una fila `(user_id, photo_id)` con clave primaria compuesta. PostgreSQL serializa los conflictos: la instrucción `INSERT ... ON CONFLICT DO NOTHING` nunca crea duplicados, y el contador se calcula con `COUNT(*)`, así que **no existe un contador compartido que se pueda corromper**.

## Aplicaciones en la vida real

| Sistema | Qué ejemplifica |
|---|---|
| **Instagram / Flickr** | Almacenamiento distribuido de imágenes, CDN, feeds en caché |
| **Netflix / Spotify** | Microservicios, replicación geográfica, recomendaciones |
| **Google Photos / Dropbox** | Sincronización y almacenamiento replicado |
| **WhatsApp** | Mensajería en tiempo real a gran escala (conexiones persistentes) |
| **Amazon** | Servicios independientes, sistemas de recomendación distribuidos |
| **Bancos y sistemas de pago** | Consistencia estricta y tolerancia a fallos |

## Ventajas y desventajas

| Ventajas | Desventajas |
|---|---|
| Escalabilidad horizontal | Mayor complejidad de diseño, depuración y despliegue |
| Tolerancia a fallos y alta disponibilidad | Latencia de red entre componentes |
| Servicios desarrollables y desplegables por separado | Consistencia de datos más difícil de garantizar |
| Reparto de carga y mejor rendimiento | Más superficie de ataque (seguridad) |
| Uso flexible de tecnologías por servicio | Mayor costo operativo y necesidad de monitoreo |
| Aislamiento: un fallo no tumba todo | Fallos parciales y difíciles de reproducir |
