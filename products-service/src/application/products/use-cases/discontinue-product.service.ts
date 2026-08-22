import { Injectable } from '@nestjs/common';

import { ProductRepository } from '@domain/products/contracts/repositories/product.repository';
import { DiscontinueProductUseCase } from '@domain/products/contracts/use-cases/discontinue-product.use-case';
import { ProductNotFoundException } from '@domain/products/exceptions/product-not-found.exception';

@Injectable()
export class DiscontinueProductService extends DiscontinueProductUseCase {
  constructor(private readonly products: ProductRepository) {
    super();
  }

  async execute(productId: string): Promise<void> {
    const product = await this.products.findById(productId);
    if (!product) {
      throw new ProductNotFoundException(productId);
    }

    // Idempotente: si ya estaba descontinuado, no hay nada que hacer ni que
    // fallar. DELETE se repite sin efectos secundarios.
    if (product.isDiscontinued) {
      return;
    }

    product.discontinue();
    await this.products.update(product);
  }
}
