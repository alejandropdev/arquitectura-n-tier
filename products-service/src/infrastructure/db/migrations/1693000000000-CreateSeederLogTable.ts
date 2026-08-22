import { MigrationInterface, QueryRunner, Table } from 'typeorm';

export class CreateSeederLogTable1693000000000 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(
      new Table({
        name: 'seeder_log',
        columns: [
          {
            name: 'id',
            type: 'uuid',
            isPrimary: true,
            isGenerated: true,
            generationStrategy: 'uuid',
          },
          {
            name: 'seeder_name',
            type: 'varchar',
            length: '120',
            isUnique: true,
            isNullable: false,
          },
          {
            name: 'executed_at',
            type: 'timestamptz',
            isNullable: false,
            default: 'CURRENT_TIMESTAMP',
          },
        ],
      }),
      true,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('seeder_log');
  }
}
