import { TrendingUp, Info } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const cenarios = [
    { cenario: 'Otimista', peso: 15, kPdFl: 0.85, kLgdFl: 0.90 },
    { cenario: 'Base', peso: 70, kPdFl: 1.00, kLgdFl: 1.00 },
    { cenario: 'Pessimista', peso: 15, kPdFl: 1.25, kLgdFl: 1.15 },
]

const macroData = [
    { indicador: 'SELIC', otimista: 10.5, base: 11.75, pessimista: 14.0 },
    { indicador: 'PIB', otimista: 3.2, base: 2.1, pessimista: 0.5 },
    { indicador: 'IPCA', otimista: 3.5, base: 4.5, pessimista: 6.8 },
]

export default function ECLForwardLookingPage() {
    return (
        <div className="space-y-6">
            {/* Cenários */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {cenarios.map((c) => (
                    <div key={c.cenario} className="kpi-card">
                        <p className="text-sm text-muted-foreground">Cenário {c.cenario}</p>
                        <p className="text-2xl font-bold mt-1">{c.peso}%</p>
                        <div className="mt-3 space-y-1 text-sm">
                            <p>K_PD_FL: <span className="font-medium">{c.kPdFl}</span></p>
                            <p>K_LGD_FL: <span className="font-medium">{c.kLgdFl}</span></p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Projeções Macro */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Projeções Macroeconômicas</h3>
                <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={macroData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis type="number" stroke="var(--muted-foreground)" fontSize={12} />
                        <YAxis dataKey="indicador" type="category" stroke="var(--muted-foreground)" fontSize={12} width={60} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'var(--popover)',
                                borderColor: 'var(--border)',
                                borderRadius: '8px',
                            }}
                        />
                        <Bar dataKey="otimista" fill="#4ade80" name="Otimista" />
                        <Bar dataKey="base" fill="#3b82f6" name="Base" />
                        <Bar dataKey="pessimista" fill="#ef4444" name="Pessimista" />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            <div className="chart-container bg-primary/5 border-primary/20">
                <div className="flex items-start gap-3">
                    <Info className="h-5 w-5 text-primary mt-0.5" />
                    <div>
                        <h4 className="font-medium text-primary">Art. 36 §5º CMN 4966</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                            A estimativa de perda esperada deve incorporar informações prospectivas (forward looking),
                            incluindo cenários macroeconômicos ponderados probabilisticamente.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
