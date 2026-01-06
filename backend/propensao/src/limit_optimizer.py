"""
Limit Optimizer - Dynamic credit limit allocation.

Optimizes credit limits based on:
- Propensity scores
- PRINAD risk scores  
- Income commitment constraints
- Quarterly utilization patterns
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    PRODUTOS_CREDITO,
    LIMITE_MAXIMO_MULTIPLO,
    COMPROMETIMENTO_MAXIMO_RENDA,
    LIMITE_MINIMO_PERCENTUAL,
    COMPROMETIMENTO_GATILHO_MAXDEBT,
    calcular_comprometimento_renda,
    calcular_limite_maximo_produto,
    setup_logging
)

logger = setup_logging(__name__)


class AcaoLimite(Enum):
    """Recommended limit actions."""
    MANTER = "manter"
    AUMENTAR = "aumentar"
    REDUZIR = "reduzir"
    ZERAR = "zerar"


@dataclass
class RecomendacaoLimite:
    """Limit recommendation for a client/product."""
    cliente_id: str
    produto: str
    limite_atual: float
    limite_recomendado: float
    acao: AcaoLimite
    motivo: str
    propensao: float
    prinad: float
    trimestres_sem_uso: int


@dataclass
class ClienteLimites:
    """Complete limit profile for a client."""
    cliente_id: str
    renda_bruta: float
    comprometimento_atual: float
    recomendacoes: List[RecomendacaoLimite]
    economia_ecl_estimada: float
    notificar: bool
    motivo_notificacao: Optional[str] = None


class LimitOptimizer:
    """
    Optimizes credit limits following business rules.
    
    Rules:
    - Minimum limit: 30% of original
    - Maximum income commitment: 70%
    - PRINAD D rating: Zero limit
    - Max-debt clients (≥65%): Reduce unused limits (except credit card)
    - No utilization in quarter: Candidate for reduction
    """
    
    # Thresholds
    PROPENSAO_ALTA = 70
    PROPENSAO_BAIXA = 30
    PRINAD_D_THRESHOLD = 90  # PRINAD ≥ 90% = Rating D
    UTILIZACAO_ALTA = 0.80  # >80% = increase candidate
    
    def __init__(self):
        """Initialize limit optimizer."""
        logger.info("LimitOptimizer initialized")
    
    def avaliar_cliente_maxdebt(
        self,
        comprometimento: float,
        limites: Dict[str, float],
        utilizacao: Dict[str, float]
    ) -> Dict[str, Tuple[AcaoLimite, str]]:
        """
        Evaluate max-debt clients (≥65% income commitment).
        Unused limits should be reduced (except credit card).
        
        Args:
            comprometimento: Current income commitment ratio
            limites: Dict of produto -> current limit
            utilizacao: Dict of produto -> utilization rate
            
        Returns:
            Dict of produto -> (action, reason)
        """
        acoes = {}
        
        if comprometimento < COMPROMETIMENTO_GATILHO_MAXDEBT:
            return acoes  # Not a max-debt client
        
        for produto, limite in limites.items():
            # Credit card is exception (revolving credit)
            if produto in ['cartao_credito_rotativo', 'cartao_credito_parcelado', 
                          'cheque_especial', 'cartao_credito']:
                acoes[produto] = (AcaoLimite.MANTER, "Crédito rotativo mantido")
                continue
            
            # Check utilization
            uso = utilizacao.get(produto, 0)
            
            if uso == 0 and limite > 0:
                # Unused limit on max-debt client → reduce
                novo_limite = limite * LIMITE_MINIMO_PERCENTUAL
                acoes[produto] = (
                    AcaoLimite.REDUZIR,
                    f"Cliente no limite de endividamento ({comprometimento:.0%}), "
                    f"limite não utilizado deve ser reduzido"
                )
            else:
                acoes[produto] = (AcaoLimite.MANTER, "Limite em uso")
        
        return acoes
    
    def avaliar_propensao(
        self,
        produto: str,
        propensao: float,
        prinad: float,
        trimestres_sem_uso: int,
        limite_atual: float
    ) -> Tuple[AcaoLimite, float, str]:
        """
        Evaluate limit action based on propensity and risk.
        
        Args:
            produto: Product name
            propensao: Propensity score (0-100)
            prinad: PRINAD score (0-100)
            trimestres_sem_uso: Quarters without utilization
            limite_atual: Current limit
            
        Returns:
            Tuple of (action, new_limit, reason)
        """
        # Rule 1: PRINAD D = Zero limit
        if prinad >= self.PRINAD_D_THRESHOLD:
            return (
                AcaoLimite.ZERAR,
                0,
                f"Cliente em default iminente (PRINAD {prinad:.0f}%)"
            )
        
        # Rule 2: No utilization for 1+ quarter
        if trimestres_sem_uso >= 1 and propensao < self.PROPENSAO_BAIXA:
            novo_limite = limite_atual * LIMITE_MINIMO_PERCENTUAL
            return (
                AcaoLimite.REDUZIR,
                novo_limite,
                f"Sem uso há {trimestres_sem_uso} trimestre(s) e baixa propensão ({propensao:.0f}%)"
            )
        
        # Rule 3: High propensity + good risk = increase
        if propensao >= self.PROPENSAO_ALTA and prinad < 35:
            # Increase by 20%
            novo_limite = limite_atual * 1.20
            return (
                AcaoLimite.AUMENTAR,
                novo_limite,
                f"Alta propensão ({propensao:.0f}%) e bom risco (PRINAD {prinad:.0f}%)"
            )
        
        # Default: maintain
        return (
            AcaoLimite.MANTER,
            limite_atual,
            "Perfil estável"
        )
    
    def aplicar_constraints(
        self,
        recomendacoes: List[RecomendacaoLimite],
        renda_bruta: float,
        parcelas_atuais: float
    ) -> List[RecomendacaoLimite]:
        """
        Apply global constraints (70% income commitment).
        
        Args:
            recomendacoes: List of recommendations
            renda_bruta: Gross income
            parcelas_atuais: Current monthly installments
            
        Returns:
            Adjusted recommendations
        """
        if renda_bruta <= 0:
            return recomendacoes
        
        # Calculate maximum available for new commitments
        max_parcelas = renda_bruta * COMPROMETIMENTO_MAXIMO_RENDA
        margem_disponivel = max_parcelas - parcelas_atuais
        
        # Adjust increases if exceeding limit
        for rec in recomendacoes:
            if rec.acao == AcaoLimite.AUMENTAR:
                # Check if increase would exceed commitment limit
                limite_maximo = calcular_limite_maximo_produto(rec.produto, renda_bruta)
                rec.limite_recomendado = min(rec.limite_recomendado, limite_maximo)
        
        return recomendacoes
    
    def otimizar_cliente(
        self,
        cliente_id: str,
        renda_bruta: float,
        parcelas_mensais: float,
        limites: Dict[str, float],
        propensoes: Dict[str, float],
        prinad: float,
        utilizacao_trimestral: Dict[str, int]
    ) -> ClienteLimites:
        """
        Generate limit optimization for a client.
        
        Args:
            cliente_id: Client identifier
            renda_bruta: Gross income
            parcelas_mensais: Current monthly installments
            limites: Current limits by product
            propensoes: Propensity scores by product
            prinad: PRINAD risk score
            utilizacao_trimestral: Quarters without use by product
            
        Returns:
            ClienteLimites with all recommendations
        """
        comprometimento = calcular_comprometimento_renda(parcelas_mensais, renda_bruta)
        recomendacoes = []
        economia_total = 0
        notificar = False
        motivo_notificacao = None
        
        # Check max-debt rule first
        utilizacao = {p: 1 if utilizacao_trimestral.get(p, 0) == 0 else 0 
                      for p in limites}
        acoes_maxdebt = self.avaliar_cliente_maxdebt(
            comprometimento, limites, utilizacao
        )
        
        for produto in PRODUTOS_CREDITO:
            limite_atual = limites.get(produto, 0)
            propensao = propensoes.get(produto, 50)
            trimestres_sem = utilizacao_trimestral.get(produto, 0)
            
            # Check if max-debt rule applies
            if produto in acoes_maxdebt:
                acao, motivo = acoes_maxdebt[produto]
                if acao == AcaoLimite.REDUZIR:
                    novo_limite = limite_atual * LIMITE_MINIMO_PERCENTUAL
                else:
                    novo_limite = limite_atual
            else:
                # Regular evaluation
                acao, novo_limite, motivo = self.avaliar_propensao(
                    produto, propensao, prinad, trimestres_sem, limite_atual
                )
            
            rec = RecomendacaoLimite(
                cliente_id=cliente_id,
                produto=produto,
                limite_atual=limite_atual,
                limite_recomendado=novo_limite,
                acao=acao,
                motivo=motivo,
                propensao=propensao,
                prinad=prinad,
                trimestres_sem_uso=trimestres_sem
            )
            recomendacoes.append(rec)
            
            # Calculate ECL economy estimate (simplified)
            if acao in [AcaoLimite.REDUZIR, AcaoLimite.ZERAR]:
                reducao = limite_atual - novo_limite
                # Rough ECL estimate: PD × LGD × reduction
                pd_estimate = prinad / 100
                lgd_estimate = 0.40  # Average LGD
                economia_total += pd_estimate * lgd_estimate * reducao
                
                # Flag for notification
                if acao == AcaoLimite.REDUZIR:
                    notificar = True
                    motivo_notificacao = f"Previsão de redução de limite para {produto}"
        
        # Apply constraints
        recomendacoes = self.aplicar_constraints(
            recomendacoes, renda_bruta, parcelas_mensais
        )
        
        return ClienteLimites(
            cliente_id=cliente_id,
            renda_bruta=renda_bruta,
            comprometimento_atual=comprometimento,
            recomendacoes=recomendacoes,
            economia_ecl_estimada=economia_total,
            notificar=notificar,
            motivo_notificacao=motivo_notificacao
        )
    
    def gerar_lista_notificacao(
        self,
        clientes_limites: List[ClienteLimites]
    ) -> pd.DataFrame:
        """
        Generate notification list for clients with limit reductions.
        
        Args:
            clientes_limites: List of client limit profiles
            
        Returns:
            DataFrame with notification details
        """
        notificacoes = []
        
        for cliente in clientes_limites:
            if not cliente.notificar:
                continue
            
            for rec in cliente.recomendacoes:
                if rec.acao == AcaoLimite.REDUZIR:
                    notificacoes.append({
                        'cliente_id': cliente.cliente_id,
                        'produto': rec.produto,
                        'limite_atual': rec.limite_atual,
                        'limite_futuro': rec.limite_recomendado,
                        'reducao_percentual': 1 - (rec.limite_recomendado / rec.limite_atual) if rec.limite_atual > 0 else 0,
                        'motivo': rec.motivo,
                        'canal_notificacao': 'push,sms,banner'
                    })
        
        return pd.DataFrame(notificacoes)


# Module-level instance
_limit_optimizer: Optional[LimitOptimizer] = None


def get_limit_optimizer() -> LimitOptimizer:
    """Get or create limit optimizer instance."""
    global _limit_optimizer
    if _limit_optimizer is None:
        _limit_optimizer = LimitOptimizer()
    return _limit_optimizer


if __name__ == "__main__":
    # Example usage
    optimizer = LimitOptimizer()
    
    result = optimizer.otimizar_cliente(
        cliente_id="12345678901",
        renda_bruta=10000,
        parcelas_mensais=5000,  # 50% committed
        limites={
            'consignado': 100000,
            'banparacard': 30000,
            'cartao_credito': 15000,
            'cred_veiculo': 50000
        },
        propensoes={
            'consignado': 80,
            'banparacard': 20,
            'cartao_credito': 60,
            'cred_veiculo': 15
        },
        prinad=12.5,
        utilizacao_trimestral={
            'consignado': 0,
            'banparacard': 2,  # 2 quarters without use
            'cartao_credito': 0,
            'cred_veiculo': 3
        }
    )
    
    print("=" * 60)
    print(f"Cliente: {result.cliente_id}")
    print(f"Renda: R$ {result.renda_bruta:,.2f}")
    print(f"Comprometimento: {result.comprometimento_atual:.1%}")
    print(f"Economia ECL estimada: R$ {result.economia_ecl_estimada:,.2f}")
    print(f"Notificar: {result.notificar}")
    print("=" * 60)
    
    for rec in result.recomendacoes:
        print(f"\n{rec.produto}:")
        print(f"  Ação: {rec.acao.value}")
        print(f"  Limite: R$ {rec.limite_atual:,.2f} → R$ {rec.limite_recomendado:,.2f}")
        print(f"  Motivo: {rec.motivo}")
