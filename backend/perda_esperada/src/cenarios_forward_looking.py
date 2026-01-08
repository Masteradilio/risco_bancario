#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Cenários Forward Looking Multi-Cenário
=================================================

Implementa múltiplos cenários macroeconômicos ponderados por probabilidade
para cálculo de ECL conforme Art. 36 §5º da Resolução CMN 4.966/2021.

Este módulo adiciona a capacidade de calcular ECL considerando:
- Cenário Otimista (15% peso padrão)
- Cenário Base (70% peso padrão)  
- Cenário Pessimista (15% peso padrão)

Autor: Sistema ECL
Data: Janeiro 2026
Versão: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import requests
from datetime import datetime
import numpy as np

# Configuração de logging
logger = logging.getLogger(__name__)


class TipoCenario(Enum):
    """Tipos de cenários macroeconômicos."""
    OTIMISTA = "otimista"
    BASE = "base"
    PESSIMISTA = "pessimista"


@dataclass
class CenarioMacroeconomico:
    """
    Representa um cenário macroeconômico com suas projeções.
    
    Attributes:
        nome: Nome do cenário (otimista, base, pessimista)
        peso: Peso/probabilidade do cenário (0 a 1)
        selic_projetada: Taxa SELIC projetada (%)
        pib_projetado: Variação do PIB projetada (%)
        ipca_projetado: IPCA projetado (%)
        desemprego_projetado: Taxa de desemprego projetada (%)
        endividamento_projetado: Endividamento das famílias projetado (%)
        spread_pd: Ajuste (multiplicador) aplicado à PD neste cenário
        spread_lgd: Ajuste (multiplicador) aplicado ao LGD neste cenário
    """
    nome: str
    peso: float
    selic_projetada: float = 0.0
    pib_projetado: float = 0.0
    ipca_projetado: float = 0.0
    desemprego_projetado: float = 0.0
    endividamento_projetado: float = 0.0
    spread_pd: float = 1.0  # Multiplicador para PD
    spread_lgd: float = 1.0  # Multiplicador para LGD
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "nome": self.nome,
            "peso": self.peso,
            "selic_projetada": self.selic_projetada,
            "pib_projetado": self.pib_projetado,
            "ipca_projetado": self.ipca_projetado,
            "desemprego_projetado": self.desemprego_projetado,
            "endividamento_projetado": self.endividamento_projetado,
            "spread_pd": self.spread_pd,
            "spread_lgd": self.spread_lgd
        }


@dataclass
class ResultadoCenario:
    """
    Resultado do cálculo de ECL para um cenário específico.
    
    Attributes:
        cenario: Nome do cenário
        peso: Peso do cenário
        pd_ajustado: PD ajustado para o cenário
        lgd_ajustado: LGD ajustado para o cenário
        ecl_cenario: ECL calculado para este cenário
    """
    cenario: str
    peso: float
    pd_ajustado: float
    lgd_ajustado: float
    ecl_cenario: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "cenario": self.cenario,
            "peso": self.peso,
            "pd_ajustado": self.pd_ajustado,
            "lgd_ajustado": self.lgd_ajustado,
            "ecl_cenario": self.ecl_cenario
        }


@dataclass
class ResultadoECLMultiCenario:
    """
    Resultado consolidado do ECL multi-cenário.
    
    Attributes:
        ecl_final: ECL ponderado final (soma dos ECL × peso)
        cenarios: Lista de resultados por cenário
        data_calculo: Data do cálculo
        versao: Versão do modelo
    """
    ecl_final: float
    cenarios: List[ResultadoCenario]
    data_calculo: str = field(default_factory=lambda: datetime.now().isoformat())
    versao: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "ecl_final": self.ecl_final,
            "cenarios": [c.to_dict() for c in self.cenarios],
            "data_calculo": self.data_calculo,
            "versao": self.versao
        }


