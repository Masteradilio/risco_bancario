"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, Sun, Cloud, CloudRain, AlertTriangle, RefreshCw } from "lucide-react"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    LineChart,
    Line,
    Legend,
    AreaChart,
    Area,
} from "recharts"

// Cenários padrão CMN 4966
const cenariosBase = [
    {
        id: 'otimista',
        nome: 'Otimista',
        icone: Sun,
        cor: '#22c55e',
        peso: 15,
        spread_pd: 0.85,
        spread_lgd: 0.90,
        selic: 10.5,
        pib: 3.5,
        ipca: 3.8,
        desemprego: 6.5
    },
    {
        id: 'base',
        nome: 'Base',
        icone: Cloud,
        cor: '#3b82f6',
        peso: 70,
        spread_pd: 1.00,
        spread_lgd: 1.00,
        selic: 12.25,
        pib: 2.2,
        ipca: 4.5,
        desemprego: 7.8
    },
    {
        id: 'pessimista',
        nome: 'Pessimista',
        icone: CloudRain,
        cor: '#ef4444',
        peso: 15,
        spread_pd: 1.25,
        spread_lgd: 1.15,
        selic: 14.5,
        pib: -0.5,
        ipca: 6.0,
        desemprego: 9.5
    },
]

// Projeção temporal
const projecaoTemporal = [
    { mes: 'Jan', otimista: 2100000, base: 2300000, pessimista: 2650000 },
    { mes: 'Fev', otimista: 2080000, base: 2320000, pessimista: 2700000 },
    { mes: 'Mar', otimista: 2050000, base: 2350000, pessimista: 2780000 },
    { mes: 'Abr', otimista: 2020000, base: 2380000, pessimista: 2850000 },
    { mes: 'Mai', otimista: 2000000, base: 2420000, pessimista: 2920000 },
    { mes: 'Jun', otimista: 1980000, base: 2450000, pessimista: 3000000 },
]

// Impacto por produto
const impactoPorProduto = [
    { produto: 'Consignado', base: 425000, otimista: -15, pessimista: 25 },
    { produto: 'Cartão', base: 1260000, otimista: -12, pessimista: 30 },
    { produto: 'Imobiliário', base: 125000, otimista: -10, pessimista: 20 },
    { produto: 'Veículo', base: 620000, otimista: -18, pessimista: 35 },
]

const formatCurrency = (value: number) => {
    if (value >= 1000000) return `R$ ${(value / 1000000).toFixed(2)}M`
    if (value >= 1000) return `R$ ${(value / 1000).toFixed(0)}k`
    return `R$ ${value.toFixed(0)}`
}

