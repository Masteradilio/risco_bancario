# -*- coding: utf-8 -*-
"""
Testes de API Write-off
=======================

Testes de integração para os endpoints de write-off (baixas e recuperações).

Autor: Sistema ECL
Data: Janeiro 2026
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Adicionar paths para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rastreamento_writeoff import (
    RastreadorWriteOff,
    MotivoBaixa,
    StatusRecuperacao,
    RegistroBaixa,
    RegistroRecuperacao,
    ResumoContratoBaixado,
    get_rastreador_writeoff
)


class TestRegistrarBaixa:
    """Testes para registro de baixas (write-off)."""
    
    @pytest.fixture
    def rastreador(self):
        """Cria uma instância limpa do rastreador."""
        r = RastreadorWriteOff()
        yield r
        r.limpar_dados()
    
    def test_registrar_baixa_simples(self, rastreador):
        """Testa registro de baixa básica."""
        baixa = rastreador.registrar_baixa(
            contrato_id="CTR001",
            valor_baixado=10000.0,
            motivo=MotivoBaixa.INADIMPLENCIA_PROLONGADA,
            provisao_constituida=10000.0
        )
        
        assert baixa is not None
        assert baixa.contrato_id == "CTR001"
        assert baixa.valor_baixado == 10000.0
        assert baixa.motivo == MotivoBaixa.INADIMPLENCIA_PROLONGADA
        assert baixa.estagio_na_baixa == 3
    
    def test_registrar_baixa_com_todos_campos(self, rastreador):
        """Testa registro de baixa com todos os campos opcionais."""
        data_baixa = datetime(2025, 6, 15)
        
        baixa = rastreador.registrar_baixa(
            contrato_id="CTR002",
            valor_baixado=25000.0,
            motivo=MotivoBaixa.FALENCIA_RECUPERACAO_JUDICIAL,
            provisao_constituida=22000.0,
            estagio_na_baixa=3,
            data_baixa=data_baixa,
            cliente_id="CLI001",
            produto="Consignado",
            observacoes="Baixa por RJ"
        )
        
        assert baixa.data_baixa == data_baixa
        assert baixa.cliente_id == "CLI001"
        assert baixa.produto == "Consignado"
        assert baixa.observacoes == "Baixa por RJ"
    
    def test_registrar_baixa_sobrescreve(self, rastreador):
        """Testa que registro duplicado sobrescreve o anterior."""
        rastreador.registrar_baixa(
            contrato_id="CTR001",
            valor_baixado=10000.0,
            motivo=MotivoBaixa.INADIMPLENCIA_PROLONGADA,
            provisao_constituida=10000.0
        )
        
        rastreador.registrar_baixa(
            contrato_id="CTR001",
            valor_baixado=15000.0,
            motivo=MotivoBaixa.PRESCRICAO,
            provisao_constituida=15000.0
        )
        
        resumo = rastreador.obter_resumo_contrato("CTR001")
        assert resumo.valor_baixado == 15000.0
    
    def test_baixa_to_dict(self, rastreador):
        """Testa conversão de baixa para dicionário."""
        baixa = rastreador.registrar_baixa(
            contrato_id="CTR001",
            valor_baixado=10000.0,
            motivo=MotivoBaixa.INADIMPLENCIA_PROLONGADA,
            provisao_constituida=10000.0
        )
        
        d = baixa.to_dict()
        assert "contrato_id" in d
        assert "valor_baixado" in d
        assert "motivo" in d
        assert d["motivo"] == "inadimplencia_prolongada"


class TestRegistrarRecuperacao:
    """Testes para registro de recuperações pós-baixa."""
    
    @pytest.fixture
    def rastreador_com_baixa(self):
        """Cria rastreador com uma baixa já registrada."""
        r = RastreadorWriteOff()
        r.registrar_baixa(
            contrato_id="CTR001",
            valor_baixado=10000.0,
            motivo=MotivoBaixa.INADIMPLENCIA_PROLONGADA,
            provisao_constituida=10000.0,
            data_baixa=datetime.now() - timedelta(days=30)
        )
        yield r
        r.limpar_dados()
    
    def test_registrar_recuperacao_simples(self, rastreador_com_baixa):
        """Testa registro de recuperação básica."""
        rec = rastreador_com_baixa.registrar_recuperacao(
            contrato_id="CTR001",
            valor_recuperado=2000.0
        )
        
        assert rec is not None
        assert rec.contrato_id == "CTR001"
        assert rec.valor_recuperado == 2000.0
        assert rec.tipo == "pagamento"
    
    def test_registrar_recuperacao_contrato_inexistente(self, rastreador_com_baixa):
        """Testa que recuperação de contrato inexistente retorna None."""
        rec = rastreador_com_baixa.registrar_recuperacao(
            contrato_id="CTR_INEXISTENTE",
            valor_recuperado=1000.0
        )
        
        assert rec is None
    
    def test_registrar_multiplas_recuperacoes(self, rastreador_com_baixa):
        """Testa registro de múltiplas recuperações para o mesmo contrato."""
        rastreador_com_baixa.registrar_recuperacao("CTR001", 2000.0, tipo="pagamento")
        rastreador_com_baixa.registrar_recuperacao("CTR001", 1500.0, tipo="acordo")
        rastreador_com_baixa.registrar_recuperacao("CTR001", 500.0, tipo="outro")
        
        resumo = rastreador_com_baixa.obter_resumo_contrato("CTR001")
        assert resumo.total_recuperado == 4000.0
        assert resumo.taxa_recuperacao == 40.0
    
    def test_recuperacao_to_dict(self, rastreador_com_baixa):
        """Testa conversão de recuperação para dicionário."""
        rec = rastreador_com_baixa.registrar_recuperacao(
            contrato_id="CTR001",
            valor_recuperado=2000.0,
            tipo="acordo"
        )
        
        d = rec.to_dict()
        assert d["contrato_id"] == "CTR001"
        assert d["valor_recuperado"] == 2000.0
        assert d["tipo"] == "acordo"


class TestRelatorioContrato:
    """Testes para obtenção de relatório por contrato."""
    
    @pytest.fixture
    def rastreador_completo(self):
        """Cria rastreador com baixa e recuperações."""
        r = RastreadorWriteOff()
        
        # Baixa de 30 dias atrás
        r.registrar_baixa(
            contrato_id="CTR001",
            valor_baixado=10000.0,
            motivo=MotivoBaixa.INADIMPLENCIA_PROLONGADA,
            provisao_constituida=10000.0,
            data_baixa=datetime.now() - timedelta(days=30)
        )
        
        # Recuperações
        r.registrar_recuperacao("CTR001", 3000.0)
        r.registrar_recuperacao("CTR001", 2000.0)
        
        yield r
        r.limpar_dados()
    
    def test_obter_resumo_contrato(self, rastreador_completo):
        """Testa obtenção do resumo de um contrato."""
        resumo = rastreador_completo.obter_resumo_contrato("CTR001")
        
        assert resumo is not None
        assert resumo.contrato_id == "CTR001"
        assert resumo.valor_baixado == 10000.0
        assert resumo.total_recuperado == 5000.0
        assert resumo.taxa_recuperacao == 50.0
    
    def test_obter_resumo_contrato_inexistente(self, rastreador_completo):
        """Testa que contrato inexistente retorna None."""
        resumo = rastreador_completo.obter_resumo_contrato("CTR_INEXISTENTE")
        assert resumo is None
    
    def test_status_em_acompanhamento(self, rastreador_completo):
        """Testa status 'em acompanhamento' quando há tempo restante."""
        resumo = rastreador_completo.obter_resumo_contrato("CTR001")
        
        # Como foi baixado há 30 dias, ainda está em acompanhamento
        assert resumo.status == StatusRecuperacao.RECUPERACAO_PARCIAL
        assert resumo.dias_desde_baixa >= 0
        assert resumo.tempo_restante_dias > 0
    
    def test_resumo_to_dict(self, rastreador_completo):
        """Testa conversão de resumo para dicionário."""
        resumo = rastreador_completo.obter_resumo_contrato("CTR001")
        d = resumo.to_dict()
        
        assert "contrato_id" in d
        assert "valor_baixado" in d
        assert "total_recuperado" in d
        assert "taxa_recuperacao" in d
        assert "status" in d


class TestRelatorioConsolidado:
    """Testes para relatório consolidado."""
    
    @pytest.fixture
    def rastreador_multiplos(self):
        """Cria rastreador com múltiplos contratos."""
        r = RastreadorWriteOff()
        
        # Contrato 1
        r.registrar_baixa("CTR001", 10000.0, MotivoBaixa.INADIMPLENCIA_PROLONGADA, 10000.0,
                         data_baixa=datetime.now() - timedelta(days=100))
        r.registrar_recuperacao("CTR001", 3000.0)
        
        # Contrato 2
        r.registrar_baixa("CTR002", 25000.0, MotivoBaixa.FALENCIA_RECUPERACAO_JUDICIAL, 25000.0,
                         data_baixa=datetime.now() - timedelta(days=200))
        r.registrar_recuperacao("CTR002", 10000.0)
        
        # Contrato 3 (sem recuperação)
        r.registrar_baixa("CTR003", 5000.0, MotivoBaixa.PRESCRICAO, 5000.0,
                         data_baixa=datetime.now() - timedelta(days=50))
        
        yield r
        r.limpar_dados()
    
    def test_contratos_em_acompanhamento(self, rastreador_multiplos):
        """Testa listagem de contratos em acompanhamento."""
        contratos = rastreador_multiplos.obter_contratos_em_acompanhamento()
        
        assert len(contratos) == 3
        # Deve estar ordenado por tempo restante (decrescente)
        assert contratos[0].tempo_restante_dias >= contratos[1].tempo_restante_dias
    
    def test_taxa_recuperacao_historica(self, rastreador_multiplos):
        """Testa cálculo de taxa de recuperação histórica."""
        stats = rastreador_multiplos.calcular_taxa_recuperacao_historica()
        
        assert stats["quantidade_contratos"] == 3
        assert stats["valor_total_baixado"] == 40000.0
        assert stats["valor_total_recuperado"] == 13000.0
        assert stats["taxa_recuperacao_ponderada"] == pytest.approx(32.5, rel=0.01)
    
    def test_taxa_recuperacao_filtro_motivo(self, rastreador_multiplos):
        """Testa filtro por motivo na taxa de recuperação."""
        stats = rastreador_multiplos.calcular_taxa_recuperacao_historica(
            motivo=MotivoBaixa.INADIMPLENCIA_PROLONGADA
        )
        
        assert stats["quantidade_contratos"] == 1
        assert stats["valor_total_baixado"] == 10000.0
    
    def test_relatorio_regulatorio(self, rastreador_multiplos):
        """Testa geração de relatório regulatório."""
        relatorio = rastreador_multiplos.gerar_relatorio_regulatorio()
        
        assert "data_geracao" in relatorio
        assert "resumo_geral" in relatorio
        assert relatorio["resumo_geral"]["total_contratos_baixados"] == 3
        assert "por_ano_baixa" in relatorio


class TestTaxaRecuperacao:
    """Testes para cálculo de taxa de recuperação."""
    
    @pytest.fixture
    def rastreador(self):
        """Cria rastreador limpo."""
        r = RastreadorWriteOff()
        yield r
        r.limpar_dados()
    
    def test_taxa_recuperacao_sem_baixas(self, rastreador):
        """Testa taxa de recuperação quando não há baixas."""
        stats = rastreador.calcular_taxa_recuperacao_historica()
        
        assert stats["quantidade_contratos"] == 0
        assert stats["valor_total_baixado"] == 0
        assert stats["taxa_recuperacao_ponderada"] == 0
    
    def test_taxa_recuperacao_100_porcento(self, rastreador):
        """Testa quando há recuperação total (100%)."""
        rastreador.registrar_baixa("CTR001", 10000.0, MotivoBaixa.INADIMPLENCIA_PROLONGADA, 10000.0)
        rastreador.registrar_recuperacao("CTR001", 10000.0)
        
        resumo = rastreador.obter_resumo_contrato("CTR001")
        assert resumo.taxa_recuperacao == 100.0
        assert resumo.status == StatusRecuperacao.RECUPERACAO_TOTAL
    
    def test_taxa_recuperacao_filtro_periodo(self, rastreador):
        """Testa filtro por período na taxa de recuperação."""
        # Baixa antiga (fora do período)
        rastreador.registrar_baixa("CTR001", 10000.0, MotivoBaixa.INADIMPLENCIA_PROLONGADA, 10000.0,
                                  data_baixa=datetime(2024, 1, 1))
        
        # Baixa recente (dentro do período)
        rastreador.registrar_baixa("CTR002", 5000.0, MotivoBaixa.PRESCRICAO, 5000.0,
                                  data_baixa=datetime(2026, 1, 1))
        
        stats = rastreador.calcular_taxa_recuperacao_historica(
            periodo_inicial=datetime(2025, 1, 1)
        )
        
        assert stats["quantidade_contratos"] == 1
        assert stats["valor_total_baixado"] == 5000.0


class TestPeriodoAcompanhamento:
    """Testes para o período de acompanhamento de 5 anos (Art. 49 CMN 4966)."""
    
    @pytest.fixture
    def rastreador(self):
        """Cria rastreador limpo."""
        r = RastreadorWriteOff()
        yield r
        r.limpar_dados()
    
    def test_periodo_acompanhamento_5_anos(self, rastreador):
        """Verifica que o período de acompanhamento é de 5 anos (1825 dias)."""
        assert rastreador.PERIODO_ACOMPANHAMENTO_DIAS == 1825
    
    def test_contrato_dentro_periodo(self, rastreador):
        """Testa contrato dentro do período de 5 anos."""
        # Baixa há 4 anos
        rastreador.registrar_baixa("CTR001", 10000.0, MotivoBaixa.INADIMPLENCIA_PROLONGADA, 10000.0,
                                  data_baixa=datetime.now() - timedelta(days=4*365))
        
        resumo = rastreador.obter_resumo_contrato("CTR001")
        assert resumo.tempo_restante_dias > 0
        assert resumo.status != StatusRecuperacao.PERIODO_ENCERRADO
    
    def test_contrato_fora_periodo(self, rastreador):
        """Testa contrato fora do período de 5 anos."""
        # Baixa há 6 anos
        rastreador.registrar_baixa("CTR001", 10000.0, MotivoBaixa.INADIMPLENCIA_PROLONGADA, 10000.0,
                                  data_baixa=datetime.now() - timedelta(days=6*365))
        
        resumo = rastreador.obter_resumo_contrato("CTR001")
        assert resumo.tempo_restante_dias == 0
        assert resumo.status == StatusRecuperacao.PERIODO_ENCERRADO


class TestGlobalInstance:
    """Testes para a instância global do rastreador."""
    
    def test_get_rastreador_singleton(self):
        """Testa que get_rastreador_writeoff retorna singleton."""
        r1 = get_rastreador_writeoff()
        r2 = get_rastreador_writeoff()
        
        assert r1 is r2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
