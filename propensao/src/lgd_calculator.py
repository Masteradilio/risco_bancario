"""
LGD Calculator - Dynamic Loss Given Default calculation.

Calculates LGD per operation based on:
- Guarantee type and impact
- Loan-to-Value (LTV) ratio
- Remaining term (depreciation)
- Recovery costs
- Economic cycle (downturn adjustment)

Implements Basel III Foundation IRB approach with dynamic adjustments.
"""

import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    PRODUTOS_CREDITO,
    PRODUTOS_PF,
    IMPACTO_GARANTIA,
    GARANTIA_POR_PRODUTO,
    TIPOS_GARANTIA,
    setup_logging
)

logger = setup_logging(__name__)


@dataclass
class ParametrosGarantia:
    """Parameters for a guarantee type."""
    tipo: str
    lgd_min: float
    lgd_max: float
    lgd_base: float
    ltv_max: float
    depreciacao_anual: float
    custo_recuperacao: float
    tempo_recuperacao_meses: int
    haircut_downturn: float


@dataclass
class ResultadoLGD:
    """Result of LGD calculation for an operation."""
    produto: str
    tipo_garantia: str
    lgd_base: float
    lgd_ajustado_ltv: float
    lgd_ajustado_prazo: float
    lgd_com_recuperacao: float
    lgd_downturn: float
    lgd_final: float
    detalhes: Dict[str, float]


