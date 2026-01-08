#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de integração para as funcionalidades de conformidade BACEN.

Testa:
- Integração Forward Looking Multi-Cenário com Pipeline ECL
- Integração Sistema de Cura com Triggers de Estágio
- Rastreamento de Write-off (5 anos)
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Adicionar path do módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestIntegracaoForwardLookingPipeline:
    """Testes de integração do Forward Looking Multi-Cenário com Pipeline ECL."""
    
    def test_pipeline_com_multi_cenario_ativado(self):
        """Pipeline deve usar cenários ponderados quando ativado."""
        from pipeline_ecl import ECLPipeline
        
        pipeline = ECLPipeline(usar_multi_cenario=True)
        
        assert pipeline.usar_multi_cenario == True
        assert pipeline.gerenciador_cenarios is not None
    
    def test_pipeline_sem_multi_cenario(self):
        """Pipeline deve funcionar sem multi-cenário."""
        from pipeline_ecl import ECLPipeline
        
        pipeline = ECLPipeline(usar_multi_cenario=False)
        
        assert pipeline.usar_multi_cenario == False
        assert pipeline.gerenciador_cenarios is None
    
    def test_calculo_ecl_com_multi_cenario(self):
        """ECL deve ser calculado com cenários ponderados."""
        from pipeline_ecl import ECLPipeline
        
        pipeline = ECLPipeline(usar_multi_cenario=True)
        
        resultado = pipeline.calcular_ecl_completo(
            cliente_id='12345678901',
            produto='consignado',
            saldo_utilizado=5000,
            limite_total=10000,
            dias_atraso=0,
            prinad=25.0,
            rating='B1',
            pd_12m=0.025,
            pd_lifetime=0.12,
            stage=1
        )
        
        assert resultado.usar_multi_cenario == True
        assert resultado.cenarios_detalhes is not None
        assert 'cenarios' in resultado.cenarios_detalhes
        assert len(resultado.cenarios_detalhes['cenarios']) == 3
    
    def test_k_pd_fl_multi_cenario(self):
        """K_PD_FL deve ser calculado como média ponderada dos cenários."""
        from pipeline_ecl import ECLPipeline
        
        pipeline = ECLPipeline(usar_multi_cenario=True)
        
        fl_result = pipeline._calcular_k_pd_fl('consignado', 2)
        
        assert 'k_pd_fl' in fl_result
        assert 'k_lgd_fl' in fl_result
        assert 'cenarios_detalhes' in fl_result
        
        # K_PD_FL deve estar entre limites
        assert 0.75 <= fl_result['k_pd_fl'] <= 1.25
        assert 0.80 <= fl_result['k_lgd_fl'] <= 1.20
    
    def test_resultado_ecl_inclui_detalhes_cenarios(self):
        """Resultado ECL deve incluir detalhes dos cenários aplicados."""
        from pipeline_ecl import ECLPipeline
        
        pipeline = ECLPipeline(usar_multi_cenario=True)
        
        resultado = pipeline.calcular_ecl_completo(
            cliente_id='12345678901',
            produto='parcelado',
            saldo_utilizado=10000,
            limite_total=15000,
            dias_atraso=0,
            prinad=50.0,
            rating='C1',
            pd_12m=0.05,
            pd_lifetime=0.20,
            stage=2
        )
        
        # Verificar detalhes
        assert resultado.cenarios_detalhes is not None
        
        for cenario in resultado.cenarios_detalhes['cenarios']:
            assert 'nome' in cenario
            assert 'peso' in cenario
            assert 'spread_pd' in cenario
            assert 'spread_lgd' in cenario


