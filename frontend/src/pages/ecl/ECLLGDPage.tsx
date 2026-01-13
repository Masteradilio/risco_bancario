import { Activity, Info } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const lgdData = [
    { produto: 'Consignado', lgdBase: 35, lgdDownturn: 44 },
    { produto: 'Cartão', lgdBase: 70, lgdDownturn: 88 },
    { produto: 'Imobiliário', lgdBase: 12, lgdDownturn: 15 },
    { produto: 'Veículo', lgdBase: 30, lgdDownturn: 38 },
    { produto: 'Banparacard', lgdBase: 45, lgdDownturn: 56 },
]

export default function ECLLGDPage() {
    return (
        <div className="space-y-6">
            {/* Gráfico */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">LGD por Produto (Basel III)</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={lgdData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis dataKey="produto" stroke="var(--muted-foreground)" fontSize={12} />
                        <YAxis stroke="var(--muted-foreground)" fontSize={12} tickFormatter={(v) => `${v}%`} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'var(--popover)',
                                borderColor: 'var(--border)',
                                borderRadius: '8px',
                            }}
                            formatter={(value: number) => [`${value}%`, '']}
                        />
                        <Bar dataKey="lgdBase" fill="#3b82f6" name="LGD Base" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="lgdDownturn" fill="#ef4444" name="LGD Downturn" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Tabela */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Parâmetros LGD</h3>
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-border">
                            <th className="text-left py-2">Produto</th>
                            <th className="text-right py-2">LGD Base</th>
                            <th className="text-right py-2">LGD Downturn</th>
                        </tr>
                    </thead>
                    <tbody>
                        {lgdData.map((l) => (
                            <tr key={l.produto} className="border-b border-border hover:bg-muted/50">
                                <td className="py-2 font-medium">{l.produto}</td>
                                <td className="py-2 text-right">{l.lgdBase}%</td>
                                <td className="py-2 text-right text-red-500">{l.lgdDownturn}%</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="chart-container bg-primary/5 border-primary/20">
                <div className="flex items-start gap-3">
                    <Info className="h-5 w-5 text-primary mt-0.5" />
                    <div>
                        <h4 className="font-medium text-primary">LGD Segmentado</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                            O LGD é segmentado por produto, considerando fatores como tipo de garantia, prazo e
                            valor da operação. Em cenário de downturn, aplica-se o fator 1.25x sobre o LGD base.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
