# auth-common

Librería de autenticación reutilizable para el Taller 2 (Requerimiento 9).
La consumen `auth-service`, `web` y (cuando exista) `products-service` — nadie
reimplementa la lógica de tokens, solo la conectan.

## Qué expone

- `auth_common.tokens.encode_token` / `decode_token` — núcleo puro (sin
  FastAPI) para emitir y validar JWT: firma, `iss`, `exp` y, opcionalmente,
  pertenencia a `aud` (audiencia).
- `auth_common.claims.TokenClaims` — claims decodificados (`sub`, `username`,
  `role`, `aud`, `issued_at`, `expires_at`, `issuer`).
- `auth_common.errors` — jerarquía de errores agnóstica de framework
  (`InvalidTokenError`, `ExpiredTokenError`, `AudienceError`,
  `RoleForbiddenError`, `OwnershipForbiddenError`).
- `auth_common.fastapi_ext.dependencies` — fábricas de dependencias de
  FastAPI:
  - `require_auth(expected_audience, get_settings, get_request_id=...)`:
    exige un `Authorization: Bearer <token>` válido, firmado y con la
    audiencia indicada.
  - `require_role(*roles, require_auth_dep=...)`: además exige que
    `claims.role` esté en la lista.
  - `require_owner_or_role(id_param, *roles, require_auth_dep=...)`: permite
    la petición si `claims.sub` coincide con el parámetro de ruta `id_param`
    **o** el rol está autorizado.

Cada servicio construye su propia instancia de `require_auth` con su
`expected_audience` (p. ej. `"auth-service"` o `"products-service"`) — la
regla de audiencia es configuración, no código hardcodeado, tal como exige el
principio de modificabilidad del taller (ver `docs/05-taller2-plan.md`,
sección 6).

## Instalación

En desarrollo local (usado por `make venv`):

```bash
pip install -e "libs/auth_common[fastapi]"
```

En contenedores, cada `Dockerfile` copia `libs/auth_common` dentro de su
etapa `builder` y lo instala con `pip install`. Requiere que el `build:` del
servicio en `docker-compose.yml` use la raíz del repo como contexto
(`context: .`), no el subdirectorio del servicio.
