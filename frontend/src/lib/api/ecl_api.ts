import { apiUrl } from '@/stores/useAuth'

export interface StageAssessment {
    origination_stage: number
    current_stage: number
    origination_rating: string
    current_rating: string
    origination_lifetime_pd: string
    current_lifetime_pd: string
    reason_codes: string[]
}

export interface ResultPayload {
    stage: number
    stage_assessment: StageAssessment
    scenario_kind: string
    scenario_weight: string
    reference_date: string
    survival_at_start: string
    marginal_pd: string
    lgd: string
    ead: string
    ccf: string
    discount_factor: string
    expected_loss: string
    adjustments: {
        status: string
        management_overlay: string | null
        regulatory_floor: string | null
        reported_ecl: string | null
    }
}

export interface ExecutionEvidence {
    execution_id: string
    execution_key: string
    revision: number
    previous_execution_id: string | null
    reference_date: string
    lineage_hash: string
    status: string
    created_at: string
    lineage: Record<string, unknown>
    results: Array<{
        contract_id: string
        period: number
        scenario_id: string
        ecl_amount: string
        payload_hash: string
        payload: ResultPayload
    }>
}

export interface LimitationRegister {
    status: string
    source_path: string
    source_hash: string
    content: string
}

export interface AgentResponse {
    answer: string
    citations: Array<{
        citation_id: string
        source_type: 'execution_lineage' | 'execution_result' | 'document'
        locator: string
        source_hash: string
    }>
    guardrail_status: 'GROUNDED' | 'LIMITED' | 'REFUSED'
    data_classification: 'SYNTHETIC'
    official_conformity: 'NOT_ASSESSED'
}

async function authorizedGet<T>(path: string, token: string): Promise<T> {
    const response = await fetch(apiUrl(path), { headers: { Authorization: `Bearer ${token}` } })
    if (!response.ok) {
        const detail = await response.text()
        throw new Error(`API ${response.status}: ${detail}`)
    }
    return response.json() as Promise<T>
}

export const getExecutionEvidence = (executionId: string, token: string) =>
    authorizedGet<ExecutionEvidence>(`/api/v1/ecl/executions/${encodeURIComponent(executionId)}`, token)

export const getLimitationRegister = (token: string) =>
    authorizedGet<LimitationRegister>('/api/v1/validation/limitations', token)

export async function queryEvidenceAgent(
    executionId: string,
    question: string,
    token: string,
): Promise<AgentResponse> {
    const response = await fetch(apiUrl('/api/v1/agent/query'), {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ execution_id: executionId, question }),
    })
    if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`)
    return response.json() as Promise<AgentResponse>
}
