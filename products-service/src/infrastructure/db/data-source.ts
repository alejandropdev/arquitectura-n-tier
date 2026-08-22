import { config as loadEnv } from 'dotenv';
import { DataSource, DataSourceOptions } from 'typeorm';

import { ORM_ENTITIES } from '@infrastructure/db/entities/orm-entities';
import { envConfig } from '@shared/config/env.config';

loadEnv();

const db = envConfig().database;

/**
 * Opciones compartidas por el CLI de TypeORM (migraciones) y por el
 * `DatabaseModule` de Nest, para que ambos vean exactamente el mismo esquema.
 *
 * `synchronize` siempre en false: el esquema solo cambia por migraciones
 * versionadas, nunca por arranque del servicio.
 */
export const dataSourceOptions: DataSourceOptions = {
  type: 'postgres',
  host: db.host,
  port: db.port,
  username: db.username,
  password: db.password,
  database: db.database,
  entities: ORM_ENTITIES,
  migrations: [__dirname + '/migrations/*.{ts,js}'],
  migrationsTableName: 'migrations',
  synchronize: false,
  logging: db.logging,
  // Timeouts explicitos servicio -> BD (requerimiento 6 del taller).
  connectTimeoutMS: db.connectTimeoutMs,
  extra: {
    statement_timeout: db.statementTimeoutMs,
    query_timeout: db.statementTimeoutMs,
  },
};

/** Export por defecto: es lo que consume `typeorm migration:generate/run`. */
export default new DataSource(dataSourceOptions);