export default function ForwardLookingPage() {
    const [cenarios, setCenarios] = useState(cenariosBase)
    const [editMode, setEditMode] = useState(false)

    const atualizarPeso = (id: string, novoPeso: number) => {
        const outros = cenarios.filter(c => c.id !== id)
        const diferencaProporcional = (cenarios.find(c => c.id === id)?.peso || 0) - novoPeso
        const pesoTotal = outros.reduce((s, c) => s + c.peso, 0)

        setCenarios(cenarios.map(c => {
            if (c.id === id) return { ...c, peso: novoPeso }
            return { ...c, peso: c.peso + (c.peso / pesoTotal) * diferencaProporcional }
        }))
    }

    const resetarPesos = () => {
        setCenarios(cenariosBase)
    }

    const eclPonderado = cenarios.reduce((sum, c) => {
        const eclCenario = c.id === 'otimista' ? 2100000 : c.id === 'base' ? 2430000 : 2850000
        return sum + (eclCenario * c.peso / 100)
    }, 0)

    return (
        <div className="space-y-6">
            {/* Info Card */}
            <Card className="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
                <CardContent className="pt-6">
                    <div className="flex gap-4">
                        <div className="flex-shrink-0">
                            <TrendingUp className="h-8 w-8 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-blue-900 dark:text-blue-100">Cenários Forward Looking</h3>
                            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                                Incorporação de informações prospectivas (futuras) e cenários macroeconômicos (Otimista, Base, Pessimista)
                                na estimativa de perdas, garantindo que o modelo reaja a expectativas econômicas e não apenas ao passado.
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 font-medium">
                                📜 Conformidade: Art. 36 §5º da Resolução CMN 4966/2021 - Cenários Ponderados
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Header com ECL ponderado */}
            <Card className="bg-gradient-to-br from-blue-500/10 to-purple-500/10">
                <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-muted-foreground">ECL Ponderado (Multi-Cenário)</p>
                            <p className="text-4xl font-bold">{formatCurrency(eclPonderado)}</p>
                            <p className="text-sm text-muted-foreground mt-1">
                                Art. 36 §5º CMN 4966/2021
                            </p>
                        </div>
                        <div className="text-right">
                            <p className="text-sm text-muted-foreground">Fórmula</p>
                            <code className="text-xs bg-muted px-2 py-1 rounded">
                                ECL = Σ(peso_i × ECL_i)
                            </code>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Cards de cenários */}
            <div className="grid gap-4 md:grid-cols-3">
                {cenarios.map((c) => {
                    const Icon = c.icone
                    const eclCenario = c.id === 'otimista' ? 2100000 : c.id === 'base' ? 2430000 : 2850000

                    return (
                        <Card key={c.id} className="border-2" style={{ borderColor: `${c.cor}40` }}>
                            <CardHeader className="pb-2">
                                <CardTitle className="flex items-center gap-2">
                                    <Icon className="h-5 w-5" style={{ color: c.cor }} />
                                    Cenário {c.nome}
                                </CardTitle>
                                <CardDescription>
                                    Peso: <span className="font-bold">{c.peso.toFixed(0)}%</span>
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {editMode && (
                                    <div className="space-y-2">
                                        <Slider
                                            value={[c.peso]}
                                            min={5}
                                            max={80}
                                            step={5}
                                            onValueChange={([v]) => atualizarPeso(c.id, v)}
                                        />
                                    </div>
                                )}

                                <div className="text-2xl font-bold" style={{ color: c.cor }}>
                                    {formatCurrency(eclCenario)}
                                </div>

                                <div className="grid grid-cols-2 gap-2 text-sm">
                                    <div className="p-2 bg-muted/50 rounded">
                                        <p className="text-xs text-muted-foreground">Spread PD</p>
                                        <p className="font-bold">{c.spread_pd.toFixed(2)}x</p>
                                    </div>
                                    <div className="p-2 bg-muted/50 rounded">
                                        <p className="text-xs text-muted-foreground">Spread LGD</p>
                                        <p className="font-bold">{c.spread_lgd.toFixed(2)}x</p>
                                    </div>
                                </div>

                                <div className="space-y-1 text-xs">
                                    <div className="flex justify-between">
                                        <span>SELIC</span>
                                        <span className="font-mono">{c.selic.toFixed(2)}%</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>PIB</span>
                                        <span className="font-mono">{c.pib > 0 ? '+' : ''}{c.pib.toFixed(1)}%</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>IPCA</span>
                                        <span className="font-mono">{c.ipca.toFixed(1)}%</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Desemprego</span>
                                        <span className="font-mono">{c.desemprego.toFixed(1)}%</span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )
                })}
            </div>

            {/* Controles */}
            <div className="flex gap-2">
                <Button
                    variant={editMode ? "default" : "outline"}
                    onClick={() => setEditMode(!editMode)}
                >
                    {editMode ? "Salvar Pesos" : "Editar Pesos"}
                </Button>
                <Button variant="outline" onClick={resetarPesos}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Resetar Padrão
                </Button>
            </div>

            {/* Gráfico de projeção */}
            <Card>
                <CardHeader>
                    <CardTitle>Projeção Temporal por Cenário</CardTitle>
                    <CardDescription>ECL projetado para os próximos 6 meses</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={projecaoTemporal}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="mes" />
                                <YAxis tickFormatter={(v) => formatCurrency(v)} />
                                <Tooltip formatter={(v: number | undefined) => formatCurrency(v || 0)} />
                                <Legend />
                                <Area
                                    type="monotone"
                                    dataKey="pessimista"
                                    stackId="1"
                                    stroke="#ef4444"
                                    fill="#ef4444"
                                    fillOpacity={0.3}
                                    name="Pessimista"
                                />
                                <Area
                                    type="monotone"
                                    dataKey="base"
                                    stackId="2"
                                    stroke="#3b82f6"
                                    fill="#3b82f6"
                                    fillOpacity={0.5}
                                    name="Base"
                                />
                                <Area
                                    type="monotone"
                                    dataKey="otimista"
                                    stackId="3"
                                    stroke="#22c55e"
                                    fill="#22c55e"
                                    fillOpacity={0.7}
                                    name="Otimista"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            {/* Impacto por produto */}
            <Card>
                <CardHeader>
                    <CardTitle>Impacto por Produto</CardTitle>
                    <CardDescription>Variação percentual em relação ao cenário base</CardDescription>
                </CardHeader>
                <CardContent>
                    <table className="w-full text-sm">
                        <thead className="bg-muted">
                            <tr>
                                <th className="p-3 text-left">Produto</th>
                                <th className="p-3 text-right">ECL Base</th>
                                <th className="p-3 text-right">Otimista</th>
                                <th className="p-3 text-right">Pessimista</th>
                            </tr>
                        </thead>
                        <tbody>
                            {impactoPorProduto.map((p) => (
                                <tr key={p.produto} className="border-t">
                                    <td className="p-3 font-medium">{p.produto}</td>
                                    <td className="p-3 text-right">{formatCurrency(p.base)}</td>
                                    <td className="p-3 text-right">
                                        <span className="text-green-600 font-medium">
                                            {p.otimista}%
                                        </span>
                                    </td>
                                    <td className="p-3 text-right">
                                        <span className="text-red-600 font-medium">
                                            +{p.pessimista}%
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
