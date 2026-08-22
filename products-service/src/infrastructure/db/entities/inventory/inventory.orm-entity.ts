import {
  Check,
  Column,
  Entity,
  JoinColumn,
  ManyToOne,
  PrimaryGeneratedColumn,
  Unique,
  UpdateDateColumn,
} from 'typeorm';

import { ProductVariantOrmEntity } from '@infrastructure/db/entities/product-variants/product-variant.orm-entity';
import { WarehouseOrmEntity } from '@infrastructure/db/entities/warehouses/warehouse.orm-entity';

/**
 * Existencias de una variante en una bodega. El stock vive aqui (no en
 * `products`): el mismo producto puede tener cantidades distintas por bodega.
 */
@Entity({ name: 'inventory' })
@Unique('uq_inventory_variant_warehouse', ['variantId', 'warehouseId'])
@Check('chk_inventory_quantity_non_negative', '"quantity_on_hand" >= 0')
@Check('chk_inventory_reorder_level_non_negative', '"reorder_level" >= 0')
export class InventoryOrmEntity {
  @PrimaryGeneratedColumn('uuid', { name: 'inventory_id' })
  inventoryId: string;

  @Column({ name: 'variant_id', type: 'uuid' })
  variantId: string;

  @Column({ name: 'warehouse_id', type: 'uuid' })
  warehouseId: string;

  @Column({ name: 'quantity_on_hand', type: 'int', default: 0 })
  quantityOnHand: number;

  @Column({ name: 'reorder_level', type: 'int', default: 0 })
  reorderLevel: number;

  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt: Date;

  @ManyToOne(() => ProductVariantOrmEntity, (variant) => variant.inventory, {
    onDelete: 'CASCADE',
  })
  @JoinColumn({ name: 'variant_id' })
  variant: ProductVariantOrmEntity;

  @ManyToOne(() => WarehouseOrmEntity, (warehouse) => warehouse.inventory, {
    onDelete: 'RESTRICT',
  })
  @JoinColumn({ name: 'warehouse_id' })
  warehouse: WarehouseOrmEntity;
}
