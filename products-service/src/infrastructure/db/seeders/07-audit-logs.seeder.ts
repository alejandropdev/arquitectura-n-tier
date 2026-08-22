import { Inject, Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { BaseSeeder } from './seeder.base';
import { ProductAuditLogOrmEntity, ProductAuditAction } from '@infrastructure/db/entities/product-audit-log/product-audit-log.orm-entity';
import { ProductOrmEntity } from '@infrastructure/db/entities/products/product.orm-entity';
import { ProductStatus } from '@domain/products/entities/product-status.enum';

@Injectable()
export class AuditLogsSeeder extends BaseSeeder {
  readonly name = 'audit-logs';

  constructor(@Inject(DataSource) dataSource: DataSource) {
    super(dataSource);
  }

  protected async run(): Promise<void> {
    const repository = this.dataSource.getRepository(ProductAuditLogOrmEntity);
    const productRepo = this.dataSource.getRepository(ProductOrmEntity);

    const products = await productRepo.find();

    const auditLogs: Partial<ProductAuditLogOrmEntity>[] = [];

    // Crear registros de auditoría para cada producto
    for (const product of products) {
      // Registro de creación
      auditLogs.push({
        productId: product.productId,
        action: ProductAuditAction.CREADO,
        fieldName: null,
        oldValue: null,
        newValue: JSON.stringify({ name: product.name, status: product.status }),
        changedBy: 'system@seed',
        changedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 días atrás
      });

      // Registro de cambio de estado (algunos productos)
      if (product.status !== ProductStatus.BORRADOR) {
        auditLogs.push({
          productId: product.productId,
          action: ProductAuditAction.CAMBIO_ESTADO,
          fieldName: 'status',
          oldValue: ProductStatus.BORRADOR,
          newValue: product.status,
          changedBy: 'admin@system',
          changedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), // 5 días atrás
        });
      }

      // Registro de actualización (descripción)
      if (product.description) {
        auditLogs.push({
          productId: product.productId,
          action: ProductAuditAction.ACTUALIZADO,
          fieldName: 'description',
          oldValue: '',
          newValue: product.description.substring(0, 50) + '...',
          changedBy: 'editor@system',
          changedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 días atrás
        });
      }
    }

    // Insertar en lotes
    const batchSize = 50;
    for (let i = 0; i < auditLogs.length; i += batchSize) {
      const batch = auditLogs.slice(i, i + batchSize);
      await repository.save(batch);
    }
  }
}
