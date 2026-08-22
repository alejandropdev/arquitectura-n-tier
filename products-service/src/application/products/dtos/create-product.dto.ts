import {
  IsEnum,
  IsNotEmpty,
  IsOptional,
  IsString,
  IsUUID,
  MaxLength,
  MinLength,
} from 'class-validator';

import {
  PRODUCT_STATUSES,
  ProductStatus,
} from '@domain/products/entities/product-status.enum';
import { OptionalText, TrimmedText } from '@shared/utils/transform.util';

export class CreateProductDto {
  @TrimmedText()
  @IsString({ message: 'name debe ser texto' })
  @IsNotEmpty({ message: 'name es obligatorio' })
  @MinLength(2, { message: 'name debe tener al menos 2 caracteres' })
  @MaxLength(150, { message: 'name no puede superar 150 caracteres' })
  name: string;

  @OptionalText()
  @IsString({ message: 'description debe ser texto' })
  @MaxLength(2000, { message: 'description no puede superar 2000 caracteres' })
  @IsOptional()
  description?: string | null;

  @OptionalText()
  @IsString({ message: 'brand debe ser texto' })
  @MaxLength(100, { message: 'brand no puede superar 100 caracteres' })
  @IsOptional()
  brand?: string | null;

  /**
   * Solo se valida el formato. La existencia de la categoria la garantiza la
   * llave foranea de Postgres (decision de alcance: el dominio de productos no
   * consulta el dominio de categorias).
   */
  @IsUUID('4', { message: 'categoryId debe ser un UUID v4' })
  categoryId: string;

  @IsEnum(ProductStatus, {
    message: `status debe ser uno de: ${PRODUCT_STATUSES.join(', ')}`,
  })
  @IsOptional()
  status?: ProductStatus;
}
