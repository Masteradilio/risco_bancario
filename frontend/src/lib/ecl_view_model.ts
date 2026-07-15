import type { ExecutionEvidence } from '@/lib/api/ecl_api'

export interface ScenarioSummary {
    scenarioId: string
    kind: string
    weight: number
    ecl: number
    weightedEcl: number
}

export function summarizeScenarios(evidence: ExecutionEvidence): ScenarioSummary[] {
    const grouped = new Map<string, ScenarioSummary>()
    for (const result of evidence.results) {
        const current = grouped.get(result.scenario_id) ?? {
            scenarioId: result.scenario_id,
            kind: result.payload.scenario_kind,
            weight: Number(result.payload.scenario_weight),
            ecl: 0,
            weightedEcl: 0,
        }
        current.ecl += Number(result.ecl_amount)
        current.weightedEcl += Number(result.ecl_amount) * current.weight
        grouped.set(result.scenario_id, current)
    }
    return [...grouped.values()].sort((a, b) => a.scenarioId.localeCompare(b.scenarioId))
}

export function probabilityWeightedEcl(evidence: ExecutionEvidence): number {
    return summarizeScenarios(evidence).reduce((total, item) => total + item.weightedEcl, 0)
}
