"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, TrendingUp, TrendingDown, ArrowRight, Clock, CheckCircle2, XCircle } from "lucide-react"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Sankey,
    Treemap,
    Cell,
} from "recharts"

// Dados de triggers
const triggersConfig = [
    {
        id: 'atraso_30',
        nome: 'Atraso > 30 dias',
        descricao: 'Migração automática para Stage 2',
        stage_destino: 2,
        tipo: 'quantitativo'
    },
    {
        id: 'atraso_90',
        nome: 'Atraso > 90 dias',
        descricao: 'Migração automática para Stage 3',
        stage_destino: 3,
        tipo: 'quantitativo'
    },
    {
        id: 'pd_ratio',
        nome: 'PD Ratio > 3x',
        descricao: 'PD atual / PD concessão > 3',
        stage_destino: 2,
        tipo: 'quantitativo'
    },
    {
        id: 'reestruturacao',
        nome: 'Reestruturação',
        descricao: 'Operação reestruturada com perdão',
        stage_destino: 3,
        tipo: 'qualitativo'
    },
    {
        id: 'watch_list',
        nome: 'Watch List',
        descricao: 'Cliente em lista de observação',
        stage_destino: 2,
        tipo: 'qualitativo'
    },
    {
        id: 'arrasto',
        nome: 'Arrasto Contraparte',
        descricao: 'Se um produto Stage 3, todos migram',
        stage_destino: 3,
        tipo: 'arrasto'
    },
]

// Histórico de migrações
const migracoes = [
    { contrato: 'CTR2024001', de: 1, para: 2, motivo: 'atraso_30', data: '2024-12-15', dias_atraso: 35 },
    { contrato: 'CTR2024002', de: 2, para: 3, motivo: 'atraso_90', data: '2024-12-10', dias_atraso: 105 },
    { contrato: 'CTR2024003', de: 1, para: 2, motivo: 'pd_ratio', data: '2024-12-08', pd_ratio: 4.2 },
    { contrato: 'CTR2024004', de: 2, para: 1, motivo: 'cura', data: '2024-12-05', meses_observacao: 6 },
    { contrato: 'CTR2024005', de: 1, para: 3, motivo: 'arrasto', data: '2024-12-01', contrato_origem: 'CTR2024002' },
]

// Simulador state inicial
const simuladorInicial = {
    dias_atraso: 0,
    pd_concessao: 0.02,
    pd_atual: 0.025,
    reestruturado: false,
    watch_list: false,
    outro_stage3: false,
}

// Distribuição atual
const distribuicaoStages = [
    { stage: 'Stage 1', quantidade: 12500, pct: 78.9, ecl: 450000 },
    { stage: 'Stage 2', quantidade: 2500, pct: 15.8, ecl: 780000 },
    { stage: 'Stage 3', quantidade: 847, pct: 5.3, ecl: 1200000 },
]

const COLORS = ['#22c55e', '#eab308', '#ef4444']

