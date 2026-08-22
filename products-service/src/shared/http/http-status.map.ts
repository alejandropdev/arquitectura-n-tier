import { HttpStatus } from '@nestjs/common';

import { ErrorCode } from '@shared/errors/error-codes';

/**
 * Única tabla que traduce códigos de error de dominio a status HTTP.
 * El dominio no sabe de HTTP; este mapa es el que lo sabe por él.
 */
const STATUS_BY_CODE: Record<ErrorCode, HttpStatus> = {
  [ErrorCode.INTERNAL_ERROR]: HttpStatus.INTERNAL_SERVER_ERROR,
  [ErrorCode.VALIDATION_ERROR]: HttpStatus.BAD_REQUEST,
  [ErrorCode.PRODUCT_NOT_FOUND]: HttpStatus.NOT_FOUND,
  [ErrorCode.PRODUCT_ALREADY_DISCONTINUED]: HttpStatus.CONFLICT,
  [ErrorCode.PRODUCT_INVALID_STATUS_TRANSITION]:
    HttpStatus.UNPROCESSABLE_ENTITY,
  [ErrorCode.PRODUCT_CATEGORY_NOT_FOUND]: HttpStatus.UNPROCESSABLE_ENTITY,
};

export function httpStatusFor(code: ErrorCode): HttpStatus {
  return STATUS_BY_CODE[code] ?? HttpStatus.INTERNAL_SERVER_ERROR;
}
