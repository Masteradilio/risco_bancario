#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitários para o módulo de Sistema de Cura Formal.

Testa a conformidade com Art. 41 da Resolução CMN 4.966/2021.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Adicionar path do módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sistema_cura import (
    MotivoMigracao,
    StatusCura,
    HistoricoEstagio,
    ResultadoCura,
    CriteriosCura,
    SistemaCura,
    get_sistema_cura,
    avaliar_cura
)


class TestMotivoMigracao:
    """Testes para o enum MotivoMigracao."""
    
    def test_motivos_existem(self):
        """Deve existir os motivos principais."""
        assert MotivoMigracao.ATRASO_30_DIAS
        assert MotivoMigracao.ATRASO_90_DIAS
        assert MotivoMigracao.REESTRUTURACAO
        assert MotivoMigracao.CURA_APROVADA


class TestStatusCura:
    """Testes para o enum StatusCura."""
    
    def test_status_existem(self):
        """Deve existir os status principais."""
        assert StatusCura.NAO_APLICAVEL
        assert StatusCura.EM_OBSERVACAO
        assert StatusCura.ELEGIVEL
        assert StatusCura.APROVADO
        assert StatusCura.REPROVADO


class TestHistoricoEstagio:
    """Testes para HistoricoEstagio."""
    
    def test_criacao_historico(self):
        """Deve criar registro histórico corretamente."""
        agora = datetime.now()
        
        historico = HistoricoEstagio(
            data=agora,
            estagio_anterior=1,
            estagio_novo=2,
            motivo=MotivoMigracao.ATRASO_30_DIAS,
            dias_atraso=35,
            pd_atual=0.15
        )
        
        assert historico.estagio_anterior == 1
        assert historico.estagio_novo == 2
        assert historico.motivo == MotivoMigracao.ATRASO_30_DIAS
    
    def test_to_dict(self):
        """Deve converter para dicionário."""
        historico = HistoricoEstagio(
            data=datetime.now(),
            estagio_anterior=1,
            estagio_novo=2,
            motivo=MotivoMigracao.ATRASO_30_DIAS
        )
        
        d = historico.to_dict()
        
        assert "data" in d
        assert "estagio_anterior" in d
        assert "motivo" in d


class TestCriteriosCura:
    """Testes para CriteriosCura."""
    
    def test_criterios_stage2_para_stage1(self):
        """Critérios para Stage 2 → 1 devem estar corretos."""
        criterios = SistemaCura.CRITERIOS_CURA[(2, 1)]
        
        assert criterios.meses_minimos == 6
        assert criterios.dias_atraso_maximo == 30
        assert criterios.requer_melhora_pd == True
    
    def test_criterios_stage3_para_stage2(self):
        """Critérios para Stage 3 → 2 devem estar corretos."""
        criterios = SistemaCura.CRITERIOS_CURA[(3, 2)]
        
        assert criterios.meses_minimos == 12
        assert criterios.requer_amortizacao == True
        assert criterios.percentual_amortizacao == 0.30


