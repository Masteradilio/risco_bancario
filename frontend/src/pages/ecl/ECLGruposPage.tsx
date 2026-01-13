import { BarChart3, Info } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const gruposData = [
    { nome: 'GH1 - Baixo Risco', pd: '0-10%', contratos: 4250, color: '#4ade80' },
    { nome: 'GH2 - Risco Moderado', pd: '10-25%', contratos: 2890, color: '#fbbf24' },
    { nome: 'GH3 - Risco Elevado', pd: '25-50%', contratos: 1420, color: '#f97316' },
    { nome: 'GH4 - Alto Risco', pd: '50-75%', contratos: 680, color: '#ef4444' },
    { nome: 'GH5 - Crítico', pd: '>75%', contratos: 210, color: '#dc2626' },
]

export default function ECLGruposPage() {
    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Tabela */}
                <div className="chart-container">
                    <h3 className="font-semibold mb-4">Grupos Homogêneos de Risco</h3>
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-border">
                                <th className="text-left py-2">Grupo</th>
                                <th className="text-left py-2">Faixa PD</th>
                                <th className="text-right py-2">Contratos</th>
                            </tr>
                        </thead>
                        <tbody>
                            {gruposData.map((g) => (
                                <tr key={g.nome} className="border-b border-border hover:bg-muted/50">
                                    <td className="py-2 flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: g.color }} />
                                        {g.nome}
                                    </td>
                                    <td className="py-2">{g.pd}</td>
                                    <td className="py-2 text-right">{g.contratos.toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Gráfico */}
                <div className="chart-container">
                    <h3 className="font-semibold mb-4">Distribuição</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                            <Pie data={gruposData} dataKey="contratos" nameKey="nome" innerRadius={50} outerRadius={80}>
                                {gruposData.map((entry, i) => (
                                    <Cell key={i} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'var(--popover)',
                                    borderColor: 'var(--border)',
                                    borderRadius: '8px',
                                }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="chart-container bg-primary/5 border-primary/20">
                <div className="flex items-start gap-3">
                    <Info className="h-5 w-5 text-primary mt-0.5" />
                    <div>
                        <h4 className="font-medium text-primary">Segmentação por K-means</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                            Os grupos homogêneos são criados utilizando algoritmo K-means baseado na distribuição de PD, permitindo
                            aplicação de parâmetros específicos por segmento conforme Art. 36 CMN 4966.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
