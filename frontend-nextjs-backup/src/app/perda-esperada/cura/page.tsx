"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { HeartPulse, Clock, CheckCircle2, XCircle, AlertTriangle, TrendingDown, ArrowRight } from "lucide-react"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts"

// Contratos em período de cura
const contratosEmCura = [
    {
        contrato: "CTR2024001",
        cliente: "CLI001",
        estagio_atual: 2,
        estagio_destino: 1,
        meses_observacao: 4,
        meses_necessarios: 6,
        dias_atraso: 0,
        pd_entrada: 0.12,
        pd_atual: 0.08,
        elegivel: true,
        motivo: null
    },
    {
        contrato: "CTR2024002",
        cliente: "CLI002",
        estagio_atual: 3,
        estagio_destino: 2,
        meses_observacao: 8,
        meses_necessarios: 12,
        dias_atraso: 0,
        pd_entrada: 0.45,
        pd_atual: 0.25,
        elegivel: true,
        motivo: null
    },
    {
        contrato: "CTR2024003",
        cliente: "CLI003",
        estagio_atual: 2,
        estagio_destino: 1,
        meses_observacao: 5,
        meses_necessarios: 6,
        dias_atraso: 15,
        pd_entrada: 0.15,
        pd_atual: 0.10,
        elegivel: false,
        motivo: "Atraso durante observação"
    },
    {
        contrato: "CTR2024004",
        cliente: "CLI004",
        estagio_atual: 3,
        estagio_destino: 2,
        meses_observacao: 20,
        meses_necessarios: 24,
        dias_atraso: 0,
        pd_entrada: 0.60,
        pd_atual: 0.35,
        elegivel: true,
        motivo: null,
        reestruturado: true
    },
]

// Estatísticas de cura
const estatisticas = {
    total_em_observacao: 847,
    stage2_para_1: 612,
    stage3_para_2: 235,
    taxa_sucesso_historica: 0.72,
    tempo_medio_cura: 7.5,
}

// Histórico de curas
const historicoCuras = [
    { mes: "Jul", sucesso: 45, falha: 12 },
    { mes: "Ago", sucesso: 52, falha: 15 },
    { mes: "Set", sucesso: 48, falha: 18 },
    { mes: "Out", sucesso: 61, falha: 14 },
    { mes: "Nov", sucesso: 55, falha: 11 },
    { mes: "Dez", sucesso: 58, falha: 9 },
]

