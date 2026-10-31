# 7. Limitaciones, mejoras y preparación para la sustentación

## Puntos únicos de falla (SPOF)
| Componente | Impacto si cae | Mejora propuesta |
|---|---|---|
| Nginx | Todo el sistema inaccesible | Varias instancias de Nginx + balanceador externo o Keepalived |
| PostgreSQL | No hay login, fotos, likes ni comentarios | Replicación primaria/secundaria (Patroni) |
| Volumen `uploads` | No se pueden subir ni ver imágenes | Almacenamiento de objetos (MinIO / S3) con réplicas |
| Auth, Social, Notificaciones | Se pierde esa función | Más réplicas (como Fotos) |

## Limitaciones conocidas
- Base de datos y volumen compartidos por todos los servicios (simplificación académica).
- Un solo Redis sin persistencia ni réplica.
- El JWT usa un secreto compartido en el `docker-compose.yml` (en producción: variables secretas o un gestor de secretos).
- No hay HTTPS, límite de peticiones (rate limiting) ni monitoreo.
- El feed carga las 30 fotos más recientes, sin paginación.
- Nginx solo reintenta automáticamente peticiones idempotentes: si una réplica cae justo en medio de un POST, el cliente puede ver un error y reintentar.
- Las pruebas son manuales; no hay pruebas automatizadas.

## Mejoras futuras
Kubernetes (Deployments, Services, HPA para autoescalado), miniaturas de imágenes, paginación o scroll infinito, un servicio de recomendación, observabilidad (Prometheus + Grafana, logs centralizados), HTTPS, CDN para las imágenes, y una base de datos por servicio con eventos para sincronizarlas.

## Preguntas frecuentes en la sustentación

**¿Por qué es un sistema distribuido y no una aplicación normal?**
Porque está dividido en procesos independientes (contenedores) que se comunican por red, con réplicas, y el usuario percibe un único sistema.

**¿Qué pasa si dos usuarios dan like al mismo tiempo?**
La clave primaria `(user_id, photo_id)` y `ON CONFLICT DO NOTHING` lo manejan en la base de datos. El contador se calcula con `COUNT(*)`, así que no hay un valor compartido que se pueda corromper.

**¿Por qué usar Redis y no solo la base de datos?**
Para reducir la latencia y la carga de lectura del feed (caché en memoria) y para repartir eventos entre servicios con Pub/Sub.

**¿Qué pasa si cae la base de datos?**
Es un punto único de falla. La solución es replicación primaria/secundaria con conmutación automática.

**¿Por qué REST y WebSocket a la vez?**
REST es petición-respuesta (ideal para acciones puntuales); WebSocket mantiene un canal abierto para que el servidor envíe avisos sin que el cliente pregunte.

**¿Por qué Nginx?**
Hace de gateway, balanceador, servidor de estáticos y proxy de WebSockets con muy poco consumo.

**¿Cómo se escalaría?**
Agregando réplicas al `upstream` de Nginx (o con `docker compose up --scale`) y, en producción, con Kubernetes y autoescalado.

**¿Cómo se valida el token sin consultar a Auth?**
El token es un JWT firmado (HS256); cualquier servicio con el secreto verifica la firma y la expiración localmente.

**¿Cuál es el teorema CAP aquí?**
Se prioriza consistencia en los datos (PostgreSQL único); el feed en caché es eventualmente consistente; ante fallo de Redis se prioriza disponibilidad.

**¿Por qué Docker?**
Para empaquetar cada componente con sus dependencias, ejecutar todo con un solo comando, y simular varias máquinas en un equipo.

**¿Qué diferencia hay entre microservicios y arquitectura monolítica?**
En un monolito todo vive en un proceso (un fallo lo tumba todo); aquí cada servicio se despliega, escala y falla por separado, a cambio de más complejidad de red y operación.
