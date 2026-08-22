import { AppError } from '@shared/errors/app.error';
import { ErrorCode } from '@shared/errors/error-codes';

/**
 * La categoria referenciada no existe. Se detecta al traducir la violacion de
 * la llave foranea de Postgres: el dominio de productos no consulta categorias,
 * la integridad la garantiza la BD (decision de alcance del taller).
 */
export class ProductCategoryNotFoundException extends AppError {
  constructor(categoryId: string) {
    super(
      `No existe una categoria con id ${categoryId}`,
      ErrorCode.PRODUCT_CATEGORY_NOT_FOUND,
      { categoryId },
    );
  }
}
