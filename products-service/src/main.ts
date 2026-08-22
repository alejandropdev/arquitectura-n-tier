import { Logger, ValidationPipe } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NestFactory } from '@nestjs/core';

import { AppModule } from './app.module';
import { AppErrorFilter } from '@shared/http/app-error.filter';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const config = app.get(ConfigService);

  const apiPrefix = config.get<string>('apiPrefix') ?? 'api/v1';
  const port = config.get<number>('port') ?? 3000;

  // `/health` queda fuera del prefijo: lo consulta el gateway, no el cliente.
  app.setGlobalPrefix(apiPrefix, { exclude: ['health', 'health/(.*)'] });

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true, // descarta campos no declarados en el DTO
      forbidNonWhitelisted: true, // y avisa si los mandaron
      transform: true, // activa class-transformer (@Type, @Transform)
      transformOptions: { enableImplicitConversion: false },
    }),
  );

  app.useGlobalFilters(new AppErrorFilter());

  await app.listen(port);
  Logger.log(
    `products-service escuchando en :${port} (prefijo /${apiPrefix})`,
    'Bootstrap',
  );
}

void bootstrap();
