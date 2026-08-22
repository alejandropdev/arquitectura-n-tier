import { ProductSearchCriteria } from '@domain/products/contracts/repositories/product.repository';
import { Product } from '@domain/products/entities/product.entity';
import { PaginatedResult } from '@shared/pagination/paginated-result';

export interface ListProductsQuery extends ProductSearchCriteria {
  readonly page: number;
  readonly size: number;
}

export abstract class ListProductsUseCase {
  abstract execute(query: ListProductsQuery): Promise<PaginatedResult<Product>>;
}
