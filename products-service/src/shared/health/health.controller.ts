import { Controller, Get } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';

/**
 * Sondas de salud. Fuera del prefijo `/api/v1` para que el gateway y el
 * load balancer las consulten sin depender del versionado de la API.
 *
 * - `/health/live`: el proceso responde (liveness).
 * - `/health/ready`: además la BD contesta (readiness).
 */
@Controller('health')
export class HealthController {
  constructor(
    @InjectDataSource() private readonly dataSource: DataSource,
    private readonly config: ConfigService,
  ) {}

  @Get()
  root() {
    return this.live();
  }

  @Get('live')
  live() {
    return {
      status: 'ok',
      service: 'products-service',
      instance: this.config.get<string>('instanceId'),
    };
  }

  @Get('ready')
  async ready() {
    try {
      await this.dataSource.query('SELECT 1');
      return { status: 'ok', database: 'up' };
    } catch {
      return { status: 'degraded', database: 'down' };
    }
  }
}
