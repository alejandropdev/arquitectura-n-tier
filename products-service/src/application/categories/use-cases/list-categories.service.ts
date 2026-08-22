import { Injectable } from '@nestjs/common';

import { CategoryRepository } from '@domain/categories/contracts/repositories/category.repository';
import { ListCategoriesUseCase } from '@domain/categories/contracts/use-cases/list-categories.use-case';
import { Category } from '@domain/categories/entities/category.entity';

@Injectable()
export class ListCategoriesService extends ListCategoriesUseCase {
  constructor(private readonly categories: CategoryRepository) {
    super();
  }

  async execute(): Promise<Category[]> {
    return this.categories.listAll();
  }
}
