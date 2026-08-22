import {
  Check,
  Column,
  Entity,
  JoinColumn,
  ManyToOne,
  PrimaryColumn,
} from 'typeorm';

import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';
import { SupplierOrmEntity } from '@infrastructure/db/entities/suppliers/supplier.orm-entity';

/**
 * Tabla puente producto <-> proveedor. La PK es compuesta, tal como en el
 * diagrama: un proveedor no puede aparecer dos veces para el mismo producto.
 */
@Entity({ name: 'product_suppliers' })
@Check('chk_product_suppliers_cost_non_negative', '"cost_price" >= 0')
export class ProductSupplierOrmEntity {
  @PrimaryColumn({ name: 'product_id', type: 'uuid' })
  productId: string;

  @PrimaryColumn({ name: 'supplier_id', type: 'uuid' })
  supplierId: string;

  @Column({ name: 'cost_price', type: 'numeric', precision: 12, scale: 2 })
  costPrice: string;

  @ManyToOne(() => ProductOrmEntity, (product) => product.suppliers, {
    onDelete: 'CASCADE',
  })
  @JoinColumn({ name: 'product_id' })
  product: ProductOrmEntity;

  @ManyToOne(() => SupplierOrmEntity, (supplier) => supplier.products, {
    onDelete: 'CASCADE',
  })
  @JoinColumn({ name: 'supplier_id' })
  supplier: SupplierOrmEntity;
}