class TestIntegracaoSistemaCuraTriggers:
    """Testes de integração do Sistema de Cura com Triggers de Estágio."""
    
    def test_import_sistema_cura_em_triggers(self):
        """Módulo de triggers deve importar Sistema de Cura."""
        from modulo_triggers_estagios import SISTEMA_CURA_DISPONIVEL
        
        assert SISTEMA_CURA_DISPONIVEL == True
    
    def test_funcao_aplicar_avaliacao_cura_existe(self):
        """Função de avaliação de cura deve existir."""
        from modulo_triggers_estagios import aplicar_avaliacao_cura
        
        assert callable(aplicar_avaliacao_cura)
    
    def test_funcao_triggers_com_cura_existe(self):
        """Função de triggers com cura deve existir."""
        from modulo_triggers_estagios import aplicar_todos_triggers_com_cura
        
        assert callable(aplicar_todos_triggers_com_cura)
    
    def test_avaliacao_cura_adiciona_colunas(self):
        """Avaliação de cura deve adicionar colunas ao DataFrame."""
        from modulo_triggers_estagios import aplicar_avaliacao_cura
        
        df = pd.DataFrame({
            'ID_Contrato': ['CTR001', 'CTR002'],
            'estagio': [2, 1],
            'Dias Atraso': [0, 0],
            'pd_behavior_atual': [0.10, 0.05]
        })
        
        df_resultado = aplicar_avaliacao_cura(df)
        
        assert 'cura_avaliada' in df_resultado.columns
        assert 'cura_status' in df_resultado.columns
        assert 'cura_elegivel' in df_resultado.columns
        assert 'cura_aplicada' in df_resultado.columns
    
    def test_triggers_com_cura_processa_dataframe(self):
        """Triggers com cura deve processar DataFrame corretamente."""
        from modulo_triggers_estagios import aplicar_todos_triggers_com_cura
        
        df = pd.DataFrame({
            'ID_Contrato': ['CTR001', 'CTR002', 'CTR003'],
            'estagio': [1, 2, 3],
            'Dias Atraso': [0, 0, 0],
            'pd_concessao_inicial': [0.05, 0.10, 0.15],
            'pd_behavior_atual': [0.06, 0.08, 0.10],
            'Modalidade Oper.': ['Parcelado', 'Parcelado', 'Parcelado'],
            'Linha de Crédito': [None, None, None]
        })
        
        df_resultado = aplicar_todos_triggers_com_cura(
            df,
            col_pd_concessao='pd_concessao_inicial',
            col_pd_behavior='pd_behavior_atual',
            col_dias_atraso='Dias Atraso',
            aplicar_cura_flag=True
        )
        
        assert 'estagio' in df_resultado.columns
        assert 'cura_avaliada' in df_resultado.columns


class TestRastreamentoWriteoff:
    """Testes do módulo de Rastreamento de Write-off."""
    
    @pytest.fixture
    def rastreador(self):
        """Cria instância do rastreador para testes."""
        from rastreamento_writeoff import RastreadorWriteOff
        return RastreadorWriteOff()
    
    def test_registrar_baixa(self, rastreador):
        """Deve registrar baixa corretamente."""
        from rastreamento_writeoff import MotivoBaixa
        
        baixa = rastreador.registrar_baixa(
            contrato_id="CTR001",
            valor_baixado=10000.0,
            motivo=MotivoBaixa.INADIMPLENCIA_PROLONGADA,
            provisao_constituida=10000.0
        )
        
        assert baixa.contrato_id == "CTR001"
        assert baixa.valor_baixado == 10000.0
    
    def test_registrar_recuperacao(self, rastreador):
        """Deve registrar recuperação pós-baixa."""
        from rastreamento_writeoff import MotivoBaixa
        
        rastreador.registrar_baixa(
            contrato_id="CTR001",
            valor_baixado=10000.0,
            motivo=MotivoBaixa.INADIMPLENCIA_PROLONGADA,
            provisao_constituida=10000.0
        )
        
        recuperacao = rastreador.registrar_recuperacao(
            contrato_id="CTR001",
            valor_recuperado=2000.0
        )
        
        assert recuperacao is not None
        assert recuperacao.valor_recuperado == 2000.0
    
    def test_obter_resumo_contrato(self, rastreador):
        """Deve calcular resumo de recuperação."""
        from rastreamento_writeoff import MotivoBaixa
        
        rastreador.registrar_baixa(
            contrato_id="CTR001",
            valor_baixado=10000.0,
            motivo=MotivoBaixa.INADIMPLENCIA_PROLONGADA,
            provisao_constituida=10000.0
        )
        
        rastreador.registrar_recuperacao("CTR001", 3000.0)
        rastreador.registrar_recuperacao("CTR001", 2000.0)
        
        resumo = rastreador.obter_resumo_contrato("CTR001")
        
        assert resumo is not None
        assert resumo.total_recuperado == 5000.0
        assert resumo.taxa_recuperacao == 50.0
    
    def test_periodo_acompanhamento_5_anos(self, rastreador):
        """Período de acompanhamento deve ser 5 anos."""
        from rastreamento_writeoff import RastreadorWriteOff
        
        assert RastreadorWriteOff.PERIODO_ACOMPANHAMENTO_DIAS == 5 * 365
    
    def test_contratos_em_acompanhamento(self, rastreador):
        """Deve listar contratos ainda em acompanhamento."""
        from rastreamento_writeoff import MotivoBaixa
        
        # Baixa recente (em acompanhamento)
        rastreador.registrar_baixa(
            contrato_id="CTR001",
            valor_baixado=10000.0,
            motivo=MotivoBaixa.INADIMPLENCIA_PROLONGADA,
            provisao_constituida=10000.0,
            data_baixa=datetime.now() - timedelta(days=100)
        )
        
        # Baixa antiga (fora do período)
        rastreador.registrar_baixa(
            contrato_id="CTR002",
            valor_baixado=5000.0,
            motivo=MotivoBaixa.PRESCRICAO,
            provisao_constituida=5000.0,
            data_baixa=datetime.now() - timedelta(days=2000)  # > 5 anos
        )
        
        contratos_ativos = rastreador.obter_contratos_em_acompanhamento()
        
        # Apenas CTR001 deve estar em acompanhamento
        ids_ativos = [c.contrato_id for c in contratos_ativos]
        assert "CTR001" in ids_ativos
        assert "CTR002" not in ids_ativos
    
    def test_taxa_recuperacao_historica(self, rastreador):
        """Deve calcular taxa de recuperação histórica."""
        from rastreamento_writeoff import MotivoBaixa
        
        rastreador.registrar_baixa("CTR001", 10000.0, MotivoBaixa.INADIMPLENCIA_PROLONGADA, 10000.0)
        rastreador.registrar_baixa("CTR002", 20000.0, MotivoBaixa.INADIMPLENCIA_PROLONGADA, 20000.0)
        
        rastreador.registrar_recuperacao("CTR001", 5000.0)  # 50%
        rastreador.registrar_recuperacao("CTR002", 10000.0)  # 50%
        
        estatisticas = rastreador.calcular_taxa_recuperacao_historica()
        
        assert estatisticas['quantidade_contratos'] == 2
        assert estatisticas['valor_total_baixado'] == 30000.0
        assert estatisticas['valor_total_recuperado'] == 15000.0
        assert estatisticas['taxa_recuperacao_ponderada'] == 50.0
    
    def test_relatorio_regulatorio(self, rastreador):
        """Deve gerar relatório regulatório."""
        from rastreamento_writeoff import MotivoBaixa
        
        rastreador.registrar_baixa("CTR001", 10000.0, MotivoBaixa.INADIMPLENCIA_PROLONGADA, 10000.0)
        
        relatorio = rastreador.gerar_relatorio_regulatorio()
        
        assert 'data_geracao' in relatorio
        assert 'resumo_geral' in relatorio
        assert 'por_ano_baixa' in relatorio
        assert relatorio['periodo_acompanhamento_anos'] == 5


