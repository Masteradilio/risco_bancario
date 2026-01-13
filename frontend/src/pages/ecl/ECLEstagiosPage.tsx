import { Layers, ArrowRight, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

const stages = [
    { stage: 1, nome: 'Stage 1', descricao: 'Risco não aumentou significativamente', horizonte: '12 meses', cor: 'bg-emerald-500' },
    { stage: 2, nome: 'Stage 2', descricao: 'Aumento significativo do risco (SICR)', horizonte: 'Lifetime', cor: 'bg-amber-500' },
    { stage: 3, nome: 'Stage 3', descricao: 'Ativo com problema de recuperação', horizonte: 'Lifetime + LGD máx', cor: 'bg-red-500' },
]

export default function ECLEstagiosPage() {
    return (
        <div className="space-y-6">
            {/* Estágios Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {stages.map((s, i) => (
                    <div key={s.stage} className="kpi-card relative overflow-hidden">
                        <div className={cn('absolute top-0 left-0 w-1 h-full', s.cor)} />
                        <div className="pl-3">
                            <p className="text-sm text-muted-foreground">{s.nome}</p>
                            <p className="text-lg font-semibold mt-1">{s.descricao}</p>
                            <p className="text-sm text-muted-foreground mt-2">Horizonte: {s.horizonte}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Triggers */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Triggers de Migração de Estágio</h3>
                <div className="space-y-3">
                    <div className="flex items-center gap-4 p-3 rounded-lg bg-secondary/50">
                        <span className="text-emerald-500 font-medium">Stage 1 → 2</span>
                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">Atraso {'>'} 30 dias OU PD aumentou {'>'} 100%</span>
                    </div>
                    <div className="flex items-center gap-4 p-3 rounded-lg bg-secondary/50">
                        <span className="text-amber-500 font-medium">Stage 2 → 3</span>
                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">Atraso {'>'} 90 dias OU reestruturação OU classificação D-H</span>
                    </div>
                </div>
            </div>

            <div className="chart-container bg-amber-500/5 border-amber-500/20">
                <div className="flex items-start gap-3">
                    <Info className="h-5 w-5 text-amber-500 mt-0.5" />
                    <div>
                        <h4 className="font-medium text-amber-500">Regra de Arrasto (§4º Art. 51)</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                            Quando um produto de um cliente migra para Stage 3, todos os outros produtos do mesmo cliente devem ser reclassificados para Stage 3.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
