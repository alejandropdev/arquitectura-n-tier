import { Column, Entity, OneToMany, PrimaryGeneratedColumn } from 'typeorm';

import { InventoryOrmEntity } from '@infrastructure/db/entities/inventory/inventory.orm-entity';

@Entity({ name: 'warehouses' })
export class WarehouseOrmEntity {
  @PrimaryGeneratedColumn('uuid', { name: 'warehouse_id' })
  warehouseId: string;

  @Column({ name: 'name', type: 'varchar', length: 120 })
  name: string;

  @Column({ name: 'address', type: 'varchar', length: 200 })
  address: string;

  @Column({ name: 'city', type: 'varchar', length: 100 })
  city: string;

  @OneToMany(() => InventoryOrmEntity, (inventory) => inventory.warehouse)
  inventory: InventoryOrmEntity[];
}
