import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Database, Search, ShieldCheck } from 'lucide-react'
import {
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts'
import { getExecutionEvidence, getLimitationRegister, type ExecutionEvidence, type LimitationRegister } from '@/lib/api/ecl_api'
import { probabilityWeightedEcl, summarizeScenarios } from '@/lib/ecl_view_model'
import { useAuth } from '@/stores/useAuth'

const money = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const percent = new Intl.NumberFormat('pt-BR', { style: 'percent', maximumFractionDigits: 4 })

export default function ECLDashboardPage() {
    const token = useAuth((state) => state.token)
    const [executionId, setExecutionId] = useState('')
    const [evidence, setEvidence] = useState<ExecutionEvidence | null>(null)
    const [limitations, setLimitations] = useState<LimitationRegister | null>(null)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (!token) return
        getLimitationRegister(token).then(setLimitations).catch((reason: unknown) => {
            setError(reason instanceof Error ? reason.message : 'Falha ao carregar limitações')
        })
    }, [token])

    const loadEvidence = async () => {
        if (!token || !executionId.trim()) return
        setLoading(true)
        setError('')
        try {
            setEvidence(await getExecutionEvidence(executionId.trim(), token))
        } catch (reason) {
            setEvidence(null)
            setError(reason instanceof Error ? reason.message : 'Falha ao carregar execução')
        } finally {
            setLoading(false)
        }
    }

    const summaries = useMemo(() => evidence ? summarizeScenarios(evidence) : [], [evidence])
    const first = evidence?.results[0]
    const assessment = first?.payload.stage_assessment
    const curves = evidence?.results.map((result) => ({
        key: `${result.scenario_id}-${result.period}`,
        scenario: result.scenario_id,
        period: result.period,
        date: result.payload.reference_date,
        pd: Number(result.payload.marginal_pd),
        lgd: Number(result.payload.lgd),
        ead: Number(result.payload.ead),
        ecl: Number(result.ecl_amount),
        payloadHash: result.payload_hash,
    })) ?? []

    return (
        <div className="space-y-6">
            <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-800 dark:text-amber-200">
                DEMONSTRAÇÃO COM DADOS SINTÉTICOS — resultados não homologados para contabilização, crédito ou reporte oficial.
            </div>

            <section className="chart-container space-y-4">
                <div className="flex items-center gap-2"><Database className="h-5 w-5 text-primary" /><h3 className="font-semibold">Evidência persistida de execução</h3></div>
                <div className="flex gap-3">
                    <input aria-label="ID da execução" value={executionId} onChange={(event) => setExecutionId(event.target.value)} placeholder="UUID da execução ECL" className="flex-1 rounded-lg border border-border bg-input px-4 py-2" />
                    <button onClick={loadEvidence} disabled={loading || !executionId.trim()} className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50"><Search className="h-4 w-4" />{loading ? 'Carregando…' : 'Consultar'}</button>
                </div>
                {error && <div role="alert" className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}. Nenhum dado substituto foi exibido.</div>}
                {!evidence && !error && <p className="text-sm text-muted-foreground">Informe uma execução existente. O painel não gera valores fictícios quando não há evidência persistida.</p>}
            </section>

            {evidence && first && assessment && (
                <>
                    <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
                        <div className="kpi-card"><p className="text-sm text-muted-foreground">Estágio atual</p><p className="text-2xl font-bold">Stage {assessment.current_stage}</p><p className="text-xs">Originação: Stage {assessment.origination_stage}</p></div>
                        <div className="kpi-card"><p className="text-sm text-muted-foreground">Rating</p><p className="text-2xl font-bold">{assessment.current_rating}</p><p className="text-xs">Originação: {assessment.origination_rating}</p></div>
                        <div className="kpi-card"><p className="text-sm text-muted-foreground">PD lifetime</p><p className="text-2xl font-bold">{percent.format(Number(assessment.current_lifetime_pd))}</p><p className="text-xs">Originação: {percent.format(Number(assessment.origination_lifetime_pd))}</p></div>
                        <div className="kpi-card"><p className="text-sm text-muted-foreground">ECL ponderado reconciliado</p><p className="text-2xl font-bold">{money.format(probabilityWeightedEcl(evidence))}</p><p className="text-xs">{summaries.length} cenários</p></div>
                    </section>

                    <section className="chart-container">
                        <h3 className="mb-3 font-semibold">Justificativas de estágio</h3>
                        <div className="flex flex-wrap gap-2">{assessment.reason_codes.map((reason) => <span key={reason} className="status-badge status-badge-warning">{reason}</span>)}</div>
                    </section>

                    <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                        <div className="chart-container"><h3 className="mb-4 font-semibold">Curvas marginais PD / LGD</h3><ResponsiveContainer width="100%" height={300}><LineChart data={curves}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="key" hide /><YAxis tickFormatter={(value: number) => percent.format(value)} /><Tooltip /><Legend /><Line dataKey="pd" name="PD marginal" stroke="#f97316" dot={false} /><Line dataKey="lgd" name="LGD" stroke="#ef4444" dot={false} /></LineChart></ResponsiveContainer></div>
                        <div className="chart-container"><h3 className="mb-4 font-semibold">Curva EAD</h3><ResponsiveContainer width="100%" height={300}><LineChart data={curves}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="key" hide /><YAxis /><Tooltip /><Legend /><Line dataKey="ead" name="EAD" stroke="#22c55e" dot={false} /></LineChart></ResponsiveContainer></div>
                    </section>

                    <section className="chart-container overflow-x-auto"><h3 className="mb-4 font-semibold">ECL por período e cenário</h3><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-left">Cenário</th><th className="p-2 text-left">Período</th><th className="p-2 text-left">Data</th><th className="p-2 text-right">ECL</th><th className="p-2 text-left">Hash do resultado</th></tr></thead><tbody>{curves.map((row) => <tr key={row.key} className="border-b"><td className="p-2">{row.scenario}</td><td className="p-2">{row.period}</td><td className="p-2">{row.date}</td><td className="p-2 text-right">{money.format(row.ecl)}</td><td className="p-2 font-mono text-xs">{row.payloadHash}</td></tr>)}</tbody></table></section>

                    <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                        <div className="chart-container"><h3 className="mb-3 font-semibold">Reconciliação por cenário</h3>{summaries.map((item) => <div key={item.scenarioId} className="grid grid-cols-3 border-b py-2 text-sm"><span>{item.scenarioId} ({item.kind})</span><span>{money.format(item.ecl)}</span><span>Peso {percent.format(item.weight)} · {money.format(item.weightedEcl)}</span></div>)}</div>
                        <div className="chart-container"><h3 className="mb-3 font-semibold">Overlays e pisos</h3><p className="text-sm"><strong>Status:</strong> {first.payload.adjustments.status}</p><p className="mt-2 text-sm text-muted-foreground">Overlay gerencial, piso regulatório e ECL reportado não foram aplicados nesta execução; valores ausentes permanecem nulos, sem substituição por zero.</p></div>
                    </section>

                    <section className="chart-container text-sm"><div className="mb-3 flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-primary" /><h3 className="font-semibold">Linhagem e versão</h3></div><p><strong>Execução:</strong> {evidence.execution_id} · revisão {evidence.revision} · status {evidence.status}</p><p className="break-all"><strong>Hash de linhagem:</strong> {evidence.lineage_hash}</p><pre className="mt-3 overflow-auto rounded bg-muted p-3 text-xs">{JSON.stringify(evidence.lineage, null, 2)}</pre></section>
                </>
            )}

            <section className="chart-container">
                <div className="mb-3 flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-amber-500" /><h3 className="font-semibold">Status de validação e limitações</h3></div>
                {limitations ? <><p className="text-sm"><strong>Status:</strong> {limitations.status}</p><p className="break-all text-xs text-muted-foreground">Fonte: {limitations.source_path} · SHA-256 {limitations.source_hash}</p><pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap rounded bg-muted p-3 text-xs">{limitations.content}</pre></> : <p className="text-sm text-muted-foreground">Registro de limitações indisponível; nenhum status presumido.</p>}
            </section>
        </div>
    )
}
