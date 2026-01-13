import { useState } from 'react'
import { TrendingUp, DollarSign, Users, Target } from 'lucide-react'
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
} from 'recharts'
import { cn } from '@/lib/utils'

type TabId = 'dashboard' | 'recomendar' | 'score' | 'simular'

const propensaoData = [
    { mes: 'Jan', consignado: 78, cartao: 65, imobiliario: 45 },
    { mes: 'Fev', consignado: 82, cartao: 68, imobiliario: 48 },
    { mes: 'Mar', consignado: 79, cartao: 72, imobiliario: 52 },
    { mes: 'Abr', consignado: 85, cartao: 70, imobiliario: 55 },
    { mes: 'Mai', consignado: 88, cartao: 75, imobiliario: 58 },
    { mes: 'Jun', consignado: 92, cartao: 78, imobiliario: 60 },
]

const acaoDistribuicao = [
    { acao: 'MANTER', valor: 5600, color: '#3b82f6' },
    { acao: 'AUMENTAR', valor: 1120, color: '#4ade80' },
    { acao: 'REDUZIR', valor: 1120, color: '#f97316' },
    { acao: 'ZERAR', valor: 160, color: '#ef4444' },
]

export default function PropensaoPage() {
    const [activeTab, setActiveTab] = useState<TabId>('dashboard')
    const [loading, setLoading] = useState(false)

    // Estados form recomendar
    const [formData, setFormData] = useState({
        cpf: '', produto: 'consignado', prinad: '', propensity_score: '', limite_atual: '', saldo_utilizado: ''
    })
    const [result, setResult] = useState<any>(null)

    // Estados form score
    const [scoreFormData, setScoreFormData] = useState({
        cpf: '', produto: 'consignado', prinad: '', renda: '', utilizacao: '', tempo_relacionamento: ''
    })
    const [scoreResult, setScoreResult] = useState<any>(null)

    // Estados simulação
    const [cenario, setCenario] = useState('moderado')
    const [simulacaoResult, setSimulacaoResult] = useState<any>(null)

    const handleRecomendar = async () => {
        if (!formData.cpf || !formData.prinad || !formData.limite_atual) return
        setLoading(true)
        await new Promise(r => setTimeout(r, 800))
        setResult({
            acao: ['MANTER', 'AUMENTAR', 'REDUZIR'][Math.floor(Math.random() * 3)],
            justificativa: 'Cliente com bom histórico e baixo risco',
            percentual_ajuste: Math.random() * 0.3 - 0.1,
            novo_limite: parseFloat(formData.limite_atual) * (1 + Math.random() * 0.2),
            economia_ecl: Math.random() * 1000,
        })
        setLoading(false)
    }

    const handleCalcularScore = async () => {
        if (!scoreFormData.cpf || !scoreFormData.prinad || !scoreFormData.renda) return
        setLoading(true)
        await new Promise(r => setTimeout(r, 800))
        setScoreResult({
            propensity_score: Math.random(),
            classificacao: ['ALTA', 'MEDIA', 'BAIXA'][Math.floor(Math.random() * 3)],
            recomendacao: 'Cliente apto para oferta de crédito consignado',
        })
        setLoading(false)
    }

    const handleSimular = async () => {
        setLoading(true)
        await new Promise(r => setTimeout(r, 800))
        setSimulacaoResult({
            economia_ecl: Math.random() * 50000,
            receita_adicional: Math.random() * 30000,
            impacto_liquido: Math.random() * 70000,
        })
        setLoading(false)
    }

    const getActionColor = (acao: string) => {
        switch (acao) {
            case 'AUMENTAR': return 'text-emerald-500'
            case 'MANTER': return 'text-blue-500'
            case 'REDUZIR': return 'text-orange-500'
            case 'ZERAR': return 'text-red-500'
            default: return ''
        }
    }

    const getClassificacaoColor = (classificacao: string) => {
        switch (classificacao) {
            case 'ALTA': return 'text-emerald-500'
            case 'MEDIA': return 'text-amber-500'
            case 'BAIXA': return 'text-red-500'
            default: return ''
        }
    }

    return (
        <div className="space-y-6">
            {/* Tabs de Navegação - MAIORES E MAIS CHAMATIVAS */}
            <nav className="flex gap-3 p-2 bg-gradient-to-r from-muted/80 to-muted/40 rounded-xl border border-border flex-wrap">
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
                    onClick={() => setActiveTab('recomendar')}
                    className={cn(
                        'px-6 py-3.5 text-base rounded-xl transition-all duration-200 font-semibold',
                        activeTab === 'recomendar'
                            ? 'bg-primary text-primary-foreground shadow-lg scale-105 border-2 border-primary'
                            : 'bg-background/80 text-muted-foreground hover:text-foreground hover:bg-background border border-border hover:border-primary/50'
                    )}
                >
                    💰 Recomendar Limite
                </button>
                <button
                    onClick={() => setActiveTab('score')}
                    className={cn(
                        'px-6 py-3.5 text-base rounded-xl transition-all duration-200 font-semibold',
                        activeTab === 'score'
                            ? 'bg-primary text-primary-foreground shadow-lg scale-105 border-2 border-primary'
                            : 'bg-background/80 text-muted-foreground hover:text-foreground hover:bg-background border border-border hover:border-primary/50'
                    )}
                >
                    📈 Score de Propensão
                </button>
                <button
                    onClick={() => setActiveTab('simular')}
                    className={cn(
                        'px-6 py-3.5 text-base rounded-xl transition-all duration-200 font-semibold',
                        activeTab === 'simular'
                            ? 'bg-primary text-primary-foreground shadow-lg scale-105 border-2 border-primary'
                            : 'bg-background/80 text-muted-foreground hover:text-foreground hover:bg-background border border-border hover:border-primary/50'
                    )}
                >
                    🎯 Simulador de Impacto
                </button>
            </nav>

            {/* Dashboard */}
            {activeTab === 'dashboard' && (
                <div className="space-y-6 animate-fade-in">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="kpi-card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Propensão Média</p>
                                    <p className="text-2xl font-bold mt-1">72.4%</p>
                                </div>
                                <div className="p-2.5 rounded-xl bg-primary/10">
                                    <TrendingUp className="h-5 w-5 text-primary" />
                                </div>
                            </div>
                        </div>
                        <div className="kpi-card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Limites Otimizados</p>
                                    <p className="text-2xl font-bold mt-1">R$ 4.2M</p>
                                </div>
                                <div className="p-2.5 rounded-xl bg-emerald-500/10">
                                    <DollarSign className="h-5 w-5 text-emerald-500" />
                                </div>
                            </div>
                        </div>
                        <div className="kpi-card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Clientes Impactados</p>
                                    <p className="text-2xl font-bold mt-1">1.247</p>
                                </div>
                                <div className="p-2.5 rounded-xl bg-amber-500/10">
                                    <Users className="h-5 w-5 text-amber-500" />
                                </div>
                            </div>
                        </div>
                        <div className="kpi-card">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Taxa de Conversão</p>
                                    <p className="text-2xl font-bold mt-1">34.8%</p>
                                </div>
                                <div className="p-2.5 rounded-xl bg-primary/10">
                                    <Target className="h-5 w-5 text-primary" />
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="chart-container">
                            <h3 className="font-semibold mb-4">Evolução da Propensão por Produto</h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={propensaoData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                    <XAxis dataKey="mes" stroke="var(--muted-foreground)" fontSize={12} />
                                    <YAxis stroke="var(--muted-foreground)" fontSize={12} />
                                    <Tooltip contentStyle={{ backgroundColor: 'var(--popover)', borderColor: 'var(--border)', borderRadius: '8px' }} />
                                    <Line type="monotone" dataKey="consignado" stroke="#4ade80" strokeWidth={2} name="Consignado" />
                                    <Line type="monotone" dataKey="cartao" stroke="#f97316" strokeWidth={2} name="Cartão" />
                                    <Line type="monotone" dataKey="imobiliario" stroke="#3b82f6" strokeWidth={2} name="Imobiliário" />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="chart-container">
                            <h3 className="font-semibold mb-4">Distribuição de Ações Recomendadas</h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                    <Pie data={acaoDistribuicao} dataKey="valor" nameKey="acao" innerRadius={60} outerRadius={100}>
                                        {acaoDistribuicao.map((entry, i) => (
                                            <Cell key={i} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ backgroundColor: 'var(--popover)', borderColor: 'var(--border)', borderRadius: '8px' }} />
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="flex justify-center gap-4 mt-2">
                                {acaoDistribuicao.map((item) => (
                                    <div key={item.acao} className="flex items-center gap-1.5 text-xs">
                                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                                        {item.acao}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Recomendar Limite */}
            {activeTab === 'recomendar' && (
                <div className="space-y-4 animate-fade-in">
                    <div className="grid gap-6 md:grid-cols-2">
                        <div className="chart-container">
                            <h3 className="font-semibold mb-4">Gerar Recomendação</h3>
                            <p className="text-sm text-muted-foreground mb-4">Informe os dados do cliente para obter a recomendação de limite</p>

                            <div className="grid gap-4 grid-cols-2">
                                <div>
                                    <label className="text-sm text-muted-foreground">CPF</label>
                                    <input
                                        type="text"
                                        placeholder="00000000000"
                                        value={formData.cpf}
                                        onChange={(e) => setFormData({ ...formData, cpf: e.target.value.replace(/\D/g, '') })}
                                        maxLength={11}
                                        className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">Produto</label>
                                    <select
                                        value={formData.produto}
                                        onChange={(e) => setFormData({ ...formData, produto: e.target.value })}
                                        className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border"
                                    >
                                        <option value="consignado">Consignado</option>
                                        <option value="cartao">Cartão de Crédito</option>
                                        <option value="imobiliario">Imobiliário</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">PRINAD Score (%)</label>
                                    <input
                                        type="number"
                                        placeholder="0-100"
                                        value={formData.prinad}
                                        onChange={(e) => setFormData({ ...formData, prinad: e.target.value })}
                                        className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">Limite Atual (R$)</label>
                                    <input
                                        type="number"
                                        placeholder="0.00"
                                        value={formData.limite_atual}
                                        onChange={(e) => setFormData({ ...formData, limite_atual: e.target.value })}
                                        className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border"
                                    />
                                </div>
                            </div>
                            <button
                                onClick={handleRecomendar}
                                disabled={loading}
                                className="w-full mt-4 px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50"
                            >
                                {loading ? 'Gerando...' : 'Gerar Recomendação'}
                            </button>
                        </div>

                        {result && (
                            <div className="chart-container">
                                <h3 className="font-semibold mb-4">Recomendação</h3>
                                <div className="text-center mb-6">
                                    <p className={`text-4xl font-bold ${getActionColor(result.acao)}`}>{result.acao}</p>
                                    <p className="text-muted-foreground mt-2">{result.justificativa}</p>
                                </div>
                                <div className="grid gap-4 grid-cols-2">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Ajuste</p>
                                        <p className="text-xl font-bold">{(result.percentual_ajuste * 100)?.toFixed(0)}%</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Novo Limite</p>
                                        <p className="text-xl font-bold">R$ {result.novo_limite?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                                    </div>
                                    <div className="col-span-2">
                                        <p className="text-sm text-muted-foreground">Economia ECL</p>
                                        <p className="text-xl font-bold text-emerald-500">R$ {result.economia_ecl?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Score de Propensão */}
            {activeTab === 'score' && (
                <div className="space-y-4 animate-fade-in">
                    <div className="grid gap-6 md:grid-cols-2">
                        <div className="chart-container">
                            <h3 className="font-semibold mb-4">Calcular Score de Propensão</h3>
                            <p className="text-sm text-muted-foreground mb-4">Avalie a propensão do cliente para um produto</p>

                            <div className="grid gap-4 grid-cols-2">
                                <div>
                                    <label className="text-sm text-muted-foreground">CPF</label>
                                    <input
                                        type="text"
                                        placeholder="00000000000"
                                        value={scoreFormData.cpf}
                                        onChange={(e) => setScoreFormData({ ...scoreFormData, cpf: e.target.value.replace(/\D/g, '') })}
                                        maxLength={11}
                                        className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">PRINAD Score (%)</label>
                                    <input
                                        type="number"
                                        placeholder="0-100"
                                        value={scoreFormData.prinad}
                                        onChange={(e) => setScoreFormData({ ...scoreFormData, prinad: e.target.value })}
                                        className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">Renda Mensal (R$)</label>
                                    <input
                                        type="number"
                                        placeholder="0.00"
                                        value={scoreFormData.renda}
                                        onChange={(e) => setScoreFormData({ ...scoreFormData, renda: e.target.value })}
                                        className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">Tempo Relacionamento (meses)</label>
                                    <input
                                        type="number"
                                        placeholder="24"
                                        value={scoreFormData.tempo_relacionamento}
                                        onChange={(e) => setScoreFormData({ ...scoreFormData, tempo_relacionamento: e.target.value })}
                                        className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border"
                                    />
                                </div>
                            </div>
                            <button
                                onClick={handleCalcularScore}
                                disabled={loading}
                                className="w-full mt-4 px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50"
                            >
                                {loading ? 'Calculando...' : 'Calcular Score'}
                            </button>
                        </div>

                        {scoreResult && (
                            <div className="chart-container">
                                <h3 className="font-semibold mb-4">Resultado</h3>
                                <div className="text-center mb-6">
                                    <p className="text-6xl font-bold">{(scoreResult.propensity_score * 100)?.toFixed(0)}%</p>
                                    <p className={`text-2xl font-semibold ${getClassificacaoColor(scoreResult.classificacao)}`}>
                                        {scoreResult.classificacao}
                                    </p>
                                </div>
                                <div className="p-4 bg-muted rounded-lg">
                                    <p className="text-sm">{scoreResult.recomendacao}</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Simulador de Impacto */}
            {activeTab === 'simular' && (
                <div className="space-y-4 animate-fade-in">
                    <div className="chart-container">
                        <h3 className="font-semibold mb-4">Simulador de Impacto Financeiro</h3>
                        <p className="text-sm text-muted-foreground mb-4">Simule o impacto de ajustes de limite em um portfólio</p>

                        <div className="flex gap-4 items-end">
                            <div className="flex-1">
                                <label className="text-sm text-muted-foreground">Cenário</label>
                                <select
                                    value={cenario}
                                    onChange={(e) => setCenario(e.target.value)}
                                    className="w-full mt-1 px-4 py-2 rounded-lg bg-input border border-border"
                                >
                                    <option value="conservador">Conservador (10% redução)</option>
                                    <option value="moderado">Moderado (15% redução)</option>
                                    <option value="agressivo">Agressivo (20% redução)</option>
                                </select>
                            </div>
                            <button
                                onClick={handleSimular}
                                disabled={loading}
                                className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50"
                            >
                                {loading ? 'Simulando...' : 'Simular'}
                            </button>
                        </div>

                        {simulacaoResult && (
                            <div className="grid gap-4 md:grid-cols-3 mt-6">
                                <div className="kpi-card">
                                    <p className="text-sm text-muted-foreground">Economia ECL</p>
                                    <p className="text-2xl font-bold text-emerald-500">
                                        R$ {simulacaoResult.economia_ecl?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                    </p>
                                </div>
                                <div className="kpi-card">
                                    <p className="text-sm text-muted-foreground">Receita Adicional</p>
                                    <p className="text-2xl font-bold text-blue-500">
                                        R$ {simulacaoResult.receita_adicional?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                    </p>
                                </div>
                                <div className="kpi-card">
                                    <p className="text-sm text-muted-foreground">Impacto Líquido</p>
                                    <p className="text-2xl font-bold text-primary">
                                        R$ {simulacaoResult.impacto_liquido?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
