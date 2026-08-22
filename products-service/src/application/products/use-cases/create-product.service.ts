import { Injectable } from '@nestjs/common';

import { ProductRepository } from '@domain/products/contracts/repositories/product.repository';
import {
  CreateProductCommand,
  CreateProductUseCase,
} from '@domain/products/contracts/use-cases/create-product.use-case';
import { Product } from '@domain/products/entities/product.entity';

@Injectable()
export class CreateProductService extends CreateProductUseCase {
  constructor(private readonly products: ProductRepository) {
    super();
  }

  async execute(command: CreateProductCommand): Promise<Product> {
    const product = Product.create(command);
    return this.products.create(product);
  }
}