export default function CuraPage() {
    const getProgressColor = (current: number, total: number) => {
        const pct = current / total
        if (pct >= 0.9) return "bg-green-500"
        if (pct >= 0.5) return "bg-yellow-500"
        return "bg-blue-500"
    }

    return (
        <div className="space-y-6">
            {/* Info Card */}
            <Card className="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
                <CardContent className="pt-6">
                    <div className="flex gap-4">
                        <div className="flex-shrink-0">
                            <HeartPulse className="h-8 w-8 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-blue-900 dark:text-blue-100">Sistema de Cura e Reversão</h3>
                            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                                Regras estritas para o retorno de operações a estágios de menor risco (Ex: Stage 3 → 2).
                                Exige demonstração consistente de capacidade de pagamento e cumprimento de período probatório (Cura)
                                antes da reclassificação.
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 font-medium">
                                📜 Referência histórica não verificada: art. 41 da CMN 4.966/2021
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* KPIs */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                            <HeartPulse className="h-4 w-4" />
                            Em Observação
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{estatisticas.total_em_observacao}</p>
                        <p className="text-xs text-muted-foreground">contratos em período de cura</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Stage 2 → 1</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{estatisticas.stage2_para_1}</p>
                        <p className="text-xs text-muted-foreground">6 meses de observação</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Stage 3 → 2</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">{estatisticas.stage3_para_2}</p>
                        <p className="text-xs text-muted-foreground">12 meses de observação</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-muted-foreground">Taxa Sucesso</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold text-green-600">
                            {(estatisticas.taxa_sucesso_historica * 100).toFixed(0)}%
                        </p>
                        <p className="text-xs text-muted-foreground">histórico</p>
                    </CardContent>
                </Card>
            </div>

            {/* Regras de Cura */}
            <Card>
                <CardHeader>
                    <CardTitle>Regras de Cura - Art. 41 CMN 4966</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-4 md:grid-cols-2">
                        <div className="p-4 border rounded-lg border-green-500/30">
                            <div className="flex items-center gap-2 mb-2">
                                <Badge className="bg-yellow-100 text-yellow-700">Stage 2</Badge>
                                <ArrowRight className="h-4 w-4" />
                                <Badge className="bg-green-100 text-green-700">Stage 1</Badge>
                            </div>
                            <ul className="text-sm space-y-1 text-muted-foreground">
                                <li>• 6 meses de observação sem atraso &gt; 30 dias</li>
                                <li>• Melhora sustentada do PD</li>
                                <li>• Nenhum trigger ativo</li>
                            </ul>
                        </div>
                        <div className="p-4 border rounded-lg border-yellow-500/30">
                            <div className="flex items-center gap-2 mb-2">
                                <Badge className="bg-red-100 text-red-700">Stage 3</Badge>
                                <ArrowRight className="h-4 w-4" />
                                <Badge className="bg-yellow-100 text-yellow-700">Stage 2</Badge>
                            </div>
                            <ul className="text-sm space-y-1 text-muted-foreground">
                                <li>• 12 meses de observação (24 se reestruturado)</li>
                                <li>• 30% do principal amortizado (50% se reestruturado)</li>
                                <li>• Nenhum atraso &gt; 60 dias no período</li>
                            </ul>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Contratos em Cura */}
            <Card>
                <CardHeader>
                    <CardTitle>Contratos em Período de Cura</CardTitle>
                    <CardDescription>Monitoramento de elegibilidade para reversão de estágio</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {contratosEmCura.map((c) => (
                            <div
                                key={c.contrato}
                                className={`p-4 border rounded-lg ${c.elegivel ? 'border-green-500/30' : 'border-red-500/30'}`}
                            >
                                <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
                                    <div className="flex items-center gap-3">
                                        <span className="font-mono font-medium">{c.contrato}</span>
                                        <div className="flex items-center gap-1">
                                            <Badge className={c.estagio_atual === 2 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}>
                                                Stage {c.estagio_atual}
                                            </Badge>
                                            <ArrowRight className="h-4 w-4 mx-1" />
                                            <Badge className={c.estagio_destino === 1 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>
                                                Stage {c.estagio_destino}
                                            </Badge>
                                        </div>
                                        {c.reestruturado && (
                                            <Badge variant="outline" className="text-orange-600">Reestruturado</Badge>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {c.elegivel ? (
                                            <span className="text-green-600 flex items-center gap-1 text-sm">
                                                <CheckCircle2 className="h-4 w-4" /> Elegível
                                            </span>
                                        ) : (
                                            <span className="text-red-600 flex items-center gap-1 text-sm">
                                                <XCircle className="h-4 w-4" /> {c.motivo}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted-foreground">Progresso observação</span>
                                        <span className="font-medium">{c.meses_observacao} / {c.meses_necessarios} meses</span>
                                    </div>
                                    <Progress
                                        value={(c.meses_observacao / c.meses_necessarios) * 100}
                                        className={`h-2 ${getProgressColor(c.meses_observacao, c.meses_necessarios)}`}
                                    />
                                    <div className="grid grid-cols-3 gap-4 text-sm mt-2">
                                        <div>
                                            <span className="text-muted-foreground">Dias atraso:</span>
                                            <span className={`ml-2 font-medium ${c.dias_atraso > 0 ? 'text-red-600' : ''}`}>
                                                {c.dias_atraso}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-muted-foreground">PD entrada:</span>
                                            <span className="ml-2 font-mono">{(c.pd_entrada * 100).toFixed(1)}%</span>
                                        </div>
                                        <div>
                                            <span className="text-muted-foreground">PD atual:</span>
                                            <span className="ml-2 font-mono text-green-600">{(c.pd_atual * 100).toFixed(1)}%</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Histórico de Curas */}
            <Card>
                <CardHeader>
                    <CardTitle>Histórico de Curas</CardTitle>
                    <CardDescription>Sucesso vs Falha nos últimos 6 meses</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={historicoCuras}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="mes" />
                                <YAxis />
                                <Tooltip />
                                <Bar dataKey="sucesso" name="Cura Sucesso" fill="#22c55e" stackId="a" radius={[4, 4, 0, 0]} />
                                <Bar dataKey="falha" name="Cura Falha" fill="#ef4444" stackId="a" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
