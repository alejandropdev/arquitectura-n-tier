# 05 — Taller 2: alcance y distribución del trabajo

## 1. Objetivo

Extender el sistema del Taller 1 (gateway + `auth-service` + `web` + PostgreSQL +
observabilidad) con un nuevo dominio de negocio (productos), balanceo de carga
dinámico, mejoras de performance, endurecimiento de seguridad y una base de
datos propia por servicio, sin romper lo ya entregado.

## 2. Alcance: definición de cada requerimiento

| # | Requerimiento | Definición |
|---|---|---|
| 1 | CRUD de productos | Nuevo servicio `products-service` (misma arquitectura hexagonal que `auth-service`) con endpoints Create/Read/Update/Delete sobre una tabla `products`, expuesto vía gateway, con **paginación** en el listado. |
| 2 | Load Balancer | Evolucionar el gateway actual (nginx con upstreams fijos) para que soporte creación de instancias/réplicas y enrute dinámicamente entre ellas (descubrimiento de instancias vía DNS de Docker/`resolver` + `docker compose up --scale`, o un balanceador que soporte altas/bajas de réplicas sin editar `nginx.conf` a mano). |
| 3 | Base de datos por servicio | Cada servicio de negocio (`auth-service`, `products-service`) es dueño exclusivo de su base de datos (su propio contenedor PostgreSQL, su propio volumen, sus propias credenciales). Ningún servicio consulta directamente la BD de otro; si necesita datos de otro dominio, lo hace por API. |
| 4 | Cache | Capa de caché (Redis) para lecturas de alta frecuencia (catálogo/detalle de producto, resultado de validación de token), con invalidación explícita en cada escritura. |
| 5 | Índices en BD | Índices sobre las columnas usadas en filtros/joins de `users`, `login_attempts` (BD de `auth-service`) y `products` (BD de `products-service`), entregados como scripts de migración versionados por servicio. |
| 6 | Timeouts | Tiempos límite explícitos y configurables en: gateway → servicios, servicio → servicio, servicio → base de datos y servicio → cache, con manejo de error (fail-fast) en cada punto. |
| 7 | Monitoreo de condiciones | Extensión de Prometheus/Grafana/Alertmanager (ya existente desde el Taller 1) con métricas y alertas para las condiciones nuevas: instancias activas/caídas del load balancer, rate limiting, timeouts, hit/miss de cache, tasa de error de `products-service`. |
| 8 | Soft delete de usuarios | Reemplazar el borrado físico de `users` por marcado lógico (`deleted_at`), excluyendo esos registros de consultas normales y del login. |
| 9 | Seguridad | (a) Validación de token en el api gateway antes de enrutar. (b) Validación de `audience` del JWT en cada servicio (un token emitido para un servicio no debe servir en otro). (c) Autorización por propiedad: un usuario solo puede leer/modificar su propio recurso de usuario; solo roles autorizados pueden mutar productos. |
| 10 | Rate limiting | Límite de peticiones por cliente/IP/token en el api gateway, con respuesta `429` y sin afectar el enrutamiento normal del load balancer. |
| — | Modificabilidad (transversal) | No es una tarea nueva sino una restricción de calidad que aplica a **todo** lo anterior: cada pieza se construye detrás de una interfaz/puerto (repositorio, cache, validador de auth, estrategia de balanceo) para poder cambiar la implementación sin tocar el dominio. Ver sección 6. |

> Performance (antes numerado como ítem "9" en la primera versión de este
> documento) no es un ítem de trabajo aparte: es el resultado de completar
> cache (4), índices (5) y paginación (parte de 1).

## 3. Principio de distribución

Un **dueño único por requerimiento**, para que nadie edite el mismo archivo o
servicio al mismo tiempo. Los contratos compartidos (esquema de `products`,
claims del JWT, convenciones de `docker-compose`) se fijan en un **kickoff de
30–45 min antes de programar** (sección 5).

Se ajustó la carga de Diego a pedido del equipo: **Diego solo construye el
CRUD de productos con paginación**; la integración de auth y los índices de
esa base de datos quedan del lado de Andrés, quien ya tenía la especialidad de
datos/performance.

