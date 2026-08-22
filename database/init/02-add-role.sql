-- Taller 2, Requerimiento 9: rol de autorización de cada usuario.
--
-- Script aditivo — no se edita 01-schema.sql porque Andrés añade índices
-- sobre esta misma base de datos en paralelo (Requerimiento 5).
--
-- `docker-entrypoint-initdb.d` solo ejecuta los scripts de este directorio
-- en un volumen nuevo. Sobre un volumen existente, aplique este ALTER a mano
-- o recree el volumen con `make clean && make up`.

ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(16) NOT NULL DEFAULT 'user';

ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_role;
ALTER TABLE users ADD CONSTRAINT chk_users_role CHECK (role IN ('user', 'admin'));
