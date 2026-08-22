import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  HttpStatus,
  Param,
  Patch,
  Post,
  Query,
} from '@nestjs/common';

import { CreateProductDto } from '@application/products/dtos/create-product.dto';
import { ListProductsQueryDto } from '@application/products/dtos/list-products-query.dto';
import { ProductIdParamDto } from '@application/products/dtos/product-id.param.dto';
import { ProductResponseDto } from '@application/products/dtos/product-response.dto';
import { UpdateProductDto } from '@application/products/dtos/update-product.dto';
import { ProductMapper } from '@application/products/mappers/product.mapper';
import { CreateProductUseCase } from '@domain/products/contracts/use-cases/create-product.use-case';
import { DiscontinueProductUseCase } from '@domain/products/contracts/use-cases/discontinue-product.use-case';
import { GetProductByIdUseCase } from '@domain/products/contracts/use-cases/get-product-by-id.use-case';
import { ListProductsUseCase } from '@domain/products/contracts/use-cases/list-products.use-case';
import { UpdateProductUseCase } from '@domain/products/contracts/use-cases/update-product.use-case';
import { PaginatedResult } from '@shared/pagination/paginated-result';

/**
 * Adaptador de entrada HTTP. Solo traduce peticion -> comando y entidad ->
 * respuesta: no contiene reglas de negocio.
 *
 * PUNTO DE EXTENSION DE AUTH (kickoff, seccion 3 del plan de taller):
 * la proteccion de estas rutas se activa agregando aqui
 * `@UseGuards(AuthGuard)` a nivel de clase (o por metodo) y registrando el
 * guard en `ProductsModule`. Ni los casos de uso ni el dominio cambian.
 * Ver `documentation/endpoints.md`.
 */
@Controller('products')
export class ProductsController {
  constructor(
    private readonly createProduct: CreateProductUseCase,
    private readonly listProducts: ListProductsUseCase,
    private readonly getProductById: GetProductByIdUseCase,
    private readonly updateProduct: UpdateProductUseCase,
    private readonly discontinueProduct: DiscontinueProductUseCase,
  ) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async create(@Body() dto: CreateProductDto): Promise<ProductResponseDto> {
    const product = await this.createProduct.execute(
      ProductMapper.toCreateCommand(dto),
    );
    return ProductMapper.toResponse(product);
  }

  @Get()
  async list(
    @Query() query: ListProductsQueryDto,
  ): Promise<PaginatedResult<ProductResponseDto>> {
    const result = await this.listProducts.execute(
      ProductMapper.toListQuery(query),
    );
    return ProductMapper.toPaginatedResponse(result);
  }

  @Get(':id')
  async findOne(
    @Param() params: ProductIdParamDto,
  ): Promise<ProductResponseDto> {
    const product = await this.getProductById.execute(params.id);
    return ProductMapper.toResponse(product);
  }

  @Patch(':id')
  async update(
    @Param() params: ProductIdParamDto,
    @Body() dto: UpdateProductDto,
  ): Promise<ProductResponseDto> {
    const product = await this.updateProduct.execute(
      ProductMapper.toUpdateCommand(params.id, dto),
    );
    return ProductMapper.toResponse(product);
  }

  /** No borra la fila: marca el producto como `descontinuado`. */
  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  async discontinue(@Param() params: ProductIdParamDto): Promise<void> {
    await this.discontinueProduct.execute(params.id);
  }
}
