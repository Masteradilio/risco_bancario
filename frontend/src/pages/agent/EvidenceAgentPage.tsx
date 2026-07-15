import { useState } from 'react'
import { Bot, Send, ShieldAlert } from 'lucide-react'
import { queryEvidenceAgent, type AgentResponse } from '@/lib/api/ecl_api'
import { useAuth } from '@/stores/useAuth'

export default function EvidenceAgentPage() {
    const token = useAuth((state) => state.token)
    const [executionId, setExecutionId] = useState('')
    const [question, setQuestion] = useState('')
    const [response, setResponse] = useState<AgentResponse | null>(null)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const submit = async (event: React.FormEvent) => {
        event.preventDefault()
        if (!token || !executionId.trim() || !question.trim()) return
        setLoading(true)
        setError('')
        try {
            setResponse(await queryEvidenceAgent(executionId.trim(), question.trim(), token))
        } catch (reason) {
            setResponse(null)
            setError(reason instanceof Error ? reason.message : 'Falha ao consultar o agente')
        } finally {
            setLoading(false)
        }
    }

    return <div className="space-y-6">
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-800 dark:text-amber-200">AGENTE RESTRITO A EVIDÊNCIAS SINTÉTICAS PERSISTIDAS — não atesta conformidade oficial e não executa ferramentas arbitrárias.</div>
        <section className="chart-container"><div className="mb-4 flex items-center gap-2"><Bot className="h-5 w-5 text-primary" /><h3 className="font-semibold">Consulta fundamentada</h3></div><form onSubmit={submit} className="space-y-3"><input aria-label="ID da execução do agente" value={executionId} onChange={(event) => setExecutionId(event.target.value)} placeholder="UUID da execução autorizada" className="w-full rounded-lg border border-border bg-input px-4 py-2" /><textarea aria-label="Pergunta ao agente" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Pergunte sobre estágio, cenários, ECL, versões ou limitações" rows={4} className="w-full rounded-lg border border-border bg-input px-4 py-2" /><button disabled={loading || !executionId.trim() || !question.trim()} className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50"><Send className="h-4 w-4" />{loading ? 'Consultando…' : 'Consultar evidência'}</button></form>{error && <p role="alert" className="mt-4 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}. Nenhuma resposta alternativa foi gerada.</p>}</section>
        {response && <section className="chart-container space-y-4"><div className="flex items-center gap-2"><ShieldAlert className="h-5 w-5 text-amber-500" /><strong>{response.guardrail_status}</strong><span className="text-xs text-muted-foreground">{response.data_classification} · conformidade {response.official_conformity}</span></div><p className="whitespace-pre-wrap text-sm leading-6">{response.answer}</p><div><h4 className="mb-2 font-semibold">Citações internas verificáveis</h4>{response.citations.length === 0 ? <p className="text-sm text-muted-foreground">Resposta recusada sem acesso a fontes.</p> : response.citations.map((citation) => <div key={citation.citation_id} className="mb-2 rounded bg-muted p-3 text-xs"><p className="font-medium">[{citation.citation_id}]</p><p>{citation.locator}</p><p className="break-all font-mono">SHA-256 {citation.source_hash}</p></div>)}</div></section>}
    </div>
}
