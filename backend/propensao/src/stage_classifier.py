"""
Stage Classifier - IFRS 9 / BACEN 4966 Compliance

This module implements the 3-stage classification system for credit risk:
- Stage 1: Normal risk (ECL 12-month horizon)
- Stage 2: Significant increase in risk (ECL lifetime horizon)
- Stage 3: Default/Impairment (ECL lifetime with max LGD)

Key features:
- Stage classification based on multiple triggers
- Drag effect (arrasto): All products migrate when one goes to Stage 3
- Cure criteria: Conditions to reverse from higher to lower stages
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import logging

# Import shared utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    CRITERIOS_STAGE,
    CRITERIOS_CURA,
    PD_POR_RATING,
    PRINAD_TO_RATING,
    get_rating_from_prinad,
    calcular_pd_por_rating,
    get_stage_from_criteria,
    setup_logging
)

logger = setup_logging(__name__)


class Stage(Enum):
    """IFRS 9 Credit Risk Stages"""
    STAGE_1 = 1  # Normal risk - 12m ECL
    STAGE_2 = 2  # Significant increase in risk - Lifetime ECL
    STAGE_3 = 3  # Default/Impairment - Lifetime ECL with max LGD


class StageGatilho(Enum):
    """Triggers that cause stage migration"""
    NENHUM = "nenhum"
    DIAS_ATRASO = "dias_atraso"
    DOWNGRADE = "downgrade"
    REDUCAO_RENDA = "reducao_renda"
    AUMENTO_DTI = "aumento_dti"
    QUEDA_SCORE_EXTERNO = "queda_score_externo"
    EVENTO_JUDICIAL = "evento_judicial"
    INSOLVENCIA = "insolvencia"
    FALHA_RENEGOCIACAO = "falha_renegociacao"


@dataclass
class StageHistory:
    """Historical stage record for a client-product"""
    cliente_id: str
    produto: str
    stage: int
    data_classificacao: datetime
    gatilho: Optional[str] = None
    dias_atraso: int = 0
    rating: str = "A1"
    observacao: Optional[str] = None


@dataclass
class StageClassification:
    """Result of stage classification"""
    cliente_id: str
    produto: str
    stage: int
    stage_anterior: int
    ecl_horizonte: str  # '12_meses' or 'lifetime'
    gatilho: Optional[str]
    arrasto: bool
    arrasto_origem: Optional[str] = None  # Product that triggered drag
    data_classificacao: datetime = field(default_factory=datetime.now)
    detalhes: Dict = field(default_factory=dict)
    
    @property
    def migrou(self) -> bool:
        """Check if stage changed"""
        return self.stage != self.stage_anterior
    
    @property
    def piorou(self) -> bool:
        """Check if risk increased (stage went up)"""
        return self.stage > self.stage_anterior
    
    @property
    def melhorou(self) -> bool:
        """Check if risk decreased (stage went down)"""
        return self.stage < self.stage_anterior


@dataclass
class CureEvaluation:
    """Result of cure criteria evaluation"""
    cliente_id: str
    produto: str
    stage_atual: int
    stage_proposto: Optional[int]
    pode_curar: bool
    criterios_atendidos: Dict[str, bool]
    periodo_observacao: int
    meses_adimplente: int
    data_avaliacao: datetime = field(default_factory=datetime.now)
    observacao: Optional[str] = None


class StageClassifier:
    """
    IFRS 9 Stage Classifier
    
    Classifies credit exposures into 3 stages based on:
    - Days in arrears
    - Rating downgrades
    - Income reduction
    - DTI increase
    - External score drops
    - Judicial events
    
    Implements:
    - Stage migration rules
    - Drag effect (arrasto) for Stage 3
    - Cure criteria for stage reversal
    """
    
    # Rating order for downgrade calculation
    RATING_ORDER = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D', 'DEFAULT']
    
    def __init__(self, historico: List[StageHistory] = None):
        """
        Initialize classifier.
        
        Args:
            historico: Optional historical stage records for cure evaluation
        """
        self.historico = historico or []
        self.criterios_stage = CRITERIOS_STAGE
        self.criterios_cura = CRITERIOS_CURA
    
    def classificar_stage(
        self,
        cliente_id: str,
        produto: str,
        dias_atraso: int = 0,
        prinad: float = None,
        rating_atual: str = None,
        rating_anterior: str = None,
        renda_atual: float = None,
        renda_anterior: float = None,
        dti_atual: float = None,
        dti_anterior: float = None,
        score_externo_atual: int = None,
        score_externo_anterior: int = None,
        evento_judicial: bool = False,
        insolvencia: bool = False,
        falha_renegociacao: bool = False,
        stage_anterior: int = 1,
        outros_produtos_cliente: List[Dict] = None
    ) -> StageClassification:
        """
        Classify a client-product into an IFRS 9 stage.
        
        Args:
            cliente_id: Client identifier
            produto: Product name
            dias_atraso: Days in arrears
            prinad: PRINAD score (0-100)
            rating_atual: Current rating
            rating_anterior: Previous rating (for downgrade)
            renda_atual: Current income
            renda_anterior: Previous income (for reduction calc)
            dti_atual: Current DTI
            dti_anterior: Previous DTI
            score_externo_atual: Current external score
            score_externo_anterior: Previous external score
            evento_judicial: Has judicial event
            insolvencia: Is insolvent
            falha_renegociacao: Failed renegotiation
            stage_anterior: Previous stage (default 1)
            outros_produtos_cliente: Other products for drag check
            
        Returns:
            StageClassification with result
        """
        # Convert PRINAD to rating if not provided
        if rating_atual is None and prinad is not None:
            rating_atual = get_rating_from_prinad(prinad)
        if rating_atual is None:
            rating_atual = 'A1'
        
        # Check for drag effect first (any other product in Stage 3)
        arrasto = False
        arrasto_origem = None
        if outros_produtos_cliente:
            for outro in outros_produtos_cliente:
                if outro.get('stage') == 3 and outro.get('produto') != produto:
                    arrasto = True
                    arrasto_origem = outro.get('produto')
                    break
        
        # If drag effect applies, force Stage 3
        if arrasto:
            return StageClassification(
                cliente_id=cliente_id,
                produto=produto,
                stage=3,
                stage_anterior=stage_anterior,
                ecl_horizonte='lifetime_max_lgd',
                gatilho=StageGatilho.NENHUM.value,
                arrasto=True,
                arrasto_origem=arrasto_origem,
                detalhes={
                    'motivo': f'Arrasto de produto {arrasto_origem}',
                    'dias_atraso': dias_atraso,
                    'rating': rating_atual
                }
            )
        
        # Evaluate Stage 3 triggers first (most severe)
        stage3_result = self._check_stage3(
            dias_atraso=dias_atraso,
            evento_judicial=evento_judicial,
            insolvencia=insolvencia,
            falha_renegociacao=falha_renegociacao
        )
        
        if stage3_result['is_stage3']:
            return StageClassification(
                cliente_id=cliente_id,
                produto=produto,
                stage=3,
                stage_anterior=stage_anterior,
                ecl_horizonte='lifetime_max_lgd',
                gatilho=stage3_result['gatilho'],
                arrasto=False,
                detalhes={
                    'dias_atraso': dias_atraso,
                    'rating': rating_atual,
                    **stage3_result
                }
            )
        
        # Evaluate Stage 2 triggers
        stage2_result = self._check_stage2(
            dias_atraso=dias_atraso,
            rating_atual=rating_atual,
            rating_anterior=rating_anterior,
            renda_atual=renda_atual,
            renda_anterior=renda_anterior,
            dti_atual=dti_atual,
            dti_anterior=dti_anterior,
            score_externo_atual=score_externo_atual,
            score_externo_anterior=score_externo_anterior
        )
        
        if stage2_result['is_stage2']:
            return StageClassification(
                cliente_id=cliente_id,
                produto=produto,
                stage=2,
                stage_anterior=stage_anterior,
                ecl_horizonte='lifetime',
                gatilho=stage2_result['gatilho'],
                arrasto=False,
                detalhes={
                    'dias_atraso': dias_atraso,
                    'rating': rating_atual,
                    **stage2_result
                }
            )
        
        # Default to Stage 1
        return StageClassification(
            cliente_id=cliente_id,
            produto=produto,
            stage=1,
            stage_anterior=stage_anterior,
            ecl_horizonte='12_meses',
            gatilho=None,
            arrasto=False,
            detalhes={
                'dias_atraso': dias_atraso,
                'rating': rating_atual,
                'motivo': 'Sem gatilhos de migração'
            }
        )
    
    def _check_stage3(
        self,
        dias_atraso: int,
        evento_judicial: bool,
        insolvencia: bool,
        falha_renegociacao: bool
    ) -> Dict[str, Any]:
        """Check Stage 3 triggers."""
        stage3_config = self.criterios_stage['STAGE_3']
        gatilhos = stage3_config['gatilhos']
        
        triggers_found = []
        
        if dias_atraso >= gatilhos['dias_atraso_min']:
            triggers_found.append(StageGatilho.DIAS_ATRASO.value)
        if evento_judicial:
            triggers_found.append(StageGatilho.EVENTO_JUDICIAL.value)
        if insolvencia:
            triggers_found.append(StageGatilho.INSOLVENCIA.value)
        if falha_renegociacao:
            triggers_found.append(StageGatilho.FALHA_RENEGOCIACAO.value)
        
        is_stage3 = len(triggers_found) > 0
        
        return {
            'is_stage3': is_stage3,
            'gatilho': triggers_found[0] if triggers_found else None,
            'todos_gatilhos': triggers_found,
            'descricao': stage3_config['descricao'] if is_stage3 else None
        }
    
    def _check_stage2(
        self,
        dias_atraso: int,
        rating_atual: str,
        rating_anterior: str = None,
        renda_atual: float = None,
        renda_anterior: float = None,
        dti_atual: float = None,
        dti_anterior: float = None,
        score_externo_atual: int = None,
        score_externo_anterior: int = None
    ) -> Dict[str, Any]:
        """Check Stage 2 triggers."""
        stage2_config = self.criterios_stage['STAGE_2']
        gatilhos = stage2_config['gatilhos']
        
        triggers_found = []
        trigger_details = {}
        
        # Days in arrears (31-90)
        if dias_atraso >= gatilhos['dias_atraso_min'] and dias_atraso <= gatilhos['dias_atraso_max']:
            triggers_found.append(StageGatilho.DIAS_ATRASO.value)
            trigger_details['dias_atraso'] = dias_atraso
        
        # Rating downgrade
        if rating_anterior and rating_atual:
            downgrade = self._calculate_downgrade(rating_anterior, rating_atual)
            if downgrade >= gatilhos['downgrade_notches']:
                triggers_found.append(StageGatilho.DOWNGRADE.value)
                trigger_details['downgrade_notches'] = downgrade
        
        # Income reduction
        if renda_atual and renda_anterior and renda_anterior > 0:
            reducao = (renda_anterior - renda_atual) / renda_anterior
            if reducao >= gatilhos['reducao_renda_pct']:
                triggers_found.append(StageGatilho.REDUCAO_RENDA.value)
                trigger_details['reducao_renda_pct'] = round(reducao, 4)
        
        # DTI increase
        if dti_atual is not None and dti_anterior is not None:
            aumento_dti = dti_atual - dti_anterior
            if aumento_dti >= gatilhos['aumento_dti_pp']:
                triggers_found.append(StageGatilho.AUMENTO_DTI.value)
                trigger_details['aumento_dti_pp'] = round(aumento_dti, 4)
        
        # External score drop
        if score_externo_atual is not None and score_externo_anterior is not None:
            queda = score_externo_anterior - score_externo_atual
            if queda >= gatilhos['queda_score_externo']:
                triggers_found.append(StageGatilho.QUEDA_SCORE_EXTERNO.value)
                trigger_details['queda_score'] = queda
        
        is_stage2 = len(triggers_found) > 0
        
        return {
            'is_stage2': is_stage2,
            'gatilho': triggers_found[0] if triggers_found else None,
            'todos_gatilhos': triggers_found,
            'detalhes': trigger_details,
            'descricao': stage2_config['descricao'] if is_stage2 else None
        }
    
    def _calculate_downgrade(self, rating_anterior: str, rating_atual: str) -> int:
        """Calculate number of notches downgraded."""
        if rating_anterior not in self.RATING_ORDER:
            return 0
        if rating_atual not in self.RATING_ORDER:
            return 0
        
        idx_anterior = self.RATING_ORDER.index(rating_anterior)
        idx_atual = self.RATING_ORDER.index(rating_atual)
        
        return max(0, idx_atual - idx_anterior)
    
    def avaliar_cura(
        self,
        cliente_id: str,
        produto: str,
        stage_atual: int,
        meses_adimplente: int,
        rating_atual: str = None,
        rating_estabilizado: bool = True,
        sem_novos_atrasos: bool = True,
        sem_eventos_negativos_internos: bool = True,
        sem_eventos_negativos_scr: bool = True,
        debito_quitado: bool = False
    ) -> CureEvaluation:
        """
        Evaluate if a client-product can be cured (reversed to lower stage).
        
        Args:
            cliente_id: Client identifier
            produto: Product name
            stage_atual: Current stage
            meses_adimplente: Months without delinquency
            rating_atual: Current rating
            rating_estabilizado: Rating is stable or improved
            sem_novos_atrasos: No new arrears
            sem_eventos_negativos_internos: No internal negative events
            sem_eventos_negativos_scr: No SCR negative events
            debito_quitado: Debt fully paid (for Stage 3 → 2)
            
        Returns:
            CureEvaluation with result
        """
        # Stage 1 cannot be cured further
        if stage_atual == 1:
            return CureEvaluation(
                cliente_id=cliente_id,
                produto=produto,
                stage_atual=1,
                stage_proposto=None,
                pode_curar=False,
                criterios_atendidos={},
                periodo_observacao=0,
                meses_adimplente=meses_adimplente,
                observacao='Já está no Stage 1 (melhor possível)'
            )
        
        # Stage 2 → Stage 1
        if stage_atual == 2:
            cura_config = self.criterios_cura['STAGE_2_para_1']
            condicoes = cura_config['condicoes']
            
            criterios = {
                'meses_adimplente': meses_adimplente >= condicoes['adimplente_meses_consecutivos'],
                'rating_estabilizado': rating_estabilizado,
                'sem_novos_atrasos': sem_novos_atrasos,
                'sem_eventos_negativos_internos': sem_eventos_negativos_internos,
                'sem_eventos_negativos_scr': sem_eventos_negativos_scr
            }
            
            pode_curar = all(criterios.values())
            
            return CureEvaluation(
                cliente_id=cliente_id,
                produto=produto,
                stage_atual=2,
                stage_proposto=1 if pode_curar else None,
                pode_curar=pode_curar,
                criterios_atendidos=criterios,
                periodo_observacao=cura_config['periodo_observacao_meses'],
                meses_adimplente=meses_adimplente,
                observacao='Cura Stage 2 → 1' if pode_curar else 'Critérios não atendidos'
            )
        
        # Stage 3 → Stage 2
        if stage_atual == 3:
            cura_config = self.criterios_cura['STAGE_3_para_2']
            condicoes = cura_config['condicoes']
            
            # Check rating minimum
            rating_ok = False
            if rating_atual:
                rating_minimo = condicoes['rating_minimo']
                if rating_atual in self.RATING_ORDER and rating_minimo in self.RATING_ORDER:
                    rating_ok = self.RATING_ORDER.index(rating_atual) <= self.RATING_ORDER.index(rating_minimo)
            
            criterios = {
                'debito_quitado': debito_quitado,
                'meses_adimplente': meses_adimplente >= condicoes['adimplente_meses_consecutivos'],
                'rating_minimo': rating_ok
            }
            
            pode_curar = all(criterios.values())
            
            return CureEvaluation(
                cliente_id=cliente_id,
                produto=produto,
                stage_atual=3,
                stage_proposto=2 if pode_curar else None,
                pode_curar=pode_curar,
                criterios_atendidos=criterios,
                periodo_observacao=cura_config['periodo_observacao_meses'],
                meses_adimplente=meses_adimplente,
                observacao='Cura Stage 3 → 2' if pode_curar else 'Critérios não atendidos'
            )
        
        # Invalid stage
        return CureEvaluation(
            cliente_id=cliente_id,
            produto=produto,
            stage_atual=stage_atual,
            stage_proposto=None,
            pode_curar=False,
            criterios_atendidos={},
            periodo_observacao=0,
            meses_adimplente=meses_adimplente,
            observacao=f'Stage inválido: {stage_atual}'
        )
    
    def classificar_portfolio(
        self,
        clientes: List[Dict]
    ) -> Dict[str, List[StageClassification]]:
        """
        Classify all products for a list of clients.
        
        Implements drag effect: if any product goes to Stage 3,
        all other products of the same client also migrate.
        
        Args:
            clientes: List of client dicts with product details
            
        Returns:
            Dict mapping cliente_id to list of classifications
        """
        resultado = {}
        
        # Group products by client
        clientes_produtos = {}
        for cliente in clientes:
            cliente_id = cliente.get('cliente_id')
            if cliente_id not in clientes_produtos:
                clientes_produtos[cliente_id] = []
            clientes_produtos[cliente_id].append(cliente)
        
        # Process each client
        for cliente_id, produtos in clientes_produtos.items():
            classificacoes = []
            
            # First pass: classify without drag
            for produto_data in produtos:
                classificacao = self.classificar_stage(
                    cliente_id=cliente_id,
                    produto=produto_data.get('produto'),
                    dias_atraso=produto_data.get('dias_atraso', 0),
                    prinad=produto_data.get('prinad'),
                    rating_atual=produto_data.get('rating'),
                    rating_anterior=produto_data.get('rating_anterior'),
                    evento_judicial=produto_data.get('evento_judicial', False),
                    insolvencia=produto_data.get('insolvencia', False),
                    falha_renegociacao=produto_data.get('falha_renegociacao', False),
                    stage_anterior=produto_data.get('stage_anterior', 1)
                )
                classificacoes.append(classificacao)
            
            # Check for Stage 3 (drag trigger)
            stage3_produtos = [c for c in classificacoes if c.stage == 3 and not c.arrasto]
            
            if stage3_produtos:
                # Second pass: apply drag to all products
                arrasto_origem = stage3_produtos[0].produto
                
                for i, classificacao in enumerate(classificacoes):
                    if classificacao.stage != 3:
                        # Create new classification with drag
                        classificacoes[i] = StageClassification(
                            cliente_id=classificacao.cliente_id,
                            produto=classificacao.produto,
                            stage=3,
                            stage_anterior=classificacao.stage_anterior,
                            ecl_horizonte='lifetime_max_lgd',
                            gatilho=classificacao.gatilho,
                            arrasto=True,
                            arrasto_origem=arrasto_origem,
                            data_classificacao=datetime.now(),
                            detalhes={
                                **classificacao.detalhes,
                                'stage_original': classificacao.stage,
                                'motivo_arrasto': f'Arrasto de produto {arrasto_origem}'
                            }
                        )
            
            resultado[cliente_id] = classificacoes
        
        return resultado
    
    def gerar_relatorio(
        self,
        classificacoes: Dict[str, List[StageClassification]]
    ) -> Dict[str, Any]:
        """
        Generate summary report of stage classifications.
        
        Args:
            classificacoes: Result from classificar_portfolio
            
        Returns:
            Summary statistics
        """
        total_clientes = len(classificacoes)
        total_produtos = sum(len(v) for v in classificacoes.values())
        
        stage_counts = {1: 0, 2: 0, 3: 0}
        migracoes = {'piorou': 0, 'melhorou': 0, 'manteve': 0}
        arrastos = 0
        
        for cliente_id, lista in classificacoes.items():
            for c in lista:
                stage_counts[c.stage] += 1
                if c.piorou:
                    migracoes['piorou'] += 1
                elif c.melhorou:
                    migracoes['melhorou'] += 1
                else:
                    migracoes['manteve'] += 1
                if c.arrasto:
                    arrastos += 1
        
        return {
            'total_clientes': total_clientes,
            'total_produtos': total_produtos,
            'distribuicao_stage': {
                'stage_1': stage_counts[1],
                'stage_2': stage_counts[2],
                'stage_3': stage_counts[3],
                'pct_stage_1': round(stage_counts[1] / total_produtos * 100, 2) if total_produtos > 0 else 0,
                'pct_stage_2': round(stage_counts[2] / total_produtos * 100, 2) if total_produtos > 0 else 0,
                'pct_stage_3': round(stage_counts[3] / total_produtos * 100, 2) if total_produtos > 0 else 0
            },
            'migracoes': migracoes,
            'arrastos': arrastos,
            'data_geracao': datetime.now().isoformat()
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def classificar_stage_simples(
    dias_atraso: int = 0,
    prinad: float = None,
    evento_judicial: bool = False
) -> int:
    """
    Simple stage classification for quick checks.
    
    Args:
        dias_atraso: Days in arrears
        prinad: PRINAD score (0-100)
        evento_judicial: Has judicial event
        
    Returns:
        Stage number (1, 2, or 3)
    """
    # Stage 3 checks
    if dias_atraso > 90 or evento_judicial:
        return 3
    
    # Stage 2 checks
    if dias_atraso >= 31:
        return 2
    
    # Check PRINAD if provided
    if prinad is not None and prinad >= 85:  # D rating or worse
        return 2
    
    return 1


def calcular_ecl_horizonte(stage: int) -> str:
    """
    Get ECL horizon based on stage.
    
    Args:
        stage: IFRS 9 stage (1, 2, or 3)
        
    Returns:
        ECL horizon string
    """
    horizontes = {
        1: '12_meses',
        2: 'lifetime',
        3: 'lifetime_max_lgd'
    }
    return horizontes.get(stage, '12_meses')


def verificar_arrasto(
    cliente_produtos: List[Dict]
) -> Tuple[bool, Optional[str]]:
    """
    Check if drag effect should apply.
    
    Args:
        cliente_produtos: List of product dicts with 'produto' and 'stage'
        
    Returns:
        Tuple of (should_drag, trigger_product)
    """
    for produto in cliente_produtos:
        if produto.get('stage') == 3:
            return True, produto.get('produto')
    return False, None


# =============================================================================
# MAIN EXECUTION (for testing)
# =============================================================================

if __name__ == '__main__':
    # Test the classifier
    print("Testing StageClassifier...")
    
    classifier = StageClassifier()
    
    # Test 1: Normal client (Stage 1)
    result = classifier.classificar_stage(
        cliente_id='CLI001',
        produto='consignado',
        dias_atraso=0,
        prinad=15.0
    )
    print(f"\nTest 1 - Normal: Stage {result.stage} (expected 1)")
    
    # Test 2: Delayed client (Stage 2)
    result = classifier.classificar_stage(
        cliente_id='CLI002',
        produto='consignado',
        dias_atraso=45,
        prinad=50.0
    )
    print(f"Test 2 - Delayed 45d: Stage {result.stage} (expected 2)")
    
    # Test 3: Default client (Stage 3)
    result = classifier.classificar_stage(
        cliente_id='CLI003',
        produto='consignado',
        dias_atraso=95,
        prinad=90.0
    )
    print(f"Test 3 - Delayed 95d: Stage {result.stage} (expected 3)")
    
    # Test 4: Judicial event (Stage 3)
    result = classifier.classificar_stage(
        cliente_id='CLI004',
        produto='consignado',
        dias_atraso=0,
        evento_judicial=True
    )
    print(f"Test 4 - Judicial: Stage {result.stage} (expected 3)")
    
    # Test 5: Cure evaluation
    cure = classifier.avaliar_cura(
        cliente_id='CLI005',
        produto='consignado',
        stage_atual=2,
        meses_adimplente=6,
        rating_estabilizado=True,
        sem_novos_atrasos=True,
        sem_eventos_negativos_internos=True,
        sem_eventos_negativos_scr=True
    )
    print(f"Test 5 - Cure S2→S1: Can cure? {cure.pode_curar} (expected True)")
    
    # Test 6: Portfolio classification with drag
    clientes = [
        {'cliente_id': 'CLI006', 'produto': 'consignado', 'dias_atraso': 95},
        {'cliente_id': 'CLI006', 'produto': 'cartao_credito', 'dias_atraso': 0},
        {'cliente_id': 'CLI006', 'produto': 'imobiliario', 'dias_atraso': 0},
    ]
    portfolio_result = classifier.classificar_portfolio(clientes)
    print(f"\nTest 6 - Portfolio with drag:")
    for c in portfolio_result['CLI006']:
        print(f"  {c.produto}: Stage {c.stage} (arrasto: {c.arrasto})")
    
    print("\n✓ All tests completed!")
