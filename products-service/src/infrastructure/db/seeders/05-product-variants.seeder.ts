import { Inject, Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { BaseSeeder } from './seeder.base';
import { ProductVariantOrmEntity } from '@infrastructure/db/entities/product-variants/product-variant.orm-entity';
import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';

@Injectable()
export class ProductVariantsSeeder extends BaseSeeder {
  readonly name = 'product-variants';

  constructor(@Inject(DataSource) dataSource: DataSource) {
    super(dataSource);
  }

  protected async run(): Promise<void> {
    const repository = this.dataSource.getRepository(ProductVariantOrmEntity);
    const productRepo = this.dataSource.getRepository(ProductOrmEntity);

    const products = await productRepo.find();

    const variants = [
      // Samsung Galaxy S24 - colores
      { productName: 'Samsung Galaxy S24', sku: 'SGS24-BLK-128', color: 'Negro', size: '128GB', price: '899.99' },
      { productName: 'Samsung Galaxy S24', sku: 'SGS24-WHT-128', color: 'Blanco', size: '128GB', price: '899.99' },
      { productName: 'Samsung Galaxy S24', sku: 'SGS24-GLD-256', color: 'Dorado', size: '256GB', price: '949.99' },
      // iPhone 15 Pro - colores y almacenamiento
      { productName: 'Apple iPhone 15 Pro', sku: 'IIP15P-BLK-128', color: 'Negro Titanio', size: '128GB', price: '999.99' },
      { productName: 'Apple iPhone 15 Pro', sku: 'IIP15P-NTL-256', color: 'Titanio Natural', size: '256GB', price: '1099.99' },
      { productName: 'Apple iPhone 15 Pro', sku: 'IIP15P-BLU-512', color: 'Azul Titanio', size: '512GB', price: '1199.99' },
      // Galaxy A54
      { productName: 'Samsung Galaxy A54', sku: 'SGA54-BLK-128', color: 'Negro', size: '128GB', price: '449.99' },
      { productName: 'Samsung Galaxy A54', sku: 'SGA54-WHT-256', color: 'Blanco', size: '256GB', price: '499.99' },
      // MacBook Pro 14"
      { productName: 'MacBook Pro 14"', sku: 'MBP14-SLV-16', color: 'Plateado', size: '16GB RAM/512GB', price: '1999.99' },
      { productName: 'MacBook Pro 14"', sku: 'MBP14-SPC-16', color: 'Espacio Negro', size: '16GB RAM/512GB', price: '1999.99' },
      // Dell XPS 15
      { productName: 'Dell XPS 15', sku: 'DXPS15-SLV-16', color: 'Plateado', size: '16GB/512GB', price: '1499.99' },
      { productName: 'Dell XPS 15', sku: 'DXPS15-BLK-32', color: 'Negro', size: '32GB/1TB', price: '1799.99' },
      // iPad Air
      { productName: 'iPad Air 12.9"', sku: 'IPAD-AIR-BLU-64', color: 'Azul Cielo', size: '64GB', price: '799.99' },
      { productName: 'iPad Air 12.9"', sku: 'IPAD-AIR-PUR-256', color: 'Púrpura', size: '256GB', price: '949.99' },
      // Galaxy Tab S9
      { productName: 'Samsung Galaxy Tab S9', sku: 'SGTS9-SLV-128', color: 'Plata', size: '128GB', price: '799.99' },
      { productName: 'Samsung Galaxy Tab S9', sku: 'SGTS9-BLK-256', color: 'Negro', size: '256GB', price: '899.99' },
      // AirPods Pro
      { productName: 'AirPods Pro Gen 2', sku: 'AIRPODS-GEN2', color: 'Blanco', size: 'Estándar', price: '249.99' },
      // Cable USB-C
      { productName: 'Cable USB-C', sku: 'USB-C-1M', color: 'Blanco', size: '1 Metro', price: '19.99' },
      { productName: 'Cable USB-C', sku: 'USB-C-2M', color: 'Blanco', size: '2 Metros', price: '24.99' },
      // Sofá
      { productName: 'Sofá Nórdico 3 Cuerpos', sku: 'SOFA-GRIS-3P', color: 'Gris', size: '3 Cuerpos', price: '599.99' },
      { productName: 'Sofá Nórdico 3 Cuerpos', sku: 'SOFA-BEIGE-3P', color: 'Beige', size: '3 Cuerpos', price: '599.99' },
      // Mesa
      { productName: 'Mesa de Comedor', sku: 'MESA-MADERA-EXT', color: 'Madera Natural', size: 'Extensible', price: '499.99' },
      // Microondas
      { productName: 'Microondas Electrolux', sku: 'MICROND-25L-BLK', color: 'Negro', size: '25L', price: '249.99' },
      // Licuadora
      { productName: 'Licuadora Bosch', sku: 'LICUA-1000W-BLK', color: 'Negro', size: '1000W', price: '189.99' },
    ];

    const variantsToSave = variants.map(v => ({
      ...v,
      productId: products.find(p => p.name === v.productName)?.productId,
    })).filter(v => v.productId);

    await repository.save(variantsToSave);
  }
}
