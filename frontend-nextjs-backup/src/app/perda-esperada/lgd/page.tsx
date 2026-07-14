"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
} from "recharts"
import { BarChart3 } from "lucide-react"

const lgdPorProduto = [
    { produto: "Consignado", lgd: 0.25, downturn: 0.32, sicr: 0.28, garantia: "Sim", tipo: "Com recurso" },
    { produto: "Cartão Crédito", lgd: 0.80, downturn: 0.88, sicr: 0.82, garantia: "Não", tipo: "Clean" },
    { produto: "Cheque Especial", lgd: 0.85, downturn: 0.92, sicr: 0.87, garantia: "Não", tipo: "Clean" },
    { produto: "Imobiliário", lgd: 0.10, downturn: 0.15, sicr: 0.12, garantia: "Sim", tipo: "Alienação fiduciária" },
    { produto: "Veículo", lgd: 0.35, downturn: 0.45, sicr: 0.38, garantia: "Sim", tipo: "Alienação fiduciária" },
    { produto: "Energia Solar", lgd: 0.40, downturn: 0.50, sicr: 0.42, garantia: "Sim", tipo: "Equipamento" },
    { produto: "Pessoal", lgd: 0.70, downturn: 0.78, sicr: 0.72, garantia: "Não", tipo: "Clean" },
    { produto: "Capital Giro", lgd: 0.60, downturn: 0.70, sicr: 0.63, garantia: "Parcial", tipo: "Recebíveis" },
]

const componentes = [
    { nome: "Taxa Recuperação", valor: 35, desc: "% médio recuperado pós-default" },
    { nome: "Custo Recuperação", valor: 12, desc: "% gasto no processo" },
    { nome: "Desconto Temporal", valor: 8, desc: "VPL do valor recuperado" },
    { nome: "Perda Incorrida", valor: 45, desc: "Efetivamente perdido" },
]

const radarData = lgdPorProduto.slice(0, 6).map(p => ({
    produto: p.produto.slice(0, 10),
    lgd: p.lgd * 100,
    downturn: p.downturn * 100,
}))

const formatPct = (v: number) => `${(v * 100).toFixed(0)}%`

export default function LGDPage() {
    const lgdMedio = lgdPorProduto.reduce((s, p) => s + p.lgd, 0) / lgdPorProduto.length

    return (
        <div className="space-y-6">
            {/* Info Card */}
            <Card className="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
                <CardContent className="pt-6">
                    <div className="flex gap-4">
                        <div className="flex-shrink-0">
                            <BarChart3 className="h-8 w-8 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-blue-900 dark:text-blue-100">LGD - Loss Given Default</h3>
                            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                                Estimativa da perda efetiva em caso de default (LGD = 1 - Taxa de Recuperação),
                                considerando custos de cobrança, valor do dinheiro no tempo e valor de mercado das garantias.
                                O modelo considera cenários Base e Downturn (estresse).
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 font-medium">
                                📜 Referência histórica não verificada: art. 29 da CMN 4.966/2021
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* KPIs */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">LGD Médio Ponderado</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{formatPct(lgdMedio)}</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Produtos Mapeados</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{lgdPorProduto.length}</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Menor LGD</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold text-green-600">
                            {formatPct(Math.min(...lgdPorProduto.map(p => p.lgd)))}
                        </p>
                        <p className="text-xs text-muted-foreground">Imobiliário</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Maior LGD</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold text-red-600">
                            {formatPct(Math.max(...lgdPorProduto.map(p => p.lgd)))}
                        </p>
                        <p className="text-xs text-muted-foreground">Cheque Especial</p>
                    </CardContent>
                </Card>
            </div>

            <Tabs defaultValue="produtos" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="produtos">Por Produto</TabsTrigger>
                    <TabsTrigger value="componentes">Componentes</TabsTrigger>
                    <TabsTrigger value="comparativo">Comparativo</TabsTrigger>
                </TabsList>

                <TabsContent value="produtos" className="space-y-4">
                    {/* Gráfico de barras */}
                    <Card>
                        <CardHeader>
                            <CardTitle>LGD por Produto</CardTitle>
                            <CardDescription>Comparativo Base vs Downturn</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="h-[350px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={lgdPorProduto} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis type="number" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} domain={[0, 1]} />
                                        <YAxis dataKey="produto" type="category" width={100} />
                                        <Tooltip formatter={(v: number | undefined) => formatPct(v || 0)} />
                                        <Legend />
                                        <Bar dataKey="lgd" name="LGD Base" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                                        <Bar dataKey="downturn" name="LGD Downturn" fill="#ef4444" radius={[0, 4, 4, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Tabela detalhada */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Detalhamento LGD</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <table className="w-full text-sm">
                                <thead className="bg-muted">
                                    <tr>
                                        <th className="p-3 text-left">Produto</th>
                                        <th className="p-3 text-right">LGD Base</th>
                                        <th className="p-3 text-right">LGD Downturn</th>
                                        <th className="p-3 text-right">LGD SICR</th>
                                        <th className="p-3 text-center">Garantia</th>
                                        <th className="p-3 text-left">Tipo</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {lgdPorProduto.map((p) => (
                                        <tr key={p.produto} className="border-t hover:bg-muted/50">
                                            <td className="p-3 font-medium">{p.produto}</td>
                                            <td className="p-3 text-right">{formatPct(p.lgd)}</td>
                                            <td className="p-3 text-right text-red-600">{formatPct(p.downturn)}</td>
                                            <td className="p-3 text-right text-yellow-600">{formatPct(p.sicr)}</td>
                                            <td className="p-3 text-center">
                                                <Badge variant={p.garantia === "Sim" ? "default" : p.garantia === "Parcial" ? "secondary" : "outline"}>
                                                    {p.garantia}
                                                </Badge>
                                            </td>
                                            <td className="p-3 text-muted-foreground">{p.tipo}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="componentes" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Composição do LGD</CardTitle>
                            <CardDescription>Breakdown dos componentes de perda</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-4 md:grid-cols-2">
                                {componentes.map((c) => (
                                    <div key={c.nome} className="p-4 border rounded-lg">
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="font-medium">{c.nome}</span>
                                            <Badge>{c.valor}%</Badge>
                                        </div>
                                        <div className="w-full bg-muted rounded-full h-2">
                                            <div
                                                className="bg-blue-600 h-2 rounded-full transition-all"
                                                style={{ width: `${c.valor}%` }}
                                            />
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-2">{c.desc}</p>
                                    </div>
                                ))}
                            </div>
                            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
                                <p className="font-medium">Fórmula LGD:</p>
                                <code className="text-sm">
                                    LGD = 1 - Taxa Recuperação × (1 - Custo) × Fator Desconto
                                </code>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="comparativo" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Radar Comparativo</CardTitle>
                            <CardDescription>LGD Base vs Downturn por produto</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="h-[400px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <RadarChart data={radarData}>
                                        <PolarGrid />
                                        <PolarAngleAxis dataKey="produto" />
                                        <PolarRadiusAxis angle={30} domain={[0, 100]} />
                                        <Radar name="LGD Base" dataKey="lgd" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.5} />
                                        <Radar name="LGD Downturn" dataKey="downturn" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
                                        <Legend />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
