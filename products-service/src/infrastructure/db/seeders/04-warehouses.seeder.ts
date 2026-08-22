import { Inject, Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { BaseSeeder } from './seeder.base';
import { WarehouseOrmEntity } from '@infrastructure/db/entities/warehouses/warehouse.orm-entity';

@Injectable()
export class WarehousesSeeder extends BaseSeeder {
  readonly name = 'warehouses';

  constructor(@Inject(DataSource) dataSource: DataSource) {
    super(dataSource);
  }

  protected async run(): Promise<void> {
    const repository = this.dataSource.getRepository(WarehouseOrmEntity);

    const warehouses = [
      {
        name: 'Bodega Central - Bogotá',
        address: 'Cra 50 #10-50, Zona Franca',
        city: 'Bogotá',
      },
      {
        name: 'Bodega Occidente - Medellín',
        address: 'Calle 30 #45-15, Itagüí',
        city: 'Medellín',
      },
      {
        name: 'Bodega Oriente - Bucaramanga',
        address: 'Av. Prado #40-60, Girón',
        city: 'Bucaramanga',
      },
      {
        name: 'Bodega Sur - Cali',
        address: 'Cra 100 #25-50, Área Industrial',
        city: 'Cali',
      },
      {
        name: 'Bodega Costa - Barranquilla',
        address: 'Calle 80 #55-40, Puerto Viejo',
        city: 'Barranquilla',
      },
    ];

    await repository.save(warehouses);
  }
}
