import { PaginationMeta } from './pagination.types';

/** Forma de respuesta de cualquier listado paginado del servicio. */
export class PaginatedResult<T> {
  readonly data: T[];
  readonly meta: PaginationMeta;

  constructor(data: T[], meta: PaginationMeta) {
    this.data = data;
    this.meta = meta;
  }

  /** Aplica una transformación a los elementos conservando la misma metadata. */
  map<U>(fn: (item: T) => U): PaginatedResult<U> {
    return new PaginatedResult<U>(this.data.map(fn), this.meta);
  }
}

export function buildPaginationMeta(
  page: number,
  size: number,
  total: number,
): PaginationMeta {
  const totalPages = size > 0 ? Math.ceil(total / size) : 0;
  return {
    page,
    size,
    total,
    totalPages,
    hasNext: page < totalPages,
    hasPrevious: page > 1 && total > 0,
  };
}

export function buildPaginatedResult<T>(
  items: T[],
  total: number,
  page: number,
  size: number,
): PaginatedResult<T> {
  return new PaginatedResult<T>(items, buildPaginationMeta(page, size, total));
}