class LGDCalculator:
    """
    Calculates Loss Given Default (LGD) dynamically per operation.
    
    LGD represents the expected loss as a percentage of EAD if default occurs.
    
    Formula:
    LGD = 1 - (Recovery Rate × (1 - Depreciation) × (1 - LTV_Excess)) - Recovery Costs
    
    With adjustments for:
    - LTV deviation from maximum
    - Remaining term (collateral depreciation)
    - Recovery/workout costs
    - Downturn (stress scenario)
    """
    
    # Downturn multiplier for stress scenarios (Basel III)
    DOWNTURN_MULTIPLIER = 1.25
    
    def __init__(
        self, 
        aplicar_downturn: bool = True,
        ciclo_economico: str = 'normal'  # 'normal', 'expansao', 'recessao'
    ):
        """
        Initialize LGD calculator.
        
        Args:
            aplicar_downturn: Whether to apply downturn adjustment
            ciclo_economico: Economic cycle phase
        """
        self.aplicar_downturn = aplicar_downturn
        self.ciclo_economico = ciclo_economico
        
        # Load guarantee parameters
        self.parametros_garantia: Dict[str, ParametrosGarantia] = {}
        self._carregar_parametros()
        
        logger.info(f"LGDCalculator initialized (downturn={aplicar_downturn}, cycle={ciclo_economico})")
    
    def _carregar_parametros(self):
        """Load guarantee parameters from configuration."""
        for tipo, params in IMPACTO_GARANTIA.items():
            self.parametros_garantia[tipo] = ParametrosGarantia(
                tipo=tipo,
                lgd_min=params['lgd_min'],
                lgd_max=params['lgd_max'],
                lgd_base=params['lgd_base'],
                ltv_max=params['ltv_max'],
                depreciacao_anual=params['depreciacao_anual'],
                custo_recuperacao=params['custo_recuperacao'],
                tempo_recuperacao_meses=params['tempo_recuperacao_meses'],
                haircut_downturn=params['haircut_downturn']
            )
    
    def _ajustar_por_ltv(
        self,
        lgd_base: float,
        ltv_atual: float,
        ltv_max: float,
        lgd_min: float,
        lgd_max: float
    ) -> float:
        """
        Adjust LGD based on LTV ratio.
        
        Higher LTV = Higher LGD (less collateral coverage)
        """
        if ltv_max <= 0:  # Unsecured
            return lgd_base
        
        # Calculate LTV ratio relative to max
        ltv_ratio = min(1.0, ltv_atual / ltv_max)
        
        # Linear interpolation between min and max LGD
        lgd_ajustado = lgd_min + (lgd_max - lgd_min) * ltv_ratio
        
        return lgd_ajustado
    
    def _ajustar_por_prazo(
        self,
        lgd_atual: float,
        prazo_restante_meses: int,
        prazo_total_meses: int,
        depreciacao_anual: float,
        lgd_max: float
    ) -> float:
        """
        Adjust LGD based on remaining term (collateral depreciation).
        
        Longer remaining term = More depreciation = Higher LGD
        """
        if depreciacao_anual <= 0:
            return lgd_atual
        
        # Calculate accumulated depreciation
        anos_restantes = prazo_restante_meses / 12
        depreciacao_acumulada = 1 - (1 - depreciacao_anual) ** anos_restantes
        
        # Increase LGD proportionally to depreciation
        lgd_ajustado = lgd_atual * (1 + depreciacao_acumulada)
        
        return min(lgd_max, lgd_ajustado)
    
    def _adicionar_custo_recuperacao(
        self,
        lgd_atual: float,
        custo_recuperacao: float
    ) -> float:
        """Add recovery/workout costs to LGD."""
        return min(1.0, lgd_atual + custo_recuperacao)
    
    def _aplicar_downturn(
        self,
        lgd_atual: float,
        haircut_downturn: float
    ) -> float:
        """Apply downturn adjustment for stress scenarios."""
        if not self.aplicar_downturn:
            return lgd_atual
        
        # Add downturn haircut (collateral value decreases in crisis)
        lgd_downturn = lgd_atual + haircut_downturn
        
        # Also apply Basel multiplier
        lgd_downturn = lgd_downturn * self.DOWNTURN_MULTIPLIER
        
        return min(1.0, lgd_downturn)
    
    def calcular_lgd_operacao(
        self,
        produto: str,
        valor_operacao: float,
        valor_garantia: float = 0,
        prazo_total_meses: int = 12,
        prazo_restante_meses: Optional[int] = None,
        tipo_garantia_override: Optional[str] = None
    ) -> ResultadoLGD:
        """
        Calculate LGD dynamically for a specific operation.
        
        Args:
            produto: Product name
            valor_operacao: Loan amount (EAD)
            valor_garantia: Collateral value (0 for unsecured)
            prazo_total_meses: Total loan term in months
            prazo_restante_meses: Remaining term (defaults to total)
            tipo_garantia_override: Override default guarantee type
            
        Returns:
            ResultadoLGD with complete breakdown
        """
        # Get guarantee type for product
        tipo_garantia = tipo_garantia_override or GARANTIA_POR_PRODUTO.get(produto, 'nenhuma')
        
        # Get guarantee parameters
        params = self.parametros_garantia.get(tipo_garantia)
        if params is None:
            params = self.parametros_garantia['nenhuma']
            tipo_garantia = 'nenhuma'
        
        # Calculate LTV
        if valor_garantia > 0 and tipo_garantia != 'nenhuma':
            ltv_atual = valor_operacao / valor_garantia
        else:
            ltv_atual = 0  # Unsecured
        
        # Default prazo_restante to total
        if prazo_restante_meses is None:
            prazo_restante_meses = prazo_total_meses
        
        # Step 1: Base LGD
        lgd_base = params.lgd_base
        
        # Step 2: Adjust by LTV
        lgd_ajustado_ltv = self._ajustar_por_ltv(
            lgd_base, ltv_atual, params.ltv_max,
            params.lgd_min, params.lgd_max
        )
        
        # Step 3: Adjust by remaining term (depreciation)
        lgd_ajustado_prazo = self._ajustar_por_prazo(
            lgd_ajustado_ltv, prazo_restante_meses, prazo_total_meses,
            params.depreciacao_anual, params.lgd_max
        )
        
        # Step 4: Add recovery costs
        lgd_com_recuperacao = self._adicionar_custo_recuperacao(
            lgd_ajustado_prazo, params.custo_recuperacao
        )
        
        # Step 5: Apply downturn adjustment
        lgd_downturn = self._aplicar_downturn(
            lgd_com_recuperacao, params.haircut_downturn
        )
        
        # Final LGD depends on downturn setting
        lgd_final = lgd_downturn if self.aplicar_downturn else lgd_com_recuperacao
        
        return ResultadoLGD(
            produto=produto,
            tipo_garantia=tipo_garantia,
            lgd_base=lgd_base,
            lgd_ajustado_ltv=lgd_ajustado_ltv,
            lgd_ajustado_prazo=lgd_ajustado_prazo,
            lgd_com_recuperacao=lgd_com_recuperacao,
            lgd_downturn=lgd_downturn,
            lgd_final=lgd_final,
            detalhes={
                'ltv_atual': ltv_atual,
                'ltv_max': params.ltv_max,
                'prazo_restante_meses': prazo_restante_meses,
                'depreciacao_anual': params.depreciacao_anual,
                'custo_recuperacao': params.custo_recuperacao,
                'haircut_downturn': params.haircut_downturn,
                'aplicar_downturn': float(self.aplicar_downturn)
            }
        )
    
    def get_lgd(
        self, 
        produto: str, 
        valor_operacao: float = 100000,
        valor_garantia: float = 0,
        prazo_meses: int = 12,
        downturn: Optional[bool] = None
    ) -> float:
        """
        Get LGD for a product (convenience method).
        
        Args:
            produto: Product name
            valor_operacao: Loan amount
            valor_garantia: Collateral value
            prazo_meses: Loan term
            downturn: Override downturn setting
            
        Returns:
            LGD as decimal (0-1)
        """
        # Auto-calculate collateral for secured products
        if valor_garantia == 0:
            tipo = GARANTIA_POR_PRODUTO.get(produto, 'nenhuma')
            if tipo != 'nenhuma':
                # Assume 80% LTV for simulation
                valor_garantia = valor_operacao / 0.80
        
        resultado = self.calcular_lgd_operacao(
            produto=produto,
            valor_operacao=valor_operacao,
            valor_garantia=valor_garantia,
            prazo_total_meses=prazo_meses
        )
        
        if downturn is not None:
            return resultado.lgd_downturn if downturn else resultado.lgd_com_recuperacao
        
        return resultado.lgd_final
    
    def get_lgd_produto_default(self, produto: str) -> float:
        """Get default LGD for a product (for quick reference)."""
        tipo = GARANTIA_POR_PRODUTO.get(produto, 'nenhuma')
        params = self.parametros_garantia.get(tipo, self.parametros_garantia['nenhuma'])
        return params.lgd_base + params.custo_recuperacao
    
    def get_parametros(self, produto: str) -> Optional[ParametrosGarantia]:
        """Get guarantee parameters for a product."""
        tipo = GARANTIA_POR_PRODUTO.get(produto, 'nenhuma')
        return self.parametros_garantia.get(tipo)
    
    def get_all_lgd(self) -> Dict[str, float]:
        """Get default LGD for all products."""
        return {p: self.get_lgd_produto_default(p) for p in PRODUTOS_CREDITO}
    
    def calcular_perda_esperada_default(
        self,
        produto: str,
        ead: float,
        valor_garantia: float = 0,
        prazo_meses: int = 12
    ) -> float:
        """
        Calculate expected loss amount if default occurs.
        
        Args:
            produto: Product name
            ead: Exposure at Default
            valor_garantia: Collateral value
            prazo_meses: Remaining term
            
        Returns:
            Expected loss amount in currency
        """
        lgd = self.get_lgd(produto, ead, valor_garantia, prazo_meses)
        return ead * lgd
    
    def display_lgd_table(self) -> str:
        """Generate a formatted table of LGD values by guarantee type."""
        lines = [
            "=" * 90,
            "LGD por Tipo de Garantia (Cálculo Dinâmico)",
            "=" * 90,
            f"{'Garantia':<20} {'LGD Min':>10} {'LGD Base':>10} {'LGD Max':>10} "
            f"{'+ Recup':>10} {'Downturn':>10}",
            "-" * 90
        ]
        
        for tipo in TIPOS_GARANTIA:
            params = self.parametros_garantia.get(tipo)
            if params:
                lgd_com_recup = params.lgd_base + params.custo_recuperacao
                lgd_downturn = min(1.0, lgd_com_recup * self.DOWNTURN_MULTIPLIER + params.haircut_downturn)
                lines.append(
                    f"{tipo:<20} {params.lgd_min:>10.1%} {params.lgd_base:>10.1%} "
                    f"{params.lgd_max:>10.1%} {lgd_com_recup:>10.1%} {lgd_downturn:>10.1%}"
                )
        
        lines.append("=" * 90)
        lines.append("")
        lines.append("LGD por Produto (com garantia padrão):")
        lines.append("-" * 50)
        
        for produto in PRODUTOS_CREDITO:
            tipo = GARANTIA_POR_PRODUTO.get(produto, 'nenhuma')
            lgd = self.get_lgd_produto_default(produto)
            lines.append(f"  {produto:<30} ({tipo}): {lgd:.1%}")
        
        lines.append("=" * 90)
        return "\n".join(lines)


