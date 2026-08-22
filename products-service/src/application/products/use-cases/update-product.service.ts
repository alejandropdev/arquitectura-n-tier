import { Injectable } from '@nestjs/common';

import { ProductRepository } from '@domain/products/contracts/repositories/product.repository';
import {
  UpdateProductCommand,
  UpdateProductUseCase,
} from '@domain/products/contracts/use-cases/update-product.use-case';
import { Product } from '@domain/products/entities/product.entity';
import { ProductNotFoundException } from '@domain/products/exceptions/product-not-found.exception';

@Injectable()
export class UpdateProductService extends UpdateProductUseCase {
  constructor(private readonly products: ProductRepository) {
    super();
  }

  async execute(command: UpdateProductCommand): Promise<Product> {
    const product = await this.products.findById(command.productId);
    if (!product) {
      throw new ProductNotFoundException(command.productId);
    }

    // `undefined` = campo ausente en el PATCH; `null` = limpiar el campo.
    if (command.name !== undefined) product.rename(command.name);
    if (command.description !== undefined) {
      product.changeDescription(command.description);
    }
    if (command.brand !== undefined) product.changeBrand(command.brand);
    if (command.categoryId !== undefined) {
      product.moveToCategory(command.categoryId);
    }
    if (command.status !== undefined) product.changeStatus(command.status);

    return this.products.update(product);
  }
}
