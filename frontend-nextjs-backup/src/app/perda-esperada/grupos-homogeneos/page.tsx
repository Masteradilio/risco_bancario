"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Users, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react"
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
    Legend,
    ScatterChart,
    Scatter,
    ZAxis,
} from "recharts"

const grupos = [
    {
        id: 1,
        nome: "GH 1 - Baixo Risco",
        faixa: "0% - 2.5%",
        pd_medio: 0.012,
        clientes: 12500,
        carteira: 85000000,
        ecl: 125000,
        woe: -0.85,
        cor: "#22c55e"
    },
    {
        id: 2,
        nome: "GH 2 - Risco Moderado",
        faixa: "2.5% - 8%",
        pd_medio: 0.048,
        clientes: 5200,
        carteira: 42000000,
        ecl: 380000,
        woe: -0.15,
        cor: "#84cc16"
    },
    {
        id: 3,
        nome: "GH 3 - Risco Alto",
        faixa: "8% - 20%",
        pd_medio: 0.135,
        clientes: 2100,
        carteira: 18000000,
        ecl: 920000,
        woe: 0.25,
        cor: "#eab308"
    },
    {
        id: 4,
        nome: "GH 4 - Risco Muito Alto",
        faixa: "> 20%",
        pd_medio: 0.42,
        clientes: 847,
        carteira: 5000000,
        ecl: 1005000,
        woe: 0.65,
        cor: "#ef4444"
    },
]

const distribuicaoClientes = grupos.map(g => ({
    name: `GH ${g.id}`,
    value: g.clientes,
    color: g.cor
}))

const scatterData = grupos.map(g => ({
    x: g.pd_medio * 100,
    y: g.carteira / 1000000,
    z: g.ecl / 10000,
    name: `GH ${g.id}`
}))

const formatCurrency = (value: number) => {
    if (value >= 1000000) return `R$ ${(value / 1000000).toFixed(1)}M`
    if (value >= 1000) return `R$ ${(value / 1000).toFixed(0)}k`
    return `R$ ${value.toFixed(0)}`
}

export default function GruposHomogeneosPage() {
    const totalClientes = grupos.reduce((s, g) => s + g.clientes, 0)
    const totalCarteira = grupos.reduce((s, g) => s + g.carteira, 0)
    const totalECL = grupos.reduce((s, g) => s + g.ecl, 0)

    return (
        <div className="space-y-6">
            {/* Info Card */}
            <Card className="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
                <CardContent className="pt-6">
                    <div className="flex gap-4">
                        <div className="flex-shrink-0">
                            <Users className="h-8 w-8 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-blue-900 dark:text-blue-100">Grupos Homogêneos de Risco</h3>
                            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                                Segmentação da carteira em grupos com características de risco similares (Produtos, PD, Garantias)
                                para permitir a mensuração coletiva da perda esperada quando a avaliação individual não é viável ou necessária.
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 font-medium">
                                📜 Conformidade: Art. 23 da Resolução CMN 4966/2021 - Metodologias de Mensuração
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Cards de resumo */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Total Clientes</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{totalClientes.toLocaleString()}</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Carteira Total</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{formatCurrency(totalCarteira)}</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">ECL Total</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{formatCurrency(totalECL)}</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Grupos Ativos</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{grupos.length}</p>
                    </CardContent>
                </Card>
            </div>

            {/* Cards por grupo */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {grupos.map((g) => (
                    <Card key={g.id} className="border-l-4" style={{ borderLeftColor: g.cor }}>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-base">{g.nome}</CardTitle>
                            <CardDescription>PD: {g.faixa}</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-muted-foreground">Clientes</span>
                                <span className="font-bold">{g.clientes.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-muted-foreground">Carteira</span>
                                <span className="font-bold">{formatCurrency(g.carteira)}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-muted-foreground">ECL</span>
                                <span className="font-bold">{formatCurrency(g.ecl)}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-muted-foreground">PD Médio</span>
                                <Badge variant={g.pd_medio > 0.1 ? "destructive" : "secondary"}>
                                    {(g.pd_medio * 100).toFixed(2)}%
                                </Badge>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-muted-foreground">WOE</span>
                                <span className={`font-mono ${g.woe < 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    {g.woe > 0 ? '+' : ''}{g.woe.toFixed(2)}
                                </span>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Gráficos */}
            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Distribuição de Clientes</CardTitle>
                        <CardDescription>Por grupo homogêneo</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={distribuicaoClientes}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        paddingAngle={5}
                                        dataKey="value"
                                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    >
                                        {distribuicaoClientes.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip formatter={(v: number) => v.toLocaleString()} />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>ECL por Grupo</CardTitle>
                        <CardDescription>Valor absoluto</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={grupos}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey={(d) => `GH ${d.id}`} />
                                    <YAxis tickFormatter={(v) => formatCurrency(v)} />
                                    <Tooltip formatter={(v: number) => formatCurrency(v)} />
                                    <Bar dataKey="ecl" radius={[4, 4, 0, 0]}>
                                        {grupos.map((g, i) => (
                                            <Cell key={`cell-${i}`} fill={g.cor} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Tabela completa */}
            <Card>
                <CardHeader>
                    <CardTitle>Detalhamento por Grupo</CardTitle>
                </CardHeader>
                <CardContent>
                    <table className="w-full text-sm">
                        <thead className="bg-muted">
                            <tr>
                                <th className="p-3 text-left">Grupo</th>
                                <th className="p-3 text-left">Faixa PD</th>
                                <th className="p-3 text-right">Clientes</th>
                                <th className="p-3 text-right">Carteira</th>
                                <th className="p-3 text-right">ECL</th>
                                <th className="p-3 text-right">PD Médio</th>
                                <th className="p-3 text-right">WOE</th>
                                <th className="p-3 text-right">Cobertura</th>
                            </tr>
                        </thead>
                        <tbody>
                            {grupos.map((g) => (
                                <tr key={g.id} className="border-t hover:bg-muted/50">
                                    <td className="p-3 font-medium">{g.nome}</td>
                                    <td className="p-3">{g.faixa}</td>
                                    <td className="p-3 text-right">{g.clientes.toLocaleString()}</td>
                                    <td className="p-3 text-right">{formatCurrency(g.carteira)}</td>
                                    <td className="p-3 text-right">{formatCurrency(g.ecl)}</td>
                                    <td className="p-3 text-right">{(g.pd_medio * 100).toFixed(2)}%</td>
                                    <td className="p-3 text-right font-mono">{g.woe.toFixed(2)}</td>
                                    <td className="p-3 text-right">{((g.ecl / g.carteira) * 100).toFixed(2)}%</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