class TestConformidadeCMN4966Integrada:
    """Testes de conformidade integrada com CMN 4966."""
    
    def test_art36_forward_looking_integrado(self):
        """Art. 36 §5º: Forward Looking multi-cenário no pipeline."""
        from pipeline_ecl import ECLPipeline
        
        pipeline = ECLPipeline(usar_multi_cenario=True)
        
        resultado = pipeline.calcular_ecl_completo(
            cliente_id='TEST001',
            produto='consignado',
            saldo_utilizado=50000,
            limite_total=50000,
            dias_atraso=0,
            prinad=30.0,
            rating='B2',
            pd_12m=0.03,
            pd_lifetime=0.15,
            stage=1
        )
        
        # Deve usar multi-cenário
        assert resultado.usar_multi_cenario == True
        
        # Deve ter detalhes dos 3 cenários
        assert len(resultado.cenarios_detalhes['cenarios']) == 3
    
    def test_art41_cura_integrada(self):
        """Art. 41: Sistema de cura integrado com triggers."""
        from modulo_triggers_estagios import aplicar_avaliacao_cura
        
        df = pd.DataFrame({
            'ID_Contrato': ['CTR001'],
            'estagio': [2],
            'Dias Atraso': [0],
            'pd_behavior_atual': [0.05]
        })
        
        df_resultado = aplicar_avaliacao_cura(df)
        
        # Deve ter avaliado cura
        assert df_resultado.loc[0, 'cura_avaliada'] == True
    
    def test_art49_writeoff_5_anos(self):
        """Art. 49: Acompanhamento de write-off por 5 anos."""
        from rastreamento_writeoff import RastreadorWriteOff
        
        rastreador = RastreadorWriteOff()
        
        # Período deve ser exatamente 5 anos (1825 dias)
        assert rastreador.PERIODO_ACOMPANHAMENTO_DIAS == 1825


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
