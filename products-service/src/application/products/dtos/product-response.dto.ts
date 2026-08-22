import { ProductStatus } from '@domain/products/entities/product-status.enum';

/** Forma exacta con la que un producto sale del servicio. */
export class ProductResponseDto {
  id: string;
  name: string;
  description: string | null;
  brand: string | null;
  categoryId: string;
  status: ProductStatus;
  createdAt: string;
  updatedAt: string;
}
