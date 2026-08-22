import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ORM_ENTITIES } from '@infrastructure/db/entities/orm-entities';
import { CategoriesSeeder } from './00-categories.seeder';
import { SuppliersSeeder } from './01-suppliers.seeder';
import { ProductsSeeder } from './02-products.seeder';
import { ProductSuppliersSeeder } from './03-product-suppliers.seeder';
import { WarehousesSeeder } from './04-warehouses.seeder';
import { ProductVariantsSeeder } from './05-product-variants.seeder';
import { InventorySeeder } from './06-inventory.seeder';
import { AuditLogsSeeder } from './07-audit-logs.seeder';
import { SeederService } from './seeder.service';

@Module({
  imports: [TypeOrmModule.forFeature(ORM_ENTITIES)],
  providers: [
    CategoriesSeeder,
    SuppliersSeeder,
    ProductsSeeder,
    ProductSuppliersSeeder,
    WarehousesSeeder,
    ProductVariantsSeeder,
    InventorySeeder,
    AuditLogsSeeder,
    SeederService,
  ],
})
export class SeedersModule {}
