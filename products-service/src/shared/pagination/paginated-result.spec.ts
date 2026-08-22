import { buildPaginationMeta } from './paginated-result';
import { PaginationQueryDto } from './pagination-query.dto';

describe('buildPaginationMeta', () => {
  it('calcula totalPages redondeando hacia arriba', () => {
    expect(buildPaginationMeta(1, 10, 25).totalPages).toBe(3);
  });

  it('marca hasNext solo si quedan paginas por delante', () => {
    expect(buildPaginationMeta(1, 10, 25).hasNext).toBe(true);
    expect(buildPaginationMeta(3, 10, 25).hasNext).toBe(false);
  });

  it('marca hasPrevious solo a partir de la segunda pagina', () => {
    expect(buildPaginationMeta(1, 10, 25).hasPrevious).toBe(false);
    expect(buildPaginationMeta(2, 10, 25).hasPrevious).toBe(true);
  });

  it('un resultado vacio no reporta paginas ni vecinos', () => {
    expect(buildPaginationMeta(1, 20, 0)).toEqual({
      page: 1,
      size: 20,
      total: 0,
      totalPages: 0,
      hasNext: false,
      hasPrevious: false,
    });
  });
});

describe('PaginationQueryDto', () => {
  it('traduce page/size a skip/take', () => {
    const dto = new PaginationQueryDto();
    dto.page = 3;
    dto.size = 15;

    expect(dto.toPageParams()).toEqual({ skip: 30, take: 15 });
  });

  it('usa los valores por defecto cuando no se envian', () => {
    expect(new PaginationQueryDto().toPageParams()).toEqual({
      skip: 0,
      take: 20,
    });
  });
});
