import { IsUUID } from 'class-validator';

/** Valida el `:id` de la ruta antes de llegar al caso de uso. */
export class ProductIdParamDto {
  @IsUUID('4', { message: 'id debe ser un UUID v4' })
  id: string;
}
