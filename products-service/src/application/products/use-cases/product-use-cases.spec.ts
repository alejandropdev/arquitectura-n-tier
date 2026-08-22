import { CreateProductService } from './create-product.service';
import { DiscontinueProductService } from './discontinue-product.service';
import { GetProductByIdService } from './get-product-by-id.service';
import { ListProductsService } from './list-products.service';
import { UpdateProductService } from './update-product.service';
import {
  ProductRepository,
  ProductSearchCriteria,
} from '@domain/products/contracts/repositories/product.repository';
import { ProductStatus } from '@domain/products/entities/product-status.enum';
import { Product } from '@domain/products/entities/product.entity';
import { ProductNotFoundException } from '@domain/products/exceptions/product-not-found.exception';

const CATEGORY_ID = '11111111-1111-4111-8111-111111111111';
const PRODUCT_ID = '22222222-2222-4222-8222-222222222222';

function aProduct(
  overrides: Partial<Parameters<typeof Product.rehydrate>[0]> = {},
) {
  return Product.rehydrate({
    productId: PRODUCT_ID,
    name: 'Camiseta basica',
    description: null,
    brand: 'Acme',
    categoryId: CATEGORY_ID,
    status: ProductStatus.ACTIVO,
    createdAt: new Date('2026-01-01T00:00:00Z'),
    updatedAt: new Date('2026-01-01T00:00:00Z'),
    ...overrides,
  });
}

/** Mock del puerto: la clase abstracta hace trivial construirlo. */
function mockRepository(): jest.Mocked<ProductRepository> {
  return {
    create: jest.fn(),
    findById: jest.fn(),
    search: jest.fn(),
    update: jest.fn(),
  };
}

describe('CreateProductService', () => {
  it('crea el producto en estado borrador cuando no se especifica status', async () => {
    const repository = mockRepository();
    repository.create.mockImplementation(async (product) => product);

    const created = await new CreateProductService(repository).execute({
      name: '  Camiseta basica  ',
      categoryId: CATEGORY_ID,
    });

    expect(created.status).toBe(ProductStatus.BORRADOR);
    expect(created.name).toBe('Camiseta basica'); // normalizado por el dominio
    expect(repository.create).toHaveBeenCalledTimes(1);
  });

  it('respeta el status recibido', async () => {
    const repository = mockRepository();
    repository.create.mockImplementation(async (product) => product);

    const created = await new CreateProductService(repository).execute({
      name: 'Camiseta',
      categoryId: CATEGORY_ID,
      status: ProductStatus.ACTIVO,
    });

    expect(created.status).toBe(ProductStatus.ACTIVO);
  });
});

describe('GetProductByIdService', () => {
  it('devuelve el producto cuando existe', async () => {
    const repository = mockRepository();
    repository.findById.mockResolvedValue(aProduct());

    const found = await new GetProductByIdService(repository).execute(
      PRODUCT_ID,
    );

    expect(found.productId).toBe(PRODUCT_ID);
  });

  it('lanza ProductNotFoundException cuando no existe', async () => {
    const repository = mockRepository();
    repository.findById.mockResolvedValue(null);

    await expect(
      new GetProductByIdService(repository).execute(PRODUCT_ID),
    ).rejects.toBeInstanceOf(ProductNotFoundException);
  });
});

describe('ListProductsService', () => {
  it('traduce page/size a skip/take y construye la metadata', async () => {
    const repository = mockRepository();
    repository.search.mockResolvedValue({ items: [aProduct()], total: 25 });

    const result = await new ListProductsService(repository).execute({
      page: 3,
      size: 10,
      sortBy: 'createdAt',
      order: 'DESC',
    });

    const [, pageParams] = repository.search.mock.calls[0];
    expect(pageParams).toEqual({ skip: 20, take: 10 });
    expect(result.meta).toEqual({
      page: 3,
      size: 10,
      total: 25,
      totalPages: 3,
      hasNext: false,
      hasPrevious: true,
    });
  });

  it('no filtra page/size hacia el repositorio, solo criterios de dominio', async () => {
    const repository = mockRepository();
    repository.search.mockResolvedValue({ items: [], total: 0 });

    await new ListProductsService(repository).execute({
      page: 1,
      size: 20,
      brand: 'Acme',
      sortBy: 'name',
      order: 'ASC',
    });

    const [criteria] = repository.search.mock.calls[0] as [
      ProductSearchCriteria,
    ];
    expect(criteria).toEqual({ brand: 'Acme', sortBy: 'name', order: 'ASC' });
  });
});

describe('UpdateProductService', () => {
  it('solo aplica los campos presentes en el comando', async () => {
    const repository = mockRepository();
    const product = aProduct({ description: 'original', brand: 'Acme' });
    repository.findById.mockResolvedValue(product);
    repository.update.mockImplementation(async (p) => p);

    const updated = await new UpdateProductService(repository).execute({
      productId: PRODUCT_ID,
      name: 'Camiseta premium',
    });

    expect(updated.name).toBe('Camiseta premium');
    expect(updated.description).toBe('original'); // intacto
    expect(updated.brand).toBe('Acme'); // intacto
  });

  it('limpia el campo cuando se envia null explicito', async () => {
    const repository = mockRepository();
    repository.findById.mockResolvedValue(
      aProduct({ description: 'original' }),
    );
    repository.update.mockImplementation(async (p) => p);

    const updated = await new UpdateProductService(repository).execute({
      productId: PRODUCT_ID,
      description: null,
    });

    expect(updated.description).toBeNull();
  });

  it('falla con 404 de dominio si el producto no existe', async () => {
    const repository = mockRepository();
    repository.findById.mockResolvedValue(null);

    await expect(
      new UpdateProductService(repository).execute({
        productId: PRODUCT_ID,
        name: 'X',
      }),
    ).rejects.toBeInstanceOf(ProductNotFoundException);
    expect(repository.update).not.toHaveBeenCalled();
  });
});

describe('DiscontinueProductService', () => {
  it('marca el producto como descontinuado', async () => {
    const repository = mockRepository();
    repository.findById.mockResolvedValue(aProduct());
    repository.update.mockImplementation(async (p) => p);

    await new DiscontinueProductService(repository).execute(PRODUCT_ID);

    const [saved] = repository.update.mock.calls[0];
    expect(saved.status).toBe(ProductStatus.DESCONTINUADO);
  });

  it('es idempotente: descontinuar dos veces no falla ni reescribe', async () => {
    const repository = mockRepository();
    repository.findById.mockResolvedValue(
      aProduct({ status: ProductStatus.DESCONTINUADO }),
    );

    await expect(
      new DiscontinueProductService(repository).execute(PRODUCT_ID),
    ).resolves.toBeUndefined();
    expect(repository.update).not.toHaveBeenCalled();
  });

  it('falla si el producto no existe', async () => {
    const repository = mockRepository();
    repository.findById.mockResolvedValue(null);

    await expect(
      new DiscontinueProductService(repository).execute(PRODUCT_ID),
    ).rejects.toBeInstanceOf(ProductNotFoundException);
  });
});
