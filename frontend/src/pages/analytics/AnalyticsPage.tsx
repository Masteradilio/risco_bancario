/**
 * Analytics Page - Dashboard de Performance do Modelo PRINAD
 * 
 * Monitoramento de Drift (PSI), Acurácia e Backtesting
 */

import { useState, useEffect } from 'react';
import {
    TrendingUp,
    AlertTriangle,
    CheckCircle,
    AlertCircle,
    RefreshCw,
    Activity,
    Target,
    BarChart3
} from 'lucide-react';
import {
    getModelPerformance,
    getDriftReport,
    getAccuracyTrend,
    runBacktest,
    type PerformanceResponse,
    type DriftResponse,
    type BacktestResult,
    type TrendDataPoint
} from '@/lib/api/analytics_api';
import { cn } from '@/lib/utils';

// Status indicator colors
const statusColors = {
    verde: 'bg-emerald-500',
    amarelo: 'bg-amber-500',
    vermelho: 'bg-red-500',
};

const statusLabels = {
    verde: 'Normal',
    amarelo: 'Atenção',
    vermelho: 'Crítico',
};

// KPI Card Component
function KPICard({
    title,
    value,
    subtitle,
    icon: Icon,
    trend,
    status
}: {
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ComponentType<{ className?: string }>;
    trend?: 'up' | 'down' | 'neutral';
    status?: 'verde' | 'amarelo' | 'vermelho';
}) {
    return (
        <div className="bg-card rounded-xl p-6 border border-border shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm text-muted-foreground font-medium">{title}</p>
                    <p className="text-3xl font-bold mt-2">
                        {typeof value === 'number' ? value.toFixed(4) : value}
                    </p>
                    {subtitle && (
                        <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
                    )}
                </div>
                <div className={cn(
                    "p-3 rounded-xl",
                    status === 'verde' ? 'bg-emerald-500/10 text-emerald-500' :
                        status === 'amarelo' ? 'bg-amber-500/10 text-amber-500' :
                            status === 'vermelho' ? 'bg-red-500/10 text-red-500' :
                                'bg-primary/10 text-primary'
                )}>
                    <Icon className="h-6 w-6" />
                </div>
            </div>
        </div>
    );
}

