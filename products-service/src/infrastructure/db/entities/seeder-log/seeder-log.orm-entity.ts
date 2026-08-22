import { Column, CreateDateColumn, Entity, PrimaryGeneratedColumn } from 'typeorm';

@Entity({ name: 'seeder_log' })
export class SeederLogOrmEntity {
  @PrimaryGeneratedColumn('uuid', { name: 'id' })
  id: string;

  @Column({ name: 'seeder_name', type: 'varchar', length: 120, unique: true })
  seederName: string;

  @CreateDateColumn({ name: 'executed_at', type: 'timestamptz' })
  executedAt: Date;
}
