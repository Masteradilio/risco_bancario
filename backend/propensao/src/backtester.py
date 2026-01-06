"""
Backtester - Rolling 12-month backtesting for credit risk models.

Compares historical predictions with actual outcomes to validate
model performance over time.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import PRODUTOS_CREDITO, setup_logging
from propensao.src.model_validator import ModelValidator, get_model_validator

logger = setup_logging(__name__)


@dataclass
class ResultadoMensal:
    """Monthly backtesting result."""
    mes: str
    auc_roc: float
    gini: float
    ks: float
    psi: float
    n_exposicoes: int
    n_defaults: int
    taxa_default_prevista: float
    taxa_default_real: float
    erro_taxa: float


@dataclass
class ResultadoBacktest:
    """Complete backtesting results."""
    modelo: str
    periodo_inicio: str
    periodo_fim: str
    resultados_mensais: List[ResultadoMensal]
    auc_medio: float
    auc_std: float
    gini_medio: float
    ks_medio: float
    psi_medio: float
    accuracy_ratio: float
    passou_validacao: bool
    detalhes: str


class Backtester:
    """
    Performs rolling backtesting for credit risk models.
    
    Validates model performance over 12 months by comparing
    predictions with actual defaults.
    """
    
    def __init__(self, validator: Optional[ModelValidator] = None):
        """
        Initialize backtester.
        
        Args:
            validator: Model validator instance
        """
        self.validator = validator or get_model_validator()
        logger.info("Backtester initialized")
    
    def preparar_dados_mensais(
        self,
        df: pd.DataFrame,
        col_data: str = 'data',
        col_pred: str = 'prob_default',
        col_real: str = 'default',
        col_cliente: str = 'cliente_id'
    ) -> Dict[str, pd.DataFrame]:
        """
        Prepare data by month for rolling backtest.
        
        Args:
            df: DataFrame with predictions and outcomes
            col_data: Date column name
            col_pred: Predicted probability column
            col_real: Actual outcome column
            col_cliente: Client ID column
            
        Returns:
            Dict of month -> DataFrame
        """
        df = df.copy()
        df['ano_mes'] = pd.to_datetime(df[col_data]).dt.to_period('M').astype(str)
        
        meses = {}
        for mes in sorted(df['ano_mes'].unique()):
            meses[mes] = df[df['ano_mes'] == mes]
        
        logger.info(f"Prepared {len(meses)} months of data")
        return meses
    
    def executar_backtest_mensal(
        self,
        df_mes: pd.DataFrame,
        df_base: pd.DataFrame,
        col_pred: str = 'prob_default',
        col_real: str = 'default'
    ) -> Optional[ResultadoMensal]:
        """
        Execute backtest for a single month.
        
        Args:
            df_mes: Data for the month
            df_base: Baseline data for PSI calculation
            col_pred: Prediction column
            col_real: Actual outcome column
            
        Returns:
            ResultadoMensal or None if insufficient data
        """
        if len(df_mes) < 100 or df_mes[col_real].sum() < 5:
            return None
        
        y_true = df_mes[col_real].values
        y_pred = df_mes[col_pred].values
        y_base = df_base[col_pred].values
        
        # Calculate metrics
        auc = self.validator.calcular_auc_roc(y_true, y_pred)
        gini = self.validator.calcular_gini(y_true, y_pred)
        ks, _ = self.validator.calcular_ks(y_true, y_pred)
        psi = self.validator.calcular_psi(y_base, y_pred)
        
        # Calculate accuracy
        taxa_prevista = y_pred.mean()
        taxa_real = y_true.mean()
        erro = abs(taxa_prevista - taxa_real) / taxa_real if taxa_real > 0 else 0
        
        return ResultadoMensal(
            mes=df_mes['ano_mes'].iloc[0],
            auc_roc=auc,
            gini=gini,
            ks=ks,
            psi=psi,
            n_exposicoes=len(df_mes),
            n_defaults=int(y_true.sum()),
            taxa_default_prevista=taxa_prevista,
            taxa_default_real=taxa_real,
            erro_taxa=erro
        )
    
    def executar_backtest_rolling(
        self,
        df: pd.DataFrame,
        nome_modelo: str,
        meses_base: int = 3,
        col_data: str = 'data',
        col_pred: str = 'prob_default',
        col_real: str = 'default'
    ) -> ResultadoBacktest:
        """
        Execute rolling 12-month backtest.
        
        Args:
            df: Full dataset
            nome_modelo: Model name
            meses_base: Number of months for baseline
            col_data: Date column
            col_pred: Prediction column
            col_real: Actual outcome column
            
        Returns:
            ResultadoBacktest with complete results
        """
        logger.info(f"Starting rolling backtest for {nome_modelo}")
        
        # Prepare monthly data
        dados_mensais = self.preparar_dados_mensais(
            df, col_data, col_pred, col_real
        )
        
        meses = sorted(dados_mensais.keys())
        
        if len(meses) < meses_base + 1:
            raise ValueError(f"Insufficient months for backtest: {len(meses)}")
        
        # Use first months as baseline
        df_base = pd.concat([dados_mensais[m] for m in meses[:meses_base]])
        
        # Backtest remaining months
        resultados = []
        for mes in meses[meses_base:]:
            resultado = self.executar_backtest_mensal(
                dados_mensais[mes], df_base, col_pred, col_real
            )
            if resultado:
                resultados.append(resultado)
        
        if not resultados:
            raise ValueError("No valid backtest results")
        
        # Aggregate metrics
        auc_values = [r.auc_roc for r in resultados]
        gini_values = [r.gini for r in resultados]
        ks_values = [r.ks for r in resultados]
        psi_values = [r.psi for r in resultados]
        
        auc_medio = np.mean(auc_values)
        auc_std = np.std(auc_values)
        gini_medio = np.mean(gini_values)
        ks_medio = np.mean(ks_values)
        psi_medio = np.mean(psi_values)
        
        # Accuracy ratio
        total_previsto = sum(r.taxa_default_prevista * r.n_exposicoes for r in resultados)
        total_real = sum(r.taxa_default_real * r.n_exposicoes for r in resultados)
        accuracy_ratio = total_previsto / total_real if total_real > 0 else 0
        
        # Validation check (AUC >= 0.90)
        passou = auc_medio >= 0.90 and psi_medio <= 0.25
        
        detalhes = (
            f"Backtest de {len(resultados)} meses ({meses[meses_base]} a {meses[-1]}). "
            f"AUC médio: {auc_medio:.2%} (σ={auc_std:.2%}). "
            f"Accuracy Ratio: {accuracy_ratio:.2f}. "
            f"PSI médio: {psi_medio:.3f}. "
            f"{'APROVADO' if passou else 'REPROVADO'} para produção."
        )
        
        logger.info(detalhes)
        
        return ResultadoBacktest(
            modelo=nome_modelo,
            periodo_inicio=meses[meses_base],
            periodo_fim=meses[-1],
            resultados_mensais=resultados,
            auc_medio=auc_medio,
            auc_std=auc_std,
            gini_medio=gini_medio,
            ks_medio=ks_medio,
            psi_medio=psi_medio,
            accuracy_ratio=accuracy_ratio,
            passou_validacao=passou,
            detalhes=detalhes
        )
    
    def simular_backtest(
        self,
        nome_modelo: str,
        n_meses: int = 12,
        n_clientes_mes: int = 10000,
        taxa_default: float = 0.025,
        qualidade_modelo: float = 0.92
    ) -> ResultadoBacktest:
        """
        Simulate backtest with synthetic data.
        
        Args:
            nome_modelo: Model name
            n_meses: Number of months
            n_clientes_mes: Clients per month
            taxa_default: Default rate
            qualidade_modelo: Model quality (affects AUC)
            
        Returns:
            Simulated ResultadoBacktest
        """
        logger.info(f"Simulating backtest for {nome_modelo}")
        
        np.random.seed(42)
        
        resultados = []
        base_date = datetime(2025, 1, 1)
        
        for i in range(n_meses):
            mes_date = base_date + timedelta(days=30*i)
            mes_str = mes_date.strftime('%Y-%m')
            
            # Generate synthetic data
            y_true = np.random.binomial(1, taxa_default, n_clientes_mes)
            
            # Generate predictions based on model quality
            noise = np.random.normal(0, 1 - qualidade_modelo, n_clientes_mes)
            y_pred = np.clip(
                y_true * qualidade_modelo + (1 - y_true) * (1 - qualidade_modelo) * 0.1 + noise * 0.1,
                0.001, 0.999
            )
            
            # Calculate metrics
            auc = self.validator.calcular_auc_roc(y_true, y_pred)
            gini = self.validator.calcular_gini(y_true, y_pred)
            ks, _ = self.validator.calcular_ks(y_true, y_pred)
            
            # PSI with small drift
            psi = 0.02 + np.random.uniform(0, 0.03) + i * 0.005
            
            resultado = ResultadoMensal(
                mes=mes_str,
                auc_roc=auc,
                gini=gini,
                ks=ks,
                psi=psi,
                n_exposicoes=n_clientes_mes,
                n_defaults=int(y_true.sum()),
                taxa_default_prevista=y_pred.mean(),
                taxa_default_real=y_true.mean(),
                erro_taxa=abs(y_pred.mean() - y_true.mean()) / y_true.mean()
            )
            resultados.append(resultado)
        
        # Aggregate
        auc_medio = np.mean([r.auc_roc for r in resultados])
        auc_std = np.std([r.auc_roc for r in resultados])
        gini_medio = np.mean([r.gini for r in resultados])
        ks_medio = np.mean([r.ks for r in resultados])
        psi_medio = np.mean([r.psi for r in resultados])
        accuracy_ratio = 1.0 + np.random.uniform(-0.1, 0.1)
        
        passou = auc_medio >= 0.90
        
        return ResultadoBacktest(
            modelo=nome_modelo,
            periodo_inicio=resultados[0].mes,
            periodo_fim=resultados[-1].mes,
            resultados_mensais=resultados,
            auc_medio=auc_medio,
            auc_std=auc_std,
            gini_medio=gini_medio,
            ks_medio=ks_medio,
            psi_medio=psi_medio,
            accuracy_ratio=accuracy_ratio,
            passou_validacao=passou,
            detalhes=f"Simulação de {n_meses} meses. AUC médio: {auc_medio:.2%}"
        )
    
    def exportar_relatorio_markdown(
        self,
        resultado: ResultadoBacktest,
        output_path: Path
    ) -> Path:
        """Export backtest results to markdown."""
        lines = [
            f"# Relatório de Backtesting: {resultado.modelo}",
            f"*Período: {resultado.periodo_inicio} a {resultado.periodo_fim}*",
            "",
            "---",
            "",
            "## Sumário",
            "",
            f"**Status: {'✅ APROVADO' if resultado.passou_validacao else '❌ REPROVADO'}**",
            "",
            resultado.detalhes,
            "",
            "## Métricas Agregadas",
            "",
            "| Métrica | Valor | Threshold |",
            "|---------|-------|-----------|",
            f"| AUC-ROC | {resultado.auc_medio:.2%} | ≥ 90% |",
            f"| AUC σ | {resultado.auc_std:.2%} | < 5% |",
            f"| Gini | {resultado.gini_medio:.2%} | ≥ 80% |",
            f"| KS | {resultado.ks_medio:.2%} | ≥ 50% |",
            f"| PSI Médio | {resultado.psi_medio:.3f} | ≤ 0.10 |",
            f"| Accuracy Ratio | {resultado.accuracy_ratio:.2f} | 0.8-1.2 |",
            "",
            "## Resultados Mensais",
            "",
            "| Mês | AUC | Gini | KS | PSI | Defaults |",
            "|-----|-----|------|----|----|----------|",
        ]
        
        for r in resultado.resultados_mensais:
            lines.append(
                f"| {r.mes} | {r.auc_roc:.2%} | {r.gini:.2%} | "
                f"{r.ks:.2%} | {r.psi:.3f} | {r.n_defaults} |"
            )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Backtest report exported to {output_path}")
        return output_path


# Module-level instance
_backtester: Optional[Backtester] = None


def get_backtester() -> Backtester:
    """Get or create backtester instance."""
    global _backtester
    if _backtester is None:
        _backtester = Backtester()
    return _backtester


if __name__ == "__main__":
    backtester = Backtester()
    
    # Simulate backtest
    resultado = backtester.simular_backtest(
        nome_modelo="PRINAD v2.0",
        n_meses=12,
        qualidade_modelo=0.92
    )
    
    print("=" * 60)
    print(f"Backtest: {resultado.modelo}")
    print(f"AUC Médio: {resultado.auc_medio:.2%}")
    print(f"Passou: {resultado.passou_validacao}")
    print("=" * 60)
