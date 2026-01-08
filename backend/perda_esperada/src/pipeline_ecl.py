"""
Pipeline ECL Integrado - BACEN 4966/IFRS 9 Compliant

Este pipeline CONSOME os resultados do módulo PRINAD e adiciona
as funcionalidades específicas do módulo perda_esperada:
- Grupos Homogêneos de Risco
- Forward Looking (K_PD_FL, K_LGD_FL)
- LGD Segmentado
- EAD com CCF específico
- Pisos Mínimos (Stage 3)

O PRINAD já fornece: PRINAD, Rating, PD_12m, PD_lifetime, Stage
Este módulo NÃO duplica esses cálculos.
"""

import logging
import sys
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

# Adicionar caminhos ao sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import do PRINAD (módulo anterior no fluxo)
try:
    from prinad.src.classifier import ClassificationResult
    PRINAD_AVAILABLE = True
except ImportError:
    PRINAD_AVAILABLE = False
    ClassificationResult = None

# Imports do shared/utils
try:
    from shared.utils import (
        calcular_ecl_por_stage,
        LGD_POR_PRODUTO,
        CCF_POR_PRODUTO
    )
    SHARED_AVAILABLE = True
except ImportError:
    SHARED_AVAILABLE = False

# Imports locais
from .modulo_grupos_homogeneos import GruposHomogeneosConsolidado
from .modulo_forward_looking import (
    ModeloForwardLooking,
    WOE_SCORES,
    EQUACOES_FL
)
# Forward Looking Multi-Cenário (CMN 4966 Art. 36 §5º)
from .cenarios_forward_looking import GerenciadorCenarios, TipoCenario
from .modulo_lgd_segmentado import LGDSegmentado
from .modulo_ead_ccf_especifico import EADCCFEspecifico
from .pisos_minimos import aplicar_piso_minimo, obter_carteira_produto

logger = logging.getLogger(__name__)


