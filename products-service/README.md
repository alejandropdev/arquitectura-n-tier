# products-service

Microservicio de catalogo de productos del Taller 2. NestJS + TypeORM +
PostgreSQL, con **Clean Architecture + DDD**: las capas se cortan primero por
capa y dentro de cada capa por dominio.

- Por que NestJS y no FastAPI: [`documentation/tech-decision.md`](./documentation/tech-decision.md)
- Modelo de datos: [`documentation/db-diagram.md`](./documentation/db-diagram.md)
- Contrato REST (endpoints, errores, puntos de extension): [`documentation/endpoints.md`](./documentation/endpoints.md)

## Alcance de esta entrega

Requerimiento 1 del [plan de Taller 2](../../docs/05-taller2-plan.md): **CRUD de
productos con paginacion**, con el repositorio detras de un puerto.

- Dominio de negocio implementado: **solo `products`**.
- Las 8 tablas del diagrama existen como entidades ORM y las crea la migracion;
  las otras 7 no tienen todavia casos de uso ni endpoints.
- Identificadores: **UUID v4**.
- `DELETE` no borra: marca `status = descontinuado`.
- Fuera de alcance (otras personas del equipo): cache Redis e indices (Andres),
  auth y rate limiting (Alejandro), load balancer y docker-compose (Carlos).

## Arquitectura

```
src/
  shared/          Transversal a todos los dominios
    errors/          AppError (clase base con message + code) y catalogo de codigos
    http/            Filtro global de errores y mapa codigo -> status HTTP
    pagination/      PaginationQueryDto, PaginatedResult, buildPaginationMeta
    config/          Configuracion tipada por variables de entorno
    utils/           Utilidades genericas (slug, normalizacion de texto)
    health/          Sondas /health/live y /health/ready

  domain/          Reglas de negocio. Sin Nest, sin TypeORM, sin HTTP
    products/
      entities/      Product (clase pura con las reglas de estado)
      exceptions/    Errores de dominio, todos extienden AppError
      contracts/
        repositories/  ProductRepository       (clase abstracta = puerto)
        use-cases/     *UseCase                (clases abstractas)

  application/     Orquestacion. Implementa los contratos del dominio
    products/
      dtos/          class-validator + class-transformer
      mappers/       DTO <-> comando de dominio <-> respuesta
      use-cases/     *Service, implementacion de cada *UseCase

  infrastructure/  Detalles reemplazables
    db/
      entities/      Las 8 entidades TypeORM, una carpeta por tabla
      migrations/    Autogeneradas por el CLI de TypeORM
      data-source.ts DataSource compartido por el CLI y por Nest
      database.module.ts
    products/
      repositories/  TypeOrmProductRepository, implementa el puerto
      mappers/       Fila de Postgres <-> entidad de dominio
      http/          ProductsController (adaptador de entrada)
      products.module.ts
```

### La regla que sostiene todo

Los contratos del dominio son **clases abstractas**, no interfaces: TypeScript
borra las interfaces al compilar y Nest necesita un token real para inyectar.
Asi el contrato y el token de DI son la misma cosa, y el cableado vive en un
solo archivo por dominio:

```ts
// infrastructure/products/products.module.ts
providers: [
  { provide: ProductRepository,    useClass: TypeOrmProductRepository },
  { provide: CreateProductUseCase, useClass: CreateProductService },
  // ...
]
```

Consecuencia practica: cambiar Postgres por otro motor, o envolver el
repositorio en una capa de cache, es cambiar una linea de ese `providers`. Ni
el dominio ni los casos de uso se enteran. Eso es el requisito de
modificabilidad de la seccion 6 del plan del taller.

### Direccion de las dependencias

`infrastructure` -> `application` -> `domain` -> `shared`.
El dominio no importa nada de las otras capas (solo `shared/errors` y
`shared/pagination`, que son tipos sin dependencias externas).

## Puesta en marcha

```bash
npm install
cp .env.example .env          # ajustar credenciales de la BD
npm run migration:run         # crea las 8 tablas
npm run start:dev
```

El servicio queda en `http://localhost:3000/api/v1/products`.

### Despliegue en Docker Compose

Desde la raíz del repositorio, el servicio ya está configurado en
`docker-compose.yml` con redundancia activa (dos réplicas) y su propia base de
datos PostgreSQL:

```bash
cd ../..                      # volver a la raíz
cp .env.example .env          # ajustar si es necesario
docker-compose build services/products-service
docker-compose up -d products-db products-service-1 products-service-2
docker-compose exec products-service-1 npm run migration:run
```

El gateway (nginx) enruta `/api/v1/products/*` y `/products/health` a ambas
réplicas con balanceo de carga y detección de fallas (ver
[`gateway/nginx.conf`](../../gateway/nginx.conf)). Accesible en
`http://localhost:8081/api/v1/products` desde dentro de la red Docker.

Monitoreo:
```bash
docker-compose ps              # estado de servicios
docker-compose logs products-service-1  # logs de una réplica
docker compose exec products-db psql -U products -d productsdb  # conectar a BD
```

### Variables de entorno

Ver [`.env.example`](./.env.example). Los timeouts servicio -> BD
(`DB_CONNECT_TIMEOUT_MS`, `DB_STATEMENT_TIMEOUT_MS`) son configurables, nunca
hardcodeados: es el requerimiento 6 del taller.

## Migraciones

El esquema **solo** cambia por migraciones versionadas: `synchronize` esta en
`false` de forma permanente.

```bash
npm run migration:generate    # diffea entidades vs BD y escribe el archivo
npm run migration:run         # aplica las pendientes
npm run migration:revert      # deshace la ultima
npm run migration:show        # estado de cada migracion
```

`migration:generate` necesita la base de datos **corriendo**: TypeORM compara el
esquema real contra las entidades para escribir el diff.

> **Pendiente:** `src/infrastructure/db/migrations/` esta vacia todavia. La
> primera migracion se genera con `npm run migration:generate` contra una BD
> limpia; las 8 entidades ya estan definidas y su metadata valida. Hasta que
> exista ese archivo, `migration:run` no crea nada.

> Los indices de performance sobre `products` son el requerimiento 5 y los
> entrega Andres en su propia migracion. Aqui solo estan los indices implicitos
> de llaves primarias, unicas y foraneas.

## Pruebas

```bash
npm test          # unitarias: entidad de dominio, casos de uso, paginacion
npm run test:e2e  # API completa con un repositorio en memoria (sin Postgres)
npm run lint
npm run build
```

Las pruebas de API sustituyen el provider `ProductRepository` por
[`InMemoryProductRepository`](./test/support/in-memory-product.repository.ts).
Que eso sea posible en unas pocas lineas es la evidencia de que el puerto
cumple su funcion.
