"""
Pisos Mínimos de Provisão - BACEN 4966 / Resolução BCB 352

Este módulo implementa os pisos mínimos de provisão para Stage 3 (default)
conforme a Resolução BCB nº 352/2023 e a documentação técnica.

Os pisos mínimos são aplicados APÓS o cálculo do ECL normal.
Se o ECL calculado for menor que o piso, o piso prevalece.

Tabela de Pisos por Carteira e Faixa de Atraso:
- Carteira 1 (C1): Crédito pessoal sem garantia
- Carteira 2 (C2): Cartão de crédito e rotativos
- Carteira 3 (C3): Consignado
- Carteira 4 (C4): Imobiliário residencial
- Carteira 5 (C5): Veículos
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# TABELA DE PISOS MÍNIMOS - RESOLUÇÃO BCB 352/2023
# =============================================================================
# Formato: PISOS_MINIMOS[faixa_atraso][carteira] = percentual_minimo

PISOS_MINIMOS_STAGE_3 = {
    # Faixa: 0-14 dias (Stage 3 por evento qualitativo, não por atraso)
    '0-14': {
        'C1': 0.005,   # 0.5%
        'C2': 0.005,
        'C3': 0.003,   # Consignado tem menor risco
        'C4': 0.001,   # Imobiliário com garantia
        'C5': 0.002,   # Veículo com garantia
    },
    # Faixa: 15-30 dias
    '15-30': {
        'C1': 0.01,    # 1%
        'C2': 0.03,    # 3%
        'C3': 0.01,
        'C4': 0.005,
        'C5': 0.005,
    },
    # Faixa: 31-60 dias
    '31-60': {
        'C1': 0.03,    # 3%
        'C2': 0.10,    # 10%
        'C3': 0.03,
        'C4': 0.01,
        'C5': 0.01,
    },
    # Faixa: 61-90 dias
    '61-90': {
        'C1': 0.10,    # 10%
        'C2': 0.30,    # 30%
        'C3': 0.10,
        'C4': 0.03,
        'C5': 0.05,
    },
    # Faixa: 91-120 dias
    '91-120': {
        'C1': 0.30,    # 30%
        'C2': 0.50,    # 50%
        'C3': 0.25,
        'C4': 0.10,
        'C5': 0.15,
    },
    # Faixa: 121-150 dias
    '121-150': {
        'C1': 0.50,    # 50%
        'C2': 0.70,    # 70%
        'C3': 0.40,
        'C4': 0.20,
        'C5': 0.25,
    },
    # Faixa: 151-180 dias
    '151-180': {
        'C1': 0.70,    # 70%
        'C2': 0.80,    # 80%
        'C3': 0.55,
        'C4': 0.30,
        'C5': 0.35,
    },
    # Faixa: 181-360 dias
    '181-360': {
        'C1': 0.85,    # 85%
        'C2': 0.95,    # 95%
        'C3': 0.70,
        'C4': 0.40,
        'C5': 0.50,
    },
    # Faixa: > 360 dias
    '>360': {
        'C1': 1.00,    # 100%
        'C2': 1.00,    # 100%
        'C3': 0.85,
        'C4': 0.50,
        'C5': 0.70,
    },
}


# =============================================================================
# MAPEAMENTO DE PRODUTOS PARA CARTEIRAS
# =============================================================================

PRODUTO_PARA_CARTEIRA = {
    # Sem garantia
    'pessoal': 'C1',
    'emprestimo_pessoal': 'C1',
    'credito_pessoal': 'C1',
    
    # Rotativos
    'cartao_credito': 'C2',
    'cartao_credito_rotativo': 'C2',
    'cartao_credito_parcelado': 'C2',
    'banparacard': 'C2',
    'cheque_especial': 'C2',
    
    # Consignado
    'consignado': 'C3',
    'consignado_inss': 'C3',
    'consignado_publico': 'C3',
    
    # Imobiliário
    'imobiliario': 'C4',
    'financiamento_imobiliario': 'C4',
    'credito_imobiliario': 'C4',
    
    # Veículos
    'veiculo': 'C5',
    'cred_veiculo': 'C5',
    'financiamento_veiculo': 'C5',
    
    # Outros com garantia de bem
    'energia_solar': 'C5',  # Equipamento como garantia
}


@dataclass
class PisoResult:
    """Resultado da aplicação do piso mínimo."""
    ecl_original: float
    ecl_ajustado: float
    piso_aplicado: float
    carteira: str
    faixa_atraso: str
    piso_foi_aplicado: bool


def obter_faixa_atraso(dias_atraso: int) -> str:
    """
    Determina a faixa de atraso a partir do número de dias.
    
    Args:
        dias_atraso: Número de dias em atraso
        
    Returns:
        String identificando a faixa
    """
    if dias_atraso <= 14:
        return '0-14'
    elif dias_atraso <= 30:
        return '15-30'
    elif dias_atraso <= 60:
        return '31-60'
    elif dias_atraso <= 90:
        return '61-90'
    elif dias_atraso <= 120:
        return '91-120'
    elif dias_atraso <= 150:
        return '121-150'
    elif dias_atraso <= 180:
        return '151-180'
    elif dias_atraso <= 360:
        return '181-360'
    else:
        return '>360'


def obter_carteira_produto(produto: str) -> str:
    """
    Mapeia um produto para sua carteira regulatória.
    
    Args:
        produto: Nome do produto
        
    Returns:
        Código da carteira (C1-C5)
    """
    produto_normalizado = produto.lower().replace(' ', '_')
    return PRODUTO_PARA_CARTEIRA.get(produto_normalizado, 'C1')


def obter_piso_minimo(dias_atraso: int, carteira: str) -> float:
    """
    Obtém o piso mínimo de provisão.
    
    Args:
        dias_atraso: Número de dias em atraso
        carteira: Código da carteira (C1-C5)
        
    Returns:
        Percentual mínimo de provisão (0 a 1)
    """
    faixa = obter_faixa_atraso(dias_atraso)
    
    if faixa not in PISOS_MINIMOS_STAGE_3:
        logger.warning(f"Faixa de atraso '{faixa}' não encontrada. Usando piso máximo.")
        return 1.0
    
    if carteira not in PISOS_MINIMOS_STAGE_3[faixa]:
        logger.warning(f"Carteira '{carteira}' não encontrada. Usando C1 como padrão.")
        carteira = 'C1'
    
    return PISOS_MINIMOS_STAGE_3[faixa][carteira]


def aplicar_piso_minimo(
    ecl_calculado: float,
    ead: float,
    dias_atraso: int,
    produto: str,
    stage: int = 3,
    carteira_override: str = None
) -> PisoResult:
    """
    Aplica piso mínimo de provisão se o ECL calculado for menor.
    
    O piso só é aplicado para Stage 3 (default).
    
    Args:
        ecl_calculado: ECL calculado pelo modelo (valor absoluto)
        ead: Exposure at Default (para calcular o piso)
        dias_atraso: Número de dias em atraso
        produto: Nome do produto
        stage: Estágio IFRS 9 (piso só aplica para stage 3)
        carteira_override: Força uma carteira específica
        
    Returns:
        PisoResult com ECL ajustado e informações
    """
    # Piso só se aplica para Stage 3
    if stage != 3:
        return PisoResult(
            ecl_original=ecl_calculado,
            ecl_ajustado=ecl_calculado,
            piso_aplicado=0.0,
            carteira='N/A',
            faixa_atraso='N/A',
            piso_foi_aplicado=False
        )
    
    # Determinar carteira
    carteira = carteira_override or obter_carteira_produto(produto)
    faixa = obter_faixa_atraso(dias_atraso)
    
    # Obter piso
    piso_percentual = obter_piso_minimo(dias_atraso, carteira)
    piso_valor = ead * piso_percentual
    
    # Aplicar se necessário
    if ecl_calculado < piso_valor:
        logger.info(
            f"Piso mínimo aplicado: ECL {ecl_calculado:.2f} -> {piso_valor:.2f} "
            f"(carteira={carteira}, faixa={faixa}, piso={piso_percentual:.1%})"
        )
        ecl_ajustado = piso_valor
        piso_aplicado = True
    else:
        ecl_ajustado = ecl_calculado
        piso_aplicado = False
    
    return PisoResult(
        ecl_original=ecl_calculado,
        ecl_ajustado=ecl_ajustado,
        piso_aplicado=piso_percentual,
        carteira=carteira,
        faixa_atraso=faixa,
        piso_foi_aplicado=piso_aplicado
    )


def calcular_ecl_com_piso(
    pd: float,
    lgd: float,
    ead: float,
    dias_atraso: int,
    produto: str,
    stage: int
) -> Dict[str, Any]:
    """
    Calcula ECL e aplica piso mínimo se necessário.
    
    Fórmula: ECL = PD × LGD × EAD (com piso mínimo para Stage 3)
    
    Args:
        pd: Probability of Default (0-1)
        lgd: Loss Given Default (0-1)
        ead: Exposure at Default
        dias_atraso: Dias em atraso
        produto: Nome do produto
        stage: Estágio IFRS 9
        
    Returns:
        Dict com ECL, piso aplicado, e detalhes
    """
    # Calcular ECL normal
    ecl_calculado = pd * lgd * ead
    
    # Aplicar piso
    resultado_piso = aplicar_piso_minimo(
        ecl_calculado=ecl_calculado,
        ead=ead,
        dias_atraso=dias_atraso,
        produto=produto,
        stage=stage
    )
    
    return {
        'ecl': resultado_piso.ecl_ajustado,
        'ecl_antes_piso': resultado_piso.ecl_original,
        'piso_aplicado': resultado_piso.piso_foi_aplicado,
        'piso_percentual': resultado_piso.piso_aplicado,
        'carteira': resultado_piso.carteira,
        'faixa_atraso': resultado_piso.faixa_atraso,
        'componentes': {
            'pd': pd,
            'lgd': lgd,
            'ead': ead,
            'stage': stage
        }
    }


if __name__ == '__main__':
    # Teste do módulo
    logging.basicConfig(level=logging.INFO)
    
    print("=== Teste de Pisos Mínimos ===\n")
    
    # Teste 1: Stage 3 com atraso de 100 dias
    resultado = calcular_ecl_com_piso(
        pd=0.50,
        lgd=0.60,
        ead=10000,
        dias_atraso=100,
        produto='consignado',
        stage=3
    )
    print(f"Teste 1 - Consignado, 100 dias atraso:")
    print(f"  ECL calculado: R$ {resultado['ecl_antes_piso']:.2f}")
    print(f"  ECL ajustado:  R$ {resultado['ecl']:.2f}")
    print(f"  Piso aplicado: {resultado['piso_aplicado']}")
    print(f"  Carteira: {resultado['carteira']}, Faixa: {resultado['faixa_atraso']}")
    print()
    
    # Teste 2: Stage 3 com atraso de 400 dias
    resultado = calcular_ecl_com_piso(
        pd=0.95,
        lgd=0.80,
        ead=5000,
        dias_atraso=400,
        produto='cartao_credito_rotativo',
        stage=3
    )
    print(f"Teste 2 - Cartão, 400 dias atraso:")
    print(f"  ECL calculado: R$ {resultado['ecl_antes_piso']:.2f}")
    print(f"  ECL ajustado:  R$ {resultado['ecl']:.2f}")
    print(f"  Piso aplicado: {resultado['piso_aplicado']}")
    print(f"  Carteira: {resultado['carteira']}, Faixa: {resultado['faixa_atraso']}")
