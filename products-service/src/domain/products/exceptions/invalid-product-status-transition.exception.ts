import { ProductStatus } from '@domain/products/entities/product-status.enum';
import { AppError } from '@shared/errors/app.error';
import { ErrorCode } from '@shared/errors/error-codes';

export class InvalidProductStatusTransitionException extends AppError {
  constructor(from: ProductStatus, to: ProductStatus) {
    super(
      `No se permite pasar un producto de "${from}" a "${to}"`,
      ErrorCode.PRODUCT_INVALID_STATUS_TRANSITION,
      { from, to },
    );
  }
}
