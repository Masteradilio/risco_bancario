"""
Limit Predictor - Regression model for future limit utilization prediction.

Predicts which clients will have limits reduced in the next quarter,
enabling proactive notification 60/30 days in advance.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import joblib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    PRODUTOS_CREDITO,
    PROPENSAO_DIR,
    LIMITE_MINIMO_PERCENTUAL,
    setup_logging
)

logger = setup_logging(__name__)

try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


@dataclass
class PrevisaoLimite:
    """Limit prediction for next quarter."""
    cliente_id: str
    produto: str
    limite_atual: float
    utilizacao_prevista: float  # 0-1
    limite_previsto: float
    acao_prevista: str  # manter, reduzir, aumentar
    confianca: float  # 0-1
    dias_para_aplicacao: int


@dataclass
class ListaNotificacao:
    """Notification list for a batch run."""
    data_geracao: datetime
    horizonte_dias: int  # 60 or 30
    clientes: List[PrevisaoLimite]
    total_reducoes: int
    total_aumentos: int
    economia_ecl_estimada: float


class LimitPredictor:
    """
    Predicts future limit utilization to enable proactive notifications.
    
    Uses historical utilization patterns to predict if a client will
    use their credit limits in the next quarter.
    """
    
    # Prediction confidence threshold
    CONFIDENCE_THRESHOLD = 0.70
    
    def __init__(self, modelo_dir: Optional[Path] = None):
        """
        Initialize limit predictor.
        
        Args:
            modelo_dir: Directory for model artifacts
        """
        self.modelo_dir = modelo_dir or (PROPENSAO_DIR / "modelo")
        self.modelo_dir.mkdir(exist_ok=True)
        
        self.modelos: Dict[str, any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.is_trained = False
        
        logger.info("LimitPredictor initialized")
    
    def _criar_features_temporais(
        self,
        df: pd.DataFrame,
        col_mes: str = 'mes_referencia'
    ) -> pd.DataFrame:
        """
        Create temporal features from historical data.
        
        Args:
            df: DataFrame with monthly data
            col_mes: Column name for month reference
            
        Returns:
            DataFrame with temporal features
        """
        df = df.copy()
        
        if col_mes in df.columns:
            df['ano_mes'] = pd.to_datetime(df[col_mes] + '-01')
            df['mes'] = df['ano_mes'].dt.month
            df['trimestre'] = df['ano_mes'].dt.quarter
            
            # Seasonal indicators
            df['is_q4'] = (df['trimestre'] == 4).astype(int)  # Dec quarter (13th salary)
            df['is_q1'] = (df['trimestre'] == 1).astype(int)  # Jan quarter
        
        return df
    
    def _calcular_tendencia(
        self,
        valores: List[float]
    ) -> Tuple[float, float]:
        """
        Calculate trend from historical values.
        
        Args:
            valores: List of historical values
            
        Returns:
            Tuple of (slope, r_squared)
        """
        if len(valores) < 2:
            return 0.0, 0.0
        
        x = np.arange(len(valores))
        y = np.array(valores)
        
        # Simple linear regression
        x_mean = x.mean()
        y_mean = y.mean()
        
        numerator = ((x - x_mean) * (y - y_mean)).sum()
        denominator = ((x - x_mean) ** 2).sum()
        
        if denominator == 0:
            return 0.0, 0.0
        
        slope = numerator / denominator
        
        # R-squared
        y_pred = y_mean + slope * (x - x_mean)
        ss_res = ((y - y_pred) ** 2).sum()
        ss_tot = ((y - y_mean) ** 2).sum()
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return slope, max(0, r_squared)
    
    def prever_utilizacao(
        self,
        cliente_id: str,
        produto: str,
        historico_utilizacao: List[float],
        historico_meses: int = 12,
        propensao: float = 50,
        prinad: float = 20
    ) -> float:
        """
        Predict next quarter utilization.
        
        Args:
            cliente_id: Client identifier
            produto: Product name
            historico_utilizacao: List of historical utilization rates (0-1)
            historico_meses: Number of months of history
            propensao: Propensity score
            prinad: PRINAD score
            
        Returns:
            Predicted utilization rate (0-1)
        """
        if not historico_utilizacao:
            # No history: use propensity as proxy
            return propensao / 100 * 0.3  # Conservative estimate
        
        # Calculate trend
        slope, r_sq = self._calcular_tendencia(historico_utilizacao)
        
        # Last value
        ultimo = historico_utilizacao[-1]
        
        # Average last 3 months
        media_recente = np.mean(historico_utilizacao[-3:])
        
        # Predict: weighted combination
        # If strong trend (high R²), weight slope more
        # Otherwise, weight recent average more
        if r_sq > 0.7:
            # Strong trend
            previsao = ultimo + slope * 3  # Project 3 months ahead
        else:
            # Use recent average with propensity adjustment
            propensao_factor = propensao / 100
            previsao = media_recente * 0.6 + propensao_factor * 0.4
        
        # Clamp to valid range
        previsao = max(0, min(1, previsao))
        
        # Adjust for high risk clients
        if prinad > 70:
            # High risk clients might not be able to use credit
            previsao = previsao * 0.5
        
        return previsao
    
    def prever_acao_limite(
        self,
        cliente_id: str,
        produto: str,
        limite_atual: float,
        historico_utilizacao: List[float],
        propensao: float,
        prinad: float,
        trimestres_sem_uso: int
    ) -> PrevisaoLimite:
        """
        Predict limit action for next quarter.
        
        Args:
            cliente_id: Client identifier
            produto: Product name
            limite_atual: Current limit
            historico_utilizacao: Historical utilization rates
            propensao: Propensity score
            prinad: PRINAD risk score
            trimestres_sem_uso: Quarters without utilization
            
        Returns:
            PrevisaoLimite with prediction details
        """
        # Predict utilization
        utilizacao_prevista = self.prever_utilizacao(
            cliente_id, produto, historico_utilizacao,
            propensao=propensao, prinad=prinad
        )
        
        # Determine action
        if prinad >= 90:
            acao = 'zerar'
            limite_previsto = 0
            confianca = 0.95
        elif trimestres_sem_uso >= 1 and utilizacao_prevista < 0.1:
            # Low predicted use + history of no use
            acao = 'reduzir'
            limite_previsto = limite_atual * LIMITE_MINIMO_PERCENTUAL
            confianca = 0.70 + min(0.25, trimestres_sem_uso * 0.05)
        elif utilizacao_prevista > 0.8 and prinad < 35:
            # High predicted use + good risk
            acao = 'aumentar'
            limite_previsto = limite_atual * 1.20
            confianca = 0.60
        else:
            acao = 'manter'
            limite_previsto = limite_atual
            confianca = 0.80
        
        # Calculate days to application (quarterly cycle)
        hoje = datetime.now()
        proximo_trimestre = ((hoje.month - 1) // 3 + 1) * 3 + 1
        if proximo_trimestre > 12:
            proximo_trimestre = 1
            ano = hoje.year + 1
        else:
            ano = hoje.year
        
        data_aplicacao = datetime(ano, proximo_trimestre, 1)
        dias_para_aplicacao = (data_aplicacao - hoje).days
        
        return PrevisaoLimite(
            cliente_id=cliente_id,
            produto=produto,
            limite_atual=limite_atual,
            utilizacao_prevista=utilizacao_prevista,
            limite_previsto=limite_previsto,
            acao_prevista=acao,
            confianca=confianca,
            dias_para_aplicacao=max(0, dias_para_aplicacao)
        )
    
    def gerar_lista_notificacao(
        self,
        previsoes: List[PrevisaoLimite],
        horizonte_dias: int = 60
    ) -> ListaNotificacao:
        """
        Generate notification list for clients with predicted reductions.
        
        Args:
            previsoes: List of limit predictions
            horizonte_dias: Notification horizon (60 or 30)
            
        Returns:
            ListaNotificacao with filtered clients
        """
        # Filter by horizon and action
        clientes_notificar = []
        economia_total = 0
        
        for prev in previsoes:
            # Only include if within horizon and action is reduce
            if prev.dias_para_aplicacao <= horizonte_dias:
                if prev.acao_prevista == 'reduzir':
                    clientes_notificar.append(prev)
                    # Rough ECL economy
                    reducao = prev.limite_atual - prev.limite_previsto
                    economia_total += reducao * 0.15  # ~15% PD×LGD
        
        return ListaNotificacao(
            data_geracao=datetime.now(),
            horizonte_dias=horizonte_dias,
            clientes=clientes_notificar,
            total_reducoes=len([p for p in previsoes if p.acao_prevista == 'reduzir']),
            total_aumentos=len([p for p in previsoes if p.acao_prevista == 'aumentar']),
            economia_ecl_estimada=economia_total
        )
    
    def verificar_cancelamento_reducao(
        self,
        cliente_id: str,
        produto: str,
        utilizacao_atual: float
    ) -> bool:
        """
        Check if a reduction should be cancelled due to recent usage.
        
        Args:
            cliente_id: Client identifier
            produto: Product name
            utilizacao_atual: Current utilization rate
            
        Returns:
            True if reduction should be cancelled
        """
        # If client used the limit, cancel reduction
        if utilizacao_atual > 0:
            logger.info(
                f"Reduction cancelled for {cliente_id}/{produto}: "
                f"utilization detected ({utilizacao_atual:.1%})"
            )
            return True
        return False


# Module-level instance
_limit_predictor: Optional[LimitPredictor] = None


def get_limit_predictor() -> LimitPredictor:
    """Get or create limit predictor instance."""
    global _limit_predictor
    if _limit_predictor is None:
        _limit_predictor = LimitPredictor()
    return _limit_predictor


if __name__ == "__main__":
    predictor = LimitPredictor()
    
    # Example prediction
    previsao = predictor.prever_acao_limite(
        cliente_id="12345678901",
        produto="consignado",
        limite_atual=50000,
        historico_utilizacao=[0.0, 0.0, 0.0, 0.05, 0.0, 0.0],  # Low usage
        propensao=25,  # Low propensity
        prinad=15,
        trimestres_sem_uso=2
    )
    
    print("=" * 60)
    print("Limit Prediction Example")
    print("=" * 60)
    print(f"Cliente: {previsao.cliente_id}")
    print(f"Produto: {previsao.produto}")
    print(f"Limite atual: R$ {previsao.limite_atual:,.2f}")
    print(f"Utilização prevista: {previsao.utilizacao_prevista:.1%}")
    print(f"Ação prevista: {previsao.acao_prevista}")
    print(f"Limite previsto: R$ {previsao.limite_previsto:,.2f}")
    print(f"Confiança: {previsao.confianca:.0%}")
    print(f"Dias para aplicação: {previsao.dias_para_aplicacao}")
