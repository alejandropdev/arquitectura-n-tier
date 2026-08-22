import { ProductStatus } from '@domain/products/entities/product-status.enum';
import { Product } from '@domain/products/entities/product.entity';
import { PageParams, PageSlice } from '@shared/pagination/pagination.types';

/** Criterios de busqueda del listado, en lenguaje de dominio (no SQL). */
export interface ProductSearchCriteria {
  readonly categoryId?: string;
  readonly status?: ProductStatus;
  readonly brand?: string;
  readonly search?: string;
  /** Si es false (default) se ocultan los productos descontinuados. */
  readonly includeDiscontinued?: boolean;
  readonly sortBy: ProductSortField;
  readonly order: SortOrder;
}

export type ProductSortField = 'createdAt' | 'name';
export type SortOrder = 'ASC' | 'DESC';

/**
 * Puerto de persistencia de productos.
 *
 * Es una clase abstracta (no una interface) a proposito: TypeScript borra las
 * interfaces en tiempo de ejecucion y Nest necesita un token real para
 * inyectar. Asi el token de DI y el contrato son la misma cosa, y el adaptador
 * concreto (TypeORM hoy, cache o cualquier otro manana) se cambia solo en el
 * `providers` del modulo. Este es el punto de extension que usa Andres para
 * enchufar cache/indices sin tocar los casos de uso.
 */
export abstract class ProductRepository {
  abstract create(product: Product): Promise<Product>;

  abstract findById(productId: string): Promise<Product | null>;

  abstract search(
    criteria: ProductSearchCriteria,
    page: PageParams,
  ): Promise<PageSlice<Product>>;

  abstract update(product: Product): Promise<Product>;
}
