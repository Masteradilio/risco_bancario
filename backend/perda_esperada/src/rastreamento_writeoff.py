#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Rastreamento de Write-off
====================================

Implementa acompanhamento de 5 anos para operações baixadas conforme
Art. 49 da Resolução CMN 4.966/2021.

Este módulo gerencia:
- Registro de baixas (write-offs)
- Acompanhamento de recuperações pós-baixa por 5 anos
- Cálculo de taxa de recuperação histórica
- Relatórios regulatórios

Autor: Sistema ECL
Data: Janeiro 2026
Versão: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import numpy as np

# Configuração de logging
logger = logging.getLogger(__name__)


class MotivoBaixa(Enum):
    """Motivos de baixa contábil."""
    INADIMPLENCIA_PROLONGADA = "inadimplencia_prolongada"
    FALENCIA_RECUPERACAO_JUDICIAL = "falencia_rj"
    OBITO_SEM_ESPÓLIO = "obito"
    PRESCRICAO = "prescricao"
    ACORDO_JUDICIAL = "acordo_judicial"
    CESSAO_CREDITO = "cessao"
    OUTRO = "outro"


class StatusRecuperacao(Enum):
    """Status de recuperação pós-baixa."""
    EM_ACOMPANHAMENTO = "em_acompanhamento"
    RECUPERACAO_PARCIAL = "recuperacao_parcial"
    RECUPERACAO_TOTAL = "recuperacao_total"
    IRRECUPERAVEL = "irrecuperavel"
    PERIODO_ENCERRADO = "periodo_encerrado"


@dataclass
class RegistroBaixa:
    """
    Registro de uma operação baixada (write-off).
    
    Attributes:
        contrato_id: ID do contrato
        data_baixa: Data da baixa contábil
        valor_baixado: Valor baixado (write-off)
        motivo: Motivo da baixa
        provisao_constituida: Provisão que estava constituída
        estagio_na_baixa: Estágio IFRS 9 no momento da baixa
    """
    contrato_id: str
    data_baixa: datetime
    valor_baixado: float
    motivo: MotivoBaixa
    provisao_constituida: float
    estagio_na_baixa: int
    cliente_id: str = ""
    produto: str = ""
    observacoes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "contrato_id": self.contrato_id,
            "data_baixa": self.data_baixa.isoformat(),
            "valor_baixado": self.valor_baixado,
            "motivo": self.motivo.value,
            "provisao_constituida": self.provisao_constituida,
            "estagio_na_baixa": self.estagio_na_baixa,
            "cliente_id": self.cliente_id,
            "produto": self.produto,
            "observacoes": self.observacoes
        }


@dataclass
class RegistroRecuperacao:
    """
    Registro de recuperação pós-baixa.
    
    Attributes:
        contrato_id: ID do contrato
        data_recuperacao: Data da recuperação
        valor_recuperado: Valor recuperado
        tipo: Tipo de recuperação (pagamento, acordo, etc.)
    """
    contrato_id: str
    data_recuperacao: datetime
    valor_recuperado: float
    tipo: str = "pagamento"
    observacoes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "contrato_id": self.contrato_id,
            "data_recuperacao": self.data_recuperacao.isoformat(),
            "valor_recuperado": self.valor_recuperado,
            "tipo": self.tipo,
            "observacoes": self.observacoes
        }


@dataclass
class ResumoContratoBaixado:
    """
    Resumo de acompanhamento de contrato baixado.
    
    Attributes:
        contrato_id: ID do contrato
        data_baixa: Data da baixa
        valor_baixado: Valor original baixado
        total_recuperado: Total recuperado até a data
        taxa_recuperacao: Taxa de recuperação (%)
        status: Status atual
        dias_desde_baixa: Dias desde a baixa
        tempo_restante_dias: Dias restantes de acompanhamento
    """
    contrato_id: str
    data_baixa: datetime
    valor_baixado: float
    total_recuperado: float
    taxa_recuperacao: float
    status: StatusRecuperacao
    dias_desde_baixa: int
    tempo_restante_dias: int
    recuperacoes: List[RegistroRecuperacao] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "contrato_id": self.contrato_id,
            "data_baixa": self.data_baixa.isoformat(),
            "valor_baixado": self.valor_baixado,
            "total_recuperado": self.total_recuperado,
            "taxa_recuperacao": self.taxa_recuperacao,
            "status": self.status.value,
            "dias_desde_baixa": self.dias_desde_baixa,
            "tempo_restante_dias": self.tempo_restante_dias,
            "quantidade_recuperacoes": len(self.recuperacoes)
        }