## 4. Distribución por integrante

### Diego — Dominio de productos (carga reducida)
- **Requerimiento 1**: CRUD de productos completo (entidad, casos de uso,
  repositorio, endpoints REST) con **paginación** en `GET /products`.
- Su propia base de datos PostgreSQL (requerimiento 3, lado productos): al
  ser un servicio nuevo, nace con su propio contenedor/volumen desde el día
  uno — no implica trabajo adicional, solo no compartir el Postgres de
  `auth-service`.
- Deja el repositorio de productos detrás de una interfaz (puerto) para que
  Andrés pueda añadir cache e índices sin tocar los casos de uso, y deja un
  punto de extensión claro (dependencia de FastAPI/middleware) donde Andrés
  conecta la validación de auth — sin necesidad de coordinar la lógica interna
  de seguridad, solo la forma del contrato (ver kickoff).
- **Entregable:** `products-service` corriendo en Docker Compose, con pruebas
  unitarias y de API, documentado en el gateway.

### Andrés — Datos, performance y auth aplicada a productos
- **Requerimiento 4** (cache con Redis): cache de catálogo/detalle de
  productos y de validación de tokens, con invalidación en escritura.
- **Requerimiento 5** (índices): scripts de migración con los índices de
  `users`/`login_attempts` (BD de `auth-service`) y de `products` (BD de
  `products-service`).
- **Integración de auth en `products-service`**: conecta en el punto de
  extensión que deja Diego la librería/dependencia de validación de token +
  audience + ownership que **diseña Alejandro**, y la aplica a cada endpoint
  de productos (ej. solo el dueño o un rol autorizado puede editar/eliminar
  un producto). Andrés consume el contrato de seguridad, no lo diseña.
- **Entregable:** contenedor Redis en `docker-compose.yml`, capa de cache
  desacoplada por puerto/adaptador, scripts SQL de índices con evidencia
  antes/después (`EXPLAIN ANALYZE`), y `products-service` protegido por auth.

### Alejandro — Seguridad y políticas del gateway
- **Requerimiento 9** completo: diseño de claims del JWT (`sub`, `aud`,
  `role`), emisión en `auth-service`, validación de token en el api gateway,
  validación de `audience` por servicio y reglas de autorización por
  propiedad (`users/{id}` propio; roles autorizados para mutar productos).
- Construye la **librería/dependencia de auth reutilizable** (interfaz común)
  que `auth-service`, `web` y `products-service` consumen — Andrés solo la
  conecta en productos, no la reimplementa.
- **Requerimiento 10** (rate limiting en el api gateway): límite de peticiones
  por IP/token, con `429` como respuesta, coexistiendo con el load balancer de
  Carlos en el mismo `nginx.conf` (bloques/`include` separados para evitar
  choques al fusionar ramas — acordado en el kickoff).
- Puede arrancar de inmediato en `auth-service` y el gateway; la integración
  puntual con `products-service` la hace Andrés cuando el contrato esté listo.
- **Entregable:** middleware/dependencia de auth reutilizable + reglas de
  rate limiting activas + pruebas que demuestren que un token de un usuario no
  opera sobre otro, que un token de un servicio no sirve en otro, y que se
  respeta el límite de peticiones.

### Carlos — Infraestructura, resiliencia y ciclo de vida de usuarios
- **Requerimiento 2** (Load Balancer): evolución del gateway para creación de
  instancias/réplicas y enrutamiento dinámico entre ellas (reemplaza los
  upstreams estáticos actuales de `nginx.conf`).
- **Requerimiento 3** (lado infraestructura): separa `auth-service` en su
  propio contenedor/volumen PostgreSQL independiente (hoy ya es el único
  consumidor de la BD, así que es formalizar el aislamiento) y define en
  `docker-compose.yml` la convención que Diego sigue para la BD de productos.
- **Requerimiento 6** (timeouts): ya existen timeouts base en el gateway desde
  el Taller 1 (`proxy_connect_timeout`, etc.); se extienden a las llamadas
  nuevas — servicio → `products-service`, servicio → Redis, servicio → BD
  propia — con manejo de error consistente.
