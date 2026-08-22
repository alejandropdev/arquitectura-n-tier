import { ErrorCode } from './error-codes';

/**
 * Clase superior de la que extiende cualquier error propio del servicio.
 *
 * Vive en `shared` porque es transversal a todos los dominios: el dominio lanza
 * subclases de `AppError` sin conocer HTTP, y es la capa de infraestructura
 * (`AppErrorFilter`) la que traduce el `code` a un status. Así el dominio queda
 * libre de detalles de transporte.
 */
export abstract class AppError extends Error {
  readonly code: ErrorCode;

  /** Datos extra opcionales para el consumidor (ids involucrados, campos, etc.). */
  readonly details?: Record<string, unknown>;

  protected constructor(
    message: string,
    code: ErrorCode,
    details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = new.target.name;
    this.code = code;
    this.details = details;

    // Necesario para que `instanceof` funcione al extender Error transpilado.
    Object.setPrototypeOf(this, new.target.prototype);
    Error.captureStackTrace?.(this, new.target);
  }

  toJSON(): Record<string, unknown> {
    return {
      code: this.code,
      message: this.message,
      ...(this.details ? { details: this.details } : {}),
    };
  }
}
