import { ProductStatus } from './product-status.enum';
import { Product } from './product.entity';
import { InvalidProductStatusTransitionException } from '@domain/products/exceptions/invalid-product-status-transition.exception';
import { ProductAlreadyDiscontinuedException } from '@domain/products/exceptions/product-already-discontinued.exception';

const CATEGORY_ID = '11111111-1111-4111-8111-111111111111';

function aProduct(status: ProductStatus) {
  return Product.rehydrate({
    productId: '22222222-2222-4222-8222-222222222222',
    name: 'Camiseta',
    description: null,
    brand: null,
    categoryId: CATEGORY_ID,
    status,
    createdAt: new Date('2026-01-01T00:00:00Z'),
    updatedAt: new Date('2026-01-01T00:00:00Z'),
  });
}

describe('Product', () => {
  it('normaliza los textos al crear y convierte vacio en null', () => {
    const product = Product.create({
      name: '  Camiseta  ',
      description: '   ',
      brand: '  Acme ',
      categoryId: CATEGORY_ID,
    });

    expect(product.name).toBe('Camiseta');
    expect(product.description).toBeNull();
    expect(product.brand).toBe('Acme');
  });

  it('descontinuar es una transicion terminal', () => {
    const product = aProduct(ProductStatus.DESCONTINUADO);

    expect(() => product.changeStatus(ProductStatus.ACTIVO)).toThrow(
      InvalidProductStatusTransitionException,
    );
  });

  it('rechaza descontinuar un producto ya descontinuado', () => {
    const product = aProduct(ProductStatus.DESCONTINUADO);

    expect(() => product.discontinue()).toThrow(
      ProductAlreadyDiscontinuedException,
    );
  });

  it('permite pasar de borrador a activo y actualiza updatedAt', () => {
    const product = aProduct(ProductStatus.BORRADOR);
    const before = product.updatedAt.getTime();

    product.changeStatus(ProductStatus.ACTIVO);

    expect(product.status).toBe(ProductStatus.ACTIVO);
    expect(product.updatedAt.getTime()).toBeGreaterThan(before);
  });

  it('cambiar al mismo status no hace nada', () => {
    const product = aProduct(ProductStatus.ACTIVO);
    const before = product.updatedAt.getTime();

    product.changeStatus(ProductStatus.ACTIVO);

    expect(product.updatedAt.getTime()).toBe(before);
  });
});
