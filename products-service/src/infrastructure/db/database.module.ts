import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

import { dataSourceOptions } from './data-source';
import { SeedersModule } from './seeders/seeders.module';

/**
 * Unico punto donde el servicio se conecta a Postgres. Cambiar de motor o de
 * estrategia de conexion se hace aqui, sin tocar dominio ni casos de uso.
 */
@Module({
  imports: [
    TypeOrmModule.forRoot({ ...dataSourceOptions, autoLoadEntities: false }),
    SeedersModule,
  ],
})
export class DatabaseModule {}
