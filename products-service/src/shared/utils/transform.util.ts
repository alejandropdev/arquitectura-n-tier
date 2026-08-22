import { Transform } from 'class-transformer';

import { normalizeText } from './slug.util';

/**
 * Decoradores de `class-transformer` reutilizables por los DTOs de cualquier
 * dominio. Centralizarlos evita repetir la misma lambda en cada campo y
 * mantiene el tipado (las lambdas sueltas devuelven `any`).
 */

/** Colapsa espacios y recorta. Deja intactos los valores que no son texto. */
export function TrimmedText(): PropertyDecorator {
  return Transform(({ value }: { value: unknown }): unknown =>
    typeof value === 'string' ? normalizeText(value) : value,
  );
}

/**
 * Como `TrimmedText`, pero convierte el texto vacio en `null`.
 * `undefined` se conserva para distinguir "no enviado" de "limpiar el campo".
 */
export function OptionalText(): PropertyDecorator {
  return Transform(({ value }: { value: unknown }): unknown => {
    if (value === undefined || value === null) return value;
    if (typeof value !== 'string') return value;
    const text = normalizeText(value);
    return text.length > 0 ? text : null;
  });
}

/** Normaliza a mayusculas (usado por `order=asc` -> `ASC`). */
export function UpperCaseText(): PropertyDecorator {
  return Transform(({ value }: { value: unknown }): unknown =>
    typeof value === 'string' ? value.toUpperCase() : value,
  );
}
