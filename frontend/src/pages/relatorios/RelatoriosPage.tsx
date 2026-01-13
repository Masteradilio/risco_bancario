import { FileText, Download, Calendar, Filter } from 'lucide-react'

const relatorios = [
    { id: 1, nome: 'Relatório Mensal ECL', tipo: 'PDF', data: '2026-01-10', tamanho: '2.4 MB' },
    { id: 2, nome: 'Exportação BACEN Doc3040', tipo: 'XML', data: '2026-01-08', tamanho: '1.8 MB' },
    { id: 3, nome: 'Análise de Portfólio PRINAD', tipo: 'PDF', data: '2026-01-05', tamanho: '3.1 MB' },
    { id: 4, nome: 'Propensão Trimestral', tipo: 'XLSX', data: '2026-01-01', tamanho: '4.5 MB' },
]

export default function RelatoriosPage() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-4 py-2 bg-secondary rounded-lg hover:bg-accent transition-colors text-sm">
                        <Filter className="h-4 w-4" />
                        Filtrar
                    </button>
                    <button className="flex items-center gap-2 px-4 py-2 bg-secondary rounded-lg hover:bg-accent transition-colors text-sm">
                        <Calendar className="h-4 w-4" />
                        Período
                    </button>
                </div>
            </div>

            {/* Grid de Relatórios */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {relatorios.map((rel) => (
                    <div key={rel.id} className="kpi-card">
                        <div className="flex items-start justify-between mb-3">
                            <div className="p-2.5 rounded-xl bg-primary/10">
                                <FileText className="h-5 w-5 text-primary" />
                            </div>
                            <span className="text-xs px-2 py-1 bg-secondary rounded">
                                {rel.tipo}
                            </span>
                        </div>
                        <h4 className="font-medium mb-1">{rel.nome}</h4>
                        <p className="text-sm text-muted-foreground mb-3">
                            {new Date(rel.data).toLocaleDateString('pt-BR')} • {rel.tamanho}
                        </p>
                        <button className="flex items-center gap-2 text-primary text-sm hover:underline">
                            <Download className="h-4 w-4" />
                            Download
                        </button>
                    </div>
                ))}
            </div>

            {/* Gerar Novo Relatório */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Gerar Novo Relatório</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <button className="p-4 rounded-xl border border-border hover:border-primary transition-colors text-left">
                        <h4 className="font-medium">Laudo Técnico de Crédito</h4>
                        <p className="text-sm text-muted-foreground mt-1">PDF com análise individual</p>
                    </button>
                    <button className="p-4 rounded-xl border border-border hover:border-primary transition-colors text-left">
                        <h4 className="font-medium">Relatório ECL Consolidado</h4>
                        <p className="text-sm text-muted-foreground mt-1">Perda esperada do portfólio</p>
                    </button>
                    <button className="p-4 rounded-xl border border-border hover:border-primary transition-colors text-left">
                        <h4 className="font-medium">Exportação BACEN</h4>
                        <p className="text-sm text-muted-foreground mt-1">Doc3040 - CMN 4966</p>
                    </button>
                </div>
            </div>
        </div>
    )
}
