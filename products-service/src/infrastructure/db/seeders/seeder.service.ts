import { Injectable, OnApplicationBootstrap } from '@nestjs/common';
import { CategoriesSeeder } from './00-categories.seeder';
import { SuppliersSeeder } from './01-suppliers.seeder';
import { ProductsSeeder } from './02-products.seeder';
import { ProductSuppliersSeeder } from './03-product-suppliers.seeder';
import { WarehousesSeeder } from './04-warehouses.seeder';
import { ProductVariantsSeeder } from './05-product-variants.seeder';
import { InventorySeeder } from './06-inventory.seeder';
import { AuditLogsSeeder } from './07-audit-logs.seeder';
import { BaseSeeder } from './seeder.base';

@Injectable()
export class SeederService implements OnApplicationBootstrap {
  constructor(
    private categoriesSeeder: CategoriesSeeder,
    private suppliersSeeder: SuppliersSeeder,
    private productsSeeder: ProductsSeeder,
    private productSuppliersSeeder: ProductSuppliersSeeder,
    private warehousesSeeder: WarehousesSeeder,
    private productVariantsSeeder: ProductVariantsSeeder,
    private inventorySeeder: InventorySeeder,
    private auditLogsSeeder: AuditLogsSeeder,
  ) {}

  async onApplicationBootstrap(): Promise<void> {
    console.log('🌱 Iniciando seeders de la base de datos...\n');

    const seeders: BaseSeeder[] = [
      this.categoriesSeeder,
      this.suppliersSeeder,
      this.productsSeeder,
      this.productSuppliersSeeder,
      this.warehousesSeeder,
      this.productVariantsSeeder,
      this.inventorySeeder,
      this.auditLogsSeeder,
    ];

    try {
      for (const seeder of seeders) {
        await seeder.execute();
      }
      console.log('\n✅ Todos los seeders completados exitosamente.');
    } catch (error) {
      console.error('\n❌ Error durante la ejecución de seeders:', error);
      throw error;
    }
  }
}
