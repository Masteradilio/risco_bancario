import { Calculator, TrendingDown, Layers, Activity } from 'lucide-react'
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
} from 'recharts'

const eclData = [
    { mes: 'Jul', ecl: 2.1 },
    { mes: 'Ago', ecl: 2.3 },
    { mes: 'Set', ecl: 2.0 },
    { mes: 'Out', ecl: 2.4 },
    { mes: 'Nov', ecl: 2.6 },
    { mes: 'Dez', ecl: 2.9 },
]

const stageData = [
    { name: 'Stage 1', value: 75, color: '#4ade80' },
    { name: 'Stage 2', value: 18, color: '#f97316' },
    { name: 'Stage 3', value: 7, color: '#ef4444' },
]

export default function ECLDashboardPage() {
    return (
        <div className="space-y-6">
            {/* KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="kpi-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">ECL Total</p>
                            <p className="text-2xl font-bold mt-1">R$ 2.9M</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-red-500/10">
                            <Calculator className="h-5 w-5 text-red-500" />
                        </div>
                    </div>
                </div>
                <div className="kpi-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">PD Médio</p>
                            <p className="text-2xl font-bold mt-1">12.4%</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-amber-500/10">
                            <TrendingDown className="h-5 w-5 text-amber-500" />
                        </div>
                    </div>
                </div>
                <div className="kpi-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">LGD Médio</p>
                            <p className="text-2xl font-bold mt-1">45.2%</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-primary/10">
                            <Layers className="h-5 w-5 text-primary" />
                        </div>
                    </div>
                </div>
                <div className="kpi-card">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">EAD Total</p>
                            <p className="text-2xl font-bold mt-1">R$ 124M</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-emerald-500/10">
                            <Activity className="h-5 w-5 text-emerald-500" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Evolução ECL */}
                <div className="chart-container">
                    <h3 className="font-semibold mb-4">Evolução do ECL</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <AreaChart data={eclData}>
                            <defs>
                                <linearGradient id="colorEcl" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                            <XAxis dataKey="mes" stroke="var(--muted-foreground)" fontSize={12} />
                            <YAxis stroke="var(--muted-foreground)" fontSize={12} tickFormatter={(v) => `R$ ${v}M`} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'var(--popover)',
                                    borderColor: 'var(--border)',
                                    borderRadius: '8px',
                                }}
                                formatter={(value: number) => [`R$ ${value}M`, 'ECL']}
                            />
                            <Area type="monotone" dataKey="ecl" stroke="#ef4444" fill="url(#colorEcl)" strokeWidth={2} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                {/* Distribuição por Stage */}
                <div className="chart-container">
                    <h3 className="font-semibold mb-4">Distribuição por Estágio IFRS 9</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                            <Pie
                                data={stageData}
                                innerRadius={60}
                                outerRadius={90}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {stageData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'var(--popover)',
                                    borderColor: 'var(--border)',
                                    borderRadius: '8px',
                                }}
                                formatter={(value: number) => [`${value}%`, '']}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="flex justify-center gap-6 mt-4">
                        {stageData.map((item) => (
                            <div key={item.name} className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                                <span className="text-sm">{item.name}: {item.value}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Info Card */}
            <div className="chart-container bg-primary/5 border-primary/20">
                <h4 className="font-medium text-primary mb-2">📋 Conformidade CMN 4966 - Art. 36</h4>
                <p className="text-sm text-muted-foreground">
                    A perda esperada (ECL) é calculada considerando três estágios de risco conforme IFRS 9,
                    aplicando a fórmula: <strong className="text-foreground">ECL = PD × LGD × EAD</strong>.
                    O horizonte temporal varia entre 12 meses (Stage 1) e lifetime (Stages 2 e 3).
                </p>
            </div>
        </div>
    )
}
