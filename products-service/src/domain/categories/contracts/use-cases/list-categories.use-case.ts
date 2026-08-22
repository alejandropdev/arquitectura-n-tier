import { Category } from '@domain/categories/entities/category.entity';

export abstract class ListCategoriesUseCase {
  abstract execute(): Promise<Category[]>;
}