class TestSistemaCura:
    """Testes para o SistemaCura."""
    
    @pytest.fixture
    def sistema(self):
        """Cria instância do sistema para testes."""
        return SistemaCura()
    
    def test_inicializacao(self, sistema):
        """Deve inicializar corretamente."""
        assert sistema._historico == {}
        assert sistema._em_cura == {}
    
    def test_registrar_migracao(self, sistema):
        """Deve registrar migração no histórico."""
        sistema.registrar_migracao(
            contrato_id="CTR001",
            estagio_anterior=1,
            estagio_novo=2,
            motivo=MotivoMigracao.ATRASO_30_DIAS
        )
        
        assert "CTR001" in sistema._historico
        assert len(sistema._historico["CTR001"]) == 1
    
    def test_iniciar_periodo_cura(self, sistema):
        """Deve iniciar período de cura."""
        sistema.iniciar_periodo_cura("CTR001")
        
        assert "CTR001" in sistema._em_cura
    
    def test_calcular_meses_observacao(self, sistema):
        """Deve calcular meses em observação corretamente."""
        data_inicio = datetime.now() - timedelta(days=180)  # 6 meses atrás
        sistema._em_cura["CTR001"] = data_inicio
        
        meses = sistema.calcular_meses_em_observacao("CTR001")
        
        assert meses >= 5  # Aproximadamente 6 meses
        assert meses <= 7
    
    def test_contrato_sem_cura_retorna_zero_meses(self, sistema):
        """Contrato sem período de cura deve retornar 0 meses."""
        meses = sistema.calcular_meses_em_observacao("INEXISTENTE")
        
        assert meses == 0
    
    def test_eh_reestruturacao(self, sistema):
        """Deve identificar reestruturações corretamente."""
        sistema.registrar_migracao(
            contrato_id="CTR001",
            estagio_anterior=1,
            estagio_novo=3,
            motivo=MotivoMigracao.REESTRUTURACAO
        )
        
        assert sistema.eh_reestruturacao("CTR001") == True
        assert sistema.eh_reestruturacao("CTR002") == False
    
    def test_stage1_nao_aplicavel(self, sistema):
        """Stage 1 não deve ter cura (já é o melhor)."""
        resultado = sistema.avaliar_elegibilidade_cura(
            contrato_id="CTR001",
            estagio_atual=1,
            dias_atraso=0,
            pd_atual=0.05
        )
        
        assert resultado.status == StatusCura.NAO_APLICAVEL
        assert resultado.elegivel_cura == False
    
    def test_stage2_em_observacao(self, sistema):
        """Stage 2 recém-migrado deve estar em observação."""
        # Registrar migração recente
        sistema.registrar_migracao(
            contrato_id="CTR001",
            estagio_anterior=1,
            estagio_novo=2,
            motivo=MotivoMigracao.ATRASO_30_DIAS,
            pd_atual=0.15
        )
        
        resultado = sistema.avaliar_elegibilidade_cura(
            contrato_id="CTR001",
            estagio_atual=2,
            dias_atraso=0,
            pd_atual=0.10
        )
        
        assert resultado.status == StatusCura.EM_OBSERVACAO
        assert resultado.meses_em_observacao < resultado.meses_necessarios
    
    def test_stage2_elegivel_apos_6_meses(self, sistema):
        """Stage 2 deve estar elegível após 6 meses adimplente."""
        # Registrar migração antiga
        data_migracao = datetime.now() - timedelta(days=200)  # ~6.5 meses
        
        sistema.registrar_migracao(
            contrato_id="CTR001",
            estagio_anterior=1,
            estagio_novo=2,
            motivo=MotivoMigracao.ATRASO_30_DIAS,
            pd_atual=0.15,
            data=data_migracao
        )
        
        sistema.iniciar_periodo_cura("CTR001", data_migracao)
        
        resultado = sistema.avaliar_elegibilidade_cura(
            contrato_id="CTR001",
            estagio_atual=2,
            dias_atraso=0,
            pd_atual=0.10  # Melhorou o PD
        )
        
        assert resultado.meses_em_observacao >= 6
        assert resultado.elegivel_cura == True
    
    def test_stage3_requer_12_meses(self, sistema):
        """Stage 3 deve requerer 12 meses para cura."""
        criterios = SistemaCura.CRITERIOS_CURA[(3, 2)]
        assert criterios.meses_minimos == 12
    
    def test_stage3_requer_amortizacao(self, sistema):
        """Stage 3 deve requerer amortização mínima."""
        # Registrar migração antiga
        data_migracao = datetime.now() - timedelta(days=400)  # ~13 meses
        
        sistema.registrar_migracao(
            contrato_id="CTR001",
            estagio_anterior=1,
            estagio_novo=3,
            motivo=MotivoMigracao.ATRASO_90_DIAS,
            pd_atual=0.20,
            data=data_migracao
        )
        
        sistema.iniciar_periodo_cura("CTR001", data_migracao)
        
        # Sem amortização suficiente
        resultado = sistema.avaliar_elegibilidade_cura(
            contrato_id="CTR001",
            estagio_atual=3,
            dias_atraso=0,
            pd_atual=0.12,
            percentual_amortizacao=0.10  # Apenas 10%
        )
        
        assert resultado.elegivel_cura == False
        assert "Amortização" in resultado.motivo
    
    def test_stage3_elegivel_com_amortizacao(self, sistema):
        """Stage 3 deve estar elegível com amortização ≥30%."""
        data_migracao = datetime.now() - timedelta(days=400)
        
        sistema.registrar_migracao(
            contrato_id="CTR001",
            estagio_anterior=1,
            estagio_novo=3,
            motivo=MotivoMigracao.ATRASO_90_DIAS,
            pd_atual=0.20,
            data=data_migracao
        )
        
        sistema.iniciar_periodo_cura("CTR001", data_migracao)
        
        resultado = sistema.avaliar_elegibilidade_cura(
            contrato_id="CTR001",
            estagio_atual=3,
            dias_atraso=0,
            pd_atual=0.12,
            percentual_amortizacao=0.35  # 35% amortizado
        )
        
        assert resultado.elegivel_cura == True
    
    def test_atraso_reseta_periodo_cura(self, sistema):
        """Novo atraso deve resetar o período de cura."""
        data_migracao = datetime.now() - timedelta(days=200)
        
        sistema.registrar_migracao(
            contrato_id="CTR001",
            estagio_anterior=1,
            estagio_novo=2,
            motivo=MotivoMigracao.ATRASO_30_DIAS,
            pd_atual=0.15,
            data=data_migracao
        )
        
        sistema.iniciar_periodo_cura("CTR001", data_migracao)
        
        # Contrato com novo atraso
        resultado = sistema.avaliar_elegibilidade_cura(
            contrato_id="CTR001",
            estagio_atual=2,
            dias_atraso=45,  # Novo atraso
            pd_atual=0.18
        )
        
        assert resultado.status == StatusCura.REPROVADO
        assert resultado.meses_em_observacao == 0  # Reset
    
    def test_aplicar_cura(self, sistema):
        """Deve aplicar cura quando elegível."""
        data_migracao = datetime.now() - timedelta(days=200)
        
        sistema.registrar_migracao(
            contrato_id="CTR001",
            estagio_anterior=1,
            estagio_novo=2,
            motivo=MotivoMigracao.ATRASO_30_DIAS,
            pd_atual=0.15,
            data=data_migracao
        )
        
        sistema.iniciar_periodo_cura("CTR001", data_migracao)
        
        sucesso, novo_estagio, motivo = sistema.aplicar_cura(
            contrato_id="CTR001",
            estagio_atual=2,
            dias_atraso=0,
            pd_atual=0.10
        )
        
        assert sucesso == True
        assert novo_estagio == 1
        assert "Cura aprovada" in motivo
    
    def test_processar_dataframe(self, sistema):
        """Deve processar DataFrame corretamente."""
        # Preparar histórico
        data_migracao = datetime.now() - timedelta(days=200)
        sistema.registrar_migracao("CTR001", 1, 2, MotivoMigracao.ATRASO_30_DIAS, 
                                  pd_atual=0.15, data=data_migracao)
        sistema.iniciar_periodo_cura("CTR001", data_migracao)
        
        df = pd.DataFrame([
            {"ID_Contrato": "CTR001", "estagio": 2, "dias_atraso": 0, "pd_atual": 0.10},
            {"ID_Contrato": "CTR002", "estagio": 1, "dias_atraso": 0, "pd_atual": 0.05}
        ])
        
        df_resultado = sistema.processar_dataframe(df)
        
        assert "cura_status" in df_resultado.columns
        assert "cura_elegivel" in df_resultado.columns
        assert "em_periodo_cura" in df_resultado.columns
    
    def test_obter_historico(self, sistema):
        """Deve retornar histórico de um contrato."""
        sistema.registrar_migracao("CTR001", 1, 2, MotivoMigracao.ATRASO_30_DIAS)
        sistema.registrar_migracao("CTR001", 2, 3, MotivoMigracao.ATRASO_90_DIAS)
        
        historico = sistema.obter_historico("CTR001")
        
        assert len(historico) == 2
    
    def test_limpar_cache(self, sistema):
        """Deve limpar o cache."""
        sistema._cache_cura["test"] = ResultadoCura(
            contrato_id="test",
            status=StatusCura.NAO_APLICAVEL,
            estagio_atual=1,
            estagio_alvo=1,
            meses_em_observacao=0,
            meses_necessarios=0,
            percentual_progresso=0,
            elegivel_cura=False,
            motivo=""
        )
        
        sistema.limpar_cache()
        
        assert len(sistema._cache_cura) == 0


