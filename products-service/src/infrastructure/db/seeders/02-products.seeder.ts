import { Inject, Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { BaseSeeder } from './seeder.base';
import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';
import { CategoryOrmEntity } from '@infrastructure/db/entities/categories/category.orm-entity';
import { ProductStatus } from '@domain/products/entities/product-status.enum';

@Injectable()
export class ProductsSeeder extends BaseSeeder {
  readonly name = 'products';

  constructor(@Inject(DataSource) dataSource: DataSource) {
    super(dataSource);
  }

  protected async run(): Promise<void> {
    const productRepo = this.dataSource.getRepository(ProductOrmEntity);
    const categoryRepo = this.dataSource.getRepository(CategoryOrmEntity);

    // Obtener categorías por slug
    const smartphones = await categoryRepo.findOne({ where: { slug: 'smartphones' } });
    const laptops = await categoryRepo.findOne({ where: { slug: 'laptops' } });
    const tablets = await categoryRepo.findOne({ where: { slug: 'tablets' } });
    const accElectronicos = await categoryRepo.findOne({ where: { slug: 'accesorios-electronicos' } });
    const muebles = await categoryRepo.findOne({ where: { slug: 'muebles' } });
    const cocina = await categoryRepo.findOne({ where: { slug: 'cocina' } });

    if (!smartphones || !laptops || !tablets || !accElectronicos || !muebles || !cocina) {
      throw new Error('No se encontraron todas las categorías requeridas');
    }

    const products = [
      // Smartphones
      {
        name: 'Samsung Galaxy S24',
        description: 'Smartphone insignia con pantalla AMOLED 6.1" y procesador Snapdragon 8 Gen 3',
        brand: 'Samsung',
        categoryId: smartphones.categoryId,
        status: ProductStatus.ACTIVO,
      },
      {
        name: 'Apple iPhone 15 Pro',
        description: 'iPhone 15 Pro con chip A17 Pro y cámara de 48MP',
        brand: 'Apple',
        categoryId: smartphones.categoryId,
        status: ProductStatus.ACTIVO,
      },
      {
        name: 'Samsung Galaxy A54',
        description: 'Smartphone asequible con buena batería y cámara de 50MP',
        brand: 'Samsung',
        categoryId: smartphones.categoryId,
        status: ProductStatus.ACTIVO,
      },
      // Laptops
      {
        name: 'MacBook Pro 14"',
        description: 'MacBook Pro con chip M3 Max, 16GB RAM y 512GB SSD',
        brand: 'Apple',
        categoryId: laptops.categoryId,
        status: ProductStatus.ACTIVO,
      },
      {
        name: 'Dell XPS 15',
        description: 'Laptop de alta performance con pantalla OLED 4K',
        brand: 'Dell',
        categoryId: laptops.categoryId,
        status: ProductStatus.ACTIVO,
      },
      // Tablets
      {
        name: 'iPad Air 12.9"',
        description: 'Tablet con chip M1 y Apple Pencil compatible',
        brand: 'Apple',
        categoryId: tablets.categoryId,
        status: ProductStatus.ACTIVO,
      },
      {
        name: 'Samsung Galaxy Tab S9',
        description: 'Tablet con pantalla AMOLED 11.0" y S Pen integrado',
        brand: 'Samsung',
        categoryId: tablets.categoryId,
        status: ProductStatus.ACTIVO,
      },
      // Accesorios
      {
        name: 'AirPods Pro Gen 2',
        description: 'Audífonos inalámbricos con cancelación activa de ruido',
        brand: 'Apple',
        categoryId: accElectronicos.categoryId,
        status: ProductStatus.ACTIVO,
      },
      {
        name: 'Cable USB-C',
        description: 'Cable USB-C de carga rápida 1 metro',
        brand: 'Genérico',
        categoryId: accElectronicos.categoryId,
        status: ProductStatus.ACTIVO,
      },
      // Muebles
      {
        name: 'Sofá Nórdico 3 Cuerpos',
        description: 'Sofá tapizado en tela gris con patas de madera',
        brand: 'IKEA',
        categoryId: muebles.categoryId,
        status: ProductStatus.ACTIVO,
      },
      {
        name: 'Mesa de Comedor',
        description: 'Mesa extensible para 6-8 personas',
        brand: 'IKEA',
        categoryId: muebles.categoryId,
        status: ProductStatus.ACTIVO,
      },
      // Cocina
      {
        name: 'Microondas Electrolux',
        description: 'Microondas 25L con control digital',
        brand: 'Electrolux',
        categoryId: cocina.categoryId,
        status: ProductStatus.ACTIVO,
      },
      {
        name: 'Licuadora Bosch',
        description: 'Licuadora potente 1000W con 5 velocidades',
        brand: 'Bosch',
        categoryId: cocina.categoryId,
        status: ProductStatus.BORRADOR,
      },
    ];

    await productRepo.save(products);
  }
}
