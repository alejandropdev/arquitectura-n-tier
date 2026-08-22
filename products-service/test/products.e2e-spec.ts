import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';

import { InMemoryProductRepository } from './support/in-memory-product.repository';
import { CreateProductService } from '@application/products/use-cases/create-product.service';
import { DiscontinueProductService } from '@application/products/use-cases/discontinue-product.service';
import { GetProductByIdService } from '@application/products/use-cases/get-product-by-id.service';
import { ListProductsService } from '@application/products/use-cases/list-products.service';
import { UpdateProductService } from '@application/products/use-cases/update-product.service';
import { ProductRepository } from '@domain/products/contracts/repositories/product.repository';
import { CreateProductUseCase } from '@domain/products/contracts/use-cases/create-product.use-case';
import { DiscontinueProductUseCase } from '@domain/products/contracts/use-cases/discontinue-product.use-case';
import { GetProductByIdUseCase } from '@domain/products/contracts/use-cases/get-product-by-id.use-case';
import { ListProductsUseCase } from '@domain/products/contracts/use-cases/list-products.use-case';
import { UpdateProductUseCase } from '@domain/products/contracts/use-cases/update-product.use-case';
import { ProductStatus } from '@domain/products/entities/product-status.enum';
import { ProductsController } from '@infrastructure/products/http/products.controller';
import { AppErrorFilter } from '@shared/http/app-error.filter';

const CATEGORY_ID = '11111111-1111-4111-8111-111111111111';
const OTHER_CATEGORY_ID = '33333333-3333-4333-8333-333333333333';
const UNKNOWN_ID = '99999999-9999-4999-8999-999999999999';

