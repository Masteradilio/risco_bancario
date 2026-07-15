CREATE TABLE operational_contracts (
    contract_id TEXT NOT NULL,
    source_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contract_id, source_version)
);

CREATE TABLE operational_snapshots (
    snapshot_id TEXT NOT NULL,
    reference_date TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (snapshot_id, reference_date)
);

CREATE TABLE operational_macro_observations (
    series_id TEXT NOT NULL,
    observation_date TEXT NOT NULL,
    source_version TEXT NOT NULL,
    value_decimal TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    PRIMARY KEY (series_id, observation_date, source_version)
);

CREATE TABLE model_registry_models (
    model_id TEXT NOT NULL,
    version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (model_id, version)
);

CREATE TABLE model_registry_scenarios (
    scenario_id TEXT NOT NULL,
    version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (scenario_id, version)
);

CREATE TABLE calculation_executions (
    execution_id TEXT PRIMARY KEY,
    execution_key TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    previous_execution_id TEXT REFERENCES calculation_executions(execution_id),
    reference_date TEXT NOT NULL,
    lineage_json TEXT NOT NULL,
    lineage_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (execution_key, revision)
);

CREATE TABLE calculation_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL REFERENCES calculation_executions(execution_id),
    contract_id TEXT NOT NULL,
    period INTEGER NOT NULL CHECK (period >= 0),
    scenario_id TEXT NOT NULL,
    ecl_amount TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (execution_id, contract_id, period, scenario_id)
);

CREATE TABLE audit_lineage_events (
    event_id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES calculation_executions(execution_id),
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);

CREATE TRIGGER audit_lineage_events_no_update
BEFORE UPDATE ON audit_lineage_events
BEGIN
    SELECT RAISE(ABORT, 'audit lineage events are immutable');
END;

CREATE TRIGGER audit_lineage_events_no_delete
BEFORE DELETE ON audit_lineage_events
BEGIN
    SELECT RAISE(ABORT, 'audit lineage events are immutable');
END;
