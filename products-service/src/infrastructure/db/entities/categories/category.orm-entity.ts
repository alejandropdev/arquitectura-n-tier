import {
  Column,
  Entity,
  JoinColumn,
  ManyToOne,
  OneToMany,
  PrimaryGeneratedColumn,
} from 'typeorm';

import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';

@Entity({ name: 'categories' })
export class CategoryOrmEntity {
  @PrimaryGeneratedColumn('uuid', { name: 'category_id' })
  categoryId: string;

  @Column({ name: 'parent_category_id', type: 'uuid', nullable: true })
  parentCategoryId: string | null;

  @Column({ name: 'name', type: 'varchar', length: 120 })
  name: string;

  @Column({ name: 'slug', type: 'varchar', length: 140, unique: true })
  slug: string;

  /** Jerarquia: una categoria puede ser subcategoria de otra. */
  @ManyToOne(() => CategoryOrmEntity, (category) => category.children, {
    nullable: true,
    onDelete: 'SET NULL',
  })
  @JoinColumn({ name: 'parent_category_id' })
  parent: CategoryOrmEntity | null;

  @OneToMany(() => CategoryOrmEntity, (category) => category.parent)
  children: CategoryOrmEntity[];

  @OneToMany(() => ProductOrmEntity, (product) => product.category)
  products: ProductOrmEntity[];
}
