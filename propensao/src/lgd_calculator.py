"""
LGD Calculator - Loss Given Default calculation by product type.

Implements Basel III Foundation IRB approach for LGD estimation,
with downturn adjustment for stress scenarios.
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import LGD_POR_PRODUTO, PRODUTOS_CREDITO, setup_logging

logger = setup_logging(__name__)


class TipoGarantia(Enum):
    """Types of collateral for LGD adjustment."""
    NENHUMA = "nenhuma"
    IMOVEL_RESIDENCIAL = "imovel_residencial"
    IMOVEL_COMERCIAL = "imovel_comercial"
    VEICULO = "veiculo"
    RECEBIVEL = "recebivel"
    CONSIGNACAO = "consignacao"
    FINANCEIRO = "financeiro"


@dataclass
class ParametrosLGD:
    """LGD parameters for a product."""
    lgd_base: float
    lgd_downturn: float
    tipo_garantia: TipoGarantia
    taxa_recuperacao_esperada: float
    custo_workout: float


class LGDCalculator:
    """
    Calculates Loss Given Default (LGD) following Basel III guidelines.
    
    LGD represents the expected loss as a percentage of EAD if default occurs.
    """
    
    # Basel III Foundation IRB LGD values by collateral type
    LGD_POR_GARANTIA = {
        TipoGarantia.NENHUMA: 0.45,  # Unsecured senior
        TipoGarantia.IMOVEL_RESIDENCIAL: 0.10,
        TipoGarantia.IMOVEL_COMERCIAL: 0.15,
        TipoGarantia.VEICULO: 0.25,
        TipoGarantia.RECEBIVEL: 0.10,
        TipoGarantia.CONSIGNACAO: 0.20,
        TipoGarantia.FINANCEIRO: 0.00,
    }
    
    # Downturn multiplier (stress scenario)
    DOWNTURN_MULTIPLIER = 1.25
    
    # Product to collateral mapping
    PRODUTO_GARANTIA = {
        'consignado': TipoGarantia.CONSIGNACAO,
        'banparacard': TipoGarantia.NENHUMA,
        'cartao_credito': TipoGarantia.NENHUMA,
        'imobiliario': TipoGarantia.IMOVEL_RESIDENCIAL,
        'antecipacao_13_sal': TipoGarantia.CONSIGNACAO,
        'cred_veiculo': TipoGarantia.VEICULO,
    }
    
    # Workout costs by product (percentage of EAD)
    CUSTO_WORKOUT = {
        'consignado': 0.05,
        'banparacard': 0.10,
        'cartao_credito': 0.15,
        'imobiliario': 0.08,
        'antecipacao_13_sal': 0.03,
        'cred_veiculo': 0.10,
    }
    
    def __init__(self, aplicar_downturn: bool = True):
        """
        Initialize LGD calculator.
        
        Args:
            aplicar_downturn: Whether to apply downturn adjustment
        """
        self.aplicar_downturn = aplicar_downturn
        self._parametros_cache: Dict[str, ParametrosLGD] = {}
        self._build_params()
        
        logger.info(f"LGDCalculator initialized (downturn={aplicar_downturn})")
    
    def _build_params(self):
        """Build parameters for each product."""
        for produto in PRODUTOS_CREDITO:
            garantia = self.PRODUTO_GARANTIA.get(produto, TipoGarantia.NENHUMA)
            lgd_base = self.LGD_POR_GARANTIA.get(garantia, 0.45)
            
            # Apply product-specific adjustments
            lgd_produto = LGD_POR_PRODUTO.get(produto, lgd_base)
            
            # Use the more conservative (higher) value
            lgd_final = max(lgd_base, lgd_produto)
            
            # Downturn adjustment
            lgd_downturn = min(1.0, lgd_final * self.DOWNTURN_MULTIPLIER)
            
            # Recovery rate = 1 - LGD (before workout costs)
            taxa_recuperacao = 1.0 - lgd_final
            
            custo_workout = self.CUSTO_WORKOUT.get(produto, 0.10)
            
            self._parametros_cache[produto] = ParametrosLGD(
                lgd_base=lgd_final,
                lgd_downturn=lgd_downturn,
                tipo_garantia=garantia,
                taxa_recuperacao_esperada=taxa_recuperacao,
                custo_workout=custo_workout
            )
    
    def get_lgd(
        self, 
        produto: str, 
        downturn: Optional[bool] = None,
        incluir_workout: bool = True
    ) -> float:
        """
        Get LGD for a product.
        
        Args:
            produto: Product name
            downturn: Override downturn setting
            incluir_workout: Include workout costs
            
        Returns:
            LGD as decimal (0-1)
        """
        params = self._parametros_cache.get(produto)
        
        if params is None:
            logger.warning(f"Unknown product '{produto}', using default LGD 0.45")
            base_lgd = 0.45
            workout = 0.10
        else:
            aplicar_dt = downturn if downturn is not None else self.aplicar_downturn
            base_lgd = params.lgd_downturn if aplicar_dt else params.lgd_base
            workout = params.custo_workout if incluir_workout else 0
        
        lgd_total = min(1.0, base_lgd + workout)
        return lgd_total
    
    def get_parametros(self, produto: str) -> Optional[ParametrosLGD]:
        """Get full LGD parameters for a product."""
        return self._parametros_cache.get(produto)
    
    def get_all_lgd(self) -> Dict[str, float]:
        """Get LGD for all products."""
        return {produto: self.get_lgd(produto) for produto in PRODUTOS_CREDITO}
    
    def calcular_perda_esperada_default(
        self,
        produto: str,
        ead: float,
        downturn: Optional[bool] = None
    ) -> float:
        """
        Calculate expected loss amount if default occurs.
        
        Args:
            produto: Product name
            ead: Exposure at Default
            downturn: Override downturn setting
            
        Returns:
            Expected loss amount in currency
        """
        lgd = self.get_lgd(produto, downturn=downturn)
        return ead * lgd
    
    def display_lgd_table(self) -> str:
        """Generate a formatted table of LGD values."""
        lines = [
            "=" * 70,
            "LGD por Produto (Basel III Foundation IRB)",
            "=" * 70,
            f"{'Produto':<20} {'Garantia':<20} {'LGD Base':>10} {'LGD Downturn':>12}",
            "-" * 70
        ]
        
        for produto in PRODUTOS_CREDITO:
            params = self._parametros_cache.get(produto)
            if params:
                lines.append(
                    f"{produto:<20} {params.tipo_garantia.value:<20} "
                    f"{params.lgd_base:>10.1%} {params.lgd_downturn:>12.1%}"
                )
        
        lines.append("=" * 70)
        return "\n".join(lines)


# Module-level instance
_lgd_calculator: Optional[LGDCalculator] = None


def get_lgd_calculator(aplicar_downturn: bool = True) -> LGDCalculator:
    """Get or create LGD calculator instance."""
    global _lgd_calculator
    if _lgd_calculator is None:
        _lgd_calculator = LGDCalculator(aplicar_downturn=aplicar_downturn)
    return _lgd_calculator


def get_lgd(produto: str) -> float:
    """Convenience function to get LGD for a product."""
    return get_lgd_calculator().get_lgd(produto)


if __name__ == "__main__":
    calc = LGDCalculator()
    print(calc.display_lgd_table())
    print()
    print("LGD Values (with workout costs):")
    for produto, lgd in calc.get_all_lgd().items():
        print(f"  {produto}: {lgd:.1%}")
