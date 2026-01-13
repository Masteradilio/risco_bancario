import { RefreshCw, Clock, CheckCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

const contratosCura = [
    { id: 'C001', cliente: 'João Silva', estagioAtual: 2, mesesCura: 4, progresso: 67, meta: 6 },
    { id: 'C002', cliente: 'Maria Santos', estagioAtual: 3, mesesCura: 8, progresso: 67, meta: 12 },
    { id: 'C003', cliente: 'Pedro Costa', estagioAtual: 2, mesesCura: 5, progresso: 83, meta: 6 },
]

export default function ECLCuraPage() {
    return (
        <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Em Período de Cura</p>
                    <p className="text-2xl font-bold mt-1">127</p>
                    <p className="text-xs text-muted-foreground mt-2">Contratos em observação</p>
                </div>
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Curados Este Mês</p>
                    <p className="text-2xl font-bold text-emerald-500 mt-1">23</p>
                    <p className="text-xs text-muted-foreground mt-2">Retornaram para estágio anterior</p>
                </div>
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Taxa de Cura</p>
                    <p className="text-2xl font-bold mt-1">18.1%</p>
                    <p className="text-xs text-muted-foreground mt-2">Últimos 12 meses</p>
                </div>
            </div>

            {/* Tabela de Contratos */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Contratos em Período de Cura</h3>
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-border">
                            <th className="text-left py-2">Contrato</th>
                            <th className="text-left py-2">Cliente</th>
                            <th className="text-left py-2">Estágio</th>
                            <th className="text-left py-2">Progresso</th>
                        </tr>
                    </thead>
                    <tbody>
                        {contratosCura.map((c) => (
                            <tr key={c.id} className="border-b border-border hover:bg-muted/50">
                                <td className="py-2 font-medium">{c.id}</td>
                                <td className="py-2">{c.cliente}</td>
                                <td className="py-2">
                                    <span className={cn(
                                        'status-badge',
                                        c.estagioAtual === 2 && 'status-badge-warning',
                                        c.estagioAtual === 3 && 'status-badge-danger',
                                    )}>
                                        Stage {c.estagioAtual}
                                    </span>
                                </td>
                                <td className="py-2">
                                    <div className="flex items-center gap-2">
                                        <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-primary"
                                                style={{ width: `${c.progresso}%` }}
                                            />
                                        </div>
                                        <span className="text-xs text-muted-foreground">
                                            {c.mesesCura}/{c.meta} meses
                                        </span>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Regras de Cura */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Critérios de Cura (Art. 41 CMN 4966)</h3>
                <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-secondary/50">
                        <p className="font-medium text-amber-500">Stage 2 → Stage 1</p>
                        <p className="text-sm text-muted-foreground mt-1">
                            6 meses consecutivos sem atraso {'>'} 30 dias + PD atual menor que PD na migração
                        </p>
                    </div>
                    <div className="p-3 rounded-lg bg-secondary/50">
                        <p className="font-medium text-red-500">Stage 3 → Stage 2</p>
                        <p className="text-sm text-muted-foreground mt-1">
                            12 meses consecutivos + amortização ≥ 30% + sem novos eventos de crédito
                        </p>
                    </div>
                    <div className="p-3 rounded-lg bg-secondary/50">
                        <p className="font-medium text-primary">Reestruturações</p>
                        <p className="text-sm text-muted-foreground mt-1">
                            24 meses de observação + 50% de amortização (critérios mais rigorosos)
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
