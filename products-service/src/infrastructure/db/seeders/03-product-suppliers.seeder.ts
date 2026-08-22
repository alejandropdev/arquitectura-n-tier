import { Inject, Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { BaseSeeder } from './seeder.base';
import { ProductSupplierOrmEntity } from '@infrastructure/db/entities/product-suppliers/product-supplier.orm-entity';
import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';
import { SupplierOrmEntity } from '@infrastructure/db/entities/suppliers/supplier.orm-entity';

@Injectable()
export class ProductSuppliersSeeder extends BaseSeeder {
  readonly name = 'product-suppliers';

  constructor(@Inject(DataSource) dataSource: DataSource) {
    super(dataSource);
  }

  protected async run(): Promise<void> {
    const repository = this.dataSource.getRepository(ProductSupplierOrmEntity);
    const productRepo = this.dataSource.getRepository(ProductOrmEntity);
    const supplierRepo = this.dataSource.getRepository(SupplierOrmEntity);

    // Obtener productos y proveedores
    const products = await productRepo.find();
    const suppliers = await supplierRepo.find();

    // Mapeo de proveedores por nombre
    const supplierMap = new Map(suppliers.map(s => [s.name, s.supplierId]));

    const productSuppliers = [
      // Samsung Galaxy S24
      { productName: 'Samsung Galaxy S24', supplierName: 'Samsung Electronics', costPrice: '320.00' },
      // iPhone 15 Pro
      { productName: 'Apple iPhone 15 Pro', supplierName: 'Apple Inc.', costPrice: '720.00' },
      // Galaxy A54
      { productName: 'Samsung Galaxy A54', supplierName: 'Samsung Electronics', costPrice: '240.00' },
      // MacBook Pro
      { productName: 'MacBook Pro 14"', supplierName: 'Apple Inc.', costPrice: '1200.00' },
      // Dell XPS 15
      { productName: 'Dell XPS 15', supplierName: 'Sony Corporation', costPrice: '800.00' },
      // iPad Air
      { productName: 'iPad Air 12.9"', supplierName: 'Apple Inc.', costPrice: '450.00' },
      // Galaxy Tab S9
      { productName: 'Samsung Galaxy Tab S9', supplierName: 'Samsung Electronics', costPrice: '380.00' },
      // AirPods Pro
      { productName: 'AirPods Pro Gen 2', supplierName: 'Apple Inc.', costPrice: '150.00' },
      // Cable USB-C
      { productName: 'Cable USB-C', supplierName: 'Sony Corporation', costPrice: '4.00' },
      // Sofá
      { productName: 'Sofá Nórdico 3 Cuerpos', supplierName: 'IKEA', costPrice: '350.00' },
      // Mesa
      { productName: 'Mesa de Comedor', supplierName: 'IKEA', costPrice: '280.00' },
      // Microondas
      { productName: 'Microondas Electrolux', supplierName: 'Electrolux', costPrice: '120.00' },
      // Licuadora
      { productName: 'Licuadora Bosch', supplierName: 'Bosch', costPrice: '85.00' },
    ];

    const psToSave = productSuppliers.map(ps => ({
      productId: products.find(p => p.name === ps.productName)?.productId,
      supplierId: supplierMap.get(ps.supplierName),
      costPrice: ps.costPrice,
    })).filter(ps => ps.productId && ps.supplierId);

    await repository.save(psToSave);
  }
}
