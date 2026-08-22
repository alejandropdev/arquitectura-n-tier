# Decisión técnica: uso de NestJS en el microservicio de productos

## Contexto

El sistema está compuesto por microservicios independientes, entre ellos `auth-service` (autenticación, implementado en Python con FastAPI siguiendo una arquitectura hexagonal manual: `domain/`, `application/`, `infrastructure/`, `api/`) y `products-service` (catálogo de productos).

Ambos servicios tienen necesidades distintas:

- **auth-service** resuelve un dominio acotado y estable: registro, login, verificación de tokens. La lógica de negocio no crece indefinidamente una vez cubiertos esos casos.
- **products-service** es un dominio que tiende a expandirse con el tiempo: catálogo, categorías, variantes, precios, inventario, promociones, búsquedas/filtros, integración con otros servicios (órdenes, inventario, pagos). Es decir, más superficie de negocio y más probabilidad de que el equipo crezca y trabaje en paralelo sobre el mismo servicio.

## Decisión

Se usará **NestJS** como framework para `products-service`.

**Nota importante sobre el alcance de esta decisión:** la elección no se basa en una superioridad técnica de Nest sobre FastAPI (en capacidad, rendimiento o calidad de código, ambos son igual de válidos), sino en que la rigidez estructural que impone Nest reduce el costo de coordinación entre desarrolladores en un servicio con mayor crecimiento esperado de lógica de negocio y de colaboradores. Es una razón de gobernanza de arquitectura a escala de equipo, no de mérito técnico absoluto de un framework sobre otro.

## Justificación

### 1. Arquitectura modular impuesta por el framework, no dejada a criterio del equipo

NestJS organiza el código en `Modules`, `Controllers` y `Providers` como ciudadanos de primera clase del framework, con un sistema de inyección de dependencias nativo (inspirado en Angular) integrado en el core (`@nestjs/common`, `@nestjs/core`).

Esto es relevante para un servicio que va a crecer: la modularidad no depende de que cada desarrollador respete una convención manual, el framework la exige mediante decoradores (`@Module`, `@Injectable`, `@Controller`) y un contenedor de DI que resuelve las dependencias. Eso reduce el riesgo de que, a medida que se agreguen features (variantes, inventario, promociones), el código se vuelva un monolito desordenado dentro del propio microservicio.


### 2. Validación declarativa con class-validator / class-transformer

Un catálogo de productos tiene muchos DTOs con reglas de validación no triviales (precios positivos, SKUs con formato, stock no negativo, rangos de fechas de promociones, campos opcionales según el tipo de producto, anidamiento de variantes, etc.). NestJS integra `class-validator` y `class-transformer` de forma nativa a través del `ValidationPipe`, permitiendo declarar las reglas como decoradores sobre el propio DTO (`@IsPositive()`, `@IsUUID()`, `@ValidateNested()`, etc.) y transformarlos automáticamente desde el payload HTTP.

Esto es un punto correcto y bien identificado: entre más validaciones estructuradas tenga el servicio, más valor aporta tener esto integrado por defecto en el framework en lugar de escribir validación manual.



### 3. Desacoplamiento de infraestructura (persistencia, mensajería)

NestJS separa la lógica de aplicación de los detalles de infraestructura mediante su sistema de módulos e inyección de dependencias, y ofrece integraciones oficiales para múltiples motores de persistencia (`@nestjs/typeorm`, `@nestjs/mongoose`) y para múltiples transportes de mensajería/colas bajo una misma abstracción (`@nestjs/microservices` soporta Kafka, RabbitMQ, Redis, NATS, gRPC con la misma interfaz de `ClientProxy`).

Esto permite definir interfaces/puertos en la capa de aplicación e inyectar la implementación concreta (repositorio TypeORM hoy, otro mañana; RabbitMQ hoy, Kafka mañana) sin reescribir la lógica de negocio, siempre que el equipo respete la separación de capas (que el framework facilita pero no garantiza por sí solo).

Este punto también es correcto, con la misma salvedad: no es exclusivo de Nest (es factible en cualquier framework con buena disciplina de arquitectura, como demuestra `auth-service`), pero Nest lo hace más natural "out of the box" gracias a su contenedor de DI y su ecosistema oficial de adaptadores.

### 4. Alineación con el tamaño y trayectoria esperada del servicio

Dado que `products-service` es el servicio con mayor probabilidad de crecimiento en lógica de negocio, número de endpoints y personas trabajando sobre él en paralelo, conviene priorizar una estructura más rígida y explícita (Nest) sobre una más minimalista y flexible (FastAPI), que exige más disciplina del equipo para no degradar con el tiempo.


## Alternativas consideradas

- **FastAPI** (mismo stack que auth-service, para consistencia entre servicios): descartado para este servicio porque exige diseñar y mantener manualmente la estructura modular y de capas a medida que crece el dominio de negocio, mientras que Nest la provee por defecto.
- **Express.js puro**: descartado por no ofrecer estructura, DI ni validación de forma nativa, dejando todo el diseño arquitectónico a criterio del equipo, lo cual es un riesgo mayor en un servicio que se espera que crezca.
