/** Traducción de `page`/`size` al lenguaje que entiende un repositorio. */
export interface PageParams {
  readonly skip: number;
  readonly take: number;
}

export interface PaginationMeta {
  readonly page: number;
  readonly size: number;
  readonly total: number;
  readonly totalPages: number;
  readonly hasNext: boolean;
  readonly hasPrevious: boolean;
}

/** Lo que devuelve un repositorio al listar: la página y el total sin paginar. */
export interface PageSlice<T> {
  readonly items: T[];
  readonly total: number;
}
