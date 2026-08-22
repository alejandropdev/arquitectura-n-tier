import { Inject, Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { BaseSeeder } from './seeder.base';
import { SupplierOrmEntity } from '@infrastructure/db/entities/suppliers/supplier.orm-entity';

@Injectable()
export class SuppliersSeeder extends BaseSeeder {
  readonly name = 'suppliers';

  constructor(@Inject(DataSource) dataSource: DataSource) {
    super(dataSource);
  }

  protected async run(): Promise<void> {
    const repository = this.dataSource.getRepository(SupplierOrmEntity);

    const suppliers = [
      {
        name: 'Samsung Electronics',
        contactEmail: 'ventas@samsung.com',
        contactPhone: '+82-2-6001-1114',
      },
      {
        name: 'Apple Inc.',
        contactEmail: 'business@apple.com',
        contactPhone: '+1-408-996-1010',
      },
      {
        name: 'LG Electronics',
        contactEmail: 'sales@lg.com',
        contactPhone: '+82-2-3777-1114',
      },
      {
        name: 'Sony Corporation',
        contactEmail: 'biz@sony.com',
        contactPhone: '+81-3-6748-2111',
      },
      {
        name: 'Inditex (Zara)',
        contactEmail: 'ventas@inditex.com',
        contactPhone: '+34-943-359-000',
      },
      {
        name: 'LVMH',
        contactEmail: 'business@lvmh.com',
        contactPhone: '+33-1-4411-8000',
      },
      {
        name: 'H&M',
        contactEmail: 'supplier@hm.com',
        contactPhone: '+46-8-406-50-00',
      },
      {
        name: 'IKEA',
        contactEmail: 'supplier@ikea.com',
        contactPhone: '+46-250-40-00-00',
      },
      {
        name: 'Electrolux',
        contactEmail: 'sales@electrolux.com',
        contactPhone: '+46-8-738-60-00',
      },
      {
        name: 'Bosch',
        contactEmail: 'vendas@bosch.com',
        contactPhone: '+49-7142-470',
      },
    ];

    await repository.save(suppliers);
  }
}
