# Taller 1 — Aplicación N-tier de autenticación

Arquitectura de Software · Pontificia Universidad Javeriana

Aplicación de autenticación de usuarios con **arquitectura N-tier de tres
niveles**, tácticas de disponibilidad para 99.99%, manejo de excepciones y
observabilidad por capas, desplegada con Docker.

```
                       :8080                                  :8081
   Navegador ────► gateway (nginx) ────► web-1 / web-2 ────► gateway ────► auth-service-1 / -2 ────► postgres
                    balanceador          Tier 1 · MVC                       Tier 2 · capas          Tier 3 · datos
```

## Puesta en marcha

```bash
cp .env.example .env      # ajuste JWT_SECRET si va a exponer el servicio
make up                   # construye y levanta los 6 contenedores
```

- Aplicación web: <http://localhost:8080>
- API del microservicio: <http://localhost:8081/health>, documentación OpenAPI en
  <http://localhost:8081/docs>

```bash
make ps        # estado de los contenedores
make logs      # logs estructurados en JSON
make down      # detener   /   make clean para borrar también los datos
```

## Verificación

```bash
make test      # 87 pruebas (Tier 1 + Tier 2 + Tier 3)
make coverage  # con reporte de cobertura (94% / 95%)
make smoke     # end-to-end contra el despliegue en Docker
make chaos     # apaga una instancia del Tier 2 y mide la disponibilidad
```

## Los tres tiers

| Tier | Rol | Tecnología | Código |
|---|---|---|---|
| 1 · Presentación | Web con patrón **MVC** | FastAPI + Jinja2 | `web/app/{controllers,views,models}` |
| 2 · Lógica de negocio | Microservicio **en capas** (api → application → domain, con puertos y adaptadores) | FastAPI | `auth-service/app/` |
| 3 · Datos | **Repositorio** + unidad de trabajo → base de datos | SQLAlchemy + PostgreSQL | `auth-service/app/infrastructure/persistence/`, `database/` |

Funcionalidad: registro con política de contraseñas, inicio de sesión con
Argon2id y JWT, sesión en cookie `HttpOnly`, panel protegido, cierre de sesión y
bloqueo temporal de la cuenta tras varios intentos fallidos.

## Disponibilidad — una táctica por rama

| Rama | Táctica | Dónde |
|---|---|---|
| **Detección** | Ping/Echo y Monitor: `/health` y `/health/ready`, `HEALTHCHECK` de Docker, `max_fails` de nginx | `*/routers/health.py`, `Dockerfile`, `gateway/nginx.conf` |
| **Recuperación (reparación)** | Redundancia activa (2 instancias por tier), reintentos con backoff, rollback transaccional | `docker-compose.yml`, `web/app/services/auth_client.py`, `unit_of_work.py` |
| **Recuperación (reintroducción)** | Reinicio automático y servicios sin estado (JWT) | `restart: unless-stopped`, `jwt_provider.py` |
| **Prevención** | Circuit breaker, timeouts, validación estricta, bloqueo de cuenta, `pool_pre_ping` | `circuit_breaker.py`, `policies.py`, `database.py` |

Medición real: al detener `auth-service-1`, **20/20 peticiones siguieron siendo
atendidas**. Detalle y cálculo del 99.99% en [docs/02-disponibilidad.md](docs/02-disponibilidad.md).

## Observabilidad

Todos los servicios emiten JSON por `stdout`; cada evento responde **quién**
(`actor`, `client_ip`), **cuándo** (`timestamp` ISO-8601 UTC) y **qué**
(`action`, `outcome`, `message`), con `request_id` para seguir una operación a
través de los tres tiers:

```bash
make smoke                              # imprime la traza usada
docker compose logs | grep <request_id> # la historia completa de esa petición
```

## Documentación

| Documento | Contenido |
|---|---|
| [01 — Diseño](docs/01-diseno.md) | Vistas de contexto, componentes, datos, secuencia y despliegue; decisiones de diseño |
| [02 — Disponibilidad](docs/02-disponibilidad.md) | Tácticas por rama, modelo de disponibilidad, SPOF y evidencia experimental |
| [03 — Observabilidad](docs/03-observabilidad.md) | Formato de log, correlación y cadena de manejo de excepciones |
| [04 — Pruebas](docs/04-pruebas.md) | Estrategia, cobertura y resultados |

## Estructura

```
.
├── web/                 # Tier 1 — presentación (MVC)
│   └── app/{controllers,views,models,services,core}
├── auth-service/        # Tier 2 — lógica de negocio en capas
│   └── app/{api,application,domain,infrastructure,core}
├── database/init/       # Tier 3 — esquema SQL
├── gateway/nginx.conf   # balanceador y detección pasiva de fallas
├── docker-compose.yml   # despliegue de 6 contenedores
├── scripts/             # smoke.sh (end-to-end) y chaos.sh (tolerancia a fallas)
└── docs/                # diseño, disponibilidad, observabilidad y pruebas
```

## Notas de seguridad

- Contraseñas con **Argon2id**; nunca se registran ni se devuelven.
- Cookie de sesión `HttpOnly` + `SameSite=Lax`; active `COOKIE_SECURE=true` tras HTTPS.
- PostgreSQL no publica puertos: solo es alcanzable desde la red interna.
- Los contenedores corren como usuario sin privilegios (uid 10001).
- El puerto 8081 se publica **solo para las pruebas del taller**; en producción el
  Tier 2 no debería ser accesible desde fuera.
- Cambie `JWT_SECRET` en `.env` antes de cualquier despliegue real.