class TestFuncoesConveniencia:
    """Testes para funções de conveniência."""
    
    def test_get_sistema_cura(self):
        """Deve retornar instância global."""
        s1 = get_sistema_cura()
        s2 = get_sistema_cura()
        
        assert s1 is s2
    
    def test_avaliar_cura_funcao(self):
        """Função de conveniência deve funcionar."""
        resultado = avaliar_cura(
            contrato_id="CTR_TEST",
            estagio_atual=2,
            dias_atraso=0,
            pd_atual=0.10
        )
        
        assert isinstance(resultado, ResultadoCura)


class TestConformidadeCMN4966:
    """Testes específicos de conformidade com CMN 4966."""
    
    @pytest.fixture
    def sistema(self):
        return SistemaCura()
    
    def test_art41_inciso1_condicoes_originais(self, sistema):
        """
        Art. 41 I: A migração para estágio anterior pode ocorrer quando
        as condições que originaram a migração deixarem de existir.
        """
        # Simular contrato que migrou por atraso
        data_migracao = datetime.now() - timedelta(days=200)
        
        sistema.registrar_migracao(
            "CTR001", 1, 2,
            motivo=MotivoMigracao.ATRASO_30_DIAS,
            dias_atraso=35,
            pd_atual=0.15,
            data=data_migracao
        )
        sistema.iniciar_periodo_cura("CTR001", data_migracao)
        
        # Condições que originaram (atraso) deixaram de existir
        resultado = sistema.avaliar_elegibilidade_cura(
            contrato_id="CTR001",
            estagio_atual=2,
            dias_atraso=0,  # Sem atraso
            pd_atual=0.10   # PD melhorou
        )
        
        assert resultado.elegivel_cura == True
    
    def test_art41_inciso2_periodo_observacao(self, sistema):
        """
        Art. 41 II: A migração requer período de observação adequado.
        """
        # Contrato recém-regularizado (sem período de observação)
        sistema.registrar_migracao(
            "CTR001", 1, 2,
            MotivoMigracao.ATRASO_30_DIAS,
            pd_atual=0.15
        )
        
        resultado = sistema.avaliar_elegibilidade_cura(
            contrato_id="CTR001",
            estagio_atual=2,
            dias_atraso=0,
            pd_atual=0.10
        )
        
        # Não deve estar elegível ainda (precisa período de observação)
        assert resultado.elegivel_cura == False
        assert resultado.meses_em_observacao < resultado.meses_necessarios
    
    def test_periodo_cura_stage2_6_meses(self, sistema):
        """Stage 2 → 1 deve requerer 6 meses de observação."""
        criterios = SistemaCura.CRITERIOS_CURA[(2, 1)]
        assert criterios.meses_minimos == 6
    
    def test_periodo_cura_stage3_12_meses(self, sistema):
        """Stage 3 → 2 deve requerer 12 meses de observação."""
        criterios = SistemaCura.CRITERIOS_CURA[(3, 2)]
        assert criterios.meses_minimos == 12
    
    def test_reestruturacao_criterios_rigorosos(self, sistema):
        """Reestruturações devem ter critérios mais rigorosos."""
        criterios_normal = SistemaCura.CRITERIOS_CURA[(3, 2)]
        criterios_reestr = SistemaCura.CRITERIOS_REESTRUTURACAO
        
        # Reestruturações precisam de mais tempo
        assert criterios_reestr.meses_minimos > criterios_normal.meses_minimos
        
        # Reestruturações precisam de mais amortização
        assert criterios_reestr.percentual_amortizacao > criterios_normal.percentual_amortizacao
    
    def test_flag_em_periodo_cura(self, sistema):
        """Deve ter flag indicando contratos em período de cura."""
        data_migracao = datetime.now() - timedelta(days=60)  # 2 meses
        
        sistema.registrar_migracao("CTR001", 1, 2, MotivoMigracao.ATRASO_30_DIAS,
                                  pd_atual=0.15, data=data_migracao)
        sistema.iniciar_periodo_cura("CTR001", data_migracao)
        
        resultado = sistema.avaliar_elegibilidade_cura(
            contrato_id="CTR001",
            estagio_atual=2,
            dias_atraso=0,
            pd_atual=0.10
        )
        
        # Deve estar em observação (flag em_periodo_cura)
        assert resultado.status == StatusCura.EM_OBSERVACAO


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
