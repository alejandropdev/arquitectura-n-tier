import { Injectable } from '@nestjs/common';

import { ProductRepository } from '@domain/products/contracts/repositories/product.repository';
import { GetProductByIdUseCase } from '@domain/products/contracts/use-cases/get-product-by-id.use-case';
import { Product } from '@domain/products/entities/product.entity';
import { ProductNotFoundException } from '@domain/products/exceptions/product-not-found.exception';

@Injectable()
export class GetProductByIdService extends GetProductByIdUseCase {
  constructor(private readonly products: ProductRepository) {
    super();
  }

  async execute(productId: string): Promise<Product> {
    const product = await this.products.findById(productId);
    if (!product) {
      throw new ProductNotFoundException(productId);
    }
    return product;
  }
}
