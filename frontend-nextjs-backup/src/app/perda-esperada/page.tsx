"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useSettings } from "@/stores/useSettings"
import { eclApi } from "@/services/api"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    LineChart,
    Line,
    Legend,
    Area,
    AreaChart,
} from "recharts"

// KPIs mockados
const kpis = {
    eclTotal: 2430000,
    lgdMedio: 0.325,
    eadTotal: 156000000,
    cobertura: 0.0156,
    operacoes: 15847,
    stage1Pct: 0.70,
    stage2Pct: 0.20,
    stage3Pct: 0.10,
}

// Dados para gráficos
const eclPorStage = [
    { name: "Stage 1", value: 450000, color: "#22c55e", pct: 18.5 },
    { name: "Stage 2", value: 780000, color: "#eab308", pct: 32.1 },
    { name: "Stage 3", value: 1200000, color: "#ef4444", pct: 49.4 },
]

const eclPorGrupo = [
    { grupo: "GH 1", ecl: 125000, clientes: 4500, pd: 0.005 },
    { grupo: "GH 2", ecl: 380000, clientes: 1800, pd: 0.05 },
    { grupo: "GH 3", ecl: 920000, clientes: 850, pd: 0.15 },
    { grupo: "GH 4", ecl: 1005000, clientes: 350, pd: 0.40 },
]

const eclPorProduto = [
    { produto: "Consignado", carteira: 85000000, ecl: 425000, lgd: 0.25, cobertura: 0.005 },
    { produto: "Cartão", carteira: 42000000, ecl: 1260000, lgd: 0.80, cobertura: 0.030 },
    { produto: "Imobiliário", carteira: 25000000, ecl: 125000, lgd: 0.10, cobertura: 0.005 },
    { produto: "Veículo", carteira: 4000000, ecl: 620000, lgd: 0.35, cobertura: 0.155 },
]

const evolucaoECL = [
    { mes: "Jul", ecl: 2100000, provisao: 2200000 },
    { mes: "Ago", ecl: 2150000, provisao: 2250000 },
    { mes: "Set", ecl: 2280000, provisao: 2350000 },
    { mes: "Out", ecl: 2320000, provisao: 2400000 },
    { mes: "Nov", ecl: 2380000, provisao: 2420000 },
    { mes: "Dez", ecl: 2430000, provisao: 2500000 },
]

const formatCurrency = (value: number) => {
    if (value >= 1000000) return `R$ ${(value / 1000000).toFixed(2)}M`
    if (value >= 1000) return `R$ ${(value / 1000).toFixed(0)}k`
    return `R$ ${value.toFixed(2)}`
}

const formatPct = (value: number) => `${(value * 100).toFixed(2)}%`

