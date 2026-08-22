import { Column, Entity, OneToMany, PrimaryGeneratedColumn } from 'typeorm';

import { ProductSupplierOrmEntity } from '@infrastructure/db/entities/product-suppliers/product-supplier.orm-entity';

@Entity({ name: 'suppliers' })
export class SupplierOrmEntity {
  @PrimaryGeneratedColumn('uuid', { name: 'supplier_id' })
  supplierId: string;

  @Column({ name: 'name', type: 'varchar', length: 150 })
  name: string;

  @Column({
    name: 'contact_email',
    type: 'varchar',
    length: 150,
    nullable: true,
  })
  contactEmail: string | null;

  @Column({
    name: 'contact_phone',
    type: 'varchar',
    length: 40,
    nullable: true,
  })
  contactPhone: string | null;

  @OneToMany(() => ProductSupplierOrmEntity, (link) => link.supplier)
  products: ProductSupplierOrmEntity[];
}
