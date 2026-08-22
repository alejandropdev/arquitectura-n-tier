/**
 * Configuración tipada del servicio, cargada una sola vez por `ConfigModule`.
 *
 * Los timeouts salen de aquí (no hardcodeados) porque el requerimiento 6 del
 * taller pide que sean explícitos y configurables por punto de integración.
 */
export interface DatabaseConfig {
  host: string;
  port: number;
  username: string;
  password: string;
  database: string;
  /** Timeout de conexión servicio -> BD, en milisegundos. */
  connectTimeoutMs: number;
  /** Timeout de una consulta, en milisegundos. */
  statementTimeoutMs: number;
  logging: boolean;
}

export interface AppConfig {
  port: number;
  nodeEnv: string;
  apiPrefix: string;
  instanceId: string;
  database: DatabaseConfig;
}

function num(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export const envConfig = (): AppConfig => ({
  port: num(process.env.PORT, 3000),
  nodeEnv: process.env.NODE_ENV ?? 'development',
  apiPrefix: process.env.API_PREFIX ?? 'api/v1',
  instanceId: process.env.INSTANCE_ID ?? 'products-service',
  database: {
    host: process.env.DB_HOST ?? 'localhost',
    port: num(process.env.DB_PORT, 5432),
    username: process.env.DB_USERNAME ?? 'products',
    password: process.env.DB_PASSWORD ?? 'products',
    database: process.env.DB_NAME ?? 'productsdb',
    connectTimeoutMs: num(process.env.DB_CONNECT_TIMEOUT_MS, 5000),
    statementTimeoutMs: num(process.env.DB_STATEMENT_TIMEOUT_MS, 5000),
    logging: process.env.DB_LOGGING === 'true',
  },
});
