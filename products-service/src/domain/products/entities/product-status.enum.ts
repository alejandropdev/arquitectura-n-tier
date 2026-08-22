/**
 * Estados del ciclo de vida de un producto, tal como los fija el diagrama de BD.
 *
 *   borrador  -> producto en preparacion, no visible en el catalogo publico.
 *   activo    -> producto publicado y vendible.
 *   descontinuado -> retirado del catalogo (equivale al "delete" del API).
 */
export enum ProductStatus {
  BORRADOR = 'borrador',
  ACTIVO = 'activo',
  DESCONTINUADO = 'descontinuado',
}

export const PRODUCT_STATUSES: readonly ProductStatus[] =
  Object.values(ProductStatus);
