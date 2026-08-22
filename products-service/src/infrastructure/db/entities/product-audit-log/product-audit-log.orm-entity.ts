import {
  Column,
  CreateDateColumn,
  Entity,
  JoinColumn,
  ManyToOne,
  PrimaryGeneratedColumn,
} from 'typeorm';

import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';

export enum ProductAuditAction {
  CREADO = 'creado',
  ACTUALIZADO = 'actualizado',
  ELIMINADO = 'eliminado',
  CAMBIO_ESTADO = 'cambio_estado',
}

/**
 * Bitacora de cambios sobre productos.
 *
 * La tabla existe (viene del diagrama de BD y su migracion la crea), pero los
 * casos de uso de productos todavia no escriben en ella: queda como punto de
 * extension para una iteracion posterior.
 */
@Entity({ name: 'product_audit_log' })
export class ProductAuditLogOrmEntity {
  @PrimaryGeneratedColumn('uuid', { name: 'audit_id' })
  auditId: string;

  @Column({ name: 'product_id', type: 'uuid' })
  productId: string;

  @Column({
    name: 'action',
    type: 'enum',
    enum: ProductAuditAction,
    enumName: 'product_audit_action',
  })
  action: ProductAuditAction;

  @Column({ name: 'field_name', type: 'varchar', length: 60, nullable: true })
  fieldName: string | null;

  @Column({ name: 'old_value', type: 'text', nullable: true })
  oldValue: string | null;

  @Column({ name: 'new_value', type: 'text', nullable: true })
  newValue: string | null;

  /** Usuario o servicio responsable del cambio (`sub` del JWT, o el servicio). */
  @Column({ name: 'changed_by', type: 'varchar', length: 120 })
  changedBy: string;

  @CreateDateColumn({ name: 'changed_at', type: 'timestamptz' })
  changedAt: Date;

  @ManyToOne(() => ProductOrmEntity, (product) => product.auditLog, {
    onDelete: 'CASCADE',
  })
  @JoinColumn({ name: 'product_id' })
  product: ProductOrmEntity;
}
