import { Inject } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { SeederLogOrmEntity } from '@infrastructure/db/entities/seeder-log/seeder-log.orm-entity';

export abstract class BaseSeeder {
  abstract readonly name: string;

  constructor(@Inject(DataSource) protected dataSource: DataSource) {}

  async execute(): Promise<void> {
    const repository = this.dataSource.getRepository(SeederLogOrmEntity);
    const exists = await repository.findOne({ where: { seederName: this.name } });

    if (exists) {
      console.log(`⏭️  Seeder "${this.name}" ya fue ejecutado. Saltando...`);
      return;
    }

    try {
      console.log(`▶️  Ejecutando seeder: "${this.name}"...`);
      await this.run();
      await repository.save({ seederName: this.name });
      console.log(`✅ Seeder "${this.name}" completado.`);
    } catch (error) {
      console.error(`❌ Error en seeder "${this.name}":`, error);
      throw error;
    }
  }

  protected abstract run(): Promise<void>;
}
