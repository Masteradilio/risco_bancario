CREATE TABLE security_users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('ANALYST', 'MANAGER', 'AUDITOR', 'ADMIN')),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    token_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE security_sessions (
    jti_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES security_users(user_id),
    token_version INTEGER NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE security_confirmations (
    confirmation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES security_users(user_id),
    action TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);