class GerenciadorCenarios:
    """
    Gerenciador de cenários macroeconômicos para Forward Looking.
    
    Implementa a lógica de múltiplos cenários ponderados conforme
    Art. 36 §5º da Resolução CMN 4.966/2021.
    """
    
    # Pesos padrão dos cenários (soma deve ser 1.0)
    PESOS_PADRAO = {
        TipoCenario.OTIMISTA: 0.15,
        TipoCenario.BASE: 0.70,
        TipoCenario.PESSIMISTA: 0.15
    }
    
    # Spreads padrão de PD por cenário
    SPREADS_PD_PADRAO = {
        TipoCenario.OTIMISTA: 0.85,     # PD 15% menor
        TipoCenario.BASE: 1.00,          # PD base
        TipoCenario.PESSIMISTA: 1.25     # PD 25% maior
    }
    
    # Spreads padrão de LGD por cenário
    SPREADS_LGD_PADRAO = {
        TipoCenario.OTIMISTA: 0.90,     # LGD 10% menor
        TipoCenario.BASE: 1.00,          # LGD base
        TipoCenario.PESSIMISTA: 1.15     # LGD 15% maior (Downturn LGD)
    }
    
    # URL da API SGS do BACEN
    SGS_API_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados/ultimos/1?formato=json"
    
    # Códigos das séries no SGS
    SERIES_SGS = {
        "selic": 432,           # Taxa SELIC
        "ipca": 433,            # IPCA
        "pib": 4380,            # PIB variação
        "desemprego": 24369,    # Taxa de desemprego
        "endividamento": 19882  # Endividamento das famílias
    }
    
    def __init__(
        self,
        pesos_customizados: Optional[Dict[TipoCenario, float]] = None,
        spreads_pd_customizados: Optional[Dict[TipoCenario, float]] = None,
        spreads_lgd_customizados: Optional[Dict[TipoCenario, float]] = None
    ):
        """
        Inicializa o gerenciador de cenários.
        
        Args:
            pesos_customizados: Pesos customizados para os cenários
            spreads_pd_customizados: Spreads de PD customizados
            spreads_lgd_customizados: Spreads de LGD customizados
        """
        self.pesos = pesos_customizados or self.PESOS_PADRAO.copy()
        self.spreads_pd = spreads_pd_customizados or self.SPREADS_PD_PADRAO.copy()
        self.spreads_lgd = spreads_lgd_customizados or self.SPREADS_LGD_PADRAO.copy()
        
        # Cache para dados macroeconômicos
        self._cache_macro: Dict[str, float] = {}
        self._cache_timestamp: Optional[datetime] = None
        
        # Validar que pesos somam 1.0
        soma_pesos = sum(self.pesos.values())
        if not np.isclose(soma_pesos, 1.0, atol=0.001):
            logger.warning(f"Soma dos pesos ({soma_pesos:.4f}) diferente de 1.0. Normalizando...")
            for tipo in self.pesos:
                self.pesos[tipo] /= soma_pesos
        
        logger.info(f"GerenciadorCenarios inicializado com pesos: {self.pesos}")
    
    def obter_dados_macroeconomicos(self, usar_cache: bool = True) -> Dict[str, float]:
        """
        Obtém dados macroeconômicos atuais da API SGS do BACEN.
        
        Args:
            usar_cache: Se True, usa cache se disponível (válido por 24h)
            
        Returns:
            Dict com indicadores macroeconômicos
        """
        # Verificar cache
        if usar_cache and self._cache_macro and self._cache_timestamp:
            idade_cache = (datetime.now() - self._cache_timestamp).total_seconds()
            if idade_cache < 86400:  # 24 horas
                logger.debug("Usando dados macroeconômicos do cache")
                return self._cache_macro
        
        dados = {}
        
        for indicador, codigo in self.SERIES_SGS.items():
            try:
                url = self.SGS_API_URL.format(codigo)
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    resultado = response.json()
                    if resultado and len(resultado) > 0:
                        dados[indicador] = float(resultado[0].get("valor", 0))
                        logger.debug(f"Obtido {indicador}: {dados[indicador]}")
                else:
                    logger.warning(f"Erro ao obter {indicador} do SGS: HTTP {response.status_code}")
                    dados[indicador] = self._obter_valor_fallback(indicador)
                    
            except Exception as e:
                logger.warning(f"Exceção ao obter {indicador} do SGS: {e}")
                dados[indicador] = self._obter_valor_fallback(indicador)
        
        # Atualizar cache
        self._cache_macro = dados
        self._cache_timestamp = datetime.now()
        
        return dados
    
    def _obter_valor_fallback(self, indicador: str) -> float:
        """Retorna valor fallback para indicador."""
        fallbacks = {
            "selic": 11.75,      # Janeiro 2026
            "ipca": 4.5,
            "pib": 2.5,
            "desemprego": 7.5,
            "endividamento": 48.0
        }
        return fallbacks.get(indicador, 0.0)
    
    def criar_cenarios(
        self,
        dados_macro: Optional[Dict[str, float]] = None
    ) -> List[CenarioMacroeconomico]:
        """
        Cria os três cenários macroeconômicos com projeções.
        
        Args:
            dados_macro: Dados macroeconômicos base (se None, busca do SGS)
            
        Returns:
            Lista com 3 cenários (otimista, base, pessimista)
        """
        if dados_macro is None:
            dados_macro = self.obter_dados_macroeconomicos()
        
        cenarios = []
        
        for tipo_cenario in TipoCenario:
            # Ajustes por cenário
            if tipo_cenario == TipoCenario.OTIMISTA:
                ajuste_selic = -1.5      # SELIC 1.5pp menor
                ajuste_pib = 1.0         # PIB 1pp maior
                ajuste_ipca = -0.5       # IPCA 0.5pp menor
                ajuste_desemprego = -1.0 # Desemprego 1pp menor
                ajuste_endiv = -2.0      # Endividamento 2pp menor
            elif tipo_cenario == TipoCenario.BASE:
                ajuste_selic = 0
                ajuste_pib = 0
                ajuste_ipca = 0
                ajuste_desemprego = 0
                ajuste_endiv = 0
            else:  # PESSIMISTA
                ajuste_selic = 2.0       # SELIC 2pp maior
                ajuste_pib = -1.5        # PIB 1.5pp menor
                ajuste_ipca = 1.0        # IPCA 1pp maior
                ajuste_desemprego = 2.0  # Desemprego 2pp maior
                ajuste_endiv = 5.0       # Endividamento 5pp maior
            
            cenario = CenarioMacroeconomico(
                nome=tipo_cenario.value,
                peso=self.pesos[tipo_cenario],
                selic_projetada=dados_macro.get("selic", 11.75) + ajuste_selic,
                pib_projetado=dados_macro.get("pib", 2.5) + ajuste_pib,
                ipca_projetado=dados_macro.get("ipca", 4.5) + ajuste_ipca,
                desemprego_projetado=dados_macro.get("desemprego", 7.5) + ajuste_desemprego,
                endividamento_projetado=dados_macro.get("endividamento", 48.0) + ajuste_endiv,
                spread_pd=self.spreads_pd[tipo_cenario],
                spread_lgd=self.spreads_lgd[tipo_cenario]
            )
            
            cenarios.append(cenario)
            logger.debug(f"Cenário {tipo_cenario.value} criado: peso={cenario.peso}, spread_pd={cenario.spread_pd}")
        
        return cenarios
    
    def calcular_k_pd_fl_ponderado(
        self,
        pd_base: float,
        cenarios: Optional[List[CenarioMacroeconomico]] = None
    ) -> Tuple[float, List[Dict[str, float]]]:
        """
        Calcula o fator K_PD_FL ponderado pelos cenários.
        
        Args:
            pd_base: PD base (antes do Forward Looking)
            cenarios: Lista de cenários (se None, cria novos)
            
        Returns:
            Tuple com (K_PD_FL ponderado, detalhes por cenário)
        """
        if cenarios is None:
            cenarios = self.criar_cenarios()
        
        k_pd_fl_ponderado = 0.0
        detalhes = []
        
        for cenario in cenarios:
            # K_PD_FL do cenário = spread do cenário
            k_pd_cenario = cenario.spread_pd
            
            # Contribuição ponderada
            contribuicao = k_pd_cenario * cenario.peso
            k_pd_fl_ponderado += contribuicao
            
            detalhes.append({
                "cenario": cenario.nome,
                "peso": cenario.peso,
                "k_pd_cenario": k_pd_cenario,
                "contribuicao": contribuicao
            })
        
        # Limitar variação a ±25% conforme boas práticas
        k_pd_fl_ponderado = max(0.75, min(1.25, k_pd_fl_ponderado))
        
        logger.info(f"K_PD_FL ponderado calculado: {k_pd_fl_ponderado:.4f}")
        return k_pd_fl_ponderado, detalhes
    
    def calcular_k_lgd_fl_ponderado(
        self,
        lgd_base: float,
        cenarios: Optional[List[CenarioMacroeconomico]] = None
    ) -> Tuple[float, List[Dict[str, float]]]:
        """
        Calcula o fator K_LGD_FL ponderado pelos cenários.
        
        Args:
            lgd_base: LGD base (antes do Forward Looking)
            cenarios: Lista de cenários (se None, cria novos)
            
        Returns:
            Tuple com (K_LGD_FL ponderado, detalhes por cenário)
        """
        if cenarios is None:
            cenarios = self.criar_cenarios()
        
        k_lgd_fl_ponderado = 0.0
        detalhes = []
        
        for cenario in cenarios:
            # K_LGD_FL do cenário = spread do cenário
            k_lgd_cenario = cenario.spread_lgd
            
            # Contribuição ponderada
            contribuicao = k_lgd_cenario * cenario.peso
            k_lgd_fl_ponderado += contribuicao
            
            detalhes.append({
                "cenario": cenario.nome,
                "peso": cenario.peso,
                "k_lgd_cenario": k_lgd_cenario,
                "contribuicao": contribuicao
            })
        
        # Limitar variação a ±20% conforme boas práticas
        k_lgd_fl_ponderado = max(0.80, min(1.20, k_lgd_fl_ponderado))
        
        logger.info(f"K_LGD_FL ponderado calculado: {k_lgd_fl_ponderado:.4f}")
        return k_lgd_fl_ponderado, detalhes
    
    def calcular_ecl_multi_cenario(
        self,
        pd_base: float,
        lgd_base: float,
        ead: float,
        cenarios: Optional[List[CenarioMacroeconomico]] = None
    ) -> ResultadoECLMultiCenario:
        """
        Calcula ECL considerando múltiplos cenários ponderados.
        
        ECL_final = Σ(peso_i × ECL_i) para i em {otimista, base, pessimista}
        
        onde ECL_i = PD_i × LGD_i × EAD
        
        Args:
            pd_base: PD base (0-1)
            lgd_base: LGD base (0-1)
            ead: Exposure at Default (R$)
            cenarios: Lista de cenários (se None, cria novos)
            
        Returns:
            ResultadoECLMultiCenario com ECL ponderado e detalhes
        """
        if cenarios is None:
            cenarios = self.criar_cenarios()
        
        resultados_cenarios = []
        ecl_ponderado = 0.0
        
        for cenario in cenarios:
            # Ajustar PD e LGD pelo spread do cenário
            pd_ajustado = pd_base * cenario.spread_pd
            lgd_ajustado = lgd_base * cenario.spread_lgd
            
            # Garantir limites
            pd_ajustado = max(0.0, min(1.0, pd_ajustado))
            lgd_ajustado = max(0.0, min(1.0, lgd_ajustado))
            
            # Calcular ECL do cenário
            ecl_cenario = pd_ajustado * lgd_ajustado * ead
            
            # Acumular ECL ponderado
            ecl_ponderado += ecl_cenario * cenario.peso
            
            resultado = ResultadoCenario(
                cenario=cenario.nome,
                peso=cenario.peso,
                pd_ajustado=pd_ajustado,
                lgd_ajustado=lgd_ajustado,
                ecl_cenario=ecl_cenario
            )
            resultados_cenarios.append(resultado)
            
            logger.debug(
                f"Cenário {cenario.nome}: PD={pd_ajustado:.4f}, "
                f"LGD={lgd_ajustado:.4f}, ECL=R$ {ecl_cenario:,.2f}"
            )
        
        resultado_final = ResultadoECLMultiCenario(
            ecl_final=ecl_ponderado,
            cenarios=resultados_cenarios
        )
        
        logger.info(f"ECL Multi-Cenário calculado: R$ {ecl_ponderado:,.2f}")
        
        return resultado_final
    
    def atualizar_pesos(
        self,
        otimista: Optional[float] = None,
        base: Optional[float] = None,
        pessimista: Optional[float] = None
    ) -> None:
        """
        Atualiza os pesos dos cenários.
        
        Args:
            otimista: Novo peso do cenário otimista
            base: Novo peso do cenário base
            pessimista: Novo peso do cenário pessimista
        """
        if otimista is not None:
            self.pesos[TipoCenario.OTIMISTA] = otimista
        if base is not None:
            self.pesos[TipoCenario.BASE] = base
        if pessimista is not None:
            self.pesos[TipoCenario.PESSIMISTA] = pessimista
        
        # Normalizar para somar 1.0
        soma = sum(self.pesos.values())
        for tipo in self.pesos:
            self.pesos[tipo] /= soma
        
        logger.info(f"Pesos atualizados: {self.pesos}")
    
    def atualizar_spreads(
        self,
        spreads_pd: Optional[Dict[TipoCenario, float]] = None,
        spreads_lgd: Optional[Dict[TipoCenario, float]] = None
    ) -> None:
        """
        Atualiza os spreads dos cenários.
        
        Args:
            spreads_pd: Novos spreads de PD por cenário
            spreads_lgd: Novos spreads de LGD por cenário
        """
        if spreads_pd:
            self.spreads_pd.update(spreads_pd)
        if spreads_lgd:
            self.spreads_lgd.update(spreads_lgd)
        
        logger.info(f"Spreads atualizados - PD: {self.spreads_pd}, LGD: {self.spreads_lgd}")