describe('Products API (e2e)', () => {
  let app: INestApplication;

  beforeEach(async () => {
    // Se monta el mismo cableado de ProductsModule pero con el adaptador de
    // persistencia en memoria: se prueba el API completo sin Postgres.
    const moduleRef = await Test.createTestingModule({
      controllers: [ProductsController],
      providers: [
        { provide: ProductRepository, useClass: InMemoryProductRepository },
        { provide: CreateProductUseCase, useClass: CreateProductService },
        { provide: ListProductsUseCase, useClass: ListProductsService },
        { provide: GetProductByIdUseCase, useClass: GetProductByIdService },
        { provide: UpdateProductUseCase, useClass: UpdateProductService },
        {
          provide: DiscontinueProductUseCase,
          useClass: DiscontinueProductService,
        },
      ],
    }).compile();

    app = moduleRef.createNestApplication();
    app.setGlobalPrefix('api/v1');
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    );
    app.useGlobalFilters(new AppErrorFilter());
    await app.init();
  });

  afterEach(async () => {
    await app.close();
  });

  const createProduct = (body: Record<string, unknown> = {}) =>
    request(app.getHttpServer())
      .post('/api/v1/products')
      .send({ name: 'Camiseta basica', categoryId: CATEGORY_ID, ...body });

  describe('POST /products', () => {
    it('crea un producto en estado borrador', async () => {
      const response = await createProduct().expect(201);

      expect(response.body).toMatchObject({
        name: 'Camiseta basica',
        categoryId: CATEGORY_ID,
        status: ProductStatus.BORRADOR,
        description: null,
        brand: null,
      });
      expect(response.body.id).toEqual(expect.any(String));
    });

    it('rechaza un body sin name', async () => {
      const response = await request(app.getHttpServer())
        .post('/api/v1/products')
        .send({ categoryId: CATEGORY_ID })
        .expect(400);

      expect(response.body.code).toBe('VALIDATION_ERROR');
    });

    it('rechaza un categoryId que no es UUID', async () => {
      const response = await createProduct({ categoryId: 'no-es-uuid' }).expect(
        400,
      );

      expect(response.body.message).toContain('categoryId');
    });

    it('rechaza campos no declarados en el DTO', async () => {
      const response = await createProduct({ price: 1000 }).expect(400);

      expect(response.body.message).toContain('price');
    });
  });

  describe('GET /products', () => {
    it('pagina el listado y devuelve la metadata', async () => {
      for (let i = 0; i < 25; i++) {
        await createProduct({ name: `Producto ${i}` }).expect(201);
      }

      const response = await request(app.getHttpServer())
        .get('/api/v1/products?page=2&size=10')
        .expect(200);

      expect(response.body.data).toHaveLength(10);
      expect(response.body.meta).toEqual({
        page: 2,
        size: 10,
        total: 25,
        totalPages: 3,
        hasNext: true,
        hasPrevious: true,
      });
    });

    it('aplica los valores de paginacion por defecto', async () => {
      await createProduct().expect(201);

      const response = await request(app.getHttpServer())
        .get('/api/v1/products')
        .expect(200);

      expect(response.body.meta).toMatchObject({ page: 1, size: 20, total: 1 });
    });

    it('rechaza un size mayor al maximo permitido', async () => {
      await request(app.getHttpServer())
        .get('/api/v1/products?size=500')
        .expect(400);
    });

    it('filtra por categoria', async () => {
      await createProduct({ name: 'De la categoria A' }).expect(201);
      await createProduct({
        name: 'De la categoria B',
        categoryId: OTHER_CATEGORY_ID,
      }).expect(201);

      const response = await request(app.getHttpServer())
        .get(`/api/v1/products?categoryId=${OTHER_CATEGORY_ID}`)
        .expect(200);

      expect(response.body.meta.total).toBe(1);
      expect(response.body.data[0].name).toBe('De la categoria B');
    });

    it('busca por nombre sin distinguir mayusculas', async () => {
      await createProduct({ name: 'Camiseta Deportiva' }).expect(201);
      await createProduct({ name: 'Pantalon' }).expect(201);

      const response = await request(app.getHttpServer())
        .get('/api/v1/products?search=camiseta')
        .expect(200);

      expect(response.body.meta.total).toBe(1);
    });
  });

  describe('GET /products/:id', () => {
    it('devuelve el producto', async () => {
      const created = await createProduct().expect(201);

      const response = await request(app.getHttpServer())
        .get(`/api/v1/products/${created.body.id}`)
        .expect(200);

      expect(response.body.id).toBe(created.body.id);
    });

    it('devuelve 404 con codigo de dominio si no existe', async () => {
      const response = await request(app.getHttpServer())
        .get(`/api/v1/products/${UNKNOWN_ID}`)
        .expect(404);

      expect(response.body).toMatchObject({ code: 'PRODUCT_NOT_FOUND' });
    });

    it('devuelve 400 si el id no es un UUID', async () => {
      await request(app.getHttpServer())
        .get('/api/v1/products/123')
        .expect(400);
    });
  });

  describe('PATCH /products/:id', () => {
    it('actualiza solo los campos enviados', async () => {
      const created = await createProduct({ brand: 'Acme' }).expect(201);

      const response = await request(app.getHttpServer())
        .patch(`/api/v1/products/${created.body.id}`)
        .send({ name: 'Camiseta premium' })
        .expect(200);

      expect(response.body.name).toBe('Camiseta premium');
      expect(response.body.brand).toBe('Acme');
    });

    it('permite activar un producto en borrador', async () => {
      const created = await createProduct().expect(201);

      const response = await request(app.getHttpServer())
        .patch(`/api/v1/products/${created.body.id}`)
        .send({ status: ProductStatus.ACTIVO })
        .expect(200);

      expect(response.body.status).toBe(ProductStatus.ACTIVO);
    });

    it('devuelve 404 si el producto no existe', async () => {
      await request(app.getHttpServer())
        .patch(`/api/v1/products/${UNKNOWN_ID}`)
        .send({ name: 'Camiseta premium' })
        .expect(404);
    });
  });

  describe('DELETE /products/:id', () => {
    it('descontinua el producto y lo saca del listado por defecto', async () => {
      const created = await createProduct().expect(201);

      await request(app.getHttpServer())
        .delete(`/api/v1/products/${created.body.id}`)
        .expect(204);

      const listado = await request(app.getHttpServer())
        .get('/api/v1/products')
        .expect(200);
      expect(listado.body.meta.total).toBe(0);

      const descontinuados = await request(app.getHttpServer())
        .get(`/api/v1/products?status=${ProductStatus.DESCONTINUADO}`)
        .expect(200);
      expect(descontinuados.body.meta.total).toBe(1);
    });

    it('el producto sigue siendo consultable por id (no se borro la fila)', async () => {
      const created = await createProduct().expect(201);
      await request(app.getHttpServer())
        .delete(`/api/v1/products/${created.body.id}`)
        .expect(204);

      const response = await request(app.getHttpServer())
        .get(`/api/v1/products/${created.body.id}`)
        .expect(200);

      expect(response.body.status).toBe(ProductStatus.DESCONTINUADO);
    });

    it('es idempotente', async () => {
      const created = await createProduct().expect(201);

      await request(app.getHttpServer())
        .delete(`/api/v1/products/${created.body.id}`)
        .expect(204);
      await request(app.getHttpServer())
        .delete(`/api/v1/products/${created.body.id}`)
        .expect(204);
    });

    it('no se puede reactivar un producto descontinuado', async () => {
      const created = await createProduct().expect(201);
      await request(app.getHttpServer())
        .delete(`/api/v1/products/${created.body.id}`)
        .expect(204);

      const response = await request(app.getHttpServer())
        .patch(`/api/v1/products/${created.body.id}`)
        .send({ status: ProductStatus.ACTIVO })
        .expect(422);

      expect(response.body.code).toBe('PRODUCT_INVALID_STATUS_TRANSITION');
    });
  });
});
