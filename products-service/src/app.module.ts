import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';

import { CategoriesModule } from '@infrastructure/categories/categories.module';
import { DatabaseModule } from '@infrastructure/db/database.module';
import { ProductsModule } from '@infrastructure/products/products.module';
import { envConfig } from '@shared/config/env.config';
import { HealthModule } from '@shared/health/health.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true, load: [envConfig] }),
    DatabaseModule,
    HealthModule,
    // Un modulo por dominio: agregar `inventory` manana es agregar una linea.
    ProductsModule,
    CategoriesModule,
  ],
})
export class AppModule {}
