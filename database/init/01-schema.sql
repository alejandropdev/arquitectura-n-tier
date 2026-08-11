-- Tier 3 — esquema de datos.
-- PostgreSQL ejecuta este script la primera vez que se crea el volumen.

CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY,
    username        VARCHAR(32)  NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    failed_attempts INTEGER      NOT NULL DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE INDEX IF NOT EXISTS ix_users_email    ON users (email);

-- Bitácora de auditoría: quién intentó autenticarse, cuándo y con qué resultado.
CREATE TABLE IF NOT EXISTS login_attempts (
    id          UUID PRIMARY KEY,
    username    VARCHAR(32) NOT NULL,
    successful  BOOLEAN     NOT NULL,
    reason      VARCHAR(64),
    client_ip   VARCHAR(64) NOT NULL DEFAULT '-',
    request_id  VARCHAR(64) NOT NULL DEFAULT '-',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id     UUID REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_login_attempts_username    ON login_attempts (username);
CREATE INDEX IF NOT EXISTS ix_login_attempts_occurred_at ON login_attempts (occurred_at);
