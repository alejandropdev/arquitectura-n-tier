import { randomUUID } from 'node:crypto';

import {
  ProductRepository,
  ProductSearchCriteria,
} from '@domain/products/contracts/repositories/product.repository';
import { ProductStatus } from '@domain/products/entities/product-status.enum';
import { Product } from '@domain/products/entities/product.entity';
import { PageParams, PageSlice } from '@shared/pagination/pagination.types';

interface Row {
  productId: string;
  name: string;
  description: string | null;
  brand: string | null;
  categoryId: string;
  status: ProductStatus;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Doble de prueba del puerto `ProductRepository`.
 *
 * Que exista y sea trivial de escribir es la evidencia de que el puerto cumple
 * su proposito: los casos de uso y el API se pueden ejercitar completos sin
 * Postgres de por medio.
 */
export class InMemoryProductRepository extends ProductRepository {
  private readonly rows = new Map<string, Row>();
  private sequence = 0;

  async create(product: Product): Promise<Product> {
    const now = new Date(Date.now() + this.sequence++);
    const row: Row = {
      productId: randomUUID(),
      name: product.name,
      description: product.description,
      brand: product.brand,
      categoryId: product.categoryId,
      status: product.status,
      createdAt: now,
      updatedAt: now,
    };
    this.rows.set(row.productId, row);
    return Product.rehydrate({ ...row });
  }

  async findById(productId: string): Promise<Product | null> {
    const row = this.rows.get(productId);
    return row ? Product.rehydrate({ ...row }) : null;
  }

  async search(
    criteria: ProductSearchCriteria,
    page: PageParams,
  ): Promise<PageSlice<Product>> {
    let rows = [...this.rows.values()];

    if (criteria.categoryId) {
      rows = rows.filter((r) => r.categoryId === criteria.categoryId);
    }
    if (criteria.brand) {
      const brand = criteria.brand.toLowerCase();
      rows = rows.filter((r) => r.brand?.toLowerCase() === brand);
    }
    if (criteria.search) {
      const needle = criteria.search.toLowerCase();
      rows = rows.filter((r) => r.name.toLowerCase().includes(needle));
    }
    if (criteria.status) {
      rows = rows.filter((r) => r.status === criteria.status);
    } else if (!criteria.includeDiscontinued) {
      rows = rows.filter((r) => r.status !== ProductStatus.DESCONTINUADO);
    }

    const direction = criteria.order === 'ASC' ? 1 : -1;
    rows.sort((a, b) => {
      const left = criteria.sortBy === 'name' ? a.name : a.createdAt.getTime();
      const right = criteria.sortBy === 'name' ? b.name : b.createdAt.getTime();
      if (left === right) return a.productId.localeCompare(b.productId);
      return left > right ? direction : -direction;
    });

    const items = rows
      .slice(page.skip, page.skip + page.take)
      .map((row) => Product.rehydrate({ ...row }));

    return { items, total: rows.length };
  }

  async update(product: Product): Promise<Product> {
    const existing = this.rows.get(product.productId);
    if (!existing) {
      throw new Error(`Producto inexistente: ${product.productId}`);
    }

    const row: Row = {
      ...existing,
      name: product.name,
      description: product.description,
      brand: product.brand,
      categoryId: product.categoryId,
      status: product.status,
      updatedAt: new Date(),
    };
    this.rows.set(row.productId, row);
    return Product.rehydrate({ ...row });
  }
}
