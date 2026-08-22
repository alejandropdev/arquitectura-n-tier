import { ProductStatus } from './product-status.enum';
import { InvalidProductStatusTransitionException } from '@domain/products/exceptions/invalid-product-status-transition.exception';
import { ProductAlreadyDiscontinuedException } from '@domain/products/exceptions/product-already-discontinued.exception';

export interface ProductProps {
  productId: string;
  name: string;
  description: string | null;
  brand: string | null;
  categoryId: string;
  status: ProductStatus;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Entidad de dominio. Es una clase pura: no conoce TypeORM, ni HTTP, ni DTOs.
 * Concentra las reglas de negocio del producto (transiciones de estado y
 * normalizacion de campos), de modo que ningun caso de uso las duplique.
 */
export class Product {
  readonly productId: string;
  private _name: string;
  private _description: string | null;
  private _brand: string | null;
  private _categoryId: string;
  private _status: ProductStatus;
  readonly createdAt: Date;
  private _updatedAt: Date;

  private constructor(props: ProductProps) {
    this.productId = props.productId;
    this._name = props.name;
    this._description = props.description;
    this._brand = props.brand;
    this._categoryId = props.categoryId;
    this._status = props.status;
    this.createdAt = props.createdAt;
    this._updatedAt = props.updatedAt;
  }

  /** Reconstruye una entidad ya existente (viene de persistencia). */
  static rehydrate(props: ProductProps): Product {
    return new Product(props);
  }

  /**
   * Crea un producto nuevo. El id y las marcas de tiempo las asigna la BD, por
   * eso quedan vacios hasta que el repositorio devuelva la fila persistida.
   */
  static create(props: {
    name: string;
    description?: string | null;
    brand?: string | null;
    categoryId: string;
    status?: ProductStatus;
  }): Product {
    return new Product({
      productId: '',
      name: props.name.trim(),
      description: props.description?.trim() || null,
      brand: props.brand?.trim() || null,
      categoryId: props.categoryId,
      status: props.status ?? ProductStatus.BORRADOR,
      createdAt: new Date(0),
      updatedAt: new Date(0),
    });
  }

  get name(): string {
    return this._name;
  }
  get description(): string | null {
    return this._description;
  }
  get brand(): string | null {
    return this._brand;
  }
  get categoryId(): string {
    return this._categoryId;
  }
  get status(): ProductStatus {
    return this._status;
  }
  get updatedAt(): Date {
    return this._updatedAt;
  }

  get isDiscontinued(): boolean {
    return this._status === ProductStatus.DESCONTINUADO;
  }

  rename(name: string): void {
    this._name = name.trim();
    this.touch();
  }

  changeDescription(description: string | null): void {
    this._description = description?.trim() || null;
    this.touch();
  }

  changeBrand(brand: string | null): void {
    this._brand = brand?.trim() || null;
    this.touch();
  }

  moveToCategory(categoryId: string): void {
    this._categoryId = categoryId;
    this.touch();
  }

  /**
   * Regla de negocio: un producto descontinuado es terminal. Para volver a
   * venderlo se crea uno nuevo, no se reactiva el historico.
   */
  changeStatus(next: ProductStatus): void {
    if (this._status === next) return;

    if (this._status === ProductStatus.DESCONTINUADO) {
      throw new InvalidProductStatusTransitionException(this._status, next);
    }

    this._status = next;
    this.touch();
  }

  /** El "delete" del API: no borra la fila, la retira del catalogo. */
  discontinue(): void {
    if (this.isDiscontinued) {
      throw new ProductAlreadyDiscontinuedException(this.productId);
    }
    this._status = ProductStatus.DESCONTINUADO;
    this.touch();
  }

  private touch(): void {
    this._updatedAt = new Date();
  }
}
