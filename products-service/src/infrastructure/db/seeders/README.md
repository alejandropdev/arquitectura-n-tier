# Database Seeders

Los seeders pueblan automáticamente la base de datos cuando el servicio se levanta. Cada seeder se ejecuta **una sola vez**.

## Cómo funcionan

1. **Tabla de control**: La tabla `seeder_log` rastrea qué seeders ya han sido ejecutados.
2. **Ejecución automática**: Al bootstrap de la aplicación, el `SeederService` ejecuta todos los seeders en orden.
3. **Idempotencia**: Si un seeder ya está registrado en `seeder_log`, se salta automáticamente.

## Estructura de datos

### Dependencias de ejecución

```
00-categories (raíz)
    ↓
01-suppliers (raíz)
    ↓
02-products (depende de: categorías)
    ↓
03-product-suppliers (depende de: productos, proveedores)
    ↓
04-warehouses (raíz)
    ↓
05-product-variants (depende de: productos)
    ↓
06-inventory (depende de: variantes, bodegas)
    ↓
07-audit-logs (depende de: productos)
```

## Datos semilla incluidos

### Categorías
- **3 categorías raíz**: Electrónica, Ropa, Hogar
- **10 subcategorías**: Smartphones, Laptops, Tablets, Accesorios, etc.

### Proveedores
- 10 proveedores internacionales: Samsung, Apple, LG, Sony, IKEA, Bosch, etc.

### Productos
- 13 productos con 3 categorías diferentes (Electrónica, Muebles, Cocina)
- Estados: PUBLICADO y BORRADOR
- Relaciones significativas con proveedores

### Variantes de productos
- 26 variantes totales con atributos realistas (color, tamaño, almacenamiento)
- SKUs únicos
- Precios variados según tamaño/color

### Bodegas
- 5 bodegas en diferentes ciudades de Colombia

### Inventario
- Cada variante disponible en cada bodega
- Stock aleatorio (50-550 unidades)
- Nivel de reorden configurado al 20% del stock

### Logs de auditoría
- Registros de creación, cambios de estado y actualizaciones
- Fechas realistas en el pasado (3-7 días atrás)
- Usuarios del sistema registrados

## Relaciones lógicas garantizadas

✅ Categorías jerárquicas (padre-hijo)  
✅ Productos vinculados a categorías válidas  
✅ Proveedores múltiples por producto  
✅ Variantes únicas por SKU  
✅ Inventario en todas las bodegas  
✅ Logs de auditoría con productos válidos  

## Agregar un nuevo seeder

1. Crear un archivo `NN-name.seeder.ts` en este directorio
2. Extender `BaseSeeder`
3. Implementar `protected async run()`
4. Agregar al `SeederService` en el orden correcto
5. Registrar en `SeedersModule`

Ejemplo:

```typescript
import { Injectable } from '@nestjs/common';
import { DataSource } from 'typeorm';
import { BaseSeeder } from './seeder.base';
import { MyOrmEntity } from '@infrastructure/db/entities/my/my.orm-entity';

@Injectable()
export class MySeeder extends BaseSeeder {
  readonly name = 'my-seeder';

  constructor(dataSource: DataSource) {
    super(dataSource);
  }

  protected async run(): Promise<void> {
    const repository = this.dataSource.getRepository(MyOrmEntity);
    await repository.save([/* datos */]);
  }
}
```

## Resetear seeders

Para forzar la re-ejecución de todos los seeders:

```sql
DELETE FROM seeder_log;
```

> ⚠️ Esto recreará todos los datos. Si tienes datos producción, usa con cuidado.
