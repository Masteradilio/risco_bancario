"""
Módulo de Perda Esperada (ECL) - BACEN 4966/IFRS 9 Compliant

IMPORTANTE: Este módulo CONSOME os resultados do módulo PRINAD.
Não duplica cálculos de PD_12m, PD_lifetime ou Stage.

O módulo PRINAD fornece:
- PRINAD score (0-100%)
- Rating (A1 a DEFAULT)
- PD_12m (calibrado por rating)
- PD_lifetime (fórmula de sobrevivência)
- Stage IFRS 9 (1, 2, 3)

Este módulo ADICIONA:
- Grupos Homogêneos de Risco (GH) com WOE
- Forward Looking (K_PD_FL, K_LGD_FL)
- LGD Segmentado por árvore de decisão
- EAD com CCF específico por cenário
- Triggers de migração entre estágios
- Análise de Write-Off
- Pisos Mínimos de Provisão (Stage 3)

Uso:
    from prinad.src.classifier import PRINADClassifier
    from perda_esperada.src import ECLPipeline
    
    # Obter resultado do PRINAD
    classifier = PRINADClassifier()
    prinad_result = classifier.classify(client_data)
    
    # Calcular ECL com enriquecimento
    pipeline = ECLPipeline()
    ecl = pipeline.calcular_ecl_completo(
        prinad_result=prinad_result,
        produto='consignado',
        saldo_devedor=5000,
        limite_total=10000,
        dias_atraso=0
    )
"""

__version__ = "2.0.0"
__author__ = "Data Science Team"

# Componentes principais
from .modulo_grupos_homogeneos import GruposHomogeneosConsolidado, CalculadorPDReais
from .modulo_forward_looking import (
    ModeloForwardLooking, 
    coletar_series_historicas,
    calcular_woe_scores,
    WOE_SCORES,
    EQUACOES_FL,
    # Funções TTC→PIT (integradas de modelos_econometricos.py)
    calibrar_pd_ttc_para_pit,
    aplicar_calibracao_pit,
    # Funções de Cenários Macroeconômicos
    gerar_cenarios_macroeconomicos_avancados,
    calcular_ecl_sob_cenarios
)
from .modulo_lgd_segmentado import LGDSegmentado
from .modulo_ead_ccf_especifico import EADCCFEspecifico
from .modulo_estadiamento import (
    classificar_estagio_aprimorado,
    aplicar_regras_cura_estagio,
    calcular_metricas_estagio
)
from .modulo_triggers_estagios import aplicar_todos_triggers_estagios
from .modulo_analise_writeoff import processar_writeoff
from .pisos_minimos import (
    aplicar_piso_minimo,
    calcular_ecl_com_piso,
    obter_carteira_produto,
    PISOS_MINIMOS_STAGE_3
)
from .pipeline_ecl import ECLPipeline, ECLCompleteResult

# PD Behavior para contratos em carteira
from .modulo_pd_behavior import (
    calcular_pd_behavior,
    executar_pd_behavior_completo,
    filtrar_dados_behavior,
    criar_variaveis_comportamentais,
    GRUPOS_HOMOGENEOS_BEHAVIOR,
    FEATURES_PD_BEHAVIOR
)

# Backtesting e Validação (integrado de modulo_backtesting legado)
from .modulo_backtesting import (
    executar_backtesting_pd,
    executar_backtesting_lgd,
    gerar_relatorio_validacao_completo,
    executar_backtesting_automatico,
    CRITERIOS_APROVACAO
)

# Testes Estatísticos
from .modulo_testes_estatisticos import (
    TestesEstatisticos,
    validar_modelo_estatisticamente
)

# Reestruturação de Créditos
from .modulo_reestruturacao import (
    SistemaReestruturacao,
    aplicar_reestruturacao_completa
)

# Períodos de Cura (integrado ao modulo_estadiamento)
from .modulo_estadiamento import PERIODOS_CURA

# Componentes legados (para compatibilidade)
try:
    from .ecl_engine import ECLEngine, ECLResult
    from .lgd_calculator import LGDCalculator
except ImportError:
    pass  # Esses módulos podem precisar de refatoração


__all__ = [
    # Pipeline principal
    'ECLPipeline',
    'ECLCompleteResult',
    
    # Grupos Homogêneos
    'GruposHomogeneosConsolidado',
    'CalculadorPDReais',
    
    # Forward Looking
    'ModeloForwardLooking',
    'coletar_series_historicas',
    'calcular_woe_scores',
    'WOE_SCORES',
    'EQUACOES_FL',
    
    # LGD
    'LGDSegmentado',
    
    # EAD
    'EADCCFEspecifico',
    
    # Estadiamento
    'classificar_estagio_aprimorado',
    'aplicar_regras_cura_estagio',
    'calcular_metricas_estagio',
    
    # Triggers
    'aplicar_todos_triggers_estagios',
    
    # Pisos Mínimos
    'aplicar_piso_minimo',
    'calcular_ecl_com_piso',
    'PISOS_MINIMOS_STAGE_3',
    
    # Write-off
    'processar_writeoff',
    
    # PD Behavior (Carteira)
    'calcular_pd_behavior',
    'executar_pd_behavior_completo',
    'filtrar_dados_behavior',
    'GRUPOS_HOMOGENEOS_BEHAVIOR',
    'FEATURES_PD_BEHAVIOR',
]