export default function EstagiosPage() {
    const [simulador, setSimulador] = useState(simuladorInicial)
    const [stageCalculado, setStageCalculado] = useState<number | null>(null)

    const calcularStage = () => {
        // Lógica de cálculo
        if (simulador.dias_atraso > 90 || simulador.reestruturado || simulador.outro_stage3) {
            setStageCalculado(3)
        } else if (
            simulador.dias_atraso > 30 ||
            simulador.watch_list ||
            (simulador.pd_atual / simulador.pd_concessao) > 3
        ) {
            setStageCalculado(2)
        } else {
            setStageCalculado(1)
        }
    }

    const getStageStyle = (stage: number) => {
        if (stage === 1) return 'bg-green-100 text-green-700 border-green-300'
        if (stage === 2) return 'bg-yellow-100 text-yellow-700 border-yellow-300'
        return 'bg-red-100 text-red-700 border-red-300'
    }

    return (
        <div className="space-y-6">
            {/* Info Card */}
            <Card className="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
                <CardContent className="pt-6">
                    <div className="flex gap-4">
                        <div className="flex-shrink-0">
                            <Badge variant="outline" className="h-8 w-8 rounded-full flex items-center justify-center border-blue-600 text-blue-600 font-bold">
                                1-3
                            </Badge>
                        </div>
                        <div>
                            <h3 className="font-semibold text-blue-900 dark:text-blue-100">Classificação de Estágios (Staging)</h3>
                            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                                O IFRS 9 exige a classificação das operações em 3 estágios de risco crescente:
                                <strong> Stage 1</strong> (Risco Normal - PD 12 meses),
                                <strong> Stage 2</strong> (Aumento Significativo de Risco - PD Lifetime) e
                                <strong> Stage 3</strong> (Inadimplente/Problemático - PD Lifetime).
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 font-medium">
                                📜 Conformidade: Art. 25 a 27 da Resolução CMN 4966/2021 - Caracterização de Ativos Problemáticos
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Tabs defaultValue="visao-geral" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="visao-geral">Visão Geral</TabsTrigger>
                    <TabsTrigger value="simulador">Simulador</TabsTrigger>
                    <TabsTrigger value="historico">Histórico</TabsTrigger>
                    <TabsTrigger value="regras">Regras</TabsTrigger>
                </TabsList>

                <TabsContent value="visao-geral" className="space-y-4">
                    {/* Distribuição Stages */}
                    <div className="grid gap-4 md:grid-cols-3">
                        {distribuicaoStages.map((s, i) => (
                            <Card key={s.stage} className={`border-2 ${i === 0 ? 'border-green-500/30' :
                                i === 1 ? 'border-yellow-500/30' : 'border-red-500/30'
                                }`}>
                                <CardHeader className="pb-2">
                                    <CardTitle className="flex items-center justify-between">
                                        <span>{s.stage}</span>
                                        <Badge className={getStageStyle(i + 1)}>{s.pct}%</Badge>
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-3xl font-bold">{s.quantidade.toLocaleString()}</p>
                                    <p className="text-sm text-muted-foreground">operações</p>
                                    <p className="text-lg font-semibold mt-2">
                                        R$ {(s.ecl / 1000).toFixed(0)}k ECL
                                    </p>
                                </CardContent>
                            </Card>
                        ))}
                    </div>

                    {/* Gráfico de barras */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Distribuição por Stage</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="h-[300px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={distribuicaoStages} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis type="number" />
                                        <YAxis dataKey="stage" type="category" width={80} />
                                        <Tooltip />
                                        <Bar dataKey="quantidade" radius={[0, 4, 4, 0]}>
                                            {distribuicaoStages.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index]} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="simulador" className="space-y-4">
                    <div className="grid gap-6 lg:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Simulador de Triggers</CardTitle>
                                <CardDescription>
                                    Simule a classificação de estágio IFRS 9
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Dias em Atraso</label>
                                    <input
                                        type="range"
                                        min="0"
                                        max="180"
                                        value={simulador.dias_atraso}
                                        onChange={(e) => setSimulador({ ...simulador, dias_atraso: parseInt(e.target.value) })}
                                        className="w-full"
                                    />
                                    <div className="flex justify-between text-xs text-muted-foreground">
                                        <span>0</span>
                                        <span className="font-bold text-foreground">{simulador.dias_atraso} dias</span>
                                        <span>180</span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium">PD Concessão</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={simulador.pd_concessao}
                                            onChange={(e) => setSimulador({ ...simulador, pd_concessao: parseFloat(e.target.value) })}
                                            className="w-full p-2 border rounded"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium">PD Atual</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={simulador.pd_atual}
                                            onChange={(e) => setSimulador({ ...simulador, pd_atual: parseFloat(e.target.value) })}
                                            className="w-full p-2 border rounded"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Flags</label>
                                    <div className="flex flex-wrap gap-2">
                                        <Button
                                            variant={simulador.reestruturado ? "default" : "outline"}
                                            size="sm"
                                            onClick={() => setSimulador({ ...simulador, reestruturado: !simulador.reestruturado })}
                                        >
                                            Reestruturado
                                        </Button>
                                        <Button
                                            variant={simulador.watch_list ? "default" : "outline"}
                                            size="sm"
                                            onClick={() => setSimulador({ ...simulador, watch_list: !simulador.watch_list })}
                                        >
                                            Watch List
                                        </Button>
                                        <Button
                                            variant={simulador.outro_stage3 ? "default" : "outline"}
                                            size="sm"
                                            onClick={() => setSimulador({ ...simulador, outro_stage3: !simulador.outro_stage3 })}
                                        >
                                            Outro Stage 3
                                        </Button>
                                    </div>
                                </div>

                                <Button onClick={calcularStage} className="w-full">
                                    Calcular Stage
                                </Button>
                            </CardContent>
                        </Card>

                        <Card className="flex flex-col">
                            <CardHeader>
                                <CardTitle>Resultado</CardTitle>
                            </CardHeader>
                            <CardContent className="flex-1 flex items-center justify-center">
                                {stageCalculado ? (
                                    <div className="text-center">
                                        <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full border-4 ${getStageStyle(stageCalculado)}`}>
                                            <span className="text-4xl font-bold">Stage {stageCalculado}</span>
                                        </div>
                                        <p className="mt-4 text-muted-foreground">
                                            {stageCalculado === 1 && 'Horizonte: 12 meses'}
                                            {stageCalculado === 2 && 'Horizonte: Lifetime'}
                                            {stageCalculado === 3 && 'Horizonte: Lifetime + Piso'}
                                        </p>
                                        <div className="mt-4 p-3 bg-muted rounded-lg text-sm">
                                            <p className="font-medium">Triggers acionados:</p>
                                            <ul className="mt-2 text-left space-y-1">
                                                {simulador.dias_atraso > 90 && <li>• Atraso &gt; 90 dias</li>}
                                                {simulador.dias_atraso > 30 && simulador.dias_atraso <= 90 && <li>• Atraso &gt; 30 dias</li>}
                                                {(simulador.pd_atual / simulador.pd_concessao) > 3 && <li>• PD Ratio &gt; 3x</li>}
                                                {simulador.reestruturado && <li>• Reestruturação</li>}
                                                {simulador.watch_list && <li>• Watch List</li>}
                                                {simulador.outro_stage3 && <li>• Arrasto Contraparte</li>}
                                            </ul>
                                        </div>
                                    </div>
                                ) : (
                                    <p className="text-muted-foreground">Configure os parâmetros e clique em Calcular</p>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="historico" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Histórico de Migrações</CardTitle>
                            <CardDescription>Últimas migrações de estágio</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="overflow-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-muted">
                                        <tr>
                                            <th className="p-3 text-left">Contrato</th>
                                            <th className="p-3 text-center">Migração</th>
                                            <th className="p-3 text-left">Motivo</th>
                                            <th className="p-3 text-left">Data</th>
                                            <th className="p-3 text-left">Detalhes</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {migracoes.map((m) => (
                                            <tr key={m.contrato} className="border-t hover:bg-muted/50">
                                                <td className="p-3 font-mono">{m.contrato}</td>
                                                <td className="p-3 text-center">
                                                    <div className="flex items-center justify-center gap-2">
                                                        <Badge className={getStageStyle(m.de)}>{m.de}</Badge>
                                                        <ArrowRight className="h-4 w-4" />
                                                        <Badge className={getStageStyle(m.para)}>{m.para}</Badge>
                                                    </div>
                                                </td>
                                                <td className="p-3">
                                                    {triggersConfig.find(t => t.id === m.motivo)?.nome || m.motivo}
                                                </td>
                                                <td className="p-3">{m.data}</td>
                                                <td className="p-3 text-muted-foreground text-xs">
                                                    {m.dias_atraso && `${m.dias_atraso} dias atraso`}
                                                    {m.pd_ratio && `PD Ratio: ${m.pd_ratio}x`}
                                                    {m.meses_observacao && `${m.meses_observacao} meses observação`}
                                                    {m.contrato_origem && `Via ${m.contrato_origem}`}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="regras" className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {triggersConfig.map((t) => (
                            <Card key={t.id} className={`border-l-4 ${t.stage_destino === 2 ? 'border-l-yellow-500' : 'border-l-red-500'
                                }`}>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-base flex items-center justify-between">
                                        {t.nome}
                                        <Badge className={getStageStyle(t.stage_destino)}>
                                            → Stage {t.stage_destino}
                                        </Badge>
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">{t.descricao}</p>
                                    <Badge variant="outline" className="mt-2">{t.tipo}</Badge>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    )
}
