import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { ILike, Not, Repository } from 'typeorm';

import {
  ProductRepository,
  ProductSearchCriteria,
} from '@domain/products/contracts/repositories/product.repository';
import { ProductStatus } from '@domain/products/entities/product-status.enum';
import { Product } from '@domain/products/entities/product.entity';
import { ProductCategoryNotFoundException } from '@domain/products/exceptions/product-category-not-found.exception';
import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';
import { ProductOrmMapper } from '@infrastructure/products/mappers/product.orm-mapper';
import { PageParams, PageSlice } from '@shared/pagination/pagination.types';

/** Violacion de llave foranea en Postgres. */
const PG_FOREIGN_KEY_VIOLATION = '23503';

/** Columnas por las que se puede ordenar, mapeadas a su nombre en la tabla. */
const SORT_COLUMNS: Record<string, keyof ProductOrmEntity> = {
  createdAt: 'createdAt',
  name: 'name',
};

/**
 * Adaptador de persistencia: implementacion concreta del puerto
 * `ProductRepository` sobre Postgres/TypeORM. Es la unica clase del servicio
 * que sabe que existe SQL.
 */
@Injectable()
export class TypeOrmProductRepository extends ProductRepository {
  constructor(
    @InjectRepository(ProductOrmEntity)
    private readonly repository: Repository<ProductOrmEntity>,
  ) {
    super();
  }

  async create(product: Product): Promise<Product> {
    const row = this.repository.create(ProductOrmMapper.toPersistence(product));

    try {
      const saved = await this.repository.save(row);
      return ProductOrmMapper.toDomain(saved);
    } catch (error) {
      throw this.translate(error, product.categoryId);
    }
  }

  async findById(productId: string): Promise<Product | null> {
    const row = await this.repository.findOne({ where: { productId } });
    return row ? ProductOrmMapper.toDomain(row) : null;
  }

  async search(
    criteria: ProductSearchCriteria,
    page: PageParams,
  ): Promise<PageSlice<Product>> {
    const where: Record<string, unknown> = {};

    if (criteria.categoryId) where.categoryId = criteria.categoryId;
    if (criteria.brand) where.brand = ILike(criteria.brand);
    if (criteria.search) where.name = ILike(`%${criteria.search}%`);

    if (criteria.status) {
      where.status = criteria.status;
    } else if (!criteria.includeDiscontinued) {
      // Por defecto el catalogo no muestra productos retirados.
      where.status = Not(ProductStatus.DESCONTINUADO);
    }

    const sortColumn = SORT_COLUMNS[criteria.sortBy] ?? 'createdAt';

    const [rows, total] = await this.repository.findAndCount({
      where,
      order: { [sortColumn]: criteria.order, productId: 'ASC' },
      skip: page.skip,
      take: page.take,
    });

    return { items: rows.map((row) => ProductOrmMapper.toDomain(row)), total };
  }

  async update(product: Product): Promise<Product> {
    try {
      await this.repository.update(
        { productId: product.productId },
        ProductOrmMapper.toPersistence(product),
      );
    } catch (error) {
      throw this.translate(error, product.categoryId);
    }

    const updated = await this.repository.findOneOrFail({
      where: { productId: product.productId },
    });
    return ProductOrmMapper.toDomain(updated);
  }

  /**
   * Traduce errores del driver a errores de dominio, para que el caso de uso
   * nunca vea un error de Postgres.
   */
  private translate(error: unknown, categoryId: string): unknown {
    const code =
      (error as { code?: string; driverError?: { code?: string } })?.driverError
        ?.code ?? (error as { code?: string })?.code;

    if (code === PG_FOREIGN_KEY_VIOLATION) {
      return new ProductCategoryNotFoundException(categoryId);
    }
    return error;
  }
}