class RastreadorWriteOff:
    """
    Sistema de rastreamento de write-offs com acompanhamento de 5 anos.
    
    Implementa os requisitos do Art. 49 da Resolução CMN 4.966/2021.
    """
    
    # Período de acompanhamento em dias (5 anos)
    PERIODO_ACOMPANHAMENTO_DIAS = 5 * 365  # 1825 dias
    
    def __init__(self):
        """Inicializa o rastreador de write-offs."""
        # Registro de baixas
        self._baixas: Dict[str, RegistroBaixa] = {}
        
        # Recuperações por contrato
        self._recuperacoes: Dict[str, List[RegistroRecuperacao]] = {}
        
        # Cache de resumos
        self._cache_resumos: Dict[str, ResumoContratoBaixado] = {}
        
        logger.info("RastreadorWriteOff inicializado")
    
    def registrar_baixa(
        self,
        contrato_id: str,
        valor_baixado: float,
        motivo: MotivoBaixa,
        provisao_constituida: float,
        estagio_na_baixa: int = 3,
        data_baixa: Optional[datetime] = None,
        cliente_id: str = "",
        produto: str = "",
        observacoes: str = ""
    ) -> RegistroBaixa:
        """
        Registra uma baixa contábil (write-off).
        
        Args:
            contrato_id: ID do contrato
            valor_baixado: Valor a ser baixado
            motivo: Motivo da baixa
            provisao_constituida: Provisão que estava constituída
            estagio_na_baixa: Estágio IFRS 9 (geralmente 3)
            data_baixa: Data da baixa (default: agora)
            cliente_id: ID do cliente
            produto: Produto do contrato
            observacoes: Observações adicionais
            
        Returns:
            RegistroBaixa criado
        """
        if data_baixa is None:
            data_baixa = datetime.now()
        
        if contrato_id in self._baixas:
            logger.warning(f"Contrato {contrato_id} já possui baixa registrada. Sobrescrevendo.")
        
        registro = RegistroBaixa(
            contrato_id=contrato_id,
            data_baixa=data_baixa,
            valor_baixado=valor_baixado,
            motivo=motivo,
            provisao_constituida=provisao_constituida,
            estagio_na_baixa=estagio_na_baixa,
            cliente_id=cliente_id,
            produto=produto,
            observacoes=observacoes
        )
        
        self._baixas[contrato_id] = registro
        
        # Inicializar lista de recuperações
        if contrato_id not in self._recuperacoes:
            self._recuperacoes[contrato_id] = []
        
        # Limpar cache
        if contrato_id in self._cache_resumos:
            del self._cache_resumos[contrato_id]
        
        logger.info(
            f"Baixa registrada: {contrato_id}, valor=R$ {valor_baixado:,.2f}, "
            f"motivo={motivo.value}"
        )
        
        return registro
    
    def registrar_recuperacao(
        self,
        contrato_id: str,
        valor_recuperado: float,
        data_recuperacao: Optional[datetime] = None,
        tipo: str = "pagamento",
        observacoes: str = ""
    ) -> Optional[RegistroRecuperacao]:
        """
        Registra uma recuperação pós-baixa.
        
        Args:
            contrato_id: ID do contrato
            valor_recuperado: Valor recuperado
            data_recuperacao: Data da recuperação (default: agora)
            tipo: Tipo de recuperação
            observacoes: Observações
            
        Returns:
            RegistroRecuperacao ou None se contrato não encontrado
        """
        if contrato_id not in self._baixas:
            logger.warning(f"Contrato {contrato_id} não possui baixa registrada.")
            return None
        
        if data_recuperacao is None:
            data_recuperacao = datetime.now()
        
        baixa = self._baixas[contrato_id]
        
        # Verificar se ainda está no período de acompanhamento
        dias_desde_baixa = (data_recuperacao - baixa.data_baixa).days
        if dias_desde_baixa > self.PERIODO_ACOMPANHAMENTO_DIAS:
            logger.warning(
                f"Recuperação fora do período de acompanhamento de 5 anos "
                f"({dias_desde_baixa} dias desde baixa)."
            )
        
        registro = RegistroRecuperacao(
            contrato_id=contrato_id,
            data_recuperacao=data_recuperacao,
            valor_recuperado=valor_recuperado,
            tipo=tipo,
            observacoes=observacoes
        )
        
        self._recuperacoes[contrato_id].append(registro)
        
        # Limpar cache
        if contrato_id in self._cache_resumos:
            del self._cache_resumos[contrato_id]
        
        # Calcular total recuperado
        total_recuperado = sum(r.valor_recuperado for r in self._recuperacoes[contrato_id])
        taxa = (total_recuperado / baixa.valor_baixado * 100) if baixa.valor_baixado > 0 else 0
        
        logger.info(
            f"Recuperação registrada: {contrato_id}, valor=R$ {valor_recuperado:,.2f}, "
            f"total={taxa:.1f}%"
        )
        
        return registro
    
    def obter_resumo_contrato(
        self,
        contrato_id: str,
        data_referencia: Optional[datetime] = None
    ) -> Optional[ResumoContratoBaixado]:
        """
        Obtém resumo de acompanhamento de um contrato baixado.
        
        Args:
            contrato_id: ID do contrato
            data_referencia: Data de referência (default: agora)
            
        Returns:
            ResumoContratoBaixado ou None se não encontrado
        """
        if contrato_id not in self._baixas:
            return None
        
        if data_referencia is None:
            data_referencia = datetime.now()
        
        baixa = self._baixas[contrato_id]
        recuperacoes = self._recuperacoes.get(contrato_id, [])
        
        # Calcular totais
        total_recuperado = sum(r.valor_recuperado for r in recuperacoes)
        taxa_recuperacao = (total_recuperado / baixa.valor_baixado * 100) if baixa.valor_baixado > 0 else 0
        
        # Calcular dias
        dias_desde_baixa = (data_referencia - baixa.data_baixa).days
        tempo_restante = max(0, self.PERIODO_ACOMPANHAMENTO_DIAS - dias_desde_baixa)
        
        # Determinar status
        if tempo_restante == 0:
            status = StatusRecuperacao.PERIODO_ENCERRADO
        elif taxa_recuperacao >= 100:
            status = StatusRecuperacao.RECUPERACAO_TOTAL
        elif total_recuperado > 0:
            status = StatusRecuperacao.RECUPERACAO_PARCIAL
        else:
            status = StatusRecuperacao.EM_ACOMPANHAMENTO
        
        resumo = ResumoContratoBaixado(
            contrato_id=contrato_id,
            data_baixa=baixa.data_baixa,
            valor_baixado=baixa.valor_baixado,
            total_recuperado=total_recuperado,
            taxa_recuperacao=taxa_recuperacao,
            status=status,
            dias_desde_baixa=dias_desde_baixa,
            tempo_restante_dias=tempo_restante,
            recuperacoes=recuperacoes
        )
        
        return resumo
    
    def obter_contratos_em_acompanhamento(
        self,
        data_referencia: Optional[datetime] = None
    ) -> List[ResumoContratoBaixado]:
        """
        Obtém todos os contratos ainda em período de acompanhamento (5 anos).
        
        Args:
            data_referencia: Data de referência (default: agora)
            
        Returns:
            Lista de resumos de contratos em acompanhamento
        """
        if data_referencia is None:
            data_referencia = datetime.now()
        
        contratos_ativos = []
        
        for contrato_id in self._baixas:
            resumo = self.obter_resumo_contrato(contrato_id, data_referencia)
            if resumo and resumo.tempo_restante_dias > 0:
                contratos_ativos.append(resumo)
        
        # Ordenar por tempo restante (decrescente)
        contratos_ativos.sort(key=lambda x: x.tempo_restante_dias, reverse=True)
        
        logger.info(f"Contratos em acompanhamento: {len(contratos_ativos)}")
        
        return contratos_ativos
    
    def calcular_taxa_recuperacao_historica(
        self,
        produto: Optional[str] = None,
        motivo: Optional[MotivoBaixa] = None,
        periodo_inicial: Optional[datetime] = None,
        periodo_final: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calcula taxa de recuperação histórica com filtros opcionais.
        
        Args:
            produto: Filtrar por produto
            motivo: Filtrar por motivo de baixa
            periodo_inicial: Data inicial do período
            periodo_final: Data final do período
            
        Returns:
            Dict com estatísticas de recuperação
        """
        contratos_filtrados = []
        
        for contrato_id, baixa in self._baixas.items():
            # Aplicar filtros
            if produto and baixa.produto != produto:
                continue
            if motivo and baixa.motivo != motivo:
                continue
            if periodo_inicial and baixa.data_baixa < periodo_inicial:
                continue
            if periodo_final and baixa.data_baixa > periodo_final:
                continue
            
            resumo = self.obter_resumo_contrato(contrato_id)
            if resumo:
                contratos_filtrados.append(resumo)
        
        if not contratos_filtrados:
            return {
                "quantidade_contratos": 0,
                "valor_total_baixado": 0,
                "valor_total_recuperado": 0,
                "taxa_recuperacao_media": 0,
                "taxa_recuperacao_ponderada": 0
            }
        
        # Calcular estatísticas
        qtd = len(contratos_filtrados)
        valor_baixado = sum(c.valor_baixado for c in contratos_filtrados)
        valor_recuperado = sum(c.total_recuperado for c in contratos_filtrados)
        
        taxa_media = np.mean([c.taxa_recuperacao for c in contratos_filtrados])
        taxa_ponderada = (valor_recuperado / valor_baixado * 100) if valor_baixado > 0 else 0
        
        # Distribuição por status
        distribuicao_status = {}
        for status in StatusRecuperacao:
            qtd_status = sum(1 for c in contratos_filtrados if c.status == status)
            distribuicao_status[status.value] = qtd_status
        
        resultado = {
            "quantidade_contratos": qtd,
            "valor_total_baixado": valor_baixado,
            "valor_total_recuperado": valor_recuperado,
            "taxa_recuperacao_media": taxa_media,
            "taxa_recuperacao_ponderada": taxa_ponderada,
            "distribuicao_status": distribuicao_status,
            "periodo_analise": {
                "inicio": periodo_inicial.isoformat() if periodo_inicial else None,
                "fim": periodo_final.isoformat() if periodo_final else None
            },
            "filtros": {
                "produto": produto,
                "motivo": motivo.value if motivo else None
            }
        }
        
        logger.info(
            f"Taxa recuperação histórica: {taxa_ponderada:.2f}% "
            f"({qtd} contratos, R$ {valor_recuperado:,.2f} / R$ {valor_baixado:,.2f})"
        )
        
        return resultado
    
    def gerar_relatorio_regulatorio(
        self,
        data_referencia: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Gera relatório para envio regulatório (BACEN).
        
        Args:
            data_referencia: Data de referência
            
        Returns:
            Dict com dados formatados para relatório
        """
        if data_referencia is None:
            data_referencia = datetime.now()
        
        contratos_ativos = self.obter_contratos_em_acompanhamento(data_referencia)
        estatisticas = self.calcular_taxa_recuperacao_historica()
        
        # Agrupar por ano de baixa
        por_ano = {}
        for contrato_id, baixa in self._baixas.items():
            ano = baixa.data_baixa.year
            if ano not in por_ano:
                por_ano[ano] = {"quantidade": 0, "valor_baixado": 0, "valor_recuperado": 0}
            por_ano[ano]["quantidade"] += 1
            por_ano[ano]["valor_baixado"] += baixa.valor_baixado
            
            resumo = self.obter_resumo_contrato(contrato_id, data_referencia)
            if resumo:
                por_ano[ano]["valor_recuperado"] += resumo.total_recuperado
        
        # Calcular taxa por ano
        for ano in por_ano:
            if por_ano[ano]["valor_baixado"] > 0:
                por_ano[ano]["taxa_recuperacao"] = (
                    por_ano[ano]["valor_recuperado"] / 
                    por_ano[ano]["valor_baixado"] * 100
                )
            else:
                por_ano[ano]["taxa_recuperacao"] = 0
        
        relatorio = {
            "data_geracao": datetime.now().isoformat(),
            "data_referencia": data_referencia.isoformat(),
            "periodo_acompanhamento_anos": 5,
            "resumo_geral": {
                "total_contratos_baixados": len(self._baixas),
                "contratos_em_acompanhamento": len(contratos_ativos),
                "valor_total_baixado": estatisticas["valor_total_baixado"],
                "valor_total_recuperado": estatisticas["valor_total_recuperado"],
                "taxa_recuperacao_global": estatisticas["taxa_recuperacao_ponderada"]
            },
            "por_ano_baixa": por_ano,
            "distribuicao_status": estatisticas.get("distribuicao_status", {}),
            "contratos_ativos_detalhes": [c.to_dict() for c in contratos_ativos[:100]]  # Top 100
        }
        
        logger.info(f"Relatório regulatório gerado com {len(self._baixas)} contratos")
        
        return relatorio
    
    def processar_dataframe_baixas(
        self,
        df: pd.DataFrame,
        col_contrato: str = "ID_Contrato",
        col_valor: str = "valor_baixado",
        col_data: str = "data_baixa",
        col_motivo: str = "motivo_baixa",
        col_provisao: str = "provisao_constituida",
        col_estagio: str = "estagio"
    ) -> int:
        """
        Processa um DataFrame para registrar múltiplas baixas.
        
        Args:
            df: DataFrame com dados de baixas
            col_contrato: Coluna de ID do contrato
            col_valor: Coluna de valor baixado
            col_data: Coluna de data da baixa
            col_motivo: Coluna de motivo
            col_provisao: Coluna de provisão
            col_estagio: Coluna de estágio
            
        Returns:
            Quantidade de baixas registradas
        """
        registrados = 0
        
        for _, row in df.iterrows():
            try:
                # Converter motivo
                motivo_str = str(row.get(col_motivo, "outro")).lower()
                motivo = MotivoBaixa.OUTRO
                for m in MotivoBaixa:
                    if m.value in motivo_str:
                        motivo = m
                        break
                
                # Converter data
                data_baixa = pd.to_datetime(row.get(col_data, datetime.now()))
                if pd.isna(data_baixa):
                    data_baixa = datetime.now()
                
                self.registrar_baixa(
                    contrato_id=str(row[col_contrato]),
                    valor_baixado=float(row.get(col_valor, 0)),
                    motivo=motivo,
                    provisao_constituida=float(row.get(col_provisao, 0)),
                    estagio_na_baixa=int(row.get(col_estagio, 3)),
                    data_baixa=data_baixa
                )
                registrados += 1
            except Exception as e:
                logger.warning(f"Erro ao processar baixa: {e}")
        
        logger.info(f"Processamento concluído: {registrados} baixas registradas")
        return registrados
    
    def obter_todas_baixas(self) -> List[Dict[str, Any]]:
        """Retorna todas as baixas registradas."""
        return [b.to_dict() for b in self._baixas.values()]
    
    def obter_todas_recuperacoes(self, contrato_id: str) -> List[Dict[str, Any]]:
        """Retorna todas as recuperações de um contrato."""
        if contrato_id not in self._recuperacoes:
            return []
        return [r.to_dict() for r in self._recuperacoes[contrato_id]]
    
    def limpar_dados(self) -> None:
        """Limpa todos os dados do rastreador."""
        self._baixas.clear()
        self._recuperacoes.clear()
        self._cache_resumos.clear()
        logger.info("Dados do rastreador limpos")


# Instância global
_rastreador_writeoff: Optional[RastreadorWriteOff] = None


def get_rastreador_writeoff() -> RastreadorWriteOff:
    """Obtém ou cria instância global do rastreador."""
    global _rastreador_writeoff
    if _rastreador_writeoff is None:
        _rastreador_writeoff = RastreadorWriteOff()
    return _rastreador_writeoff


if __name__ == "__main__":
    # Configurar logging para teste
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("TESTE DO RASTREADOR DE WRITE-OFF")
    print("=" * 60)
    
    rastreador = RastreadorWriteOff()
    
    # Registrar algumas baixas
    print("\n1. Registrando baixas...")
    
    baixas_teste = [
        ("CTR001", 10000.0, MotivoBaixa.INADIMPLENCIA_PROLONGADA, 10000.0),
        ("CTR002", 25000.0, MotivoBaixa.FALENCIA_RECUPERACAO_JUDICIAL, 25000.0),
        ("CTR003", 5000.0, MotivoBaixa.PRESCRICAO, 5000.0),
    ]
    
    for contrato, valor, motivo, provisao in baixas_teste:
        # Simular baixas em datas diferentes
        data = datetime.now() - timedelta(days=np.random.randint(30, 1000))
        rastreador.registrar_baixa(
            contrato_id=contrato,
            valor_baixado=valor,
            motivo=motivo,
            provisao_constituida=provisao,
            data_baixa=data
        )
    
    print(f"\n   {len(baixas_teste)} baixas registradas")
    
    # Registrar recuperações
    print("\n2. Registrando recuperações...")
    
    # Recuperações para CTR001
    rastreador.registrar_recuperacao("CTR001", 2000.0, tipo="acordo")
    rastreador.registrar_recuperacao("CTR001", 1500.0, tipo="pagamento")
    
    # Recuperações para CTR002
    rastreador.registrar_recuperacao("CTR002", 5000.0, tipo="acordo_judicial")
    
    print("   Recuperações registradas")
    
    # Resumo por contrato
    print("\n3. Resumos por contrato:")
    
    for contrato, _, _, _ in baixas_teste:
        resumo = rastreador.obter_resumo_contrato(contrato)
        if resumo:
            print(f"\n   {contrato}:")
            print(f"   - Valor baixado: R$ {resumo.valor_baixado:,.2f}")
            print(f"   - Total recuperado: R$ {resumo.total_recuperado:,.2f}")
            print(f"   - Taxa recuperação: {resumo.taxa_recuperacao:.1f}%")
            print(f"   - Status: {resumo.status.value}")
            print(f"   - Dias desde baixa: {resumo.dias_desde_baixa}")
            print(f"   - Tempo restante: {resumo.tempo_restante_dias} dias")
    
    # Taxa de recuperação histórica
    print("\n4. Taxa de recuperação histórica:")
    estatisticas = rastreador.calcular_taxa_recuperacao_historica()
    
    print(f"   - Contratos: {estatisticas['quantidade_contratos']}")
    print(f"   - Valor baixado: R$ {estatisticas['valor_total_baixado']:,.2f}")
    print(f"   - Valor recuperado: R$ {estatisticas['valor_total_recuperado']:,.2f}")
    print(f"   - Taxa média: {estatisticas['taxa_recuperacao_media']:.1f}%")
    print(f"   - Taxa ponderada: {estatisticas['taxa_recuperacao_ponderada']:.1f}%")
    
    # Relatório regulatório
    print("\n5. Gerando relatório regulatório...")
    relatorio = rastreador.gerar_relatorio_regulatorio()
    print(f"   - Data geração: {relatorio['data_geracao']}")
    print(f"   - Total contratos: {relatorio['resumo_geral']['total_contratos_baixados']}")
    print(f"   - Em acompanhamento: {relatorio['resumo_geral']['contratos_em_acompanhamento']}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
