"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { useSettings } from "@/stores/useSettings"
import { usePipelineStore } from "@/stores/usePipeline"
import { toast } from "sonner"
import Link from "next/link"
import {
    Zap, Play, Pause, CheckCircle2, XCircle, Loader2, Clock,
    Users, Layers, TrendingUp, Calculator, HeartPulse, BarChart3,
    ArrowRight, FileOutput
} from "lucide-react"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
} from "recharts"

// Etapas do pipeline
const etapasPipeline = [
    { id: 1, nome: "Carregar Dados", icone: Users, tempo_estimado: 5 },
    { id: 2, nome: "Classificar Estágios", icone: Layers, tempo_estimado: 10 },
    { id: 3, nome: "Calcular PD/LGD", icone: BarChart3, tempo_estimado: 15 },
    { id: 4, nome: "Aplicar Forward Looking", icone: TrendingUp, tempo_estimado: 8 },
    { id: 5, nome: "Calcular ECL", icone: Calculator, tempo_estimado: 12 },
    { id: 6, nome: "Verificar Cura", icone: HeartPulse, tempo_estimado: 5 },
    { id: 7, nome: "Consolidar Resultados", icone: Zap, tempo_estimado: 5 },
]

// Resultado mock
const resultadoMock = {
    totalOperacoes: 15847,
    eclTotal: 2430000,
    eclStage1: 450000,
    eclStage2: 780000,
    eclStage3: 1200000,
    distribuicaoStages: [
        { stage: "Stage 1", quantidade: 12500, ecl: 450000, cor: "#22c55e" },
        { stage: "Stage 2", quantidade: 2500, ecl: 780000, cor: "#eab308" },
        { stage: "Stage 3", quantidade: 847, ecl: 1200000, cor: "#ef4444" },
    ],
}

const formatCurrency = (v: number) => {
    if (v >= 1000000) return `R$ ${(v / 1000000).toFixed(2)}M`
    if (v >= 1000) return `R$ ${(v / 1000).toFixed(0)}k`
    return `R$ ${v.toFixed(0)}`
}

