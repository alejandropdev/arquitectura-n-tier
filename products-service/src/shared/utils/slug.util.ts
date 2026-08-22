/**
 * Normaliza un texto a slug (`Ropa de Nino` -> `ropa-de-nino`).
 * Vive en shared porque lo necesitaran tanto `categories` como futuras
 * busquedas por nombre en `products`.
 */
export function toSlug(value: string): string {
  return value
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/** Colapsa espacios y recorta; usado por los DTOs antes de persistir texto. */
export function normalizeText(value: string): string {
  return value.replace(/\s+/g, ' ').trim();
}
