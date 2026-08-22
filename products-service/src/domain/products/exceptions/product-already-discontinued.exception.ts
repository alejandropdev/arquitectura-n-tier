import { AppError } from '@shared/errors/app.error';
import { ErrorCode } from '@shared/errors/error-codes';

export class ProductAlreadyDiscontinuedException extends AppError {
  constructor(productId: string) {
    super(
      `El producto ${productId} ya esta descontinuado`,
      ErrorCode.PRODUCT_ALREADY_DISCONTINUED,
      { productId },
    );
  }
}