- **Requerimiento 7** (monitoreo de condiciones): nuevas métricas/alertas y
  paneles de Grafana para instancias del load balancer, rate limiting,
  timeouts, cache hit/miss y errores de `products-service`.
- **Requerimiento 8** (soft delete de usuarios): columna `deleted_at` en
  `users`, exclusión en queries y en el flujo de login, endpoint de baja
  lógica.
- Todo su trabajo vive en `gateway/`, `docker-compose.yml`, `monitoring/` y la
  capa de persistencia de `auth-service` — coordina con Alejandro solo en
  `nginx.conf` (bloques separados) y con Diego solo en la convención de
  nombres de servicios/puertos.
- **Entregable:** load balancer con altas/bajas de réplicas verificables,
  bases de datos separadas por servicio, timeouts documentados por punto de
  integración, dashboard/alertas actualizados y soft delete con pruebas.

## 5. Kickoff de coordinación (antes de programar)

Definir en conjunto, por escrito, antes de repartirse a programar:

1. **Contrato de `products`**: nombre de la tabla/servicio, campos mínimos
   (`id`, `name`, `price`, `stock`, `owner_id`, `created_at`), rutas REST
   (`/products`, `/products/{id}`) y forma de la paginación (`page`/`size` o
   cursor).
2. **Claims del JWT**: campos exactos del token (`sub`, `aud`, `role`) para
   que Alejandro (diseño/emisión), Andrés (consumo en productos) y Carlos
   (consumo en `auth-service`/gateway) usen el mismo formato desde el día uno.
3. **Punto de extensión de auth** en `products-service`: forma de la
   dependencia que Diego deja lista y que Andrés completa con la librería de
   Alejandro.
4. **Convenciones de `docker-compose.yml`**: nombres de servicios/puertos/
   volúmenes nuevos (`products-service`, `products-db`, `auth-db`, `redis`) y
   cómo se dividen los bloques de `nginx.conf` entre load balancer (Carlos) y
   rate limiting/auth gateway (Alejandro).

## 6. Principio transversal: modificabilidad

No se reparte como tarea porque aplica a todo lo demás. Cada quien entrega su
parte siguiendo el mismo estilo de puertos y adaptadores que ya usa
`auth-service`:

- **Diego**: el repositorio de productos es una interfaz; Postgres es un
  adaptador reemplazable.
- **Andrés**: la cache es un puerto (`CachePort`) con un adaptador Redis —
  se podría cambiar de proveedor sin tocar los casos de uso; los índices no
  cambian el modelo de dominio, solo el rendimiento del adaptador de BD.
- **Alejandro**: la validación de auth es una dependencia inyectable, no
  código copiado en cada servicio; las reglas de audience/ownership son
  configurables, no hardcodeadas por servicio.
- **Carlos**: la estrategia de balanceo/timeouts vive en configuración de
  infraestructura (gateway/compose), no en el código de los servicios, para
  poder escalar réplicas o cambiar timeouts sin recompilar nada.

## 7. Orden sugerido / dependencias

- Todos arrancan en paralelo el mismo día, apoyados en el contrato del
  kickoff, no en el código del otro.
- Único punto real de sincronización: Andrés necesita que `products-service`
  exponga las rutas (aunque sin lógica completa) para conectar cache, índices
  y auth — esto debería existir a mitad de taller si Diego avanza con
  normalidad.
- Alejandro entrega la librería de auth reutilizable antes de que Andrés la
  integre a productos; mientras tanto Alejandro avanza en `auth-service` y el
  gateway sin bloquearse.
- Carlos no depende de nadie más que del contrato de nombres de
  servicios/puertos fijado en el kickoff.

## 8. Definición de "hecho" (Definition of Done) por entregable

- Código con pruebas (unitarias y, cuando aplique, de API) que pasen en `make test`.
- Cambios reflejados en `docker-compose.yml` si se agregan servicios/infra.
- Sin romper las pruebas end-to-end existentes (`make smoke`, `make chaos`).
- Cada pieza nueva expone una interfaz/puerto claro (ver sección 6), no lógica
  acoplada directamente a un proveedor concreto.
- Documentación breve del cambio (README del servicio o sección en `docs/`).
