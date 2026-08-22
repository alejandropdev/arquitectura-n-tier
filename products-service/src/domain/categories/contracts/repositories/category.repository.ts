import { Category } from '@domain/categories/entities/category.entity';

/**
 * Puerto de persistencia de categorias. Clase abstracta por la misma razon
 * que `ProductRepository`: sirve de token de inyeccion real para Nest.
 */
export abstract class CategoryRepository {
  abstract listAll(): Promise<Category[]>;
}