@dataclass
class ECLCompleteResult:
    """Resultado completo do cálculo de ECL."""
    # Identificação
    cliente_id: str
    produto: str
    data_calculo: str
    
    # Do PRINAD (recebido como input)
    prinad: float
    rating: str
    pd_12m: float
    pd_lifetime: float
    stage: int
    
    # Forward Looking
    grupo_homogeneo: int
    woe_score: float
    k_pd_fl: float
    pd_ajustado: float
    
    # Forward Looking Multi-Cenário
    usar_multi_cenario: bool = False
    cenarios_detalhes: dict = None  # Detalhes dos cenários aplicados
    
    # LGD
    lgd_base: float
    lgd_segmentado: float
    k_lgd_fl: float
    lgd_final: float
    
    # EAD
    saldo_utilizado: float
    limite_disponivel: float
    ccf: float
    ead: float
    
    # ECL
    ecl_antes_piso: float
    ecl_final: float
    piso_aplicado: bool
    piso_percentual: float
    
    # Meta
    horizonte_ecl: str  # '12m' ou 'lifetime'
    carteira_regulatoria: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ECLPipeline:
    """
    Pipeline integrado para cálculo de ECL.
    
    Integra:
    - Resultado do PRINAD (pd_12m, pd_lifetime, stage)
    - Grupos Homogêneos de Risco
    - Forward Looking
    - LGD Segmentado
    - EAD com CCF
    - Pisos Mínimos
    """
    
    def __init__(
        self,
        usar_forward_looking: bool = True,
        usar_lgd_segmentado: bool = True,
        usar_ccf_especifico: bool = True,
        aplicar_pisos: bool = True,
        usar_multi_cenario: bool = True  # Novo: Multi-Cenário CMN 4966
    ):
        """
        Inicializa o pipeline.
        
        Args:
            usar_forward_looking: Aplicar ajuste Forward Looking
            usar_lgd_segmentado: Usar LGD por árvore de decisão
            usar_ccf_especifico: Usar CCF específico por produto
            aplicar_pisos: Aplicar pisos mínimos para Stage 3
            usar_multi_cenario: Usar cenários ponderados (CMN 4966 Art. 36 §5º)
        """
        self.usar_forward_looking = usar_forward_looking
        self.usar_lgd_segmentado = usar_lgd_segmentado
        self.usar_ccf_especifico = usar_ccf_especifico
        self.aplicar_pisos = aplicar_pisos
        self.usar_multi_cenario = usar_multi_cenario
        
        # Inicializar componentes
        self.grupos_homogeneos = GruposHomogeneosConsolidado()
        
        # Inicializar modelos Forward Looking por produto
        self.modelos_fl = {
            'parcelados': ModeloForwardLooking('parcelados'),
            'consignado': ModeloForwardLooking('consignado'),
            'rotativos': ModeloForwardLooking('rotativos')
        }
        
        # LGD e EAD
        self.lgd_segmentado = LGDSegmentado()
        self.ead_ccf = EADCCFEspecifico()
        
        # Forward Looking Multi-Cenário (CMN 4966 Art. 36 §5º)
        self.gerenciador_cenarios = GerenciadorCenarios() if usar_multi_cenario else None
        
        logger.info(f"ECLPipeline inicializado (multi_cenario={usar_multi_cenario})")
    
    def _mapear_produto_para_tipo_fl(self, produto: str) -> str:
        """Mapeia produto para tipo usado no Forward Looking."""
        produto_lower = produto.lower()
        
        if any(x in produto_lower for x in ['consignado', 'inss']):
            return 'consignado'
        elif any(x in produto_lower for x in ['cartao', 'cheque', 'rotativo', 'banparacard']):
            return 'rotativos'
        else:
            return 'parcelados'
    
    def _obter_grupo_homogeneo(self, prinad: float) -> int:
        """
        Obtém grupo homogêneo baseado no score PRINAD.
        
        Usa os 4 grupos padrão da documentação:
        - Grupo 1: 0-25% (baixo risco)
        - Grupo 2: 25-50% (risco moderado)
        - Grupo 3: 50-75% (risco alto)
        - Grupo 4: 75-100% (risco muito alto)
        """
        if prinad < 25:
            return 1
        elif prinad < 50:
            return 2
        elif prinad < 75:
            return 3
        else:
            return 4
    
    def _calcular_k_pd_fl(
        self,
        tipo_produto: str,
        grupo_homogeneo: int,
        dados_macro: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Calcula fator K_PD_FL (Forward Looking).
        
        Se usar_multi_cenario=True, calcula usando cenários ponderados (CMN 4966 Art. 36 §5º):
        K_PD_FL = Σ(peso_i × K_cenario_i)
        
        Caso contrário, usa cálculo simples com trava de ±10%.
        
        Returns:
            Dict com k_pd_fl, k_lgd_fl e detalhes dos cenários
        """
        if not self.usar_forward_looking:
            return {'k_pd_fl': 1.0, 'k_lgd_fl': 1.0, 'cenarios_detalhes': None}
        
        # ========== MULTI-CENÁRIO (CMN 4966 Art. 36 §5º) ==========
        if self.usar_multi_cenario and self.gerenciador_cenarios:
            try:
                cenarios = self.gerenciador_cenarios.criar_cenarios()
                
                # Calcular K_PD_FL ponderado
                k_pd_fl, detalhes_pd = self.gerenciador_cenarios.calcular_k_pd_fl_ponderado(0.10, cenarios)
                
                # Calcular K_LGD_FL ponderado
                k_lgd_fl, detalhes_lgd = self.gerenciador_cenarios.calcular_k_lgd_fl_ponderado(0.45, cenarios)
                
                cenarios_detalhes = {
                    'cenarios': [c.to_dict() for c in cenarios],
                    'k_pd_detalhes': detalhes_pd,
                    'k_lgd_detalhes': detalhes_lgd
                }
                
                logger.debug(f"Multi-cenário: K_PD_FL={k_pd_fl:.4f}, K_LGD_FL={k_lgd_fl:.4f}")
                
                return {
                    'k_pd_fl': k_pd_fl,
                    'k_lgd_fl': k_lgd_fl,
                    'cenarios_detalhes': cenarios_detalhes
                }
            except Exception as e:
                logger.warning(f"Erro no multi-cenário: {e}. Usando cálculo simples.")
        
        # ========== CÁLCULO SIMPLES (fallback) ==========
        if tipo_produto not in self.modelos_fl:
            return {'k_pd_fl': 1.0, 'k_lgd_fl': 1.0, 'cenarios_detalhes': None}
        
        modelo = self.modelos_fl[tipo_produto]
        
        # Obter WOE score do grupo
        woe_score = WOE_SCORES.get(tipo_produto, {}).get(grupo_homogeneo, 0.0)
        
        # Dados macroeconômicos default se não fornecidos
        if dados_macro is None:
            dados_macro = {
                'PIB': 7000000,  # PIB em milhões
                'INADIMPLENCIA_PF': 4.5,
                'SELIC': 12.25,
                'IPCA': 4.5
            }
        
        # Calcular PD FL usando modelo
        try:
            pd_fl = modelo.aplicar_equacao_documentada(dados_macro, grupo_homogeneo)
            
            # K é a razão entre PD_FL e PD médio do WOE
            woe_medio = WOE_SCORES.get(tipo_produto, {}).get(grupo_homogeneo, 0.1)
            if woe_medio > 0:
                k_raw = pd_fl / woe_medio
            else:
                k_raw = 1.0
            
            # Aplicar trava de ±10%
            k_pd_fl = max(0.90, min(1.10, k_raw))
            
            return {'k_pd_fl': k_pd_fl, 'k_lgd_fl': 1.0, 'cenarios_detalhes': None}
        except Exception as e:
            logger.warning(f"Erro ao calcular K_PD_FL: {e}. Retornando 1.0")
            return {'k_pd_fl': 1.0, 'k_lgd_fl': 1.0, 'cenarios_detalhes': None}
    
    def _calcular_lgd(
        self,
        produto: str,
        dias_atraso: int,
        valor_operacao: float = None,
        prazo_remanescente: int = None,
        ocupacao: str = None
    ) -> Dict[str, float]:
        """
        Calcula LGD usando modelo segmentado ou básico.
        """
        # LGD base do produto
        lgd_base = LGD_POR_PRODUTO.get(produto.lower(), 0.45) if SHARED_AVAILABLE else 0.45
        
        if not self.usar_lgd_segmentado:
            return {
                'lgd_base': lgd_base,
                'lgd_segmentado': lgd_base,
                'k_lgd_fl': 1.0,
                'lgd_final': lgd_base
            }
        
        # Usar LGD segmentado
        try:
            lgd_seg_result = self.lgd_segmentado.calcular_lgd(
                produto=produto,
                dias_atraso=dias_atraso,
                valor_operacao=valor_operacao or 5000,
                prazo_remanescente=prazo_remanescente or 36,
                ocupacao=ocupacao or 'ASSALARIADO'
            )
            
            lgd_segmentado = lgd_seg_result.get('lgd', lgd_base)
            
            # K_LGD_FL (simplificado - pode ser expandido)
            k_lgd_fl = 1.0
            
            return {
                'lgd_base': lgd_base,
                'lgd_segmentado': lgd_segmentado,
                'k_lgd_fl': k_lgd_fl,
                'lgd_final': lgd_segmentado * k_lgd_fl
            }
        except Exception as e:
            logger.warning(f"Erro ao calcular LGD segmentado: {e}. Usando LGD base.")
            return {
                'lgd_base': lgd_base,
                'lgd_segmentado': lgd_base,
                'k_lgd_fl': 1.0,
                'lgd_final': lgd_base
            }
    
    def _calcular_ead(
        self,
        produto: str,
        saldo_utilizado: float,
        limite_total: float
    ) -> Dict[str, float]:
        """
        Calcula EAD com CCF específico.
        """
        limite_disponivel = max(0, limite_total - saldo_utilizado)
        
        if self.usar_ccf_especifico:
            try:
                ead_result = self.ead_ccf.calcular_ead(
                    produto=produto,
                    saldo_utilizado=saldo_utilizado,
                    limite_disponivel=limite_disponivel
                )
                ccf = ead_result.get('ccf', 0.75)
                ead = ead_result.get('ead', saldo_utilizado + limite_disponivel * ccf)
            except Exception as e:
                logger.warning(f"Erro ao calcular EAD específico: {e}. Usando método básico.")
                ccf = CCF_POR_PRODUTO.get(produto.lower(), 0.75) if SHARED_AVAILABLE else 0.75
                ead = saldo_utilizado + limite_disponivel * ccf
        else:
            ccf = CCF_POR_PRODUTO.get(produto.lower(), 0.75) if SHARED_AVAILABLE else 0.75
            ead = saldo_utilizado + limite_disponivel * ccf
        
        return {
            'saldo_utilizado': saldo_utilizado,
            'limite_disponivel': limite_disponivel,
            'ccf': ccf,
            'ead': ead
        }
    
    def calcular_ecl_completo(
        self,
        cliente_id: str,
        produto: str,
        saldo_utilizado: float,
        limite_total: float,
        dias_atraso: int,
        # Dados do PRINAD (obrigatórios)
        prinad: float,
        rating: str,
        pd_12m: float,
        pd_lifetime: float,
        stage: int,
        # Dados opcionais
        valor_operacao: float = None,
        prazo_remanescente: int = None,
        ocupacao: str = None,
        dados_macro: Dict[str, float] = None
    ) -> ECLCompleteResult:
        """
        Calcula ECL completo integrando PRINAD com módulos locais.
        
        Args:
            cliente_id: ID do cliente
            produto: Nome do produto
            saldo_utilizado: Saldo devedor atual
            limite_total: Limite total de crédito
            dias_atraso: Dias em atraso
            
            # Dados do PRINAD (obrigatórios - já calculados pelo módulo anterior)
            prinad: Score PRINAD (0-100)
            rating: Rating (A1 a DEFAULT)
            pd_12m: PD 12 meses (já calculado pelo PRINAD)
            pd_lifetime: PD Lifetime (já calculado pelo PRINAD)
            stage: Estágio IFRS 9 (1, 2 ou 3)
            
            # Opcionais para LGD segmentado
            valor_operacao: Valor da operação
            prazo_remanescente: Prazo remanescente em meses
            ocupacao: Ocupação do cliente
            dados_macro: Dados macroeconômicos para Forward Looking
            
        Returns:
            ECLCompleteResult com todos os detalhes do cálculo
        """
        logger.info(f"Calculando ECL para cliente={cliente_id}, produto={produto}, stage={stage}")
        
        # 1. Determinar grupo homogêneo com base no PRINAD
        grupo_homogeneo = self._obter_grupo_homogeneo(prinad)
        
        # 2. Mapear produto para tipo de Forward Looking
        tipo_produto_fl = self._mapear_produto_para_tipo_fl(produto)
        
        # 3. Obter WOE score
        woe_score = WOE_SCORES.get(tipo_produto_fl, {}).get(grupo_homogeneo, 0.0)
        
        # 4. Calcular K_PD_FL e K_LGD_FL (Forward Looking Multi-Cenário)
        fl_result = self._calcular_k_pd_fl(tipo_produto_fl, grupo_homogeneo, dados_macro)
        k_pd_fl = fl_result['k_pd_fl']
        k_lgd_fl_from_cenario = fl_result.get('k_lgd_fl', 1.0)
        cenarios_detalhes = fl_result.get('cenarios_detalhes')
        
        # 5. Selecionar PD base conforme stage (usa valores do PRINAD!)
        if stage == 1:
            pd_base = pd_12m
            horizonte_ecl = '12m'
        else:  # Stage 2 ou 3
            pd_base = pd_lifetime
            horizonte_ecl = 'lifetime'
        
        # 6. Aplicar Forward Looking ao PD
        pd_ajustado = pd_base * k_pd_fl
        
        # 7. Calcular LGD
        lgd_result = self._calcular_lgd(
            produto=produto,
            dias_atraso=dias_atraso,
            valor_operacao=valor_operacao,
            prazo_remanescente=prazo_remanescente,
            ocupacao=ocupacao
        )
        
        # 8. Calcular EAD
        ead_result = self._calcular_ead(
            produto=produto,
            saldo_utilizado=saldo_utilizado,
            limite_total=limite_total
        )
        
        # 9. Calcular ECL = PD × LGD × EAD
        ecl_calculado = pd_ajustado * lgd_result['lgd_final'] * ead_result['ead']
        
        # 10. Aplicar piso mínimo (Stage 3 apenas)
        carteira = obter_carteira_produto(produto)
        
        if self.aplicar_pisos and stage == 3:
            piso_result = aplicar_piso_minimo(
                ecl_calculado=ecl_calculado,
                ead=ead_result['ead'],
                dias_atraso=dias_atraso,
                produto=produto,
                stage=stage
            )
            ecl_final = piso_result.ecl_ajustado
            piso_aplicado = piso_result.piso_foi_aplicado
            piso_percentual = piso_result.piso_aplicado
        else:
            ecl_final = ecl_calculado
            piso_aplicado = False
            piso_percentual = 0.0
        
        # Construir resultado
        resultado = ECLCompleteResult(
            cliente_id=cliente_id,
            produto=produto,
            data_calculo=datetime.now().isoformat(),
            
            # Do PRINAD
            prinad=prinad,
            rating=rating,
            pd_12m=pd_12m,
            pd_lifetime=pd_lifetime,
            stage=stage,
            
            # Forward Looking
            grupo_homogeneo=grupo_homogeneo,
            woe_score=woe_score,
            k_pd_fl=k_pd_fl,
            pd_ajustado=pd_ajustado,
            
            # Forward Looking Multi-Cenário
            usar_multi_cenario=self.usar_multi_cenario,
            cenarios_detalhes=cenarios_detalhes,
            
            # LGD
            lgd_base=lgd_result['lgd_base'],
            lgd_segmentado=lgd_result['lgd_segmentado'],
            k_lgd_fl=lgd_result['k_lgd_fl'] if not self.usar_multi_cenario else k_lgd_fl_from_cenario,
            lgd_final=lgd_result['lgd_final'] * (k_lgd_fl_from_cenario if self.usar_multi_cenario else 1.0),
            
            # EAD
            saldo_utilizado=ead_result['saldo_utilizado'],
            limite_disponivel=ead_result['limite_disponivel'],
            ccf=ead_result['ccf'],
            ead=ead_result['ead'],
            
            # ECL
            ecl_antes_piso=ecl_calculado,
            ecl_final=ecl_final,
            piso_aplicado=piso_aplicado,
            piso_percentual=piso_percentual,
            
            # Meta
            horizonte_ecl=horizonte_ecl,
            carteira_regulatoria=carteira
        )
        
        logger.info(f"ECL calculado: R$ {ecl_final:.2f} (stage={stage}, GH={grupo_homogeneo})")
        
        return resultado
    
    def calcular_ecl_de_prinad_result(
        self,
        prinad_result,  # ClassificationResult do PRINAD
        produto: str,
        saldo_utilizado: float,
        limite_total: float,
        dias_atraso: int,
        **kwargs
    ) -> ECLCompleteResult:
        """
        Calcula ECL a partir de um ClassificationResult do PRINAD.
        
        Método de conveniência que extrai os dados do resultado do PRINAD.
        """
        if not PRINAD_AVAILABLE:
            raise ImportError("Módulo PRINAD não disponível")
        
        return self.calcular_ecl_completo(
            cliente_id=prinad_result.cpf,
            produto=produto,
            saldo_utilizado=saldo_utilizado,
            limite_total=limite_total,
            dias_atraso=dias_atraso,
            prinad=prinad_result.prinad,
            rating=prinad_result.rating,
            pd_12m=prinad_result.pd_12m,
            pd_lifetime=prinad_result.pd_lifetime,
            stage=prinad_result.estagio_pe,
            **kwargs
        )


if __name__ == '__main__':
    # Teste do pipeline
    logging.basicConfig(level=logging.INFO)
    
    print("=== Teste do ECL Pipeline ===\n")
    
    pipeline = ECLPipeline()
    
    # Simular dados do PRINAD
    resultado = pipeline.calcular_ecl_completo(
        cliente_id='12345678901',
        produto='consignado',
        saldo_utilizado=5000,
        limite_total=10000,
        dias_atraso=0,
        # Dados do PRINAD
        prinad=25.0,
        rating='B1',
        pd_12m=0.025,
        pd_lifetime=0.12,
        stage=1
    )
    
    print(f"Cliente: {resultado.cliente_id}")
    print(f"Produto: {resultado.produto}")
    print(f"PRINAD: {resultado.prinad}% ({resultado.rating})")
    print(f"Stage: {resultado.stage}")
    print(f"Grupo Homogêneo: {resultado.grupo_homogeneo}")
    print(f"WOE Score: {resultado.woe_score:.4f}")
    print(f"K_PD_FL: {resultado.k_pd_fl:.4f}")
    print(f"PD Base: {resultado.pd_12m if resultado.stage == 1 else resultado.pd_lifetime:.4%}")
    print(f"PD Ajustado: {resultado.pd_ajustado:.4%}")
    print(f"LGD Final: {resultado.lgd_final:.2%}")
    print(f"EAD: R$ {resultado.ead:,.2f}")
    print(f"ECL: R$ {resultado.ecl_final:,.2f}")
    print(f"Horizonte: {resultado.horizonte_ecl}")
