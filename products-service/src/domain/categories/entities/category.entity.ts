export interface CategoryProps {
  categoryId: string;
  parentCategoryId: string | null;
  name: string;
  slug: string;
}

/** Entidad de dominio de solo lectura: el catalogo de categorias no se muta desde este servicio. */
export class Category {
  readonly categoryId: string;
  readonly parentCategoryId: string | null;
  readonly name: string;
  readonly slug: string;

  private constructor(props: CategoryProps) {
    this.categoryId = props.categoryId;
    this.parentCategoryId = props.parentCategoryId;
    this.name = props.name;
    this.slug = props.slug;
  }

  static rehydrate(props: CategoryProps): Category {
    return new Category(props);
  }
}
