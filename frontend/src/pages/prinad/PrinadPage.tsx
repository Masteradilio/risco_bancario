import { useState } from 'react'
import { Target, ArrowUpRight, Upload, FileSpreadsheet, Download } from 'lucide-react'
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    Radar,
} from 'recharts'
import { cn } from '@/lib/utils'

// Tabs simples para navegação interna
type TabId = 'dashboard' | 'individual' | 'lote'

const ratingData = [
    { rating: 'A1', count: 3250, percentage: 22 },
    { rating: 'A2', count: 2890, percentage: 19 },
    { rating: 'A3', count: 2100, percentage: 14 },
    { rating: 'B1', count: 1750, percentage: 12 },
    { rating: 'B2', count: 1420, percentage: 10 },
    { rating: 'B3', count: 1100, percentage: 7 },
    { rating: 'C1', count: 850, percentage: 6 },
    { rating: 'C2', count: 620, percentage: 4 },
    { rating: 'C3', count: 380, percentage: 3 },
    { rating: 'D', count: 210, percentage: 2 },
    { rating: 'DEFAULT', count: 150, percentage: 1 },
]

const featureImportance = [
    { feature: 'Dias Atraso', value: 95 },
    { feature: 'Histórico SCR', value: 88 },
    { feature: 'Util. Crédito', value: 75 },
    { feature: 'Tempo Conta', value: 62 },
    { feature: 'Renda', value: 58 },
    { feature: 'Nº Operações', value: 45 },
]

