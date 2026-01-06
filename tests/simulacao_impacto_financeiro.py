"""
Simulacao de Impacto Financeiro - PROLIMITE System
===================================================

Este script simula o impacto financeiro da implementacao do sistema
PROLIMITE usando os dados reais do Banpara 2025 como benchmark.

Dados de Referencia (1T-3T 2025):
- Carteira de Credito Total: R$ 15.33 bilhoes
- Provisao para PCLD: R$ 531-557 milhoes (3.6% da carteira)
- Lucro Liquido Trimestral: R$ 58-125 milhoes
- Indice de Inadimplencia: 1.66-2.51%
"""

import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class DadosBenchmark2025:
    """Dados financeiros do Banpara extraidos dos ITRs 2025."""
    
    # Carteira de Credito (R$ mil)
    carteira_credito_total: float = 15_330_261  # 2T2025
    carteira_consignado: float = 11_090_276
    carteira_banparacard: float = 1_239_264
    carteira_imobiliario: float = 1_359_084  # PF + PJ
    carteira_outros: float = 1_641_637
    
    # Provisao para PCLD (R$ mil)
    provisao_pcld: float = 557_671  # 2T2025
    indice_provisao_pct: float = 3.61
    
    # Metricas de Risco
    inadimplencia_pct: float = 2.51  # 2T2025
    indice_cobertura_pct: float = 27.86
    
    # Resultados (R$ mil) - Trimestral
    lucro_liquido_1t: float = 57_988
    lucro_liquido_2t: float = 67_639
    lucro_liquido_3t: float = 24_474
    
    # Limites (estimativa baseada na estrutura)
    # Assumindo ~30% de limites nao utilizados na media
    limite_nao_utilizado_estimado_pct: float = 30.0
    
    @property
    def lucro_liquido_9m(self) -> float:
        return self.lucro_liquido_1t + self.lucro_liquido_2t + self.lucro_liquido_3t
    
    @property
    def limite_nao_utilizado_estimado(self) -> float:
        return self.carteira_credito_total * self.limite_nao_utilizado_estimado_pct / 100


@dataclass
class ParametrosSimulacao:
    """Parametros da simulacao do sistema PROLIMITE."""
    
    # Distribuicao esperada das acoes de limite
    pct_clientes_reduzir: float = 16.0  # Propensao < 30%
    pct_clientes_manter: float = 70.0   # Propensao 30-70%  
    pct_clientes_aumentar: float = 14.0 # Propensao > 70%
    
    # Reducoes de limite para clientes com baixa propensao
    reducao_limite_media_pct: float = 35.0  # Reducao media de 35%
    
    # Aumento de limite para clientes com alta propensao
    aumento_limite_medio_pct: float = 25.0
    taxa_conversao_aumento: float = 40.0  # % que realmente usa o aumento
    
    # Taxas de juros por produto (% a.a. - media)
    taxa_consignado_aa: float = 23.51
    taxa_banparacard_aa: float = 114.71
    taxa_cartao_aa: float = 135.38
    taxa_imobiliario_aa: float = 10.40
    
    # CCF (Credit Conversion Factor) para limites nao utilizados
    ccf_medio: float = 0.75  # 75% dos limites nao utilizados viram EAD
    
    # PD medio por segmento de limite
    pd_limite_nao_utilizado: float = 0.05  # 5% PD para limites nao utilizados
    lgd_medio: float = 0.35  # 35% LGD medio


@dataclass
class ResultadoSimulacao:
    """Resultado da simulacao de impacto."""
    
    # Economia com reducao de ECL
    economia_ecl_anual: float = 0
    economia_ecl_detalhada: Dict[str, float] = None
    
    # Receita adicional com aumento de limites
    receita_adicional_anual: float = 0
    receita_adicional_detalhada: Dict[str, float] = None
    
    # Impacto total
    impacto_liquido_anual: float = 0
    impacto_pct_lucro: float = 0
    
    # Metricas adicionais
    reducao_provisao_pct: float = 0
    novos_negocios_estimados: float = 0


