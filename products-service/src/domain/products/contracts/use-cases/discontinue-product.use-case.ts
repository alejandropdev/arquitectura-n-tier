export abstract class DiscontinueProductUseCase {
  /**
   * Retira el producto del catalogo (`status = descontinuado`).
   * Es idempotente: descontinuar uno ya descontinuado no falla.
   */
  abstract execute(productId: string): Promise<void>;
}
