CREATE TABLE audit_events (
    audit_sequence BIGSERIAL PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    actor_id TEXT NOT NULL,
    actor_role TEXT,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    execution_id TEXT REFERENCES calculation_executions(execution_id),
    status TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    result_hash TEXT NOT NULL,
    versions_json TEXT NOT NULL,
    event_json TEXT NOT NULL,
    previous_event_hash TEXT,
    event_hash TEXT NOT NULL UNIQUE,
    occurred_at TIMESTAMPTZ NOT NULL
);

CREATE TRIGGER audit_events_no_update
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW EXECUTE FUNCTION reject_audit_lineage_mutation();
