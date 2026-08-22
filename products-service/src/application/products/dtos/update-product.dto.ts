import { PartialType } from '@nestjs/mapped-types';

import { CreateProductDto } from './create-product.dto';

/**
 * Todos los campos opcionales, heredando las mismas reglas de validacion.
 * `description` y `brand` aceptan `null` explicito para limpiarlos.
 */
export class UpdateProductDto extends PartialType(CreateProductDto) {}
