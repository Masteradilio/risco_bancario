CREATE TABLE calculation_jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED')),
    request_hash TEXT NOT NULL,
    request_json TEXT NOT NULL,
    result_json TEXT,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);
