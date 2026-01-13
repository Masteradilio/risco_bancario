import { useAuth } from '@/stores/useAuth'
import { Link } from 'react-router-dom'
import {
    Target,
    TrendingUp,
    Calculator,
    DollarSign,
    Users,
    Activity,
    ArrowUpRight,
    ArrowDownRight,
    BarChart3,
    PieChart as PieChartIcon,
    Layers,
    ChevronRight,
} from 'lucide-react'
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    BarChart,
    Bar,
} from 'recharts'
import { cn } from '@/lib/utils'

// Dados resumo PRINAD
const ratingDistribution = [
    { rating: 'A1-A3', count: 8240, color: '#4ade80' },
    { rating: 'B1-B3', count: 4270, color: '#facc15' },
    { rating: 'C1-C3', count: 1850, color: '#f97316' },
    { rating: 'D-H', count: 360, color: '#ef4444' },
]

// Dados resumo Propensão
const propensaoData = [
    { mes: 'Jul', consignado: 72, cartao: 58, imobiliario: 42 },
    { mes: 'Ago', consignado: 75, cartao: 62, imobiliario: 45 },
    { mes: 'Set', consignado: 78, cartao: 65, imobiliario: 48 },
    { mes: 'Out', consignado: 82, cartao: 68, imobiliario: 52 },
    { mes: 'Nov', consignado: 85, cartao: 72, imobiliario: 55 },
    { mes: 'Dez', consignado: 88, cartao: 75, imobiliario: 58 },
]

// Dados resumo ECL por estágio
const eclEstagio = [
    { estagio: 'Stage 1', valor: 1850000, percentual: 75, color: '#4ade80' },
    { estagio: 'Stage 2', valor: 580000, percentual: 18, color: '#facc15' },
    { estagio: 'Stage 3', valor: 470000, percentual: 7, color: '#ef4444' },
]

interface KPICardProps {
    title: string
    value: string | number
    subtitle?: string
    trend?: number
    icon: React.ComponentType<{ className?: string }>
    iconColor?: string
    link?: string
}

function KPICard({ title, value, subtitle, trend, icon: Icon, iconColor = 'text-primary', link }: KPICardProps) {
    const isPositive = trend && trend > 0
    const isNegative = trend && trend < 0

    const content = (
        <div className="kpi-card group hover:border-primary/50 transition-colors">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm text-muted-foreground">{title}</p>
                    <p className="text-2xl font-bold mt-1">{value}</p>
                    {subtitle && (
                        <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
                    )}
                    {trend !== undefined && (
                        <div className={cn(
                            'flex items-center gap-1 text-xs mt-2',
                            isPositive && 'text-emerald-500',
                            isNegative && 'text-red-500',
                            !isPositive && !isNegative && 'text-muted-foreground'
                        )}>
                            {isPositive && <ArrowUpRight className="h-3 w-3" />}
                            {isNegative && <ArrowDownRight className="h-3 w-3" />}
                            <span>{Math.abs(trend)}% vs mês anterior</span>
                        </div>
                    )}
                </div>
                <div className={cn('p-2.5 rounded-xl', iconColor.replace('text-', 'bg-').replace('500', '500/10'))}>
                    <Icon className={cn('h-5 w-5', iconColor)} />
                </div>
            </div>
            {link && (
                <div className="mt-3 pt-3 border-t border-border flex items-center justify-between text-xs text-muted-foreground group-hover:text-primary transition-colors">
                    <span>Ver detalhes</span>
                    <ChevronRight className="h-3 w-3" />
                </div>
            )}
        </div>
    )

    if (link) {
        return <Link to={link}>{content}</Link>
    }
    return content
}

