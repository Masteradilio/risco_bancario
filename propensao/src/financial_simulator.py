"""
Financial Simulator - Simulates financial impact of model implementation.

Projects ECL savings, capital liberation, and ROE impact under
different scenarios for executive decision-making.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    PRODUTOS_CREDITO,
    LGD_POR_PRODUTO,
    LIMITE_MINIMO_PERCENTUAL,
    COMPROMETIMENTO_GATILHO_MAXDEBT,
    setup_logging
)

logger = setup_logging(__name__)


class CenarioTipo(Enum):
    """Scenario types for simulation."""
    CONSERVADOR = "conservador"
    MODERADO = "moderado"
    OTIMISTA = "otimista"


@dataclass
class ParametrosCenario:
    """Parameters for a simulation scenario."""
    nome: str
    tipo: CenarioTipo
    reducao_limites_inativos: float  # % reduction
    aumento_alta_propensao: float  # % increase
    threshold_propensao_alta: float  # Score threshold
    threshold_utilizacao_baixa: float  # Utilization threshold
    descricao: str


@dataclass 
class ResultadoSimulacao:
    """Results of a financial simulation."""
    cenario: str
    # ECL
    ecl_atual: float
    ecl_projetado: float
    economia_ecl: float
    economia_ecl_percentual: float
    # Limits
    limite_atual: float
    limite_projetado: float
    reducao_limite: float
    # Capital
    capital_liberado: float
    capital_liberado_percentual: float
    # ROE
    roe_atual: float
    roe_projetado: float
    impacto_roe_pp: float
    # Revenue
    receita_credito_atual: float
    receita_credito_projetada: float
    impacto_receita: float
    # Risk
    inadimplencia_atual: float
    inadimplencia_projetada: float
    # Details
    clientes_afetados: int
    clientes_notificados: int


@dataclass
class RelatorioImpacto:
    """Complete impact report for executive presentation."""
    data_simulacao: str
    baseline_trimestre: str
    resultados: List[ResultadoSimulacao]
    recomendacao: str
    metricas_banco: Dict[str, float]


class FinancialSimulator:
    """
    Simulates financial impact of credit limit optimization.
    
    Uses quarterly data from Banco do Pará as baseline:
    - 1T2025: Inadimplência 2.00%, Carteira R$ 14.6B
    - 2T2025: Inadimplência 2.51%, Carteira R$ 15.2B
    - 3T2025: Inadimplência 2.60%, Carteira R$ 15.8B, Provisão R$ 533M
    """
    
    # Baseline from Banco do Pará quarterly reports
    BASELINE = {
        '1T2025': {
            'carteira_credito': 14_626_621_000,  # R$ 14.6 bilhões
            'provisao_pcld': 531_336_000,         # R$ 531 milhões
            'inadimplencia': 0.0200,               # 2.00%
            'roe': 0.165,                          # 16.5% (estimate)
            'spread_medio': 0.08,                  # 8% a.a.
        },
        '2T2025': {
            'carteira_credito': 15_200_000_000,
            'provisao_pcld': 545_000_000,
            'inadimplencia': 0.0251,
            'roe': 0.158,
            'spread_medio': 0.08,
        },
        '3T2025': {
            'carteira_credito': 15_800_000_000,
            'provisao_pcld': 533_530_000,
            'inadimplencia': 0.0260,
            'roe': 0.162,
            'spread_medio': 0.08,
        }
    }
    
    # Scenario configurations
    CENARIOS = {
        CenarioTipo.CONSERVADOR: ParametrosCenario(
            nome="Conservador",
            tipo=CenarioTipo.CONSERVADOR,
            reducao_limites_inativos=0.70,  # Reduce to 30%
            aumento_alta_propensao=0.00,     # No increase
            threshold_propensao_alta=85,
            threshold_utilizacao_baixa=0.05,
            descricao=(
                "Cenário conservador: apenas redução de limites inativos "
                "para o mínimo de 30%, sem aumentos para clientes de alta propensão."
            )
        ),
        CenarioTipo.MODERADO: ParametrosCenario(
            nome="Moderado",
            tipo=CenarioTipo.MODERADO,
            reducao_limites_inativos=0.50,   # Reduce to 50%
            aumento_alta_propensao=0.15,     # 15% increase
            threshold_propensao_alta=75,
            threshold_utilizacao_baixa=0.10,
            descricao=(
                "Cenário moderado: limites inativos reduzidos para 50%, "
                "com aumento de 15% para clientes de alta propensão e baixo risco."
            )
        ),
        CenarioTipo.OTIMISTA: ParametrosCenario(
            nome="Otimista",
            tipo=CenarioTipo.OTIMISTA,
            reducao_limites_inativos=0.70,   # Reduce to 30%
            aumento_alta_propensao=0.25,     # 25% increase
            threshold_propensao_alta=70,
            threshold_utilizacao_baixa=0.15,
            descricao=(
                "Cenário otimista: redução agressiva de inativos para 30%, "
                "com aumento de 25% para alta propensão, maximizando eficiência de capital."
            )
        )
    }
    
    def __init__(self, trimestre_base: str = '3T2025'):
        """
        Initialize financial simulator.
        
        Args:
            trimestre_base: Baseline quarter for calculations
        """
        self.trimestre_base = trimestre_base
        self.baseline = self.BASELINE.get(trimestre_base, self.BASELINE['3T2025'])
        logger.info(f"FinancialSimulator initialized with {trimestre_base} baseline")
    
    def calcular_ecl_portfolio(
        self,
        limite_total: float,
        pd_medio: float,
        lgd_medio: float = 0.40
    ) -> float:
        """
        Calculate portfolio ECL.
        
        Args:
            limite_total: Total credit limit (EAD)
            pd_medio: Average probability of default
            lgd_medio: Average loss given default
            
        Returns:
            ECL value
        """
        return limite_total * pd_medio * lgd_medio
    
    def simular_cenario(
        self,
        cenario: CenarioTipo,
        pct_limites_inativos: float = 0.15,
        pct_alta_propensao: float = 0.20,
        prinad_medio: float = 0.15
    ) -> ResultadoSimulacao:
        """
        Simulate a scenario for executive decision-making.
        
        Args:
            cenario: Scenario type
            pct_limites_inativos: % of portfolio with inactive limits
            pct_alta_propensao: % of portfolio with high propensity
            prinad_medio: Average PRINAD (default probability)
            
        Returns:
            ResultadoSimulacao with financial projections
        """
        params = self.CENARIOS[cenario]
        base = self.baseline
        
        carteira = base['carteira_credito']
        provisao_atual = base['provisao_pcld']
        inadimplencia = base['inadimplencia']
        roe_atual = base['roe']
        
        # Current state
        limite_inativo = carteira * pct_limites_inativos
        limite_alta_propensao = carteira * pct_alta_propensao
        
        # Calculate ECL reduction from inactive limit reduction
        reducao_inativos = limite_inativo * params.reducao_limites_inativos
        ecl_economizado_inativos = reducao_inativos * prinad_medio * 0.40  # LGD médio
        
        # Calculate ECL from high propensity increase
        aumento_propensao = limite_alta_propensao * params.aumento_alta_propensao
        # High propensity clients have lower default (50% of average)
        ecl_adicional_propensao = aumento_propensao * (prinad_medio * 0.5) * 0.40
        
        # Net ECL impact
        ecl_atual = provisao_atual
        economia_ecl = ecl_economizado_inativos - ecl_adicional_propensao
        ecl_projetado = ecl_atual - economia_ecl
        
        # Limit changes
        limite_atual = carteira
        limite_projetado = carteira - reducao_inativos + aumento_propensao
        reducao_limite = reducao_inativos - aumento_propensao
        
        # Capital liberation (simplified: 8% of ECL reduction as capital)
        capital_liberado = economia_ecl * 0.12  # 12% capital requirement
        capital_pct = capital_liberado / carteira
        
        # ROE impact
        # More capital efficiency = higher ROE
        receita_atual = carteira * base['spread_medio']
        patrimonio = carteira * 0.10  # 10% equity ratio
        
        # Additional revenue from high propensity increases
        receita_adicional = aumento_propensao * base['spread_medio'] * 0.8  # 80% utilization
        
        receita_projetada = receita_atual + receita_adicional
        patrimonio_novo = patrimonio - capital_liberado  # Less capital required
        
        roe_projetado = (receita_projetada * 0.30) / patrimonio_novo  # 30% margin
        impacto_roe = (roe_projetado - roe_atual) * 100  # in percentage points
        
        # Inadimplência projection
        # Reducing inactive limits doesn't change default rate
        # Increasing high propensity (low risk) slightly improves portfolio
        inadimplencia_projetada = inadimplencia * (1 - pct_alta_propensao * 0.05)
        
        # Affected clients (simplified estimate)
        clientes_afetados = int(pct_limites_inativos * 200_000)  # 200k clients
        clientes_notificados = int(clientes_afetados * 0.7)  # 70% will be notified
        
        return ResultadoSimulacao(
            cenario=params.nome,
            ecl_atual=ecl_atual,
            ecl_projetado=ecl_projetado,
            economia_ecl=economia_ecl,
            economia_ecl_percentual=economia_ecl / ecl_atual if ecl_atual > 0 else 0,
            limite_atual=limite_atual,
            limite_projetado=limite_projetado,
            reducao_limite=reducao_limite,
            capital_liberado=capital_liberado,
            capital_liberado_percentual=capital_pct,
            roe_atual=roe_atual,
            roe_projetado=roe_projetado,
            impacto_roe_pp=impacto_roe,
            receita_credito_atual=receita_atual,
            receita_credito_projetada=receita_projetada,
            impacto_receita=receita_projetada - receita_atual,
            inadimplencia_atual=inadimplencia,
            inadimplencia_projetada=inadimplencia_projetada,
            clientes_afetados=clientes_afetados,
            clientes_notificados=clientes_notificados
        )
    
    def simular_todos_cenarios(
        self,
        pct_limites_inativos: float = 0.15,
        pct_alta_propensao: float = 0.20
    ) -> RelatorioImpacto:
        """
        Simulate all scenarios and generate executive report.
        
        Args:
            pct_limites_inativos: % portfolio inactive
            pct_alta_propensao: % portfolio high propensity
            
        Returns:
            RelatorioImpacto for board presentation
        """
        from datetime import datetime
        
        resultados = []
        for cenario_tipo in CenarioTipo:
            resultado = self.simular_cenario(
                cenario_tipo,
                pct_limites_inativos,
                pct_alta_propensao
            )
            resultados.append(resultado)
        
        # Recommend based on results
        moderado = resultados[1]  # Moderate scenario
        if moderado.economia_ecl > 50_000_000 and moderado.impacto_roe_pp > 0.5:
            recomendacao = (
                f"✅ RECOMENDAÇÃO: Implementar cenário MODERADO. "
                f"Projeção de economia de R$ {moderado.economia_ecl/1e6:.1f} milhões em ECL "
                f"com impacto positivo de {moderado.impacto_roe_pp:.2f} p.p. no ROE."
            )
        else:
            recomendacao = (
                f"⚠️ RECOMENDAÇÃO: Implementar cenário CONSERVADOR com monitoramento. "
                f"Projeção de economia de R$ {resultados[0].economia_ecl/1e6:.1f} milhões "
                f"com risco controlado."
            )
        
        return RelatorioImpacto(
            data_simulacao=datetime.now().strftime('%Y-%m-%d'),
            baseline_trimestre=self.trimestre_base,
            resultados=resultados,
            recomendacao=recomendacao,
            metricas_banco=self.baseline
        )
    
    def exportar_relatorio_markdown(
        self,
        relatorio: RelatorioImpacto,
        output_path: Path
    ) -> Path:
        """Export impact report to markdown for executive presentation."""
        def fmt_money(v):
            if abs(v) >= 1e9:
                return f"R$ {v/1e9:.2f} bi"
            elif abs(v) >= 1e6:
                return f"R$ {v/1e6:.1f} mi"
            else:
                return f"R$ {v/1e3:.0f} mil"
        
        lines = [
            "# Relatório de Impacto Financeiro - Modelo PROLIMITE",
            f"*Simulação: {relatorio.data_simulacao} | Baseline: {relatorio.baseline_trimestre}*",
            "",
            "---",
            "",
            "## Sumário Executivo",
            "",
            relatorio.recomendacao,
            "",
            "## Baseline do Banco",
            "",
            f"- **Carteira de Crédito**: {fmt_money(relatorio.metricas_banco['carteira_credito'])}",
            f"- **Provisão PCLD**: {fmt_money(relatorio.metricas_banco['provisao_pcld'])}",
            f"- **Inadimplência**: {relatorio.metricas_banco['inadimplencia']:.2%}",
            f"- **ROE**: {relatorio.metricas_banco['roe']:.1%}",
            "",
            "---",
            "",
            "## Comparativo de Cenários",
            "",
            "| Métrica | Conservador | Moderado | Otimista |",
            "|---------|-------------|----------|----------|",
        ]
        
        # Build comparison table
        metricas = [
            ('Economia ECL', lambda r: fmt_money(r.economia_ecl)),
            ('% Economia ECL', lambda r: f"{r.economia_ecl_percentual:.1%}"),
            ('Capital Liberado', lambda r: fmt_money(r.capital_liberado)),
            ('Impacto ROE', lambda r: f"+{r.impacto_roe_pp:.2f} p.p."),
            ('Receita Adicional', lambda r: fmt_money(r.impacto_receita)),
            ('Inadimplência', lambda r: f"{r.inadimplencia_projetada:.2%}"),
            ('Clientes Notificados', lambda r: f"{r.clientes_notificados:,}"),
        ]
        
        for nome, fn in metricas:
            linha = f"| {nome} | "
            linha += " | ".join(fn(r) for r in relatorio.resultados)
            linha += " |"
            lines.append(linha)
        
        lines.extend([
            "",
            "---",
            "",
            "## Detalhamento por Cenário",
            ""
        ])
        
        for r in relatorio.resultados:
            params = self.CENARIOS[CenarioTipo(r.cenario.lower())]
            lines.extend([
                f"### Cenário {r.cenario}",
                "",
                params.descricao,
                "",
                f"**Impacto Projetado:**",
                f"- ECL: {fmt_money(r.ecl_atual)} → {fmt_money(r.ecl_projetado)} "
                f"(economia: {fmt_money(r.economia_ecl)})",
                f"- ROE: {r.roe_atual:.1%} → {r.roe_projetado:.1%} "
                f"({'+' if r.impacto_roe_pp > 0 else ''}{r.impacto_roe_pp:.2f} p.p.)",
                f"- Receita adicional: {fmt_money(r.impacto_receita)}",
                f"- Clientes afetados: {r.clientes_afetados:,}",
                ""
            ])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Impact report exported to {output_path}")
        return output_path


# Module-level instance
_financial_simulator: Optional[FinancialSimulator] = None


def get_financial_simulator() -> FinancialSimulator:
    """Get or create financial simulator instance."""
    global _financial_simulator
    if _financial_simulator is None:
        _financial_simulator = FinancialSimulator()
    return _financial_simulator


if __name__ == "__main__":
    simulator = FinancialSimulator('3T2025')
    
    relatorio = simulator.simular_todos_cenarios(
        pct_limites_inativos=0.15,
        pct_alta_propensao=0.20
    )
    
    print("=" * 70)
    print("SIMULAÇÃO DE IMPACTO FINANCEIRO - PROLIMITE")
    print("=" * 70)
    print(f"\nBaseline: {relatorio.baseline_trimestre}")
    print(f"\n{relatorio.recomendacao}")
    print("\n" + "=" * 70)
    
    for r in relatorio.resultados:
        print(f"\n{r.cenario}:")
        print(f"  Economia ECL: R$ {r.economia_ecl/1e6:.1f} milhões")
        print(f"  Impacto ROE: +{r.impacto_roe_pp:.2f} p.p.")
        print(f"  Clientes notificados: {r.clientes_notificados:,}")
