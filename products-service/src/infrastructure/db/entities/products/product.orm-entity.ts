import {
  Column,
  CreateDateColumn,
  Entity,
  JoinColumn,
  ManyToOne,
  OneToMany,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';

import { ProductStatus } from '@domain/products/entities/product-status.enum';
import { CategoryOrmEntity } from '@infrastructure/db/entities/categories/category.orm-entity';
import { ProductAuditLogOrmEntity } from '@infrastructure/db/entities/product-audit-log/product-audit-log.orm-entity';
import { ProductSupplierOrmEntity } from '@infrastructure/db/entities/product-suppliers/product-supplier.orm-entity';
import { ProductVariantOrmEntity } from '@infrastructure/db/entities/product-variants/product-variant.orm-entity';

@Entity({ name: 'products' })
export class ProductOrmEntity {
  @PrimaryGeneratedColumn('uuid', { name: 'product_id' })
  productId: string;

  @Column({ name: 'name', type: 'varchar', length: 150 })
  name: string;

  @Column({ name: 'description', type: 'text', nullable: true })
  description: string | null;

  @Column({ name: 'brand', type: 'varchar', length: 100, nullable: true })
  brand: string | null;

  @Column({ name: 'category_id', type: 'uuid' })
  categoryId: string;

  @Column({
    name: 'status',
    type: 'enum',
    enum: ProductStatus,
    enumName: 'product_status',
    default: ProductStatus.BORRADOR,
  })
  status: ProductStatus;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt: Date;

  /** RESTRICT: no se borra una categoria que todavia clasifica productos. */
  @ManyToOne(() => CategoryOrmEntity, (category) => category.products, {
    onDelete: 'RESTRICT',
  })
  @JoinColumn({ name: 'category_id' })
  category: CategoryOrmEntity;

  @OneToMany(() => ProductVariantOrmEntity, (variant) => variant.product)
  variants: ProductVariantOrmEntity[];

  @OneToMany(() => ProductSupplierOrmEntity, (link) => link.product)
  suppliers: ProductSupplierOrmEntity[];

  @OneToMany(() => ProductAuditLogOrmEntity, (entry) => entry.product)
  auditLog: ProductAuditLogOrmEntity[];
}
