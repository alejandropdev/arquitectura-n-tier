import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

import { CreateProductService } from '@application/products/use-cases/create-product.service';
import { DiscontinueProductService } from '@application/products/use-cases/discontinue-product.service';
import { GetProductByIdService } from '@application/products/use-cases/get-product-by-id.service';
import { ListProductsService } from '@application/products/use-cases/list-products.service';
import { UpdateProductService } from '@application/products/use-cases/update-product.service';
import { ProductRepository } from '@domain/products/contracts/repositories/product.repository';
import { CreateProductUseCase } from '@domain/products/contracts/use-cases/create-product.use-case';
import { DiscontinueProductUseCase } from '@domain/products/contracts/use-cases/discontinue-product.use-case';
import { GetProductByIdUseCase } from '@domain/products/contracts/use-cases/get-product-by-id.use-case';
import { ListProductsUseCase } from '@domain/products/contracts/use-cases/list-products.use-case';
import { UpdateProductUseCase } from '@domain/products/contracts/use-cases/update-product.use-case';
import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';
import { ProductsController } from '@infrastructure/products/http/products.controller';
import { TypeOrmProductRepository } from '@infrastructure/products/repositories/typeorm-product.repository';

/**
 * Cableado del dominio de productos.
 *
 * Las clases abstractas del dominio se usan como token de inyeccion: el
 * controller pide `CreateProductUseCase` y los casos de uso piden
 * `ProductRepository`, sin conocer jamas la clase concreta. Sustituir el
 * adaptador de persistencia (por ejemplo, uno con cache) es cambiar una linea
 * de este `providers`.
 */
@Module({
  imports: [TypeOrmModule.forFeature([ProductOrmEntity])],
  controllers: [ProductsController],
  providers: [
    { provide: ProductRepository, useClass: TypeOrmProductRepository },
    { provide: CreateProductUseCase, useClass: CreateProductService },
    { provide: ListProductsUseCase, useClass: ListProductsService },
    { provide: GetProductByIdUseCase, useClass: GetProductByIdService },
    { provide: UpdateProductUseCase, useClass: UpdateProductService },
    { provide: DiscontinueProductUseCase, useClass: DiscontinueProductService },
  ],
  exports: [ProductRepository],
})
export class ProductsModule {}
