"""
Limit Reallocation - Dynamic Limit Management Based on Propensity

This module implements:
1. Fixed Global Limit calculation (based on income, only changes when income changes)
2. Per-product limit allocation within the 70% commitment ceiling
3. Propensity-based reallocation (move limits from low to high propensity products)
4. Integration with ECL optimization (reduce EAD for low propensity → reduce ECL)

Key Concepts:
- Global Limit: Maximum theoretical credit capacity (FIXED based on income)
- Product Limits: Individual limits respecting group rules (A/B/C)
- Reallocation: Dynamic adjustment based on propensity scores
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    COMPROMETIMENTO_MAXIMO_RENDA,
    PARAMS_LIMITE_GLOBAL,
    MAX_COMPROMETIMENTO_PRODUTO,
    PRODUTOS_FORA_LIMITE_GLOBAL,
    PROPENSAO_MINIMA_PARA_AUMENTO,
    PROPENSAO_MAXIMA_PARA_REDUCAO,
    PROPENSAO_CLASSIFICACAO,
    calcular_limite_global_fixo,
    setup_logging
)

logger = setup_logging(__name__)


@dataclass
class LimiteGlobal:
    """Global limit calculation result."""
    renda_bruta: float
    limite_global: float
    limite_grupo_a: float  # Consignado, Banparacard, Pessoal
    limite_grupo_b: float  # Imobiliário
    limite_grupo_c: float  # Veículo, Solar
    comprometimento_max: float = 0.70
    data_calculo: datetime = field(default_factory=datetime.now)
    detalhes: Dict = field(default_factory=dict)


@dataclass
class LimiteProduto:
    """Individual product limit."""
    produto: str
    grupo: str
    limite_calculado: float
    limite_alocado: float
    comprometimento_max: float
    parcela_max: float
    prazo_meses: int
    taxa_mensal: float
    propensao_score: Optional[float] = None
    propensao_class: Optional[str] = None


@dataclass
class RealocacaoResultado:
    """Result of propensity-based reallocation."""
    cliente_id: str
    renda_bruta: float
    comprometimento_atual: float
    comprometimento_disponivel: float
    limites_antes: Dict[str, float]
    limites_depois: Dict[str, float]
    variacoes: Dict[str, float]
    ecl_antes: Optional[float] = None
    ecl_depois: Optional[float] = None
    ecl_economia: Optional[float] = None
    data_calculo: datetime = field(default_factory=datetime.now)
    observacoes: List[str] = field(default_factory=list)


class LimitReallocation:
    """
    Limit Reallocation Engine
    
    Manages credit limits based on:
    1. Fixed Global Limit (based on maximum theoretical capacity)
    2. Per-product limits within groups
    3. Propensity-based reallocation
    
    Key Rules:
    - Global limit only changes when income changes
    - Products compete within their group (A/B/C)
    - Total commitment cannot exceed 70%
    - Consignado 35% is a LEGAL limit (cannot exceed even with reallocation)
    - Propensity drives reallocation (not limit reduction for risk)
    """
    
    # Minimum propensity to keep full limit
    PROPENSAO_MINIMA_MANTER = 40
    
    # Propensity threshold for reduction
    PROPENSAO_THRESHOLD_REDUCAO = 30
    
    # Maximum reduction factor for low propensity
    FATOR_REDUCAO_MAX = 0.50  # Reduce by up to 50%
    
    # Minimum limit after reduction (percentage of original)
    LIMITE_MINIMO_PCT = 0.30  # Keep at least 30%
    
    # Products with fixed limits (legal/regulatory)
    LIMITES_FIXOS = {
        'consignado': 0.35  # Legal limit - cannot exceed
    }
    
    def __init__(self):
        """Initialize Limit Reallocation engine."""
        self.params_global = PARAMS_LIMITE_GLOBAL
        self.max_comprometimento = MAX_COMPROMETIMENTO_PRODUTO
        logger.info("LimitReallocation initialized")
    
    def calcular_limite_global(self, renda_bruta: float) -> LimiteGlobal:
        """
        Calculate the FIXED global limit based on income.
        
        This limit only changes when income changes (not affected by propensity).
        
        Args:
            renda_bruta: Gross monthly income
            
        Returns:
            LimiteGlobal with all components
        """
        resultado = calcular_limite_global_fixo(renda_bruta)
        
        return LimiteGlobal(
            renda_bruta=renda_bruta,
            limite_global=resultado['limite_global'],
            limite_grupo_a=resultado['detalhes']['grupo_a']['limite'],
            limite_grupo_b=resultado['detalhes']['grupo_b']['limite'],
            limite_grupo_c=resultado['detalhes']['grupo_c']['limite'],
            comprometimento_max=COMPROMETIMENTO_MAXIMO_RENDA,
            detalhes=resultado['detalhes']
        )
    
    def calcular_limites_por_produto(
        self,
        renda_bruta: float,
        comprometimento_atual: float = 0
    ) -> Dict[str, LimiteProduto]:
        """
        Calculate limits for each product within groups.
        
        Args:
            renda_bruta: Gross monthly income
            comprometimento_atual: Current income commitment (0-1)
            
        Returns:
            Dict of produto -> LimiteProduto
        """
        espaco_disponivel = max(0, COMPROMETIMENTO_MAXIMO_RENDA - comprometimento_atual)
        
        limites = {}
        
        for grupo_id, params in self.params_global.items():
            for produto in params['produtos']:
                # Get max commitment for this product
                max_pct = self.max_comprometimento.get(produto, params['pct'])
                
                # The product can use up to its max OR the remaining space (whichever is less)
                comprometimento_produto = min(max_pct, espaco_disponivel)
                
                # Calculate maximum installment
                parcela_max = renda_bruta * comprometimento_produto
                
                # Calculate limit using Price formula
                taxa = params['taxa']
                prazo = params['prazo']
                
                if taxa > 0:
                    fator = (1 - (1 + taxa) ** -prazo) / taxa
                else:
                    fator = prazo
                
                limite = parcela_max * fator
                
                limites[produto] = LimiteProduto(
                    produto=produto,
                    grupo=grupo_id,
                    limite_calculado=round(limite, 2),
                    limite_alocado=round(limite, 2),  # Initially same as calculated
                    comprometimento_max=comprometimento_produto,
                    parcela_max=round(parcela_max, 2),
                    prazo_meses=prazo,
                    taxa_mensal=taxa
                )
        
        return limites
    
    def calcular_propensao_classe(self, propensao_score: float) -> str:
        """
        Classify propensity score into category.
        
        Args:
            propensao_score: Propensity score (0-100)
            
        Returns:
            Classification string (ALTA, MEDIA, BAIXA)
        """
        for classe, bounds in PROPENSAO_CLASSIFICACAO.items():
            if bounds['min'] <= propensao_score <= bounds['max']:
                return classe
        return 'MEDIA'
    
    def realocar_por_propensao(
        self,
        cliente_id: str,
        renda_bruta: float,
        limites_atuais: Dict[str, float],
        propensoes: Dict[str, float],
        comprometimento_atual: float = 0
    ) -> RealocacaoResultado:
        """
        Reallocate limits based on propensity scores.
        
        Rules:
        1. Products with propensity < 40% have limits reduced (up to 50%)
        2. Freed space is redistributed to products with propensity > 60%
        3. Consignado 35% limit is NEVER reduced (legal limit)
        4. Total commitment stays at or below 70%
        
        Args:
            cliente_id: Client identifier
            renda_bruta: Gross monthly income
            limites_atuais: Current limits by product
            propensoes: Propensity scores by product (0-100)
            comprometimento_atual: Current income commitment (0-1)
            
        Returns:
            RealocacaoResultado with before/after limits
        """
        observacoes = []
        limites_novos = limites_atuais.copy()
        espaco_liberado = 0
        
        # Phase 1: Identify products for reduction (low propensity)
        produtos_reducao = []
        for produto, limite in limites_atuais.items():
            if produto in self.LIMITES_FIXOS:
                observacoes.append(f"{produto}: Limite legal, não pode ser reduzido")
                continue
            
            propensao = propensoes.get(produto, 50)
            
            if propensao < PROPENSAO_MAXIMA_PARA_REDUCAO:
                produtos_reducao.append({
                    'produto': produto,
                    'limite_atual': limite,
                    'propensao': propensao
                })
        
        # Phase 2: Calculate reductions
        for item in produtos_reducao:
            produto = item['produto']
            limite = item['limite_atual']
            propensao = item['propensao']
            
            # Calculate reduction factor based on propensity
            # propensao 0% -> reduce by 50%
            # propensao 45% -> reduce by 0%
            fator_reducao = (PROPENSAO_MAXIMA_PARA_REDUCAO - propensao) / PROPENSAO_MAXIMA_PARA_REDUCAO
            fator_reducao = min(self.FATOR_REDUCAO_MAX, fator_reducao)
            
            reducao = limite * fator_reducao
            novo_limite = max(limite * self.LIMITE_MINIMO_PCT, limite - reducao)
            
            limites_novos[produto] = round(novo_limite, 2)
            espaco_liberado += (limite - novo_limite)
            
            observacoes.append(
                f"{produto}: Propensão {propensao:.0f}% (baixa) → "
                f"Limite reduzido de R$ {limite:,.2f} para R$ {novo_limite:,.2f}"
            )
        
        # Phase 3: Identify products for increase (high propensity)
        produtos_aumento = []
        for produto, limite in limites_atuais.items():
            propensao = propensoes.get(produto, 50)
            
            if propensao >= PROPENSAO_MINIMA_PARA_AUMENTO:
                produtos_aumento.append({
                    'produto': produto,
                    'limite_atual': limites_novos[produto],
                    'propensao': propensao
                })
        
        # Phase 4: Distribute freed space to high propensity products
        if espaco_liberado > 0 and produtos_aumento:
            # Sort by propensity (highest first)
            produtos_aumento.sort(key=lambda x: x['propensao'], reverse=True)
            
            # Calculate weights based on propensity
            total_prop = sum(p['propensao'] for p in produtos_aumento)
            
            for item in produtos_aumento:
                produto = item['produto']
                propensao = item['propensao']
                limite_atual = item['limite_atual']
                
                # Check if product has a max commitment limit
                max_comprometimento = self.max_comprometimento.get(produto, 0.35)
                limite_maximo = self._calcular_limite_maximo(
                    renda_bruta, 
                    produto, 
                    max_comprometimento
                )
                
                # Calculate share of freed space
                peso = propensao / total_prop if total_prop > 0 else 0
                aumento = espaco_liberado * peso
                
                # Apply increase (respecting maximum)
                novo_limite = min(limite_atual + aumento, limite_maximo)
                aumento_real = novo_limite - limite_atual
                
                if aumento_real > 0:
                    limites_novos[produto] = round(novo_limite, 2)
                    espaco_liberado -= aumento_real
                    
                    observacoes.append(
                        f"{produto}: Propensão {propensao:.0f}% (alta) → "
                        f"Limite aumentado de R$ {limite_atual:,.2f} para R$ {novo_limite:,.2f}"
                    )
        
        # Calculate variations
        variacoes = {}
        for produto in set(limites_atuais.keys()) | set(limites_novos.keys()):
            antes = limites_atuais.get(produto, 0)
            depois = limites_novos.get(produto, 0)
            variacoes[produto] = round(depois - antes, 2)
        
        # Calculate new commitment
        comprometimento_disponivel = COMPROMETIMENTO_MAXIMO_RENDA - comprometimento_atual
        
        return RealocacaoResultado(
            cliente_id=cliente_id,
            renda_bruta=renda_bruta,
            comprometimento_atual=comprometimento_atual,
            comprometimento_disponivel=comprometimento_disponivel,
            limites_antes=limites_atuais,
            limites_depois=limites_novos,
            variacoes=variacoes,
            observacoes=observacoes
        )
    
    def _calcular_limite_maximo(
        self,
        renda_bruta: float,
        produto: str,
        comprometimento_max: float
    ) -> float:
        """
        Calculate maximum limit for a product.
        
        Args:
            renda_bruta: Gross monthly income
            produto: Product name
            comprometimento_max: Max commitment percentage
            
        Returns:
            Maximum limit value
        """
        # Find product parameters
        for grupo_id, params in self.params_global.items():
            if produto in params['produtos']:
                parcela_max = renda_bruta * comprometimento_max
                taxa = params['taxa']
                prazo = params['prazo']
                
                if taxa > 0:
                    fator = (1 - (1 + taxa) ** -prazo) / taxa
                else:
                    fator = prazo
                
                return parcela_max * fator
        
        # Default: use standard parameters
        return renda_bruta * comprometimento_max * 50  # ~50 months average
    
    def simular_impacto_ecl(
        self,
        realocacao: RealocacaoResultado,
        prinad: float,
        produtos_info: Dict[str, Dict]
    ) -> RealocacaoResultado:
        """
        Add ECL impact calculation to reallocation result.
        
        Args:
            realocacao: Reallocation result
            prinad: Client's PRINAD score
            produtos_info: Dict with product details (LGD, CCF, etc.)
            
        Returns:
            Updated RealocacaoResultado with ECL fields
        """
        try:
            from propensao.src.ecl_engine import calcular_ecl
            
            ecl_antes = 0
            ecl_depois = 0
            
            for produto, limite_antes in realocacao.limites_antes.items():
                ecl_antes += calcular_ecl(
                    cliente_id=realocacao.cliente_id,
                    produto=produto,
                    prinad=prinad,
                    ead=limite_antes
                )
            
            for produto, limite_depois in realocacao.limites_depois.items():
                ecl_depois += calcular_ecl(
                    cliente_id=realocacao.cliente_id,
                    produto=produto,
                    prinad=prinad,
                    ead=limite_depois
                )
            
            realocacao.ecl_antes = round(ecl_antes, 2)
            realocacao.ecl_depois = round(ecl_depois, 2)
            realocacao.ecl_economia = round(ecl_antes - ecl_depois, 2)
            
            if realocacao.ecl_economia > 0:
                realocacao.observacoes.append(
                    f"ECL reduzido em R$ {realocacao.ecl_economia:,.2f} "
                    f"({realocacao.ecl_economia / ecl_antes * 100:.1f}% de economia)"
                )
        
        except Exception as e:
            logger.warning(f"Could not calculate ECL impact: {e}")
        
        return realocacao
    
    def gerar_relatorio(
        self,
        limite_global: LimiteGlobal,
        limites_produtos: Dict[str, LimiteProduto],
        realocacao: Optional[RealocacaoResultado] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive limit report.
        
        Args:
            limite_global: Global limit calculation
            limites_produtos: Per-product limits
            realocacao: Optional reallocation result
            
        Returns:
            Report dictionary
        """
        report = {
            'limite_global': {
                'renda_bruta': limite_global.renda_bruta,
                'limite_total': limite_global.limite_global,
                'grupos': {
                    'grupo_a': limite_global.limite_grupo_a,
                    'grupo_b': limite_global.limite_grupo_b,
                    'grupo_c': limite_global.limite_grupo_c
                },
                'comprometimento_max': limite_global.comprometimento_max
            },
            'limites_produtos': {
                p: {
                    'grupo': lp.grupo,
                    'limite': lp.limite_alocado,
                    'parcela_max': lp.parcela_max,
                    'propensao': lp.propensao_score,
                    'propensao_classe': lp.propensao_class
                }
                for p, lp in limites_produtos.items()
            },
            'data_geracao': datetime.now().isoformat()
        }
        
        if realocacao:
            report['realocacao'] = {
                'cliente_id': realocacao.cliente_id,
                'limites_antes': realocacao.limites_antes,
                'limites_depois': realocacao.limites_depois,
                'variacoes': realocacao.variacoes,
                'ecl_antes': realocacao.ecl_antes,
                'ecl_depois': realocacao.ecl_depois,
                'ecl_economia': realocacao.ecl_economia,
                'observacoes': realocacao.observacoes
            }
        
        return report


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def calcular_limite_cliente(renda_bruta: float) -> Dict[str, float]:
    """
    Quick calculation of all product limits for a client.
    
    Args:
        renda_bruta: Gross monthly income
        
    Returns:
        Dict of produto -> limite
    """
    engine = LimitReallocation()
    limites = engine.calcular_limites_por_produto(renda_bruta)
    return {p: lp.limite_alocado for p, lp in limites.items()}