def calcular_economia_ecl(dados: DadosBenchmark2025, params: ParametrosSimulacao) -> Tuple[float, Dict]:
    """
    Calcula a economia de ECL com a reducao de limites nao utilizados.
    
    Formula: ECL = EAD x PD x LGD
    Onde EAD para limites = Limite * CCF
    """
    # Limite nao utilizado total estimado
    limite_nao_utilizado = dados.limite_nao_utilizado_estimado
    
    # Clientes que terao limite reduzido
    limite_para_reducao = limite_nao_utilizado * params.pct_clientes_reduzir / 100
    
    # Reducao efetiva de limite
    reducao_limite = limite_para_reducao * params.reducao_limite_media_pct / 100
    
    # Reducao de EAD
    reducao_ead = reducao_limite * params.ccf_medio
    
    # Economia de ECL = Reducao EAD * PD * LGD
    economia = reducao_ead * params.pd_limite_nao_utilizado * params.lgd_medio
    
    detalhes = {
        "limite_nao_utilizado_total": limite_nao_utilizado,
        "limite_elegivel_reducao": limite_para_reducao,
        "reducao_limite_efetiva": reducao_limite,
        "reducao_ead": reducao_ead,
        "economia_ecl": economia
    }
    
    return economia, detalhes


def calcular_receita_adicional(dados: DadosBenchmark2025, params: ParametrosSimulacao) -> Tuple[float, Dict]:
    """
    Calcula a receita adicional com aumento de limites para clientes
    com alta propensao de uso.
    """
    # Base de clientes para aumento (usando carteira consignado como proxy)
    carteira_base = dados.carteira_consignado
    
    # Clientes elegiveis para aumento
    volume_elegivel = carteira_base * params.pct_clientes_aumentar / 100
    
    # Aumento de limite
    aumento_limite = volume_elegivel * params.aumento_limite_medio_pct / 100
    
    # Novo credito efetivamente utilizado
    novo_credito = aumento_limite * params.taxa_conversao_aumento / 100
    
    # Receita de juros anual (usando taxa consignado)
    receita_juros = novo_credito * params.taxa_consignado_aa / 100
    
    detalhes = {
        "carteira_base": carteira_base,
        "volume_elegivel_aumento": volume_elegivel,
        "aumento_limite": aumento_limite,
        "novo_credito_utilizado": novo_credito,
        "taxa_juros_aplicada": params.taxa_consignado_aa,
        "receita_juros_anual": receita_juros
    }
    
    return receita_juros, detalhes


def executar_simulacao() -> ResultadoSimulacao:
    """Executa a simulacao completa de impacto financeiro."""
    
    dados = DadosBenchmark2025()
    params = ParametrosSimulacao()
    
    # Calcular economia de ECL
    economia_ecl, economia_detalhes = calcular_economia_ecl(dados, params)
    
    # Calcular receita adicional
    receita_adicional, receita_detalhes = calcular_receita_adicional(dados, params)
    
    # Impacto liquido (economia + receita - custo operacional estimado 10%)
    custo_operacional = (economia_ecl + receita_adicional) * 0.10
    impacto_liquido = economia_ecl + receita_adicional - custo_operacional
    
    # Impacto como % do lucro anualizado
    lucro_anualizado = dados.lucro_liquido_9m * 4 / 3  # Anualizando 9 meses
    impacto_pct = (impacto_liquido / lucro_anualizado) * 100
    
    # Reducao de provisao
    reducao_provisao_pct = (economia_ecl / dados.provisao_pcld) * 100
    
    resultado = ResultadoSimulacao(
        economia_ecl_anual=economia_ecl,
        economia_ecl_detalhada=economia_detalhes,
        receita_adicional_anual=receita_adicional,
        receita_adicional_detalhada=receita_detalhes,
        impacto_liquido_anual=impacto_liquido,
        impacto_pct_lucro=impacto_pct,
        reducao_provisao_pct=reducao_provisao_pct,
        novos_negocios_estimados=receita_detalhes["novo_credito_utilizado"]
    )
    
    return resultado


