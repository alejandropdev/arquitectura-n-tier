import { Inject, Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { BaseSeeder } from './seeder.base';
import { CategoryOrmEntity } from '@infrastructure/db/entities/categories/category.orm-entity';

@Injectable()
export class CategoriesSeeder extends BaseSeeder {
  readonly name = 'categories';

  constructor(@Inject(DataSource) dataSource: DataSource) {
    super(dataSource);
  }

  protected async run(): Promise<void> {
    const repository = this.dataSource.getRepository(CategoryOrmEntity);

    const categories = [
      // Categorías raíz
      {
        name: 'Electrónica',
        slug: 'electronica',
        parentCategoryId: null,
      },
      {
        name: 'Ropa',
        slug: 'ropa',
        parentCategoryId: null,
      },
      {
        name: 'Hogar',
        slug: 'hogar',
        parentCategoryId: null,
      },
    ];

    const savedCategories = await repository.save(categories);

    const electronicaId = savedCategories.find(c => c.slug === 'electronica')?.categoryId;
    const ropaId = savedCategories.find(c => c.slug === 'ropa')?.categoryId;
    const hogarId = savedCategories.find(c => c.slug === 'hogar')?.categoryId;

    // Subcategorías
    const subcategories = [
      // Electrónica
      { name: 'Smartphones', slug: 'smartphones', parentCategoryId: electronicaId },
      { name: 'Laptops', slug: 'laptops', parentCategoryId: electronicaId },
      { name: 'Tablets', slug: 'tablets', parentCategoryId: electronicaId },
      { name: 'Accesorios Electrónicos', slug: 'accesorios-electronicos', parentCategoryId: electronicaId },
      // Ropa
      { name: 'Ropa Masculina', slug: 'ropa-masculina', parentCategoryId: ropaId },
      { name: 'Ropa Femenina', slug: 'ropa-femenina', parentCategoryId: ropaId },
      { name: 'Ropa Infantil', slug: 'ropa-infantil', parentCategoryId: ropaId },
      // Hogar
      { name: 'Muebles', slug: 'muebles', parentCategoryId: hogarId },
      { name: 'Decoración', slug: 'decoracion', parentCategoryId: hogarId },
      { name: 'Cocina', slug: 'cocina', parentCategoryId: hogarId },
    ];

    await repository.save(subcategories);
  }
}
