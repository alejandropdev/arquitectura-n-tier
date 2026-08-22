import { Product } from '@domain/products/entities/product.entity';
import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';

/**
 * Frontera entre la fila de Postgres y la entidad de dominio. Existe para que
 * `Product` no tenga que llevar decoradores de TypeORM encima.
 */
export class ProductOrmMapper {
  static toDomain(row: ProductOrmEntity): Product {
    return Product.rehydrate({
      productId: row.productId,
      name: row.name,
      description: row.description,
      brand: row.brand,
      categoryId: row.categoryId,
      status: row.status,
      createdAt: row.createdAt,
      updatedAt: row.updatedAt,
    });
  }

  /**
   * Solo los campos que el dominio controla. El id y las marcas de tiempo las
   * asigna la BD, por eso no se envian al insertar.
   */
  static toPersistence(product: Product): Partial<ProductOrmEntity> {
    return {
      name: product.name,
      description: product.description,
      brand: product.brand,
      categoryId: product.categoryId,
      status: product.status,
    };
  }
}
