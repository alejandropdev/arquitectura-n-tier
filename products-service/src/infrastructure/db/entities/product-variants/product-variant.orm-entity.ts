import {
  Check,
  Column,
  CreateDateColumn,
  Entity,
  JoinColumn,
  ManyToOne,
  OneToMany,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';

import { InventoryOrmEntity } from '@infrastructure/db/entities/inventory/inventory.orm-entity';
import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';

/**
 * El precio vive aqui, no en `products`: dos variantes del mismo producto
 * (talla, color) pueden costar distinto. Asi lo fija el diagrama de BD.
 */
@Entity({ name: 'product_variants' })
@Check('chk_product_variants_price_non_negative', '"price" >= 0')
export class ProductVariantOrmEntity {
  @PrimaryGeneratedColumn('uuid', { name: 'variant_id' })
  variantId: string;

  @Column({ name: 'product_id', type: 'uuid' })
  productId: string;

  @Column({ name: 'sku', type: 'varchar', length: 64, unique: true })
  sku: string;

  @Column({ name: 'color', type: 'varchar', length: 50, nullable: true })
  color: string | null;

  @Column({ name: 'size', type: 'varchar', length: 50, nullable: true })
  size: string | null;

  @Column({ name: 'price', type: 'numeric', precision: 12, scale: 2 })
  price: string;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt: Date;

  /** CASCADE: las variantes no tienen sentido sin su producto. */
  @ManyToOne(() => ProductOrmEntity, (product) => product.variants, {
    onDelete: 'CASCADE',
  })
  @JoinColumn({ name: 'product_id' })
  product: ProductOrmEntity;

  @OneToMany(() => InventoryOrmEntity, (inventory) => inventory.variant)
  inventory: InventoryOrmEntity[];
}
