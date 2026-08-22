import { CategoryResponseDto } from '@application/categories/dtos/category-response.dto';
import { Category } from '@domain/categories/entities/category.entity';

export class CategoryMapper {
  static toResponse(category: Category): CategoryResponseDto {
    return {
      id: category.categoryId,
      parentId: category.parentCategoryId,
      name: category.name,
      slug: category.slug,
    };
  }

  static toResponseList(categories: Category[]): CategoryResponseDto[] {
    return categories.map((category) => CategoryMapper.toResponse(category));
  }
}
