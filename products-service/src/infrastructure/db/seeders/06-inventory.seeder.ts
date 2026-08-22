import { Inject, Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { BaseSeeder } from './seeder.base';
import { InventoryOrmEntity } from '@infrastructure/db/entities/inventory/inventory.orm-entity';
import { ProductVariantOrmEntity } from '@infrastructure/db/entities/product-variants/product-variant.orm-entity';
import { WarehouseOrmEntity } from '@infrastructure/db/entities/warehouses/warehouse.orm-entity';

@Injectable()
export class InventorySeeder extends BaseSeeder {
  readonly name = 'inventory';

  constructor(@Inject(DataSource) dataSource: DataSource) {
    super(dataSource);
  }

  protected async run(): Promise<void> {
    const repository = this.dataSource.getRepository(InventoryOrmEntity);
    const variantRepo = this.dataSource.getRepository(ProductVariantOrmEntity);
    const warehouseRepo = this.dataSource.getRepository(WarehouseOrmEntity);

    const variants = await variantRepo.find();
    const warehouses = await warehouseRepo.find();

    const inventoryRecords: Partial<InventoryOrmEntity>[] = [];

    // Crear registros de inventario: cada variante en cada bodega con diferentes cantidades
    for (const variant of variants) {
      for (let i = 0; i < warehouses.length; i++) {
        const warehouse = warehouses[i];
        const quantity = Math.floor(Math.random() * 500) + 50; // Random entre 50 y 550
        const reorderLevel = Math.floor(quantity * 0.2); // 20% del stock

        inventoryRecords.push({
          variantId: variant.variantId,
          warehouseId: warehouse.warehouseId,
          quantityOnHand: quantity,
          reorderLevel: reorderLevel,
        });
      }
    }

    // Insertar en lotes para evitar problemas de conexión
    const batchSize = 100;
    for (let i = 0; i < inventoryRecords.length; i += batchSize) {
      const batch = inventoryRecords.slice(i, i + batchSize);
      await repository.save(batch);
    }
  }
}