# Instância global para uso simplificado
_gerenciador_cenarios: Optional[GerenciadorCenarios] = None


def get_gerenciador_cenarios() -> GerenciadorCenarios:
    """Obtém ou cria instância global do gerenciador de cenários."""
    global _gerenciador_cenarios
    if _gerenciador_cenarios is None:
        _gerenciador_cenarios = GerenciadorCenarios()
    return _gerenciador_cenarios


def calcular_ecl_multi_cenario(
    pd_base: float,
    lgd_base: float,
    ead: float
) -> ResultadoECLMultiCenario:
    """
    Função de conveniência para calcular ECL multi-cenário.
    
    Args:
        pd_base: PD base (0-1)
        lgd_base: LGD base (0-1)
        ead: Exposure at Default (R$)
        
    Returns:
        ResultadoECLMultiCenario
    """
    gerenciador = get_gerenciador_cenarios()
    return gerenciador.calcular_ecl_multi_cenario(pd_base, lgd_base, ead)


if __name__ == "__main__":
    # Configurar logging para teste
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("TESTE DO MÓDULO DE CENÁRIOS FORWARD LOOKING")
    print("=" * 60)
    
    # Criar gerenciador
    gerenciador = GerenciadorCenarios()
    
    # Criar cenários
    print("\n1. Criando cenários macroeconômicos...")
    cenarios = gerenciador.criar_cenarios()
    
    for cenario in cenarios:
        print(f"\n   Cenário: {cenario.nome.upper()}")
        print(f"   - Peso: {cenario.peso:.0%}")
        print(f"   - SELIC projetada: {cenario.selic_projetada:.2f}%")
        print(f"   - PIB projetado: {cenario.pib_projetado:.2f}%")
        print(f"   - Spread PD: {cenario.spread_pd:.2f}")
        print(f"   - Spread LGD: {cenario.spread_lgd:.2f}")
    
    # Calcular K_PD_FL ponderado
    print("\n2. Calculando K_PD_FL ponderado...")
    k_pd_fl, detalhes_pd = gerenciador.calcular_k_pd_fl_ponderado(0.10, cenarios)
    print(f"   K_PD_FL ponderado: {k_pd_fl:.4f}")
    
    # Calcular K_LGD_FL ponderado
    print("\n3. Calculando K_LGD_FL ponderado...")
    k_lgd_fl, detalhes_lgd = gerenciador.calcular_k_lgd_fl_ponderado(0.45, cenarios)
    print(f"   K_LGD_FL ponderado: {k_lgd_fl:.4f}")
    
    # Calcular ECL multi-cenário
    print("\n4. Calculando ECL Multi-Cenário...")
    pd_base = 0.10      # 10% PD
    lgd_base = 0.45     # 45% LGD
    ead = 100000.0      # R$ 100.000 EAD
    
    resultado = gerenciador.calcular_ecl_multi_cenario(pd_base, lgd_base, ead, cenarios)
    
    print(f"\n   Parâmetros base:")
    print(f"   - PD Base: {pd_base:.2%}")
    print(f"   - LGD Base: {lgd_base:.2%}")
    print(f"   - EAD: R$ {ead:,.2f}")
    
    print(f"\n   Resultados por cenário:")
    for cenario_result in resultado.cenarios:
        print(f"\n   {cenario_result.cenario.upper()} (peso: {cenario_result.peso:.0%}):")
        print(f"   - PD ajustado: {cenario_result.pd_ajustado:.4%}")
        print(f"   - LGD ajustado: {cenario_result.lgd_ajustado:.4%}")
        print(f"   - ECL cenário: R$ {cenario_result.ecl_cenario:,.2f}")
    
    print(f"\n   ECL FINAL PONDERADO: R$ {resultado.ecl_final:,.2f}")
    
    # Validar fórmula
    ecl_simples = pd_base * lgd_base * ead
    print(f"\n   Comparação:")
    print(f"   - ECL simples (sem FL): R$ {ecl_simples:,.2f}")
    print(f"   - ECL multi-cenário: R$ {resultado.ecl_final:,.2f}")
    print(f"   - Diferença: {((resultado.ecl_final / ecl_simples) - 1) * 100:+.2f}%")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
