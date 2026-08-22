/**
 * Catálogo único de códigos de error del servicio.
 *
 * El código es el contrato estable hacia los consumidores (gateway, web, otros
 * servicios): el mensaje puede cambiar de redacción, el código no. Cada dominio
 * agrupa sus códigos con su propio prefijo.
 */
export const ErrorCode = {
  // Genéricos / transversales
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',

  // Dominio: products
  PRODUCT_NOT_FOUND: 'PRODUCT_NOT_FOUND',
  PRODUCT_ALREADY_DISCONTINUED: 'PRODUCT_ALREADY_DISCONTINUED',
  PRODUCT_INVALID_STATUS_TRANSITION: 'PRODUCT_INVALID_STATUS_TRANSITION',
  PRODUCT_CATEGORY_NOT_FOUND: 'PRODUCT_CATEGORY_NOT_FOUND',
} as const;

export type ErrorCode = (typeof ErrorCode)[keyof typeof ErrorCode];
