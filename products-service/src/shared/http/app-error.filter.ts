import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';

import { httpStatusFor } from './http-status.map';
import { AppError } from '@shared/errors/app.error';
import { ErrorCode } from '@shared/errors/error-codes';

interface ErrorBody {
  code: string;
  message: string;
  path: string;
  timestamp: string;
  details?: unknown;
}

/**
 * Filtro global: convierte cualquier excepción en un cuerpo uniforme
 * `{ code, message, path, timestamp }`.
 *
 * - `AppError` (errores de dominio) -> status según `http-status.map`.
 * - `HttpException` (incluye el 400 del ValidationPipe) -> se respeta su status.
 * - Cualquier otra cosa -> 500 sin filtrar el mensaje interno al cliente.
 */
@Catch()
export class AppErrorFilter implements ExceptionFilter {
  private readonly logger = new Logger(AppErrorFilter.name);

  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const { status, body } = this.describe(exception, request.url);

    if (status >= HttpStatus.INTERNAL_SERVER_ERROR) {
      this.logger.error(
        `${request.method} ${request.url} -> ${status}`,
        exception instanceof Error ? exception.stack : String(exception),
      );
    } else {
      this.logger.warn(
        `${request.method} ${request.url} -> ${status} (${body.code})`,
      );
    }

    response.status(status).json(body);
  }

  private describe(
    exception: unknown,
    path: string,
  ): { status: HttpStatus; body: ErrorBody } {
    const timestamp = new Date().toISOString();

    if (exception instanceof AppError) {
      return {
        status: httpStatusFor(exception.code),
        body: {
          code: exception.code,
          message: exception.message,
          path,
          timestamp,
          ...(exception.details ? { details: exception.details } : {}),
        },
      };
    }

    if (exception instanceof HttpException) {
      const status: number = exception.getStatus();
      const { message, errors } = this.readHttpMessage(exception);

      return {
        status,
        body: {
          code:
            status === Number(HttpStatus.BAD_REQUEST)
              ? ErrorCode.VALIDATION_ERROR
              : exception.name,
          message,
          path,
          timestamp,
          ...(errors ? { details: { errors } } : {}),
        },
      };
    }

    return {
      status: HttpStatus.INTERNAL_SERVER_ERROR,
      body: {
        code: ErrorCode.INTERNAL_ERROR,
        message: 'Error interno del servicio',
        path,
        timestamp,
      },
    };
  }

  /**
   * El cuerpo de una `HttpException` puede ser un string, o el objeto que arma
   * el `ValidationPipe` con `message: string[]`. Se normalizan ambos a un
   * mensaje unico, conservando la lista completa como `details.errors`.
   */
  private readHttpMessage(exception: HttpException): {
    message: string;
    errors?: string[];
  } {
    const payload: unknown = exception.getResponse();

    if (typeof payload === 'string') {
      return { message: payload };
    }

    const raw =
      typeof payload === 'object' && payload !== null
        ? (payload as { message?: unknown }).message
        : undefined;

    if (Array.isArray(raw)) {
      const errors = raw.map((item) => String(item));
      return { message: errors.join('; '), errors };
    }

    return { message: typeof raw === 'string' ? raw : exception.message };
  }
}
