import { Trash2, TrendingUp, Info } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const recuperacoes = [
    { ano: '2022', baixas: 1.2, recuperacoes: 0.18 },
    { ano: '2023', baixas: 1.5, recuperacoes: 0.22 },
    { ano: '2024', baixas: 1.8, recuperacoes: 0.28 },
    { ano: '2025', baixas: 2.1, recuperacoes: 0.35 },
    { ano: '2026', baixas: 0.4, recuperacoes: 0.08 },
]

export default function ECLWriteoffPage() {
    return (
        <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Write-offs YTD</p>
                    <p className="text-2xl font-bold text-red-500 mt-1">R$ 4.2M</p>
                </div>
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Recuperações YTD</p>
                    <p className="text-2xl font-bold text-emerald-500 mt-1">R$ 680K</p>
                </div>
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Taxa Recuperação</p>
                    <p className="text-2xl font-bold mt-1">16.2%</p>
                </div>
                <div className="kpi-card">
                    <p className="text-sm text-muted-foreground">Em Acompanhamento</p>
                    <p className="text-2xl font-bold mt-1">342</p>
                    <p className="text-xs text-muted-foreground mt-2">Contratos (janela 5 anos)</p>
                </div>
            </div>

            {/* Gráfico */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Histórico de Baixas e Recuperações</h3>
                <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={recuperacoes}>
                        <defs>
                            <linearGradient id="colorBaixas" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorRecup" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#4ade80" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#4ade80" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis dataKey="ano" stroke="var(--muted-foreground)" fontSize={12} />
                        <YAxis stroke="var(--muted-foreground)" fontSize={12} tickFormatter={(v) => `R$ ${v}M`} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'var(--popover)',
                                borderColor: 'var(--border)',
                                borderRadius: '8px',
                            }}
                            formatter={(value: number) => [`R$ ${value}M`, '']}
                        />
                        <Area type="monotone" dataKey="baixas" stroke="#ef4444" fill="url(#colorBaixas)" strokeWidth={2} name="Baixas" />
                        <Area type="monotone" dataKey="recuperacoes" stroke="#4ade80" fill="url(#colorRecup)" strokeWidth={2} name="Recuperações" />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            <div className="chart-container bg-amber-500/5 border-amber-500/20">
                <div className="flex items-start gap-3">
                    <Info className="h-5 w-5 text-amber-500 mt-0.5" />
                    <div>
                        <h4 className="font-medium text-amber-500">Art. 49 CMN 4966</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                            As recuperações de créditos baixados devem ser acompanhadas por período mínimo de 5 anos (1825 dias),
                            sendo utilizadas para calibração da taxa de recuperação histórica.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