# Module-level instance
_lgd_calculator: Optional[LGDCalculator] = None


def get_lgd_calculator(aplicar_downturn: bool = True) -> LGDCalculator:
    """Get or create LGD calculator instance."""
    global _lgd_calculator
    if _lgd_calculator is None:
        _lgd_calculator = LGDCalculator(aplicar_downturn=aplicar_downturn)
    return _lgd_calculator


def get_lgd(produto: str, **kwargs) -> float:
    """Convenience function to get LGD for a product."""
    return get_lgd_calculator().get_lgd(produto, **kwargs)


def calcular_lgd_operacao(
    produto: str,
    valor_operacao: float,
    valor_garantia: float = 0,
    prazo_meses: int = 12
) -> ResultadoLGD:
    """Convenience function to calculate LGD for an operation."""
    return get_lgd_calculator().calcular_lgd_operacao(
        produto, valor_operacao, valor_garantia, prazo_meses
    )


if __name__ == "__main__":
    calc = LGDCalculator()
    print(calc.display_lgd_table())
    
    print("\n" + "=" * 70)
    print("EXEMPLO DE CÁLCULO DINÂMICO")
    print("=" * 70)
    
    # Example: Vehicle loan with 80% LTV
    resultado = calc.calcular_lgd_operacao(
        produto='cred_veiculo',
        valor_operacao=50000,
        valor_garantia=62500,  # LTV 80%
        prazo_total_meses=48,
        prazo_restante_meses=36
    )
    
    print(f"\nProduto: {resultado.produto}")
    print(f"Garantia: {resultado.tipo_garantia}")
    print(f"LGD Base: {resultado.lgd_base:.1%}")
    print(f"LGD Ajustado LTV: {resultado.lgd_ajustado_ltv:.1%}")
    print(f"LGD Ajustado Prazo: {resultado.lgd_ajustado_prazo:.1%}")
    print(f"LGD + Recuperação: {resultado.lgd_com_recuperacao:.1%}")
    print(f"LGD Downturn: {resultado.lgd_downturn:.1%}")
    print(f"LGD Final: {resultado.lgd_final:.1%}")
