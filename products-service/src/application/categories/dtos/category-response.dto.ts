/** Forma exacta con la que una categoria sale del servicio. */
export class CategoryResponseDto {
  id: string;
  parentId: string | null;
  name: string;
  slug: string;
}