// Drift Indicator Component
function DriftIndicator({ drift }: { drift: DriftResponse | null }) {
    if (!drift) return null;

    return (
        <div className="bg-card rounded-xl p-6 border border-border">
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-lg">Análise de Drift (PSI)</h3>
                <div className={cn(
                    "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium",
                    drift.nivel_alerta === 'verde' ? 'bg-emerald-500/10 text-emerald-500' :
                        drift.nivel_alerta === 'amarelo' ? 'bg-amber-500/10 text-amber-500' :
                            'bg-red-500/10 text-red-500'
                )}>
                    <span className={cn("w-2 h-2 rounded-full", statusColors[drift.nivel_alerta])} />
                    {statusLabels[drift.nivel_alerta]}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-muted/50 rounded-lg p-4">
                    <p className="text-sm text-muted-foreground">PSI Total</p>
                    <p className="text-2xl font-bold">{drift.psi_total.toFixed(4)}</p>
                </div>
                <div className="bg-muted/50 rounded-lg p-4">
                    <p className="text-sm text-muted-foreground">Limites</p>
                    <p className="text-xs mt-1">
                        <span className="text-emerald-500">Verde: &lt; 0.10</span> |
                        <span className="text-amber-500"> Amarelo: 0.10-0.25</span> |
                        <span className="text-red-500"> Vermelho: &gt; 0.25</span>
                    </p>
                </div>
            </div>

            <p className="text-sm text-muted-foreground">{drift.interpretacao}</p>

            {/* Detalhes por faixa */}
            <div className="mt-4 max-h-48 overflow-y-auto">
                <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="text-left p-2 rounded-l">Faixa</th>
                            <th className="text-right p-2">Baseline</th>
                            <th className="text-right p-2">Atual</th>
                            <th className="text-right p-2 rounded-r">PSI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {drift.detalhes_por_faixa.map((faixa, i) => (
                            <tr key={i} className="border-b border-muted/50">
                                <td className="p-2">{faixa.faixa}</td>
                                <td className="text-right p-2">{faixa.baseline_pct}%</td>
                                <td className="text-right p-2">{faixa.atual_pct}%</td>
                                <td className="text-right p-2">{faixa.psi_contribuicao.toFixed(4)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// Simple Line Chart using CSS
function TrendChart({ data, title }: { data: TrendDataPoint[], title: string }) {
    if (!data || data.length === 0) return null;

    const max = Math.max(...data.map(d => d.valor));
    const min = Math.min(...data.map(d => d.valor));
    const range = max - min || 1;

    return (
        <div className="bg-card rounded-xl p-6 border border-border">
            <h3 className="font-semibold text-lg mb-4">{title}</h3>
            <div className="flex items-end gap-2 h-32">
                {data.map((point, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center">
                        <div
                            className="w-full bg-primary/80 rounded-t transition-all hover:bg-primary"
                            style={{
                                height: `${((point.valor - min) / range * 80) + 20}%`,
                            }}
                            title={`${point.data}: ${point.valor.toFixed(4)}`}
                        />
                        <span className="text-xs text-muted-foreground mt-1 truncate w-full text-center">
                            {point.data.split('-').slice(1).join('/')}
                        </span>
                    </div>
                ))}
            </div>
            <div className="flex justify-between text-xs text-muted-foreground mt-2">
                <span>Mín: {min.toFixed(4)}</span>
                <span>Máx: {max.toFixed(4)}</span>
            </div>
        </div>
    );
}

// Backtest Table Component
function BacktestTable({ backtest }: { backtest: BacktestResult | null }) {
    if (!backtest) return null;

    return (
        <div className="bg-card rounded-xl p-6 border border-border">
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-lg">Backtesting</h3>
                <span className={cn(
                    "px-3 py-1 rounded-full text-sm font-medium",
                    backtest.resumo.calibracao === 'OK'
                        ? 'bg-emerald-500/10 text-emerald-500'
                        : 'bg-amber-500/10 text-amber-500'
                )}>
                    Calibração: {backtest.resumo.calibracao}
                </span>
            </div>

            <div className="grid grid-cols-4 gap-3 mb-4">
                <div className="bg-muted/50 rounded-lg p-3 text-center">
                    <p className="text-xs text-muted-foreground">Observações</p>
                    <p className="text-lg font-semibold">{backtest.resumo.total_observacoes.toLocaleString()}</p>
                </div>
                <div className="bg-muted/50 rounded-lg p-3 text-center">
                    <p className="text-xs text-muted-foreground">Defaults</p>
                    <p className="text-lg font-semibold">{backtest.resumo.total_defaults.toLocaleString()}</p>
                </div>
                <div className="bg-muted/50 rounded-lg p-3 text-center">
                    <p className="text-xs text-muted-foreground">PD Esperado</p>
                    <p className="text-lg font-semibold">{backtest.resumo.pd_medio_esperado}%</p>
                </div>
                <div className="bg-muted/50 rounded-lg p-3 text-center">
                    <p className="text-xs text-muted-foreground">Default Real</p>
                    <p className="text-lg font-semibold">{backtest.resumo.default_rate_realizado}%</p>
                </div>
            </div>

            <table className="w-full text-sm">
                <thead className="bg-muted/50">
                    <tr>
                        <th className="text-left p-2 rounded-l">Faixa PD</th>
                        <th className="text-right p-2">Qtd</th>
                        <th className="text-right p-2">PD Esperado</th>
                        <th className="text-right p-2">Default Real</th>
                        <th className="text-right p-2">Ratio</th>
                        <th className="text-center p-2 rounded-r">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {backtest.por_faixa.map((faixa, i) => (
                        <tr key={i} className="border-b border-muted/50">
                            <td className="p-2">{faixa.faixa}</td>
                            <td className="text-right p-2">{faixa.quantidade.toLocaleString()}</td>
                            <td className="text-right p-2">{faixa.pd_medio_esperado}%</td>
                            <td className="text-right p-2">{faixa.default_rate_realizado}%</td>
                            <td className="text-right p-2">{faixa.ratio}</td>
                            <td className="text-center p-2">
                                {faixa.status === 'OK' ? (
                                    <CheckCircle className="h-4 w-4 text-emerald-500 inline" />
                                ) : (
                                    <AlertCircle className="h-4 w-4 text-amber-500 inline" />
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// Main Analytics Page
export default function AnalyticsPage() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [performance, setPerformance] = useState<PerformanceResponse | null>(null);
    const [drift, setDrift] = useState<DriftResponse | null>(null);
    const [aucTrend, setAucTrend] = useState<TrendDataPoint[]>([]);
    const [giniTrend, setGiniTrend] = useState<TrendDataPoint[]>([]);
    const [backtest, setBacktest] = useState<BacktestResult | null>(null);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [perfData, driftData, aucData, giniData, btData] = await Promise.all([
                getModelPerformance(),
                getDriftReport(),
                getAccuracyTrend('auc_roc', 6),
                getAccuracyTrend('gini', 6),
                runBacktest()
            ]);

            setPerformance(perfData);
            setDrift(driftData);
            setAucTrend(aucData.dados);
            setGiniTrend(giniData.dados);
            setBacktest(btData);
        } catch (err) {
            setError('Erro ao carregar dados de analytics. Verifique se o backend está rodando.');
            console.error(err);

            // Dados mock para desenvolvimento
            setPerformance({
                metricas: {
                    auc_roc: 0.9932,
                    gini: 0.9864,
                    precision: 0.9485,
                    recall: 0.9683,
                    f1_score: 0.9583,
                    ks_statistic: 0.8392,
                    data_calculo: new Date().toISOString()
                },
                status_geral: 'verde',
                alertas: [],
                ultima_atualizacao: new Date().toISOString()
            });

            setDrift({
                psi_total: 0.0423,
                nivel_alerta: 'verde',
                interpretacao: 'NORMAL: Distribuição estável, sem drift significativo.',
                detalhes_por_faixa: [
                    { faixa: '0% - 10%', baseline_pct: 45.2, atual_pct: 44.8, psi_contribuicao: 0.0012 },
                    { faixa: '10% - 20%', baseline_pct: 25.3, atual_pct: 26.1, psi_contribuicao: 0.0025 },
                    { faixa: '20% - 50%', baseline_pct: 20.1, atual_pct: 19.8, psi_contribuicao: 0.0018 },
                    { faixa: '50% - 100%', baseline_pct: 9.4, atual_pct: 9.3, psi_contribuicao: 0.0010 }
                ]
            });

            setAucTrend([
                { data: '2025-08', valor: 0.9986 },
                { data: '2025-09', valor: 0.9981 },
                { data: '2025-10', valor: 0.9976 },
                { data: '2025-11', valor: 0.9956 },
                { data: '2025-12', valor: 0.9942 },
                { data: '2026-01', valor: 0.9932 }
            ]);

            setGiniTrend([
                { data: '2025-08', valor: 0.9972 },
                { data: '2025-09', valor: 0.9962 },
                { data: '2025-10', valor: 0.9952 },
                { data: '2025-11', valor: 0.9912 },
                { data: '2025-12', valor: 0.9884 },
                { data: '2026-01', valor: 0.9864 }
            ]);

            setBacktest({
                data_execucao: new Date().toISOString(),
                periodo_analise: 'últimos 12 meses',
                resumo: {
                    total_observacoes: 15420,
                    total_defaults: 342,
                    pd_medio_esperado: 2.18,
                    default_rate_realizado: 2.22,
                    calibracao: 'OK'
                },
                por_faixa: [
                    { faixa: '0% - 5%', quantidade: 8534, pd_medio_esperado: 1.2, default_rate_realizado: 1.18, ratio: 0.98, status: 'OK' },
                    { faixa: '5% - 10%', quantidade: 3421, pd_medio_esperado: 7.5, default_rate_realizado: 7.8, ratio: 1.04, status: 'OK' },
                    { faixa: '10% - 20%', quantidade: 2156, pd_medio_esperado: 14.2, default_rate_realizado: 15.1, ratio: 1.06, status: 'OK' },
                    { faixa: '20% - 50%', quantidade: 987, pd_medio_esperado: 32.5, default_rate_realizado: 38.2, ratio: 1.18, status: 'OK' },
                    { faixa: '50% - 100%', quantidade: 322, pd_medio_esperado: 68.4, default_rate_realizado: 72.1, ratio: 1.05, status: 'OK' }
                ]
            });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">Analytics - Performance do Modelo</h1>
                    <p className="text-muted-foreground">Monitoramento de Drift, Acurácia e Backtesting</p>
                </div>
                <button
                    onClick={fetchData}
                    disabled={loading}
                    className={cn(
                        "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors",
                        "bg-primary text-primary-foreground hover:bg-primary/90",
                        loading && "opacity-50 cursor-not-allowed"
                    )}
                >
                    <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                    Atualizar
                </button>
            </div>

            {error && (
                <div className="bg-amber-500/10 border border-amber-500/20 text-amber-500 p-4 rounded-lg flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    {error} (Usando dados mock)
                </div>
            )}

            {/* KPIs Grid */}
            <div className="grid grid-cols-4 gap-4">
                <KPICard
                    title="AUC-ROC"
                    value={performance?.metricas.auc_roc || 0}
                    subtitle="Área sob a curva ROC"
                    icon={Target}
                    status={performance?.status_geral}
                />
                <KPICard
                    title="Gini"
                    value={performance?.metricas.gini || 0}
                    subtitle="Coeficiente de Gini"
                    icon={BarChart3}
                    status={performance?.status_geral}
                />
                <KPICard
                    title="Precision"
                    value={performance?.metricas.precision || 0}
                    subtitle="Taxa de verdadeiros positivos"
                    icon={CheckCircle}
                />
                <KPICard
                    title="Recall"
                    value={performance?.metricas.recall || 0}
                    subtitle="Taxa de detecção"
                    icon={Activity}
                />
            </div>

            {/* Drift & Trends */}
            <div className="grid grid-cols-2 gap-6">
                <DriftIndicator drift={drift} />
                <div className="space-y-6">
                    <TrendChart data={aucTrend} title="Evolução AUC-ROC (6 meses)" />
                    <TrendChart data={giniTrend} title="Evolução Gini (6 meses)" />
                </div>
            </div>

            {/* Backtesting */}
            <BacktestTable backtest={backtest} />

            {/* Alertas */}
            {performance?.alertas && performance.alertas.length > 0 && (
                <div className="bg-card rounded-xl p-6 border border-border">
                    <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-amber-500" />
                        Alertas Ativos
                    </h3>
                    <div className="space-y-2">
                        {performance.alertas.map((alerta, i) => (
                            <div
                                key={i}
                                className={cn(
                                    "p-3 rounded-lg flex items-center gap-3",
                                    alerta.nivel === 'vermelho' ? 'bg-red-500/10 text-red-500' : 'bg-amber-500/10 text-amber-500'
                                )}
                            >
                                <AlertCircle className="h-5 w-5 shrink-0" />
                                <span>{alerta.mensagem}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
