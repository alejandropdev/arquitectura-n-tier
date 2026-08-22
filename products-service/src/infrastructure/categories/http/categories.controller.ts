import { Controller, Get } from '@nestjs/common';

import { CategoryResponseDto } from '@application/categories/dtos/category-response.dto';
import { CategoryMapper } from '@application/categories/mappers/category.mapper';
import { ListCategoriesUseCase } from '@domain/categories/contracts/use-cases/list-categories.use-case';

/**
 * Catalogo de categorias de solo lectura: hoy solo alimenta el desplegable
 * de categoria al crear/editar un producto. No hay altas/bajas aqui.
 */
@Controller('categories')
export class CategoriesController {
  constructor(private readonly listCategories: ListCategoriesUseCase) {}

  @Get()
  async list(): Promise<CategoryResponseDto[]> {
    const categories = await this.listCategories.execute();
    return CategoryMapper.toResponseList(categories);
  }
}
