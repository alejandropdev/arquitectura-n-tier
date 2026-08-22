import { Category } from '@domain/categories/entities/category.entity';
import { CategoryOrmEntity } from '@infrastructure/db/entities/categories/category.orm-entity';

export class CategoryOrmMapper {
  static toDomain(row: CategoryOrmEntity): Category {
    return Category.rehydrate({
      categoryId: row.categoryId,
      parentCategoryId: row.parentCategoryId,
      name: row.name,
      slug: row.slug,
    });
  }
}
