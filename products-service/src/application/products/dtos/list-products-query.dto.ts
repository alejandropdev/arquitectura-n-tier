import {
  IsEnum,
  IsIn,
  IsOptional,
  IsString,
  IsUUID,
  MaxLength,
} from 'class-validator';

import type {
  ProductSortField,
  SortOrder,
} from '@domain/products/contracts/repositories/product.repository';
import {
  PRODUCT_STATUSES,
  ProductStatus,
} from '@domain/products/entities/product-status.enum';
import { PaginationQueryDto } from '@shared/pagination/pagination-query.dto';
import { TrimmedText, UpperCaseText } from '@shared/utils/transform.util';

const SORT_FIELDS: ProductSortField[] = ['createdAt', 'name'];
const SORT_ORDERS: SortOrder[] = ['ASC', 'DESC'];

export class ListProductsQueryDto extends PaginationQueryDto {
  @IsUUID('4', { message: 'categoryId debe ser un UUID v4' })
  @IsOptional()
  categoryId?: string;

  @IsEnum(ProductStatus, {
    message: `status debe ser uno de: ${PRODUCT_STATUSES.join(', ')}`,
  })
  @IsOptional()
  status?: ProductStatus;

  @TrimmedText()
  @IsString({ message: 'brand debe ser texto' })
  @MaxLength(100)
  @IsOptional()
  brand?: string;

  /** Busqueda parcial e insensible a mayusculas sobre el nombre. */
  @TrimmedText()
  @IsString({ message: 'search debe ser texto' })
  @MaxLength(150)
  @IsOptional()
  search?: string;

  @IsIn(SORT_FIELDS, {
    message: `sort debe ser uno de: ${SORT_FIELDS.join(', ')}`,
  })
  @IsOptional()
  sort: ProductSortField = 'createdAt';

  @UpperCaseText()
  @IsIn(SORT_ORDERS, {
    message: `order debe ser uno de: ${SORT_ORDERS.join(', ')}`,
  })
  @IsOptional()
  order: SortOrder = 'DESC';
}