export default function DashboardPage() {
    const { user } = useAuth()

    return (
        <div className="space-y-6">
            {/* Mensagem de boas-vindas */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">
                        Bem-vindo, {user?.nome?.split(' ')[0] || 'Usuário'}! 👋
                    </h1>
                    <p className="text-muted-foreground">
                        Resumo geral do sistema de gestão de risco bancário
                    </p>
                </div>
            </div>

            {/* KPIs Principais - Divididos por módulo */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* PRINAD */}
                <KPICard
                    title="Classificações PRINAD"
                    value="14.720"
                    subtitle="Clientes classificados"
                    trend={8}
                    icon={Target}
                    iconColor="text-violet-500"
                    link="/prinad"
                />
                {/* Propensão */}
                <KPICard
                    title="Propensão Média"
                    value="72.4%"
                    subtitle="Score médio do portfólio"
                    trend={5}
                    icon={TrendingUp}
                    iconColor="text-emerald-500"
                    link="/propensao"
                />
                {/* ECL Total */}
                <KPICard
                    title="ECL Total (IFRS 9)"
                    value="R$ 2.9M"
                    subtitle="Perda esperada provisionada"
                    trend={-3}
                    icon={Calculator}
                    iconColor="text-amber-500"
                    link="/perda-esperada"
                />
                {/* Receita Potencial */}
                <KPICard
                    title="Limites Otimizados"
                    value="R$ 4.2M"
                    subtitle="Potencial de receita adicional"
                    trend={12}
                    icon={DollarSign}
                    iconColor="text-blue-500"
                    link="/propensao"
                />
            </div>

            {/* Seção de Módulos */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* PRINAD - Distribuição de Rating */}
                <div className="chart-container">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <Target className="h-5 w-5 text-violet-500" />
                            <div>
                                <h3 className="font-semibold">PRINAD</h3>
                                <p className="text-xs text-muted-foreground">Distribuição de Rating</p>
                            </div>
                        </div>
                        <Link to="/prinad" className="text-xs text-primary hover:underline">Ver mais</Link>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={ratingDistribution} layout="vertical">
                            <XAxis type="number" hide />
                            <YAxis dataKey="rating" type="category" width={50} fontSize={12} stroke="var(--muted-foreground)" />
                            <Tooltip
                                formatter={(value: number) => value.toLocaleString()}
                                contentStyle={{ backgroundColor: 'var(--popover)', borderColor: 'var(--border)', borderRadius: '8px' }}
                            />
                            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                                {ratingDistribution.map((entry, index) => (
                                    <Cell key={index} fill={entry.color} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                    <div className="flex justify-center gap-3 mt-2">
                        {ratingDistribution.map((item) => (
                            <div key={item.rating} className="flex items-center gap-1.5 text-xs">
                                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                                {item.rating}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Propensão - Evolução */}
                <div className="chart-container">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-emerald-500" />
                            <div>
                                <h3 className="font-semibold">Propensão</h3>
                                <p className="text-xs text-muted-foreground">Evolução por Produto</p>
                            </div>
                        </div>
                        <Link to="/propensao" className="text-xs text-primary hover:underline">Ver mais</Link>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                        <AreaChart data={propensaoData}>
                            <defs>
                                <linearGradient id="colorConsignado" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#4ade80" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#4ade80" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                            <XAxis dataKey="mes" fontSize={11} stroke="var(--muted-foreground)" />
                            <YAxis fontSize={11} stroke="var(--muted-foreground)" domain={[0, 100]} />
                            <Tooltip contentStyle={{ backgroundColor: 'var(--popover)', borderColor: 'var(--border)', borderRadius: '8px' }} />
                            <Area type="monotone" dataKey="consignado" stroke="#4ade80" fill="url(#colorConsignado)" strokeWidth={2} name="Consignado" />
                            <Area type="monotone" dataKey="cartao" stroke="#f97316" fill="transparent" strokeWidth={2} name="Cartão" />
                            <Area type="monotone" dataKey="imobiliario" stroke="#3b82f6" fill="transparent" strokeWidth={2} name="Imobiliário" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                {/* ECL - Por Estágio */}
                <div className="chart-container">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <Calculator className="h-5 w-5 text-amber-500" />
                            <div>
                                <h3 className="font-semibold">Perda Esperada</h3>
                                <p className="text-xs text-muted-foreground">ECL por Estágio IFRS 9</p>
                            </div>
                        </div>
                        <Link to="/perda-esperada" className="text-xs text-primary hover:underline">Ver mais</Link>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                            <Pie
                                data={eclEstagio}
                                dataKey="valor"
                                nameKey="estagio"
                                innerRadius={50}
                                outerRadius={80}
                            >
                                {eclEstagio.map((entry, index) => (
                                    <Cell key={index} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip
                                formatter={(value: number) => `R$ ${(value / 1000000).toFixed(2)}M`}
                                contentStyle={{ backgroundColor: 'var(--popover)', borderColor: 'var(--border)', borderRadius: '8px' }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="flex justify-center gap-4 text-xs">
                        {eclEstagio.map((item) => (
                            <div key={item.estagio} className="flex items-center gap-1.5">
                                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                                <span>{item.estagio}: {item.percentual}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Métricas Secundárias */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="kpi-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-violet-500/10">
                            <BarChart3 className="h-5 w-5 text-violet-500" />
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">AUC-ROC PRINAD</p>
                            <p className="text-xl font-bold text-violet-500">0.9986</p>
                        </div>
                    </div>
                </div>

                <div className="kpi-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-emerald-500/10">
                            <Users className="h-5 w-5 text-emerald-500" />
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Clientes Impactados</p>
                            <p className="text-xl font-bold text-emerald-500">1.247</p>
                        </div>
                    </div>
                </div>

                <div className="kpi-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-amber-500/10">
                            <Layers className="h-5 w-5 text-amber-500" />
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">PD Médio</p>
                            <p className="text-xl font-bold text-amber-500">12.4%</p>
                        </div>
                    </div>
                </div>

                <div className="kpi-card">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-blue-500/10">
                            <Activity className="h-5 w-5 text-blue-500" />
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Taxa Conversão</p>
                            <p className="text-xl font-bold text-blue-500">34.8%</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Links Rápidos */}
            <div className="chart-container">
                <h3 className="font-semibold mb-4">Ações Rápidas</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <Link
                        to="/prinad"
                        className="flex items-center gap-3 p-4 rounded-xl bg-violet-500/10 hover:bg-violet-500/20 transition-colors"
                    >
                        <Target className="h-5 w-5 text-violet-500" />
                        <span className="font-medium">Classificar Cliente</span>
                    </Link>
                    <Link
                        to="/propensao"
                        className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 transition-colors"
                    >
                        <TrendingUp className="h-5 w-5 text-emerald-500" />
                        <span className="font-medium">Recomendar Limite</span>
                    </Link>
                    <Link
                        to="/perda-esperada/calculo"
                        className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 transition-colors"
                    >
                        <Calculator className="h-5 w-5 text-amber-500" />
                        <span className="font-medium">Calcular ECL</span>
                    </Link>
                    <Link
                        to="/relatorios"
                        className="flex items-center gap-3 p-4 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 transition-colors"
                    >
                        <PieChartIcon className="h-5 w-5 text-blue-500" />
                        <span className="font-medium">Gerar Relatório</span>
                    </Link>
                </div>
            </div>
        </div>
    )
}
