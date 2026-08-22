import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

import { ListCategoriesService } from '@application/categories/use-cases/list-categories.service';
import { CategoryRepository } from '@domain/categories/contracts/repositories/category.repository';
import { ListCategoriesUseCase } from '@domain/categories/contracts/use-cases/list-categories.use-case';
import { CategoryOrmEntity } from '@infrastructure/db/entities/categories/category.orm-entity';
import { CategoriesController } from '@infrastructure/categories/http/categories.controller';
import { TypeOrmCategoryRepository } from '@infrastructure/categories/repositories/typeorm-category.repository';

@Module({
  imports: [TypeOrmModule.forFeature([CategoryOrmEntity])],
  controllers: [CategoriesController],
  providers: [
    { provide: CategoryRepository, useClass: TypeOrmCategoryRepository },
    { provide: ListCategoriesUseCase, useClass: ListCategoriesService },
  ],
})
export class CategoriesModule {}
