import { Product } from '@domain/products/entities/product.entity';

export abstract class GetProductByIdUseCase {
  /** Lanza `ProductNotFoundException` si no existe. */
  abstract execute(productId: string): Promise<Product>;
}