export default function PipelinePage() {
    const { eclApiUrl } = useSettings()
    const { resultado, setResultado } = usePipelineStore()
    const [executando, setExecutando] = useState(false)
    const [etapaAtual, setEtapaAtual] = useState(0)
    const [etapasCompletas, setEtapasCompletas] = useState<number[]>([])
    const [tempoDecorrido, setTempoDecorrido] = useState(0)
    const [pipelineConcluido, setPipelineConcluido] = useState(false)

    const executarPipeline = async () => {
        setExecutando(true)
        setEtapaAtual(0)
        setEtapasCompletas([])
        setTempoDecorrido(0)
        setPipelineConcluido(false)

        const startTime = Date.now()
        const interval = setInterval(() => {
            setTempoDecorrido(Math.floor((Date.now() - startTime) / 1000))
        }, 1000)

        for (let i = 0; i < etapasPipeline.length; i++) {
            setEtapaAtual(i + 1)
            // Simular tempo de processamento
            await new Promise(r => setTimeout(r, etapasPipeline[i].tempo_estimado * 100))
            setEtapasCompletas(prev => [...prev, i + 1])
        }

        clearInterval(interval)
        const tempoFinal = Math.floor((Date.now() - startTime) / 1000)
        setTempoDecorrido(tempoFinal)

        // Salvar resultado no store global
        setResultado({
            executado: true,
            dataExecucao: new Date().toISOString(),
            totalOperacoes: resultadoMock.totalOperacoes,
            eclTotal: resultadoMock.eclTotal,
            eclStage1: resultadoMock.eclStage1,
            eclStage2: resultadoMock.eclStage2,
            eclStage3: resultadoMock.eclStage3,
            tempoExecucao: tempoFinal,
            distribuicaoStages: resultadoMock.distribuicaoStages,
        })

        setPipelineConcluido(true)
        setExecutando(false)
        toast.success("Pipeline ECL executado com sucesso!")
    }

    const progressoGeral = (etapasCompletas.length / etapasPipeline.length) * 100

    return (
        <div className="space-y-6">
            {/* Header */}
            <Card className="bg-gradient-to-br from-purple-500/10 to-blue-500/10">
                <CardContent className="pt-6">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                <Zap className="h-6 w-6 text-purple-600" />
                                Pipeline ECL Completo
                            </h2>
                            <p className="text-muted-foreground">
                                Execução full do cálculo de Perda Esperada para todo o banco
                            </p>
                        </div>
                        <Button
                            size="lg"
                            onClick={executarPipeline}
                            disabled={executando}
                            className="gap-2"
                        >
                            {executando ? (
                                <><Loader2 className="h-5 w-5 animate-spin" /> Executando...</>
                            ) : (
                                <><Play className="h-5 w-5" /> Executar Pipeline</>
                            )}
                        </Button>
                    </div>
                    {executando && (
                        <div className="mt-4">
                            <div className="flex justify-between text-sm mb-1">
                                <span>Progresso</span>
                                <span>{progressoGeral.toFixed(0)}%</span>
                            </div>
                            <Progress value={progressoGeral} className="h-3" />
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Aviso de sucesso */}
            {pipelineConcluido && (
                <Card className="bg-green-50 dark:bg-green-950/30 border-green-500/50">
                    <CardContent className="pt-6">
                        <div className="flex items-start gap-4">
                            <CheckCircle2 className="h-8 w-8 text-green-600 flex-shrink-0" />
                            <div className="flex-1">
                                <h3 className="text-lg font-semibold text-green-700 dark:text-green-400">
                                    Pipeline de Perda Esperada realizado com sucesso!
                                </h3>
                                <p className="text-green-600 dark:text-green-500 mt-1">
                                    Sistema pronto para gerar o XML ECL para envio ao BACEN (na próxima aba).
                                </p>
                                <Link href="/perda-esperada/exportacao">
                                    <Button className="mt-4 gap-2" variant="outline">
                                        <FileOutput className="h-4 w-4" />
                                        Ir para Exportação BACEN
                                        <ArrowRight className="h-4 w-4" />
                                    </Button>
                                </Link>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Etapas */}
            <Card>
                <CardHeader>
                    <CardTitle>Etapas do Pipeline</CardTitle>
                    <CardDescription>
                        {executando
                            ? `Executando etapa ${etapaAtual} de ${etapasPipeline.length}...`
                            : resultado.executado
                                ? `Último pipeline executado em ${new Date(resultado.dataExecucao!).toLocaleString('pt-BR')}`
                                : "Clique em Executar para iniciar"
                        }
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                        {etapasPipeline.map((etapa) => {
                            const Icon = etapa.icone
                            const isCompleta = etapasCompletas.includes(etapa.id)
                            const isAtual = etapaAtual === etapa.id && executando

                            return (
                                <div
                                    key={etapa.id}
                                    className={`p-4 border rounded-lg transition-all ${isCompleta
                                            ? 'border-green-500 bg-green-50 dark:bg-green-950/30'
                                            : isAtual
                                                ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/30'
                                                : 'border-muted'
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-full ${isCompleta ? 'bg-green-500 text-white' :
                                                isAtual ? 'bg-blue-500 text-white animate-pulse' :
                                                    'bg-muted'
                                            }`}>
                                            {isCompleta ? (
                                                <CheckCircle2 className="h-5 w-5" />
                                            ) : isAtual ? (
                                                <Loader2 className="h-5 w-5 animate-spin" />
                                            ) : (
                                                <Icon className="h-5 w-5" />
                                            )}
                                        </div>
                                        <div>
                                            <p className="font-medium text-sm">{etapa.id}. {etapa.nome}</p>
                                            <p className="text-xs text-muted-foreground">
                                                ~{etapa.tempo_estimado}s estimado
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </CardContent>
            </Card>

            {/* Resultado */}
            {(pipelineConcluido || resultado.executado) && (
                <>
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm text-muted-foreground">ECL Total</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-3xl font-bold text-blue-600">
                                    {formatCurrency(resultado.eclTotal)}
                                </p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm text-muted-foreground">Operações</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-3xl font-bold">{resultado.totalOperacoes.toLocaleString()}</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm text-muted-foreground">Tempo Execução</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-3xl font-bold">{resultado.tempoExecucao}s</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm text-muted-foreground">Cobertura</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-3xl font-bold">1.56%</p>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid gap-6 md:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Distribuição por Stage</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[250px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={resultado.distribuicaoStages}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="stage" />
                                            <YAxis tickFormatter={(v) => formatCurrency(v)} />
                                            <Tooltip formatter={(v: number) => formatCurrency(v)} />
                                            <Bar dataKey="ecl" radius={[4, 4, 0, 0]}>
                                                {resultado.distribuicaoStages.map((entry, i) => (
                                                    <Cell key={i} fill={entry.cor} />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Resumo por Stage</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {resultado.distribuicaoStages.map((s) => (
                                        <div key={s.stage} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                                            <div className="flex items-center gap-3">
                                                <div
                                                    className="w-4 h-4 rounded-full"
                                                    style={{ backgroundColor: s.cor }}
                                                />
                                                <div>
                                                    <p className="font-medium">{s.stage}</p>
                                                    <p className="text-xs text-muted-foreground">
                                                        {s.quantidade.toLocaleString()} operações
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-bold">{formatCurrency(s.ecl)}</p>
                                                <p className="text-xs text-muted-foreground">
                                                    {((s.ecl / resultado.eclTotal) * 100).toFixed(1)}%
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </>
            )}
        </div>
    )
}
