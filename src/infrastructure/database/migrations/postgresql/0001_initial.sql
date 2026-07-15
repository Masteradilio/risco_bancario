CREATE TABLE operational_contracts (
    contract_id TEXT NOT NULL,
    source_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contract_id, source_version)
);

CREATE TABLE operational_snapshots (
    snapshot_id TEXT NOT NULL,
    reference_date DATE NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (snapshot_id, reference_date)
);

CREATE TABLE operational_macro_observations (
    series_id TEXT NOT NULL,
    observation_date DATE NOT NULL,
    source_version TEXT NOT NULL,
    value_decimal NUMERIC NOT NULL,
    payload_hash TEXT NOT NULL,
    PRIMARY KEY (series_id, observation_date, source_version)
);

CREATE TABLE model_registry_models (
    model_id TEXT NOT NULL,
    version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (model_id, version)
);

CREATE TABLE model_registry_scenarios (
    scenario_id TEXT NOT NULL,
    version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (scenario_id, version)
);

CREATE TABLE calculation_executions (
    execution_id TEXT PRIMARY KEY,
    execution_key TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    previous_execution_id TEXT REFERENCES calculation_executions(execution_id),
    reference_date DATE NOT NULL,
    lineage_json TEXT NOT NULL,
    lineage_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (execution_key, revision)
);

CREATE TABLE calculation_results (
    result_id BIGSERIAL PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES calculation_executions(execution_id),
    contract_id TEXT NOT NULL,
    period INTEGER NOT NULL CHECK (period >= 0),
    scenario_id TEXT NOT NULL,
    ecl_amount NUMERIC NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (execution_id, contract_id, period, scenario_id)
);

CREATE TABLE audit_lineage_events (
    event_id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES calculation_executions(execution_id),
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL
);

CREATE OR REPLACE FUNCTION reject_audit_lineage_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit lineage events are immutable';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_lineage_events_no_update
BEFORE UPDATE OR DELETE ON audit_lineage_events
FOR EACH ROW EXECUTE FUNCTION reject_audit_lineage_mutation();
