import { Injectable } from '@nestjs/common';

import { ProductRepository } from '@domain/products/contracts/repositories/product.repository';
import {
  ListProductsQuery,
  ListProductsUseCase,
} from '@domain/products/contracts/use-cases/list-products.use-case';
import { Product } from '@domain/products/entities/product.entity';
import {
  buildPaginatedResult,
  PaginatedResult,
} from '@shared/pagination/paginated-result';

@Injectable()
export class ListProductsService extends ListProductsUseCase {
  constructor(private readonly products: ProductRepository) {
    super();
  }

  async execute(query: ListProductsQuery): Promise<PaginatedResult<Product>> {
    const { page, size, ...criteria } = query;
    const { items, total } = await this.products.search(criteria, {
      skip: (page - 1) * size,
      take: size,
    });

    return buildPaginatedResult(items, total, page, size);
  }
}