export default function PrinadPage() {
    const [activeTab, setActiveTab] = useState<TabId>('dashboard')
    const [cpf, setCpf] = useState('')
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState<any>(null)
    const [batchFile, setBatchFile] = useState<File | null>(null)
    const [batchResults, setBatchResults] = useState<any[]>([])

    const handleClassify = async () => {
        if (!cpf) return
        setLoading(true)
        // Simulação de classificação
        await new Promise(r => setTimeout(r, 800))
        setResult({
            cpf,
            prinad: Math.random() * 100,
            rating: ['A1', 'A2', 'B1', 'B2', 'C1'][Math.floor(Math.random() * 5)],
            estagio_pe: Math.floor(Math.random() * 3) + 1,
            pd_12m: Math.random() * 0.1,
        })
        setLoading(false)
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) setBatchFile(file)
    }

    const getRatingColor = (rating: string) => {
        if (rating?.startsWith('A')) return 'text-emerald-500'
        if (rating?.startsWith('B')) return 'text-amber-500'
        if (rating?.startsWith('C')) return 'text-orange-500'
        return 'text-red-500'
    }

    return (
        <div className="space-y-6">
            {/* Tabs de Navegação - MAIORES E MAIS CHAMATIVAS */}
            <nav className="flex gap-3 p-2 bg-gradient-to-r from-muted/80 to-muted/40 rounded-xl border border-border">
                <button
                    onClick={() => setActiveTab('dashboard')}
                    className={cn(
                        'px-6 py-3.5 text-base rounded-xl transition-all duration-200 font-semibold',
                        activeTab === 'dashboard'
                            ? 'bg-primary text-primary-foreground shadow-lg scale-105 border-2 border-primary'
                            : 'bg-background/80 text-muted-foreground hover:text-foreground hover:bg-background border border-border hover:border-primary/50'
                    )}
                >
                    📊 Dashboard
                </button>
                <button
                    onClick={() => setActiveTab('individual')}
                    className={cn(
                        'px-6 py-3.5 text-base rounded-xl transition-all duration-200 font-semibold',
                        activeTab === 'individual'
                            ? 'bg-primary text-primary-foreground shadow-lg scale-105 border-2 border-primary'
                            : 'bg-background/80 text-muted-foreground hover:text-foreground hover:bg-background border border-border hover:border-primary/50'
                    )}
                >
                    👤 Classificação Individual
                </button>
                <button
                    onClick={() => setActiveTab('lote')}
                    className={cn(
                        'px-6 py-3.5 text-base rounded-xl transition-all duration-200 font-semibold',
                        activeTab === 'lote'
                            ? 'bg-primary text-primary-foreground shadow-lg scale-105 border-2 border-primary'
                            : 'bg-background/80 text-muted-foreground hover:text-foreground hover:bg-background border border-border hover:border-primary/50'
                    )}
                >
                    📁 Classificação em Lote
                </button>
            </nav>

            {/* Conteúdo da Tab Dashboard */}
            {activeTab === 'dashboard' && (
                <div className="space-y-6 animate-fade-in">
                    {/* KPIs */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="kpi-card">
                            <p className="text-sm text-muted-foreground">Classificações Hoje</p>
                            <p className="text-2xl font-bold mt-1">2.847</p>
                            <div className="flex items-center gap-1 text-xs text-emerald-500 mt-2">
                                <ArrowUpRight className="h-3 w-3" />
                                <span>+15% vs ontem</span>
                            </div>
                        </div>
                        <div className="kpi-card">
                            <p className="text-sm text-muted-foreground">Score Médio</p>
                            <p className="text-2xl font-bold mt-1">34.2%</p>
                            <p className="text-xs text-muted-foreground mt-2">PD médio do portfólio</p>
                        </div>
                        <div className="kpi-card">
                            <p className="text-sm text-muted-foreground">Precisão do Modelo</p>
                            <p className="text-2xl font-bold text-emerald-500 mt-1">95.4%</p>
                            <p className="text-xs text-muted-foreground mt-2">Últimos 30 dias</p>
                        </div>
                        <div className="kpi-card">
                            <p className="text-sm text-muted-foreground">AUC-ROC</p>
                            <p className="text-2xl font-bold text-primary mt-1">0.9986</p>
                            <p className="text-xs text-muted-foreground mt-2">Excelente performance</p>
                        </div>
                    </div>

                    {/* Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="chart-container">
                            <div className="flex items-center justify-between mb-4">
                                <div>
                                    <h3 className="font-semibold">Distribuição por Rating</h3>
                                    <p className="text-sm text-muted-foreground">Classificação BACEN 4966</p>
                                </div>
                            </div>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={ratingData} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                    <XAxis type="number" stroke="var(--muted-foreground)" fontSize={12} />
                                    <YAxis dataKey="rating" type="category" stroke="var(--muted-foreground)" fontSize={12} width={60} />
                                    <Tooltip contentStyle={{ backgroundColor: 'var(--popover)', borderColor: 'var(--border)', borderRadius: '8px' }} />
                                    <Bar dataKey="count" fill="var(--primary)" radius={[0, 4, 4, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="chart-container">
                            <div className="flex items-center justify-between mb-4">
                                <div>
                                    <h3 className="font-semibold">Importância das Features</h3>
                                    <p className="text-sm text-muted-foreground">SHAP values do modelo</p>
                                </div>
                            </div>
                            <ResponsiveContainer width="100%" height={300}>
                                <RadarChart data={featureImportance}>
                                    <PolarGrid stroke="var(--border)" />
                                    <PolarAngleAxis dataKey="feature" stroke="var(--muted-foreground)" fontSize={11} />
                                    <Radar name="Importância" dataKey="value" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.3} />
                                    <Tooltip contentStyle={{ backgroundColor: 'var(--popover)', borderColor: 'var(--border)', borderRadius: '8px' }} />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Escala de Rating */}
                    <div className="chart-container">
                        <h3 className="font-semibold mb-4">Escala de Rating PRINAD</h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th className="text-left py-3 px-4">Rating</th>
                                        <th className="text-left py-3 px-4">Faixa PRINAD</th>
                                        <th className="text-left py-3 px-4">Descrição</th>
                                        <th className="text-left py-3 px-4">Ação Recomendada</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr className="border-b border-border hover:bg-muted/50">
                                        <td className="py-3 px-4 font-medium text-emerald-500">A1</td>
                                        <td className="py-3 px-4">0-4.99%</td>
                                        <td className="py-3 px-4">Risco Mínimo</td>
                                        <td className="py-3 px-4">Aprovação automática</td>
                                    </tr>
                                    <tr className="border-b border-border hover:bg-muted/50">
                                        <td className="py-3 px-4 font-medium text-emerald-500">A2</td>
                                        <td className="py-3 px-4">5-14.99%</td>
                                        <td className="py-3 px-4">Risco Muito Baixo</td>
                                        <td className="py-3 px-4">Aprovação automática</td>
                                    </tr>
                                    <tr className="border-b border-border hover:bg-muted/50">
                                        <td className="py-3 px-4 font-medium text-amber-500">B1</td>
                                        <td className="py-3 px-4">25-34.99%</td>
                                        <td className="py-3 px-4">Risco Baixo-Moderado</td>
                                        <td className="py-3 px-4">Análise padrão</td>
                                    </tr>
                                    <tr className="border-b border-border hover:bg-muted/50">
                                        <td className="py-3 px-4 font-medium text-orange-500">C1</td>
                                        <td className="py-3 px-4">55-64.99%</td>
                                        <td className="py-3 px-4">Risco Alto</td>
                                        <td className="py-3 px-4">Exige garantias</td>
                                    </tr>
                                    <tr className="hover:bg-muted/50">
                                        <td className="py-3 px-4 font-medium text-red-800">DEFAULT</td>
                                        <td className="py-3 px-4">95-100%</td>
                                        <td className="py-3 px-4">Default</td>
                                        <td className="py-3 px-4">Negação, cobrança</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {/* Conteúdo da Tab Classificação Individual */}
            {activeTab === 'individual' && (
                <div className="space-y-4 animate-fade-in">
                    <div className="chart-container">
                        <h3 className="font-semibold mb-4">Classificar Cliente</h3>
                        <p className="text-sm text-muted-foreground mb-4">Digite o CPF para obter a classificação de risco</p>

                        <div className="flex gap-4">
                            <div className="flex-1">
                                <label className="text-sm text-muted-foreground">CPF</label>
                                <input
                                    type="text"
                                    placeholder="00000000000"
                                    value={cpf}
                                    onChange={(e) => setCpf(e.target.value.replace(/\D/g, ""))}
                                    maxLength={11}
                                    className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border focus:ring-2 focus:ring-primary"
                                />
                            </div>
                            <div className="flex items-end">
                                <button
                                    onClick={handleClassify}
                                    disabled={loading}
                                    className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50"
                                >
                                    {loading ? 'Classificando...' : 'Classificar'}
                                </button>
                            </div>
                        </div>

                        {result && (
                            <div className="grid gap-4 md:grid-cols-4 mt-6">
                                <div className="kpi-card">
                                    <p className="text-sm text-muted-foreground">PRINAD Score</p>
                                    <p className="text-2xl font-bold">{result.prinad?.toFixed(2)}%</p>
                                </div>
                                <div className="kpi-card">
                                    <p className="text-sm text-muted-foreground">Rating</p>
                                    <p className={`text-2xl font-bold ${getRatingColor(result.rating)}`}>{result.rating}</p>
                                </div>
                                <div className="kpi-card">
                                    <p className="text-sm text-muted-foreground">Stage IFRS 9</p>
                                    <p className="text-2xl font-bold">{result.estagio_pe}</p>
                                </div>
                                <div className="kpi-card">
                                    <p className="text-sm text-muted-foreground">PD 12 meses</p>
                                    <p className="text-2xl font-bold">{(result.pd_12m * 100)?.toFixed(2)}%</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Conteúdo da Tab Classificação em Lote */}
            {activeTab === 'lote' && (
                <div className="space-y-4 animate-fade-in">
                    <div className="chart-container">
                        <div className="flex items-center gap-2 mb-4">
                            <FileSpreadsheet className="h-5 w-5" />
                            <h3 className="font-semibold">Classificação em Lote</h3>
                        </div>
                        <p className="text-sm text-muted-foreground mb-4">Faça upload de um arquivo CSV com a coluna CPF</p>

                        <div className="border-2 border-dashed rounded-lg p-8 text-center">
                            <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <label htmlFor="file-upload" className="cursor-pointer">
                                <span className="text-primary font-medium">Clique para selecionar</span>
                                <span className="text-muted-foreground"> ou arraste um arquivo CSV</span>
                            </label>
                            <input
                                id="file-upload"
                                type="file"
                                accept=".csv"
                                className="hidden"
                                onChange={handleFileChange}
                            />
                            {batchFile && (
                                <p className="text-sm text-muted-foreground mt-2">
                                    Arquivo: {batchFile.name}
                                </p>
                            )}
                        </div>

                        <button
                            disabled={!batchFile}
                            className="w-full mt-4 px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50"
                        >
                            Processar Arquivo
                        </button>

                        {batchResults.length > 0 && (
                            <div className="mt-4 flex items-center justify-between">
                                <p className="text-sm text-muted-foreground">{batchResults.length} registros processados</p>
                                <button className="flex items-center gap-2 px-4 py-2 bg-secondary rounded-lg hover:bg-accent">
                                    <Download className="h-4 w-4" />
                                    Download CSV
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
