import { ProductStatus } from '@domain/products/entities/product-status.enum';
import { Product } from '@domain/products/entities/product.entity';

/**
 * Comando de entrada del caso de uso. Es un tipo de dominio, no un DTO HTTP:
 * los DTOs de `application` se traducen a esto en el mapper, de modo que el
 * contrato sobreviva a cambios en el transporte.
 */
export interface CreateProductCommand {
  readonly name: string;
  readonly description?: string | null;
  readonly brand?: string | null;
  readonly categoryId: string;
  readonly status?: ProductStatus;
}

export abstract class CreateProductUseCase {
  abstract execute(command: CreateProductCommand): Promise<Product>;
}