export default function PerdaEsperadaDashboard() {
    const { eclApiUrl } = useSettings()
    const [apiStatus, setApiStatus] = useState<'loading' | 'online' | 'offline'>('loading')

    useEffect(() => {
        const checkApi = async () => {
            try {
                await eclApi.health(eclApiUrl)
                setApiStatus('online')
            } catch {
                setApiStatus('offline')
            }
        }
        checkApi()
    }, [eclApiUrl])

    return (
        <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            ECL Total
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-blue-600">
                            {formatCurrency(kpis.eclTotal)}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            {kpis.operacoes.toLocaleString()} operações
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            EAD Total
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-green-600">
                            {formatCurrency(kpis.eadTotal)}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Exposure at Default
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            LGD Médio
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-amber-600">
                            {formatPct(kpis.lgdMedio)}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Loss Given Default ponderado
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                            Cobertura ECL
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-purple-600">
                            {formatPct(kpis.cobertura)}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            ECL / EAD Total
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Distribuição por Stage */}
            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Distribuição por Stage IFRS 9</CardTitle>
                        <CardDescription>ECL por classificação de risco</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={eclPorStage}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        paddingAngle={5}
                                        dataKey="value"
                                        label={({ name, pct }) => `${name}: ${pct}%`}
                                    >
                                        {eclPorStage.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip formatter={(value: number) => formatCurrency(value)} />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="grid grid-cols-3 gap-4 mt-4">
                            <div className="text-center p-2 bg-green-500/10 rounded-lg">
                                <p className="text-2xl font-bold text-green-600">{formatPct(kpis.stage1Pct)}</p>
                                <p className="text-xs text-muted-foreground">Stage 1</p>
                            </div>
                            <div className="text-center p-2 bg-yellow-500/10 rounded-lg">
                                <p className="text-2xl font-bold text-yellow-600">{formatPct(kpis.stage2Pct)}</p>
                                <p className="text-xs text-muted-foreground">Stage 2</p>
                            </div>
                            <div className="text-center p-2 bg-red-500/10 rounded-lg">
                                <p className="text-2xl font-bold text-red-600">{formatPct(kpis.stage3Pct)}</p>
                                <p className="text-xs text-muted-foreground">Stage 3</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>ECL por Grupo Homogêneo</CardTitle>
                        <CardDescription>Distribuição por faixa de PD</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={eclPorGrupo}>
                                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                                    <XAxis dataKey="grupo" />
                                    <YAxis tickFormatter={(v) => formatCurrency(v)} />
                                    <Tooltip
                                        formatter={(value: number, name: string) => [
                                            name === 'ecl' ? formatCurrency(value) : value,
                                            name === 'ecl' ? 'ECL' : name
                                        ]}
                                    />
                                    <Bar dataKey="ecl" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="grid grid-cols-4 gap-2 mt-4 text-center">
                            {eclPorGrupo.map((g) => (
                                <div key={g.grupo} className="p-2 bg-muted/50 rounded">
                                    <p className="text-xs font-medium">{g.grupo}</p>
                                    <p className="text-sm text-muted-foreground">{g.clientes} clientes</p>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Evolução ECL */}
            <Card>
                <CardHeader>
                    <CardTitle>Evolução ECL vs Provisão</CardTitle>
                    <CardDescription>Últimos 6 meses</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={evolucaoECL}>
                                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                                <XAxis dataKey="mes" />
                                <YAxis tickFormatter={(v) => formatCurrency(v)} />
                                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                                <Legend />
                                <Area
                                    type="monotone"
                                    dataKey="provisao"
                                    stackId="1"
                                    stroke="#22c55e"
                                    fill="#22c55e"
                                    fillOpacity={0.3}
                                    name="Provisão Contábil"
                                />
                                <Area
                                    type="monotone"
                                    dataKey="ecl"
                                    stackId="2"
                                    stroke="#3b82f6"
                                    fill="#3b82f6"
                                    fillOpacity={0.6}
                                    name="ECL Calculado"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            {/* Tabela por Produto */}
            <Card>
                <CardHeader>
                    <CardTitle>Resumo por Produto</CardTitle>
                    <CardDescription>Métricas ECL por tipo de crédito</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="overflow-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-muted">
                                <tr>
                                    <th className="p-3 text-left font-medium">Produto</th>
                                    <th className="p-3 text-right font-medium">Carteira</th>
                                    <th className="p-3 text-right font-medium">ECL</th>
                                    <th className="p-3 text-right font-medium">LGD</th>
                                    <th className="p-3 text-right font-medium">Cobertura</th>
                                </tr>
                            </thead>
                            <tbody>
                                {eclPorProduto.map((p) => (
                                    <tr key={p.produto} className="border-t hover:bg-muted/50">
                                        <td className="p-3 font-medium">{p.produto}</td>
                                        <td className="p-3 text-right">{formatCurrency(p.carteira)}</td>
                                        <td className="p-3 text-right">{formatCurrency(p.ecl)}</td>
                                        <td className="p-3 text-right">{formatPct(p.lgd)}</td>
                                        <td className="p-3 text-right">
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${p.cobertura > 0.05
                                                    ? 'bg-red-100 text-red-700'
                                                    : p.cobertura > 0.02
                                                        ? 'bg-yellow-100 text-yellow-700'
                                                        : 'bg-green-100 text-green-700'
                                                }`}>
                                                {formatPct(p.cobertura)}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot className="bg-muted font-medium">
                                <tr>
                                    <td className="p-3">Total</td>
                                    <td className="p-3 text-right">{formatCurrency(kpis.eadTotal)}</td>
                                    <td className="p-3 text-right">{formatCurrency(kpis.eclTotal)}</td>
                                    <td className="p-3 text-right">{formatPct(kpis.lgdMedio)}</td>
                                    <td className="p-3 text-right">{formatPct(kpis.cobertura)}</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {/* Status API */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span className={`w-2 h-2 rounded-full ${apiStatus === 'online' ? 'bg-green-500' :
                        apiStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
                    }`} />
                API ECL: {apiStatus === 'online' ? 'Online' : apiStatus === 'offline' ? 'Offline' : 'Verificando...'}
            </div>
        </div>
    )
}
