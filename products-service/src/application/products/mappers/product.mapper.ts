import { CreateProductDto } from '@application/products/dtos/create-product.dto';
import { ListProductsQueryDto } from '@application/products/dtos/list-products-query.dto';
import { ProductResponseDto } from '@application/products/dtos/product-response.dto';
import { UpdateProductDto } from '@application/products/dtos/update-product.dto';
import { CreateProductCommand } from '@domain/products/contracts/use-cases/create-product.use-case';
import { ListProductsQuery } from '@domain/products/contracts/use-cases/list-products.use-case';
import { UpdateProductCommand } from '@domain/products/contracts/use-cases/update-product.use-case';
import { ProductStatus } from '@domain/products/entities/product-status.enum';
import { Product } from '@domain/products/entities/product.entity';
import { PaginatedResult } from '@shared/pagination/paginated-result';

/**
 * Traduce entre el mundo HTTP (DTOs) y el mundo del dominio (comandos y
 * entidades). Es el unico lugar del servicio que conoce ambas formas.
 */
export class ProductMapper {
  static toCreateCommand(dto: CreateProductDto): CreateProductCommand {
    return {
      name: dto.name,
      description: dto.description,
      brand: dto.brand,
      categoryId: dto.categoryId,
      status: dto.status,
    };
  }

  static toUpdateCommand(
    productId: string,
    dto: UpdateProductDto,
  ): UpdateProductCommand {
    return {
      productId,
      name: dto.name,
      description: dto.description,
      brand: dto.brand,
      categoryId: dto.categoryId,
      status: dto.status,
    };
  }

  static toListQuery(dto: ListProductsQueryDto): ListProductsQuery {
    return {
      page: dto.page,
      size: dto.size,
      categoryId: dto.categoryId,
      status: dto.status,
      brand: dto.brand,
      search: dto.search,
      // Los descontinuados solo aparecen si se piden explicitamente.
      includeDiscontinued: dto.status === ProductStatus.DESCONTINUADO,
      sortBy: dto.sort,
      order: dto.order,
    };
  }

  static toResponse(product: Product): ProductResponseDto {
    return {
      id: product.productId,
      name: product.name,
      description: product.description,
      brand: product.brand,
      categoryId: product.categoryId,
      status: product.status,
      createdAt: product.createdAt.toISOString(),
      updatedAt: product.updatedAt.toISOString(),
    };
  }

  static toPaginatedResponse(
    result: PaginatedResult<Product>,
  ): PaginatedResult<ProductResponseDto> {
    return result.map((product) => ProductMapper.toResponse(product));
  }
}
