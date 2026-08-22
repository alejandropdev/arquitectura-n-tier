import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

import { CategoryRepository } from '@domain/categories/contracts/repositories/category.repository';
import { Category } from '@domain/categories/entities/category.entity';
import { CategoryOrmEntity } from '@infrastructure/db/entities/categories/category.orm-entity';
import { CategoryOrmMapper } from '@infrastructure/categories/mappers/category.orm-mapper';

@Injectable()
export class TypeOrmCategoryRepository extends CategoryRepository {
  constructor(
    @InjectRepository(CategoryOrmEntity)
    private readonly repository: Repository<CategoryOrmEntity>,
  ) {
    super();
  }

  async listAll(): Promise<Category[]> {
    const rows = await this.repository.find({ order: { name: 'ASC' } });
    return rows.map((row) => CategoryOrmMapper.toDomain(row));
  }
}