def realocar_limites(
    cliente_id: str,
    renda_bruta: float,
    limites_atuais: Dict[str, float],
    propensoes: Dict[str, float]
) -> Dict[str, float]:
    """
    Quick reallocation of limits based on propensity.
    
    Args:
        cliente_id: Client identifier
        renda_bruta: Gross monthly income
        limites_atuais: Current limits
        propensoes: Propensity scores
        
    Returns:
        New limits after reallocation
    """
    engine = LimitReallocation()
    resultado = engine.realocar_por_propensao(
        cliente_id=cliente_id,
        renda_bruta=renda_bruta,
        limites_atuais=limites_atuais,
        propensoes=propensoes
    )
    return resultado.limites_depois


# =============================================================================
# MAIN EXECUTION (for testing)
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("Limit Reallocation - Testing")
    print("=" * 70)
    
    engine = LimitReallocation()
    
    # Test 1: Global limit calculation
    renda = 10000  # R$ 10,000
    limite_global = engine.calcular_limite_global(renda)
    
    print(f"\nTest 1: Global Limit for income R$ {renda:,.2f}")
    print(f"  Limite Global: R$ {limite_global.limite_global:,.2f}")
    print(f"  Grupo A (consignado/pessoal): R$ {limite_global.limite_grupo_a:,.2f}")
    print(f"  Grupo B (imobiliário): R$ {limite_global.limite_grupo_b:,.2f}")
    print(f"  Grupo C (veículo/solar): R$ {limite_global.limite_grupo_c:,.2f}")
    
    # Test 2: Per-product limits
    limites = engine.calcular_limites_por_produto(renda)
    print(f"\nTest 2: Per-product limits")
    for produto, lp in limites.items():
        print(f"  {produto}: R$ {lp.limite_alocado:,.2f} (parcela max: R$ {lp.parcela_max:,.2f})")
    
    # Test 3: Propensity-based reallocation
    limites_atuais = {
        'consignado': 100000,
        'imobiliario': 200000,
        'cred_veiculo': 50000,
        'energia_solar': 30000
    }
    
    propensoes = {
        'consignado': 80,      # Alta - manter/aumentar
        'imobiliario': 20,     # Baixa - reduzir
        'cred_veiculo': 70,    # Alta - aumentar
        'energia_solar': 15    # Muito baixa - reduzir
    }
    
    print(f"\nTest 3: Propensity-based reallocation")
    print("  Input propensity scores:")
    for p, s in propensoes.items():
        print(f"    {p}: {s}%")
    
    resultado = engine.realocar_por_propensao(
        cliente_id="CLI001",
        renda_bruta=renda,
        limites_atuais=limites_atuais,
        propensoes=propensoes
    )
    
    print("\n  Reallocation results:")
    for obs in resultado.observacoes:
        print(f"    - {obs}")
    
    print("\n  Before vs After:")
    for produto in limites_atuais:
        antes = resultado.limites_antes[produto]
        depois = resultado.limites_depois[produto]
        var = resultado.variacoes[produto]
        sinal = "+" if var > 0 else ""
        print(f"    {produto}: R$ {antes:,.2f} → R$ {depois:,.2f} ({sinal}R$ {var:,.2f})")
    
    print("\n" + "=" * 70)
    print("✓ All tests completed!")
    print("=" * 70)
