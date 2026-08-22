# Contrato REST de `products-service`

Este documento es el insumo del kickoff (seccion 5 del plan de Taller 2) para
Andres (cache, indices, auth aplicada) y Carlos (gateway / load balancer).

**Base URL interna:** `http://products-service:3000`
**Prefijo:** `/api/v1` (configurable con `API_PREFIX`)

## Alcance de esta entrega

- Dominio de negocio implementado: **solo `products`**.
- Las otras 7 tablas del [diagrama de BD](./db-diagram.md) existen como tablas y
  entidades ORM (creadas por la migracion), pero todavia no tienen casos de uso
  ni endpoints.
- Todos los identificadores son **UUID v4**.
- El precio vive en `product_variants` y el stock en `inventory`, tal como fija
  el diagrama. El contrato tentativo del kickoff (`products.price`,
  `products.stock`, `products.owner_id`) quedo descartado.

## Recurso: Producto

```json
{
  "id": "8f3a1c9e-4c2b-4c8e-9a1f-1b2c3d4e5f60",
  "name": "Camiseta basica",
  "description": "Algodon 100%",
  "brand": "Acme",
  "categoryId": "11111111-1111-4111-8111-111111111111",
  "status": "borrador",
  "createdAt": "2026-08-22T14:03:11.482Z",
  "updatedAt": "2026-08-22T14:03:11.482Z"
}
```

`status` es uno de `borrador` | `activo` | `descontinuado`.
`descontinuado` es un **estado terminal**: un producto retirado no se reactiva.

## Endpoints

| Metodo | Ruta | Exito | Errores |
|---|---|---|---|
| `POST` | `/api/v1/products` | `201` + producto | `400` validacion, `422` categoria inexistente |
| `GET` | `/api/v1/products` | `200` + listado paginado | `400` query invalida |
| `GET` | `/api/v1/products/:id` | `200` + producto | `400` id no UUID, `404` no existe |
| `PATCH` | `/api/v1/products/:id` | `200` + producto | `400`, `404`, `422` transicion de estado invalida |
| `DELETE` | `/api/v1/products/:id` | `204` sin cuerpo | `400`, `404` |

### `POST /api/v1/products`

```json
{
  "name": "Camiseta basica",        // obligatorio, 2..150 caracteres
  "description": "Algodon 100%",    // opcional, hasta 2000; null para vaciar
  "brand": "Acme",                  // opcional, hasta 100; null para vaciar
  "categoryId": "uuid-v4",          // obligatorio
  "status": "borrador"              // opcional, default "borrador"
}
```

Campos no declarados se rechazan con `400` (`forbidNonWhitelisted`).

### `GET /api/v1/products`

| Query param | Tipo | Default | Notas |
|---|---|---|---|
| `page` | int >= 1 | `1` | |
| `size` | int 1..100 | `20` | |
| `categoryId` | uuid | — | |
| `status` | enum | — | sin este filtro se ocultan los descontinuados |
| `brand` | string | — | coincidencia exacta, sin distinguir mayusculas |
| `search` | string | — | coincidencia parcial sobre `name` |
| `sort` | `createdAt` \| `name` | `createdAt` | |
| `order` | `ASC` \| `DESC` | `DESC` | |

Respuesta:

```json
{
  "data": [ /* productos */ ],
  "meta": {
    "page": 2, "size": 10, "total": 25,
    "totalPages": 3, "hasNext": true, "hasPrevious": true
  }
}
```

### `PATCH /api/v1/products/:id`

Actualizacion parcial con las mismas reglas de validacion del `POST`.
`null` en `description`/`brand` limpia el campo; un campo ausente no se toca.

### `DELETE /api/v1/products/:id`

**No borra la fila:** marca `status = descontinuado`. El producto desaparece del
listado por defecto pero sigue siendo consultable por id y con
`?status=descontinuado`. Es **idempotente**: repetirlo devuelve `204`.

## Errores

Todos los errores comparten la misma forma:

```json
{
  "code": "PRODUCT_NOT_FOUND",
  "message": "No existe un producto con id 999...",
  "path": "/api/v1/products/999...",
  "timestamp": "2026-08-22T14:03:11.482Z"
}
```

| `code` | HTTP | Cuando |
|---|---|---|
| `VALIDATION_ERROR` | `400` | body o query invalidos |
| `PRODUCT_NOT_FOUND` | `404` | el id no existe |
| `PRODUCT_ALREADY_DISCONTINUED` | `409` | (reservado; `DELETE` es idempotente) |
| `PRODUCT_INVALID_STATUS_TRANSITION` | `422` | intento de reactivar un descontinuado |
| `PRODUCT_CATEGORY_NOT_FOUND` | `422` | `categoryId` sin fila en `categories` |
| `INTERNAL_ERROR` | `500` | cualquier otra cosa |

El `code` es el contrato estable; el `message` puede cambiar de redaccion.

## Recurso: Categoria (solo lectura)

Catalogo plano de categorias (jerarquia via `parentId`), usado hoy para poblar
el desplegable de categoria al crear/editar un producto. No hay altas/bajas
por API todavia: el catalogo se carga por seed.

| Metodo | Ruta | Exito |
|---|---|---|
| `GET` | `/api/v1/categories` | `200` + listado plano (sin paginar) |

```json
[
  {
    "id": "11111111-1111-4111-8111-111111111111",
    "parentId": null,
    "name": "Electrónica",
    "slug": "electronica"
  },
  {
    "id": "22222222-2222-4222-8222-222222222222",
    "parentId": "11111111-1111-4111-8111-111111111111",
    "name": "Smartphones",
    "slug": "smartphones"
  }
]
```

## Sondas de salud

Fuera del prefijo `/api/v1`, para el gateway y el load balancer:

- `GET /health/live` -> `200 {"status":"ok","service":"products-service","instance":"..."}`
- `GET /health/ready` -> `200 {"status":"ok","database":"up"}` o `{"status":"degraded","database":"down"}`

## Punto de extension de auth (para Andres)

Ninguna ruta esta protegida todavia; la seguridad es del lado de Alejandro
(diseno) y Andres (integracion). El hueco esta listo:

1. La libreria de auth expone un `CanActivate` de Nest (por ejemplo `AuthGuard`).
2. Se agrega `@UseGuards(AuthGuard)` en
   [`products.controller.ts`](../src/infrastructure/products/http/products.controller.ts)
   — a nivel de clase para todo, o por metodo si las reglas difieren entre leer
   y mutar.
3. El guard se registra en
   [`products.module.ts`](../src/infrastructure/products/products.module.ts).

Ni `application/` ni `domain/` cambian. Si la regla de autorizacion necesita
datos del producto (por ejemplo, propiedad), se resuelve leyendo el recurso
desde el guard vía el puerto `ProductRepository`, que el modulo ya exporta.

> Nota: `products` **no tiene `owner_id`** (el diagrama de BD no lo define), asi
> que la autorizacion sobre productos es por **rol**, no por propiedad. Si el
> equipo decide que haga falta propiedad, es una columna nueva + migracion.

## Punto de extension de cache (para Andres)

`ProductRepository` es una clase abstracta usada como token de inyeccion. Para
enchufar Redis basta con un decorador que la implemente y delegue en
`TypeOrmProductRepository`, cambiando una linea del `providers` del modulo. Los
casos de uso no se enteran.

## Notas de infraestructura (para Carlos)

- El servicio escucha en `PORT` (default `3000`).
- Necesita su propia base de datos (`products-db`), nunca la de `auth-service`.
- Variables de entorno: ver [`.env.example`](../.env.example).
- El esquema se crea con `npm run migration:run`, no con `synchronize`.
