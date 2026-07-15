CREATE TABLE calculation_jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED')),
    request_hash TEXT NOT NULL,
    request_json TEXT NOT NULL,
    result_json TEXT,
    error_code TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT
);
