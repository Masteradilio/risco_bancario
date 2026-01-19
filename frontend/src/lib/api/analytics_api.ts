/**
 * API Client para Analytics e Monitoramento de Modelo
 * 
 * Consome os endpoints de /analytics do backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ModelMetrics {
    auc_roc: number;
    gini: number;
    precision: number;
    recall: number;
    f1_score: number;
    ks_statistic: number;
    data_calculo: string;
}

export interface PerformanceResponse {
    metricas: ModelMetrics;
    status_geral: 'verde' | 'amarelo' | 'vermelho';
    alertas: Array<{
        nivel: string;
        metrica: string;
        valor: number;
        threshold: number;
        mensagem: string;
    }>;
    ultima_atualizacao: string;
}

export interface DriftResponse {
    psi_total: number;
    nivel_alerta: 'verde' | 'amarelo' | 'vermelho';
    interpretacao: string;
    detalhes_por_faixa: Array<{
        faixa: string;
        baseline_pct: number;
        atual_pct: number;
        psi_contribuicao: number;
    }>;
}

export interface TrendDataPoint {
    data: string;
    valor: number;
}

export interface BacktestResult {
    data_execucao: string;
    periodo_analise: string;
    resumo: {
        total_observacoes: number;
        total_defaults: number;
        pd_medio_esperado: number;
        default_rate_realizado: number;
        calibracao: 'OK' | 'AJUSTAR';
    };
    por_faixa: Array<{
        faixa: string;
        quantidade: number;
        pd_medio_esperado: number;
        default_rate_realizado: number;
        ratio: number;
        status: 'OK' | 'INVESTIGAR';
    }>;
}

export interface FullReportResponse {
    data_geracao: string;
    status_geral: {
        nivel: 'verde' | 'amarelo' | 'vermelho';
        descricao: string;
        alertas_vermelhos: number;
        alertas_amarelos: number;
    };
    metricas_atuais: PerformanceResponse;
    analise_drift: DriftResponse;
    backtesting: BacktestResult;
    evolucao_auc: TrendDataPoint[];
    evolucao_gini: TrendDataPoint[];
    recomendacoes: string[];
}

/**
 * Obtém métricas atuais de performance do modelo
 */
export async function getModelPerformance(): Promise<PerformanceResponse> {
    const response = await fetch(`${API_BASE_URL}/analytics/model-performance`);
    if (!response.ok) {
        throw new Error('Falha ao obter métricas de performance');
    }
    return response.json();
}

/**
 * Obtém relatório de drift (PSI)
 */
export async function getDriftReport(): Promise<DriftResponse> {
    const response = await fetch(`${API_BASE_URL}/analytics/drift-report`);
    if (!response.ok) {
        throw new Error('Falha ao obter relatório de drift');
    }
    return response.json();
}

/**
 * Obtém evolução temporal de uma métrica
 */
export async function getAccuracyTrend(
    metrica: string = 'auc_roc',
    meses: number = 6
): Promise<{ metrica: string; periodo_meses: number; dados: TrendDataPoint[] }> {
    const response = await fetch(
        `${API_BASE_URL}/analytics/accuracy-trend?metrica=${metrica}&meses=${meses}`
    );
    if (!response.ok) {
        throw new Error('Falha ao obter evolução temporal');
    }
    return response.json();
}

/**
 * Executa backtesting do modelo
 */
export async function runBacktest(): Promise<BacktestResult> {
    const response = await fetch(`${API_BASE_URL}/analytics/backtest`, {
        method: 'POST',
    });
    if (!response.ok) {
        throw new Error('Falha ao executar backtesting');
    }
    return response.json();
}

/**
 * Obtém relatório completo de monitoramento
 */
export async function getFullReport(): Promise<FullReportResponse> {
    const response = await fetch(`${API_BASE_URL}/analytics/full-report`);
    if (!response.ok) {
        throw new Error('Falha ao obter relatório completo');
    }
    return response.json();
}
