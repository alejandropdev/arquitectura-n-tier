import { CategoryOrmEntity } from './categories/category.orm-entity';
import { InventoryOrmEntity } from './inventory/inventory.orm-entity';
import { ProductAuditLogOrmEntity } from './product-audit-log/product-audit-log.orm-entity';
import { ProductSupplierOrmEntity } from './product-suppliers/product-supplier.orm-entity';
import { ProductVariantOrmEntity } from './product-variants/product-variant.orm-entity';
import { ProductOrmEntity } from './products/product.orm-entity';
import { SeederLogOrmEntity } from './seeder-log/seeder-log.orm-entity';
import { SupplierOrmEntity } from './suppliers/supplier.orm-entity';
import { WarehouseOrmEntity } from './warehouses/warehouse.orm-entity';

/** Registro unico de entidades: lo consumen el DataSource y el TypeOrmModule. */
export const ORM_ENTITIES = [
  CategoryOrmEntity,
  ProductOrmEntity,
  ProductVariantOrmEntity,
  WarehouseOrmEntity,
  InventoryOrmEntity,
  SupplierOrmEntity,
  ProductSupplierOrmEntity,
  ProductAuditLogOrmEntity,
  SeederLogOrmEntity,
];