def gerar_relatorio(resultado: ResultadoSimulacao, dados: DadosBenchmark2025) -> str:
    """Gera relatorio formatado do impacto financeiro."""
    
    relatorio = f"""
================================================================================
                     RELATORIO DE IMPACTO FINANCEIRO
                     Sistema PROLIMITE - Simulacao 2025
================================================================================

Data da Simulacao: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

--------------------------------------------------------------------------------
DADOS DE BENCHMARK (Banpara 2025)
--------------------------------------------------------------------------------

  Carteira de Credito Total:      R$ {dados.carteira_credito_total/1000:,.0f} milhoes
  - Consignado:                   R$ {dados.carteira_consignado/1000:,.0f} milhoes
  - Banparacard:                  R$ {dados.carteira_banparacard/1000:,.0f} milhoes
  - Imobiliario:                  R$ {dados.carteira_imobiliario/1000:,.0f} milhoes
  
  Provisao para PCLD:             R$ {dados.provisao_pcld/1000:,.0f} milhoes ({dados.indice_provisao_pct:.2f}%)
  Indice de Inadimplencia:        {dados.inadimplencia_pct:.2f}%
  
  Lucro Liquido 9M2025:           R$ {dados.lucro_liquido_9m/1000:,.0f} milhoes
  - 1T2025:                       R$ {dados.lucro_liquido_1t/1000:,.0f} milhoes
  - 2T2025:                       R$ {dados.lucro_liquido_2t/1000:,.0f} milhoes
  - 3T2025:                       R$ {dados.lucro_liquido_3t/1000:,.0f} milhoes

--------------------------------------------------------------------------------
IMPACTO DA IMPLEMENTACAO DO PROLIMITE
--------------------------------------------------------------------------------

  1. ECONOMIA COM REDUCAO DE ECL
     ---------------------------------------------------------------------------
     Limite nao utilizado estimado:     R$ {resultado.economia_ecl_detalhada['limite_nao_utilizado_total']/1000:,.0f} milhoes
     Limite elegivel para reducao (16%): R$ {resultado.economia_ecl_detalhada['limite_elegivel_reducao']/1000:,.0f} milhoes
     Reducao efetiva de limite (35%):   R$ {resultado.economia_ecl_detalhada['reducao_limite_efetiva']/1000:,.0f} milhoes
     
     >> ECONOMIA ANUAL DE ECL:          R$ {resultado.economia_ecl_anual/1000:,.1f} milhoes
     >> Reducao de Provisao:            {resultado.reducao_provisao_pct:.2f}%

  2. RECEITA ADICIONAL COM AUMENTO DE LIMITES
     ---------------------------------------------------------------------------
     Clientes com alta propensao (14%): R$ {resultado.receita_adicional_detalhada['volume_elegivel_aumento']/1000:,.0f} milhoes
     Aumento de limite proposto (25%):  R$ {resultado.receita_adicional_detalhada['aumento_limite']/1000:,.0f} milhoes
     Novo credito efetivo (40% conv.):  R$ {resultado.receita_adicional_detalhada['novo_credito_utilizado']/1000:,.0f} milhoes
     
     >> RECEITA ADICIONAL ANUAL:        R$ {resultado.receita_adicional_anual/1000:,.1f} milhoes
     >> Novos Negocios Estimados:       R$ {resultado.novos_negocios_estimados/1000:,.0f} milhoes

  3. IMPACTO LIQUIDO CONSOLIDADO
     ---------------------------------------------------------------------------
     Economia de ECL:                   R$ {resultado.economia_ecl_anual/1000:,.1f} milhoes
     Receita Adicional:                 R$ {resultado.receita_adicional_anual/1000:,.1f} milhoes
     Custo Operacional (10%):           R$ -{(resultado.economia_ecl_anual + resultado.receita_adicional_anual)*0.1/1000:,.1f} milhoes
     
     >> IMPACTO LIQUIDO ANUAL:          R$ {resultado.impacto_liquido_anual/1000:,.1f} milhoes
     >> IMPACTO % DO LUCRO:             {resultado.impacto_pct_lucro:.1f}%

================================================================================
                              CONCLUSAO
================================================================================

  A implementacao do sistema PROLIMITE pode gerar um impacto positivo 
  estimado de R$ {resultado.impacto_liquido_anual/1000:,.1f} milhoes anuais, representando um 
  aumento de {resultado.impacto_pct_lucro:.1f}% no lucro liquido anualizado do banco.
  
  Este impacto vem de:
  - Reducao de provisao para perdas esperadas (ECL) em limites nao utilizados
  - Geracao de novos negocios com clientes de alta propensao e baixo risco

================================================================================
"""
    
    return relatorio


def main():
    """Executa a simulacao e exibe o relatorio."""
    
    print("Executando simulacao de impacto financeiro...")
    
    dados = DadosBenchmark2025()
    resultado = executar_simulacao()
    relatorio = gerar_relatorio(resultado, dados)
    
    print(relatorio)
    
    # Salvar relatorio
    output_path = PROJECT_ROOT / "tests" / "relatorio_impacto_financeiro.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(relatorio)
    
    print(f"\nRelatorio salvo em: {output_path}")
    
    return resultado


if __name__ == "__main__":
    main()
