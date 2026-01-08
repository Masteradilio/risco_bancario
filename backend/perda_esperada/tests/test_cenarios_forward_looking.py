#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitários para o módulo de Cenários Forward Looking Multi-Cenário.

Testa a conformidade com Art. 36 §5º da Resolução CMN 4.966/2021.
"""

import pytest
import sys
from pathlib import Path

# Adicionar path do módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cenarios_forward_looking import (
    TipoCenario,
    CenarioMacroeconomico,
    ResultadoCenario,
    ResultadoECLMultiCenario,
    GerenciadorCenarios,
    get_gerenciador_cenarios,
    calcular_ecl_multi_cenario
)


class TestTipoCenario:
    """Testes para o enum TipoCenario."""
    
    def test_tres_cenarios_existem(self):
        """Deve existir exatamente 3 tipos de cenário."""
        assert len(TipoCenario) == 3
    
    def test_cenarios_corretos(self):
        """Deve ter os cenários corretos."""
        assert TipoCenario.OTIMISTA.value == "otimista"
        assert TipoCenario.BASE.value == "base"
        assert TipoCenario.PESSIMISTA.value == "pessimista"


class TestCenarioMacroeconomico:
    """Testes para a dataclass CenarioMacroeconomico."""
    
    def test_criacao_cenario(self):
        """Deve criar cenário com atributos corretos."""
        cenario = CenarioMacroeconomico(
            nome="base",
            peso=0.70,
            selic_projetada=11.75,
            pib_projetado=2.5,
            spread_pd=1.0,
            spread_lgd=1.0
        )
        
        assert cenario.nome == "base"
        assert cenario.peso == 0.70
        assert cenario.selic_projetada == 11.75
        assert cenario.spread_pd == 1.0
    
    def test_to_dict(self):
        """Deve converter para dicionário corretamente."""
        cenario = CenarioMacroeconomico(
            nome="otimista",
            peso=0.15,
            spread_pd=0.85
        )
        
        resultado = cenario.to_dict()
        
        assert isinstance(resultado, dict)
        assert resultado["nome"] == "otimista"
        assert resultado["peso"] == 0.15
        assert resultado["spread_pd"] == 0.85


class TestGerenciadorCenarios:
    """Testes para o GerenciadorCenarios."""
    
    @pytest.fixture
    def gerenciador(self):
        """Cria instância do gerenciador para testes."""
        return GerenciadorCenarios()
    
    def test_pesos_padrao_somam_um(self, gerenciador):
        """Pesos padrão devem somar 1.0."""
        soma = sum(gerenciador.pesos.values())
        assert abs(soma - 1.0) < 0.001
    
    def test_pesos_padrao_valores(self, gerenciador):
        """Pesos padrão devem ter valores corretos."""
        assert gerenciador.pesos[TipoCenario.OTIMISTA] == 0.15
        assert gerenciador.pesos[TipoCenario.BASE] == 0.70
        assert gerenciador.pesos[TipoCenario.PESSIMISTA] == 0.15
    
    def test_spreads_pd_padrao(self, gerenciador):
        """Spreads de PD padrão devem estar corretos."""
        assert gerenciador.spreads_pd[TipoCenario.OTIMISTA] == 0.85
        assert gerenciador.spreads_pd[TipoCenario.BASE] == 1.00
        assert gerenciador.spreads_pd[TipoCenario.PESSIMISTA] == 1.25
    
    def test_spreads_lgd_padrao(self, gerenciador):
        """Spreads de LGD padrão devem estar corretos."""
        assert gerenciador.spreads_lgd[TipoCenario.OTIMISTA] == 0.90
        assert gerenciador.spreads_lgd[TipoCenario.BASE] == 1.00
        assert gerenciador.spreads_lgd[TipoCenario.PESSIMISTA] == 1.15
    
    def test_criar_cenarios_retorna_tres(self, gerenciador):
        """Deve criar exatamente 3 cenários."""
        cenarios = gerenciador.criar_cenarios()
        assert len(cenarios) == 3
    
    def test_criar_cenarios_pesos_somam_um(self, gerenciador):
        """Cenários criados devem ter pesos que somam 1.0."""
        cenarios = gerenciador.criar_cenarios()
        soma_pesos = sum(c.peso for c in cenarios)
        assert abs(soma_pesos - 1.0) < 0.001
    
    def test_criar_cenarios_tipos_corretos(self, gerenciador):
        """Cenários devem ter os tipos corretos."""
        cenarios = gerenciador.criar_cenarios()
        nomes = {c.nome for c in cenarios}
        
        assert "otimista" in nomes
        assert "base" in nomes
        assert "pessimista" in nomes
    
    def test_cenario_pessimista_tem_maior_spread_pd(self, gerenciador):
        """Cenário pessimista deve ter maior spread de PD."""
        cenarios = gerenciador.criar_cenarios()
        
        otimista = next(c for c in cenarios if c.nome == "otimista")
        base = next(c for c in cenarios if c.nome == "base")
        pessimista = next(c for c in cenarios if c.nome == "pessimista")
        
        assert pessimista.spread_pd > base.spread_pd
        assert base.spread_pd > otimista.spread_pd
    
    def test_calcular_k_pd_fl_ponderado(self, gerenciador):
        """K_PD_FL ponderado deve estar entre 0.75 e 1.25."""
        k_pd_fl, _ = gerenciador.calcular_k_pd_fl_ponderado(0.10)
        
        assert 0.75 <= k_pd_fl <= 1.25
    
    def test_calcular_k_pd_fl_ponderado_retorna_detalhes(self, gerenciador):
        """Deve retornar detalhes por cenário."""
        _, detalhes = gerenciador.calcular_k_pd_fl_ponderado(0.10)
        
        assert len(detalhes) == 3
        for d in detalhes:
            assert "cenario" in d
            assert "peso" in d
            assert "k_pd_cenario" in d
            assert "contribuicao" in d
    
    def test_calcular_k_lgd_fl_ponderado(self, gerenciador):
        """K_LGD_FL ponderado deve estar entre 0.80 e 1.20."""
        k_lgd_fl, _ = gerenciador.calcular_k_lgd_fl_ponderado(0.45)
        
        assert 0.80 <= k_lgd_fl <= 1.20
    
    def test_calcular_ecl_multi_cenario(self, gerenciador):
        """Deve calcular ECL ponderado corretamente."""
        pd_base = 0.10
        lgd_base = 0.45
        ead = 100000.0
        
        resultado = gerenciador.calcular_ecl_multi_cenario(pd_base, lgd_base, ead)
        
        assert isinstance(resultado, ResultadoECLMultiCenario)
        assert resultado.ecl_final > 0
        assert len(resultado.cenarios) == 3
    
    def test_ecl_ponderado_igual_soma_cenarios(self, gerenciador):
        """ECL final deve ser igual à soma ponderada dos cenários."""
        pd_base = 0.10
        lgd_base = 0.45
        ead = 100000.0
        
        resultado = gerenciador.calcular_ecl_multi_cenario(pd_base, lgd_base, ead)
        
        soma_ponderada = sum(c.ecl_cenario * c.peso for c in resultado.cenarios)
        
        assert abs(resultado.ecl_final - soma_ponderada) < 0.01
    
    def test_cenario_pessimista_maior_ecl(self, gerenciador):
        """Cenário pessimista deve ter maior ECL."""
        resultado = gerenciador.calcular_ecl_multi_cenario(0.10, 0.45, 100000.0)
        
        otimista = next(c for c in resultado.cenarios if c.cenario == "otimista")
        base = next(c for c in resultado.cenarios if c.cenario == "base")
        pessimista = next(c for c in resultado.cenarios if c.cenario == "pessimista")
        
        assert pessimista.ecl_cenario > base.ecl_cenario
        assert base.ecl_cenario > otimista.ecl_cenario
    
    def test_atualizar_pesos_normaliza(self, gerenciador):
        """Atualizar pesos deve normalizar para somar 1.0."""
        gerenciador.atualizar_pesos(otimista=0.20, base=0.60, pessimista=0.20)
        
        soma = sum(gerenciador.pesos.values())
        assert abs(soma - 1.0) < 0.001
    
    def test_atualizar_pesos_customizados(self):
        """Deve aceitar pesos customizados na inicialização."""
        pesos_custom = {
            TipoCenario.OTIMISTA: 0.10,
            TipoCenario.BASE: 0.80,
            TipoCenario.PESSIMISTA: 0.10
        }
        
        gerenciador = GerenciadorCenarios(pesos_customizados=pesos_custom)
        
        assert gerenciador.pesos[TipoCenario.OTIMISTA] == 0.10
        assert gerenciador.pesos[TipoCenario.BASE] == 0.80
    
    def test_pd_ajustado_limitado(self, gerenciador):
        """PD ajustado deve estar entre 0 e 1."""
        resultado = gerenciador.calcular_ecl_multi_cenario(0.95, 0.90, 100000.0)
        
        for cenario in resultado.cenarios:
            assert 0 <= cenario.pd_ajustado <= 1
            assert 0 <= cenario.lgd_ajustado <= 1


class TestFuncoesConveniencia:
    """Testes para funções de conveniência."""
    
    def test_get_gerenciador_cenarios(self):
        """Deve retornar instância global."""
        g1 = get_gerenciador_cenarios()
        g2 = get_gerenciador_cenarios()
        
        assert g1 is g2
    
    def test_calcular_ecl_multi_cenario_funcao(self):
        """Função de conveniência deve funcionar."""
        resultado = calcular_ecl_multi_cenario(0.10, 0.45, 100000.0)
        
        assert isinstance(resultado, ResultadoECLMultiCenario)
        assert resultado.ecl_final > 0


class TestResultadoECLMultiCenario:
    """Testes para ResultadoECLMultiCenario."""
    
    def test_to_dict(self):
        """Deve converter para dicionário corretamente."""
        cenarios = [
            ResultadoCenario("otimista", 0.15, 0.085, 0.405, 3442.5),
            ResultadoCenario("base", 0.70, 0.10, 0.45, 4500.0),
            ResultadoCenario("pessimista", 0.15, 0.125, 0.5175, 6468.75)
        ]
        
        resultado = ResultadoECLMultiCenario(
            ecl_final=4500.0,
            cenarios=cenarios
        )
        
        d = resultado.to_dict()
        
        assert "ecl_final" in d
        assert "cenarios" in d
        assert "data_calculo" in d
        assert "versao" in d
        assert len(d["cenarios"]) == 3


class TestConformidadeCMN4966:
    """Testes específicos de conformidade com CMN 4966."""
    
    @pytest.fixture
    def gerenciador(self):
        return GerenciadorCenarios()
    
    def test_art36_paragrafo5_multiplos_cenarios(self, gerenciador):
        """
        Art. 36 §5º: A estimativa de perda esperada deve considerar
        cenários múltiplos ponderados por probabilidade.
        """
        cenarios = gerenciador.criar_cenarios()
        
        # Deve ter múltiplos cenários (pelo menos 3)
        assert len(cenarios) >= 3
        
        # Deve ter pesos (probabilidades)
        for cenario in cenarios:
            assert cenario.peso > 0
            assert cenario.peso < 1
    
    def test_pesos_somam_100_porcento(self, gerenciador):
        """Pesos devem representar probabilidades que somam 100%."""
        cenarios = gerenciador.criar_cenarios()
        soma = sum(c.peso for c in cenarios)
        
        assert abs(soma - 1.0) < 0.001, "Soma das probabilidades deve ser 100%"
    
    def test_ecl_final_media_ponderada(self, gerenciador):
        """
        ECL final deve ser a média ponderada dos ECLs por cenário.
        ECL_final = Σ(peso_i × ECL_i)
        """
        resultado = gerenciador.calcular_ecl_multi_cenario(0.10, 0.45, 100000.0)
        
        # Calcular manualmente a média ponderada
        soma_ponderada = sum(c.ecl_cenario * c.peso for c in resultado.cenarios)
        
        assert abs(resultado.ecl_final - soma_ponderada) < 0.01
    
    def test_cenarios_refletem_condicoes_economicas(self, gerenciador):
        """Cenários devem refletir diferentes condições econômicas."""
        cenarios = gerenciador.criar_cenarios()
        
        otimista = next(c for c in cenarios if c.nome == "otimista")
        base = next(c for c in cenarios if c.nome == "base")
        pessimista = next(c for c in cenarios if c.nome == "pessimista")
        
        # Otimista deve ter melhor cenário (menor PD, menor LGD)
        assert otimista.spread_pd < base.spread_pd
        assert otimista.spread_lgd < base.spread_lgd
        
        # Pessimista deve ter pior cenário (maior PD, maior LGD)
        assert pessimista.spread_pd > base.spread_pd
        assert pessimista.spread_lgd > base.spread_lgd


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
