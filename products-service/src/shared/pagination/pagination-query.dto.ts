import { Type } from 'class-transformer';
import { IsInt, IsOptional, Max, Min } from 'class-validator';

import { PageParams } from './pagination.types';

export const DEFAULT_PAGE = 1;
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

/**
 * Query params de paginación compartidos por todos los dominios.
 * Los DTOs de listado de cada dominio extienden de aquí y agregan sus filtros.
 */
export class PaginationQueryDto {
  @Type(() => Number)
  @IsInt({ message: 'page debe ser un número entero' })
  @Min(1, { message: 'page debe ser mayor o igual a 1' })
  @IsOptional()
  page: number = DEFAULT_PAGE;

  @Type(() => Number)
  @IsInt({ message: 'size debe ser un número entero' })
  @Min(1, { message: 'size debe ser mayor o igual a 1' })
  @Max(MAX_PAGE_SIZE, { message: `size no puede ser mayor a ${MAX_PAGE_SIZE}` })
  @IsOptional()
  size: number = DEFAULT_PAGE_SIZE;

  toPageParams(): PageParams {
    const page = this.page ?? DEFAULT_PAGE;
    const size = this.size ?? DEFAULT_PAGE_SIZE;
    return { skip: (page - 1) * size, take: size };
  }
}
