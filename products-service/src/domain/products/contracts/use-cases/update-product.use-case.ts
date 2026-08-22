import { ProductStatus } from '@domain/products/entities/product-status.enum';
import { Product } from '@domain/products/entities/product.entity';

/**
 * Actualizacion parcial: `undefined` significa "no tocar el campo", mientras
 * que `null` en `description`/`brand` significa "limpiar el campo".
 */
export interface UpdateProductCommand {
  readonly productId: string;
  readonly name?: string;
  readonly description?: string | null;
  readonly brand?: string | null;
  readonly categoryId?: string;
  readonly status?: ProductStatus;
}

export abstract class UpdateProductUseCase {
  abstract execute(command: UpdateProductCommand): Promise<Product>;
}
