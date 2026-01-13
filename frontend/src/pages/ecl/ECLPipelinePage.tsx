import { Workflow, Play, CheckCircle, Clock, AlertCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

const etapas = [
    { id: 1, nome: 'Classificação PRINAD', descricao: 'Cálculo de PD por contrato', duracao: '~2min' },
    { id: 2, nome: 'Classificação de Estágios', descricao: 'IFRS 9 Stage 1, 2, 3', duracao: '~1min' },
    { id: 3, nome: 'Grupos Homogêneos', descricao: 'Segmentação por K-means', duracao: '~30s' },
    { id: 4, nome: 'Forward Looking', descricao: 'Aplicação de cenários macro', duracao: '~30s' },
    { id: 5, nome: 'Cálculo LGD/EAD', descricao: 'Parâmetros por produto', duracao: '~1min' },
    { id: 6, nome: 'Cálculo ECL Final', descricao: 'ECL = PD × LGD × EAD', duracao: '~2min' },
    { id: 7, nome: 'Validação', descricao: 'Regras CMN 4966', duracao: '~1min' },
]

export default function ECLPipelinePage() {
    const [executando, setExecutando] = useState(false)
    const [etapaAtual, setEtapaAtual] = useState(0)

    const executarPipeline = () => {
        setExecutando(true)
        setEtapaAtual(1)

        // Simular execução
        let etapa = 1
        const interval = setInterval(() => {
            etapa++
            if (etapa > etapas.length) {
                clearInterval(interval)
                setExecutando(false)
            } else {
                setEtapaAtual(etapa)
            }
        }, 1500)
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="chart-container">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="font-semibold">Pipeline ECL Completo</h3>
                        <p className="text-sm text-muted-foreground">Execução sequencial de todas as etapas de cálculo</p>
                    </div>
                    <button
                        onClick={executarPipeline}
                        disabled={executando}
                        className={cn(
                            "flex items-center gap-2 px-6 py-2 rounded-lg transition-opacity text-sm",
                            "bg-primary text-primary-foreground",
                            executando ? "opacity-50 cursor-not-allowed" : "hover:opacity-90"
                        )}
                    >
                        <Play className="h-4 w-4" />
                        {executando ? 'Executando...' : 'Iniciar Pipeline'}
                    </button>
                </div>
            </div>

            {/* Etapas */}
            <div className="space-y-3">
                {etapas.map((etapa, index) => {
                    const isCompleta = etapaAtual > etapa.id
                    const isAtual = etapaAtual === etapa.id
                    const isPendente = etapaAtual < etapa.id

                    return (
                        <div
                            key={etapa.id}
                            className={cn(
                                "chart-container flex items-center gap-4 transition-all",
                                isAtual && "ring-2 ring-primary",
                                isCompleta && "bg-emerald-500/5 border-emerald-500/20"
                            )}
                        >
                            <div className={cn(
                                "w-10 h-10 rounded-full flex items-center justify-center shrink-0",
                                isCompleta && "bg-emerald-500/20 text-emerald-500",
                                isAtual && "bg-primary/20 text-primary animate-pulse",
                                isPendente && "bg-muted text-muted-foreground"
                            )}>
                                {isCompleta ? (
                                    <CheckCircle className="h-5 w-5" />
                                ) : isAtual ? (
                                    <Clock className="h-5 w-5" />
                                ) : (
                                    <span className="font-medium">{etapa.id}</span>
                                )}
                            </div>
                            <div className="flex-1">
                                <p className="font-medium">{etapa.nome}</p>
                                <p className="text-sm text-muted-foreground">{etapa.descricao}</p>
                            </div>
                            <span className="text-xs text-muted-foreground">{etapa.duracao}</span>
                        </div>
                    )
                })}
            </div>

            {etapaAtual > etapas.length && (
                <div className="chart-container bg-emerald-500/10 border-emerald-500/20">
                    <div className="flex items-center gap-3 text-emerald-500">
                        <CheckCircle className="h-5 w-5" />
                        <div>
                            <p className="font-medium">Pipeline Concluído com Sucesso!</p>
                            <p className="text-sm opacity-80">Todos os cálculos foram executados. Você já pode gerar a exportação BACEN.</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
