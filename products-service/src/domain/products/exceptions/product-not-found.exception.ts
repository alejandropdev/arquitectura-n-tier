import { AppError } from '@shared/errors/app.error';
import { ErrorCode } from '@shared/errors/error-codes';

export class ProductNotFoundException extends AppError {
  constructor(productId: string) {
    super(
      `No existe un producto con id ${productId}`,
      ErrorCode.PRODUCT_NOT_FOUND,
      { productId },
    );
  }
}
