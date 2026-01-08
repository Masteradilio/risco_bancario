#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Sistema de Cura Formal
================================

Implementa critérios formais de reversão de estágio com período de observação
conforme Art. 41 da Resolução CMN 4.966/2021.

Este módulo gerencia:
- Período de cura para Stage 2 → Stage 1 (6 meses)
- Período de cura para Stage 3 → Stage 2 (12 meses)
- Critérios específicos para reestruturações
- Histórico de estágios por contrato

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


class MotivoMigracao(Enum):
    """Motivos de migração de estágio."""
    ATRASO_30_DIAS = "atraso_30_dias"
    ATRASO_90_DIAS = "atraso_90_dias"
    AUMENTO_RISCO_PD = "aumento_risco_pd"
    REESTRUTURACAO = "reestruturacao"
    EVENTO_JUDICIAL = "evento_judicial"
    ARRASTO_CONTRAPARTE = "arrasto_contraparte"
    CURA_APROVADA = "cura_aprovada"
    INICIAL = "inicial"


class StatusCura(Enum):
    """Status do processo de cura."""
    NAO_APLICAVEL = "nao_aplicavel"
    EM_OBSERVACAO = "em_observacao"
    ELEGIVEL = "elegivel"
    APROVADO = "aprovado"
    REPROVADO = "reprovado"


@dataclass
class HistoricoEstagio:
    """
    Registro histórico de estágio de um contrato.
    
    Attributes:
        data: Data da mudança de estágio
        estagio_anterior: Estágio antes da mudança
        estagio_novo: Novo estágio
        motivo: Motivo da migração
        dias_atraso: Dias em atraso na data
        pd_atual: PD na data da mudança
    """
    data: datetime
    estagio_anterior: int
    estagio_novo: int
    motivo: MotivoMigracao
    dias_atraso: int = 0
    pd_atual: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "data": self.data.isoformat(),
            "estagio_anterior": self.estagio_anterior,
            "estagio_novo": self.estagio_novo,
            "motivo": self.motivo.value,
            "dias_atraso": self.dias_atraso,
            "pd_atual": self.pd_atual
        }


@dataclass
class ResultadoCura:
    """
    Resultado da avaliação de cura de um contrato.
    
    Attributes:
        contrato_id: ID do contrato
        status: Status atual do processo de cura
        estagio_atual: Estágio atual
        estagio_alvo: Estágio alvo após cura (se aplicável)
        meses_em_observacao: Meses já cumpridos em observação
        meses_necessarios: Meses necessários para cura
        percentual_progresso: Progresso para cura (0-100%)
        elegivel_cura: Se está elegível para cura
        motivo: Motivo do status
        data_inicio_cura: Data de início do período de cura
        data_previsao_cura: Data prevista para conclusão da cura
    """
    contrato_id: str
    status: StatusCura
    estagio_atual: int
    estagio_alvo: int
    meses_em_observacao: int
    meses_necessarios: int
    percentual_progresso: float
    elegivel_cura: bool
    motivo: str
    data_inicio_cura: Optional[datetime] = None
    data_previsao_cura: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "contrato_id": self.contrato_id,
            "status": self.status.value,
            "estagio_atual": self.estagio_atual,
            "estagio_alvo": self.estagio_alvo,
            "meses_em_observacao": self.meses_em_observacao,
            "meses_necessarios": self.meses_necessarios,
            "percentual_progresso": self.percentual_progresso,
            "elegivel_cura": self.elegivel_cura,
            "motivo": self.motivo,
            "data_inicio_cura": self.data_inicio_cura.isoformat() if self.data_inicio_cura else None,
            "data_previsao_cura": self.data_previsao_cura.isoformat() if self.data_previsao_cura else None
        }


@dataclass
class CriteriosCura:
    """
    Critérios de cura por tipo de transição.
    
    Attributes:
        meses_minimos: Meses mínimos de observação
        dias_atraso_maximo: Máximo de dias de atraso permitido
        requer_amortizacao: Se requer amortização mínima
        percentual_amortizacao: Percentual mínimo de amortização
        requer_melhora_pd: Se requer melhora de PD
        percentual_melhora_pd: Percentual mínimo de melhora de PD
        permite_reestruturacao: Se permite reestruturações
    """
    meses_minimos: int
    dias_atraso_maximo: int
    requer_amortizacao: bool
    percentual_amortizacao: float
    requer_melhora_pd: bool
    percentual_melhora_pd: float
    permite_reestruturacao: bool


class SistemaCura:
    """
    Sistema de gerenciamento de cura de crédito.
    
    Implementa os critérios formais de reversão de estágio conforme
    Art. 41 da Resolução CMN 4.966/2021.
    """
    
    # Critérios de cura por transição de estágio
    CRITERIOS_CURA = {
        # Stage 2 → Stage 1
        (2, 1): CriteriosCura(
            meses_minimos=6,
            dias_atraso_maximo=30,
            requer_amortizacao=False,
            percentual_amortizacao=0.0,
            requer_melhora_pd=True,
            percentual_melhora_pd=0.10,  # PD atual < 90% do PD na migração
            permite_reestruturacao=True
        ),
        # Stage 3 → Stage 2
        (3, 2): CriteriosCura(
            meses_minimos=12,
            dias_atraso_maximo=30,
            requer_amortizacao=True,
            percentual_amortizacao=0.30,  # Mínimo 30% amortização
            requer_melhora_pd=True,
            percentual_melhora_pd=0.20,  # PD atual < 80% do PD na migração
            permite_reestruturacao=False  # Reestruturações não podem sair de Stage 3
        )
    }
    
    # Critérios especiais para reestruturações
    CRITERIOS_REESTRUTURACAO = CriteriosCura(
        meses_minimos=24,  # 24 meses para reestruturações
        dias_atraso_maximo=5,
        requer_amortizacao=True,
        percentual_amortizacao=0.50,  # 50% de amortização
        requer_melhora_pd=True,
        percentual_melhora_pd=0.30,  # PD < 70% do original
        permite_reestruturacao=False
    )
    
    def __init__(self):
        """Inicializa o sistema de cura."""
        # Histórico de estágios por contrato
        self._historico: Dict[str, List[HistoricoEstagio]] = {}
        
        # Contratos em período de cura
        self._em_cura: Dict[str, datetime] = {}
        
        # Cache de resultados de cura
        self._cache_cura: Dict[str, ResultadoCura] = {}
        
        logger.info("Sistema de Cura inicializado")
    
    def registrar_migracao(
        self,
        contrato_id: str,
        estagio_anterior: int,
        estagio_novo: int,
        motivo: MotivoMigracao,
        dias_atraso: int = 0,
        pd_atual: float = 0.0,
        data: Optional[datetime] = None
    ) -> None:
        """
        Registra uma migração de estágio no histórico.
        
        Args:
            contrato_id: ID do contrato
            estagio_anterior: Estágio antes da migração
            estagio_novo: Novo estágio
            motivo: Motivo da migração
            dias_atraso: Dias em atraso atual
            pd_atual: PD atual
            data: Data da migração (default: agora)
        """
        if data is None:
            data = datetime.now()
        
        registro = HistoricoEstagio(
            data=data,
            estagio_anterior=estagio_anterior,
            estagio_novo=estagio_novo,
            motivo=motivo,
            dias_atraso=dias_atraso,
            pd_atual=pd_atual
        )
        
        if contrato_id not in self._historico:
            self._historico[contrato_id] = []
        
        self._historico[contrato_id].append(registro)
        
        # Iniciar período de cura se migrou para estágio pior
        if estagio_novo > estagio_anterior:
            # Quando piora, reseta o período de cura
            if contrato_id in self._em_cura:
                del self._em_cura[contrato_id]
        
        # Limpar cache
        if contrato_id in self._cache_cura:
            del self._cache_cura[contrato_id]
        
        logger.debug(
            f"Migração registrada: {contrato_id} Stage {estagio_anterior} → {estagio_novo} "
            f"({motivo.value})"
        )
    
    def iniciar_periodo_cura(
        self,
        contrato_id: str,
        data_inicio: Optional[datetime] = None
    ) -> None:
        """
        Inicia o período de cura para um contrato.
        
        Args:
            contrato_id: ID do contrato
            data_inicio: Data de início (default: agora)
        """
        if data_inicio is None:
            data_inicio = datetime.now()
        
        self._em_cura[contrato_id] = data_inicio
        
        # Limpar cache
        if contrato_id in self._cache_cura:
            del self._cache_cura[contrato_id]
        
        logger.info(f"Período de cura iniciado para contrato {contrato_id}")
    
    def obter_ultimo_estagio_pior(
        self,
        contrato_id: str
    ) -> Optional[HistoricoEstagio]:
        """
        Obtém o último registro quando o contrato migrou para estágio pior.
        
        Args:
            contrato_id: ID do contrato
            
        Returns:
            HistoricoEstagio ou None se não houver histórico
        """
        if contrato_id not in self._historico:
            return None
        
        for registro in reversed(self._historico[contrato_id]):
            if registro.estagio_novo > registro.estagio_anterior:
                return registro
        
        return None
    
    def eh_reestruturacao(self, contrato_id: str) -> bool:
        """
        Verifica se o contrato é uma reestruturação.
        
        Args:
            contrato_id: ID do contrato
            
        Returns:
            True se for reestruturação
        """
        if contrato_id not in self._historico:
            return False
        
        for registro in self._historico[contrato_id]:
            if registro.motivo == MotivoMigracao.REESTRUTURACAO:
                return True
        
        return False
    
    def calcular_meses_em_observacao(
        self,
        contrato_id: str,
        data_referencia: Optional[datetime] = None
    ) -> int:
        """
        Calcula quantos meses o contrato está em observação para cura.
        
        Args:
            contrato_id: ID do contrato
            data_referencia: Data de referência (default: agora)
            
        Returns:
            Número de meses em observação
        """
        if data_referencia is None:
            data_referencia = datetime.now()
        
        if contrato_id not in self._em_cura:
            return 0
        
        data_inicio = self._em_cura[contrato_id]
        diferenca = data_referencia - data_inicio
        meses = diferenca.days // 30
        
        return max(0, meses)
    
    def avaliar_elegibilidade_cura(
        self,
        contrato_id: str,
        estagio_atual: int,
        dias_atraso: int,
        pd_atual: float,
        percentual_amortizacao: float = 0.0,
        data_referencia: Optional[datetime] = None,
        eh_reestruturacao_flag: Optional[bool] = None
    ) -> ResultadoCura:
        """
        Avalia se um contrato está elegível para cura.
        
        Args:
            contrato_id: ID do contrato
            estagio_atual: Estágio atual do contrato
            dias_atraso: Dias em atraso atual
            pd_atual: PD atual
            percentual_amortizacao: Percentual já amortizado (0-1)
            data_referencia: Data de referência
            eh_reestruturacao_flag: Override para checar reestruturação
            
        Returns:
            ResultadoCura com status e detalhes
        """
        if data_referencia is None:
            data_referencia = datetime.now()
        
        # Verificar se está em cache
        cache_key = f"{contrato_id}_{data_referencia.date()}"
        if cache_key in self._cache_cura:
            return self._cache_cura[cache_key]
        
        # Estágio 1 não tem cura (já é o melhor)
        if estagio_atual == 1:
            resultado = ResultadoCura(
                contrato_id=contrato_id,
                status=StatusCura.NAO_APLICAVEL,
                estagio_atual=1,
                estagio_alvo=1,
                meses_em_observacao=0,
                meses_necessarios=0,
                percentual_progresso=100.0,
                elegivel_cura=False,
                motivo="Já está em Stage 1"
            )
            self._cache_cura[cache_key] = resultado
            return resultado
        
        # Verificar se é reestruturação
        if eh_reestruturacao_flag is None:
            eh_reestruturacao_flag = self.eh_reestruturacao(contrato_id)
        
        # Determinar estágio alvo e critérios
        estagio_alvo = estagio_atual - 1
        transicao = (estagio_atual, estagio_alvo)
        
        if eh_reestruturacao_flag and estagio_atual == 3:
            # Reestruturações em Stage 3 têm critérios especiais
            criterios = self.CRITERIOS_REESTRUTURACAO
        elif transicao in self.CRITERIOS_CURA:
            criterios = self.CRITERIOS_CURA[transicao]
        else:
            resultado = ResultadoCura(
                contrato_id=contrato_id,
                status=StatusCura.NAO_APLICAVEL,
                estagio_atual=estagio_atual,
                estagio_alvo=estagio_alvo,
                meses_em_observacao=0,
                meses_necessarios=0,
                percentual_progresso=0.0,
                elegivel_cura=False,
                motivo=f"Transição {estagio_atual}→{estagio_alvo} não suportada"
            )
            self._cache_cura[cache_key] = resultado
            return resultado
        
        # Iniciar período de cura se não existir
        if contrato_id not in self._em_cura:
            self.iniciar_periodo_cura(contrato_id, data_referencia)
        
        # Calcular meses em observação
        meses_observacao = self.calcular_meses_em_observacao(contrato_id, data_referencia)
        
        # Verificar critérios
        problemas = []
        
        # 1. Verificar dias de atraso
        if dias_atraso > criterios.dias_atraso_maximo:
            problemas.append(
                f"Atraso de {dias_atraso} dias excede máximo de {criterios.dias_atraso_maximo}"
            )
            # Reset do período de cura
            self._em_cura[contrato_id] = data_referencia
            meses_observacao = 0
        
        # 2. Verificar amortização
        if criterios.requer_amortizacao:
            if percentual_amortizacao < criterios.percentual_amortizacao:
                problemas.append(
                    f"Amortização de {percentual_amortizacao:.0%} abaixo do "
                    f"mínimo de {criterios.percentual_amortizacao:.0%}"
                )
        
        # 3. Verificar melhora de PD
        if criterios.requer_melhora_pd:
            ultimo_pior = self.obter_ultimo_estagio_pior(contrato_id)
            if ultimo_pior:
                pd_limite = ultimo_pior.pd_atual * (1 - criterios.percentual_melhora_pd)
                if pd_atual > pd_limite:
                    problemas.append(
                        f"PD atual ({pd_atual:.2%}) acima do limite "
                        f"({pd_limite:.2%} = {criterios.percentual_melhora_pd:.0%} melhora)"
                    )
        
        # 4. Verificar meses de observação
        if meses_observacao < criterios.meses_minimos:
            problemas.append(
                f"Apenas {meses_observacao} meses em observação "
                f"(mínimo: {criterios.meses_minimos})"
            )
        
        # Determinar status
        if len(problemas) == 0:
            status = StatusCura.ELEGIVEL
            elegivel = True
            motivo = "Todos os critérios atendidos"
        elif dias_atraso > criterios.dias_atraso_maximo:
            status = StatusCura.REPROVADO
            elegivel = False
            motivo = "; ".join(problemas)
        else:
            status = StatusCura.EM_OBSERVACAO
            elegivel = False
            motivo = "; ".join(problemas)
        
        # Calcular progresso
        if criterios.meses_minimos > 0:
            progresso = min(100.0, (meses_observacao / criterios.meses_minimos) * 100)
        else:
            progresso = 100.0 if len(problemas) == 0 else 0.0
        
        # Calcular datas
        data_inicio = self._em_cura.get(contrato_id)
        data_previsao = None
        if data_inicio and meses_observacao < criterios.meses_minimos:
            meses_restantes = criterios.meses_minimos - meses_observacao
            data_previsao = data_referencia + timedelta(days=meses_restantes * 30)
        
        resultado = ResultadoCura(
            contrato_id=contrato_id,
            status=status,
            estagio_atual=estagio_atual,
            estagio_alvo=estagio_alvo,
            meses_em_observacao=meses_observacao,
            meses_necessarios=criterios.meses_minimos,
            percentual_progresso=progresso,
            elegivel_cura=elegivel,
            motivo=motivo,
            data_inicio_cura=data_inicio,
            data_previsao_cura=data_previsao
        )
        
        # Cachear resultado
        self._cache_cura[cache_key] = resultado
        
        logger.debug(
            f"Avaliação de cura {contrato_id}: {status.value} "
            f"({meses_observacao}/{criterios.meses_minimos} meses)"
        )
        
        return resultado
    
    def aplicar_cura(
        self,
        contrato_id: str,
        estagio_atual: int,
        dias_atraso: int,
        pd_atual: float,
        percentual_amortizacao: float = 0.0
    ) -> Tuple[bool, int, str]:
        """
        Tenta aplicar a cura a um contrato.
        
        Args:
            contrato_id: ID do contrato
            estagio_atual: Estágio atual
            dias_atraso: Dias em atraso
            pd_atual: PD atual
            percentual_amortizacao: Percentual amortizado
            
        Returns:
            Tuple (sucesso, novo_estagio, motivo)
        """
        resultado = self.avaliar_elegibilidade_cura(
            contrato_id=contrato_id,
            estagio_atual=estagio_atual,
            dias_atraso=dias_atraso,
            pd_atual=pd_atual,
            percentual_amortizacao=percentual_amortizacao
        )
        
        if resultado.elegivel_cura:
            novo_estagio = resultado.estagio_alvo
            
            # Registrar a cura
            self.registrar_migracao(
                contrato_id=contrato_id,
                estagio_anterior=estagio_atual,
                estagio_novo=novo_estagio,
                motivo=MotivoMigracao.CURA_APROVADA,
                dias_atraso=dias_atraso,
                pd_atual=pd_atual
            )
            
            # Remover do período de cura
            if contrato_id in self._em_cura:
                del self._em_cura[contrato_id]
            
            logger.info(
                f"Cura aplicada: {contrato_id} Stage {estagio_atual} → {novo_estagio}"
            )
            
            return True, novo_estagio, "Cura aprovada"
        else:
            return False, estagio_atual, resultado.motivo
    
    def processar_dataframe(
        self,
        df: pd.DataFrame,
        col_contrato: str = "ID_Contrato",
        col_estagio: str = "estagio",
        col_dias_atraso: str = "dias_atraso",
        col_pd: str = "pd_atual",
        col_amortizacao: str = "percentual_amortizacao",
        col_reestruturacao: str = "flag_reestruturacao",
        aplicar_cura: bool = False
    ) -> pd.DataFrame:
        """
        Processa um DataFrame avaliando cura para todos os contratos.
        
        Args:
            df: DataFrame com dados dos contratos
            col_contrato: Nome da coluna de ID do contrato
            col_estagio: Nome da coluna de estágio
            col_dias_atraso: Nome da coluna de dias em atraso
            col_pd: Nome da coluna de PD
            col_amortizacao: Nome da coluna de % amortização
            col_reestruturacao: Nome da coluna de flag reestruturação
            aplicar_cura: Se True, aplica a cura e atualiza estágio
            
        Returns:
            DataFrame com colunas adicionais de cura
        """
        logger.info(f"Processando {len(df)} contratos para avaliação de cura...")
        
        df_resultado = df.copy()
        
        # Adicionar colunas de resultado
        df_resultado["cura_status"] = StatusCura.NAO_APLICAVEL.value
        df_resultado["cura_elegivel"] = False
        df_resultado["cura_meses_observacao"] = 0
        df_resultado["cura_meses_necessarios"] = 0
        df_resultado["cura_progresso"] = 0.0
        df_resultado["cura_motivo"] = ""
        df_resultado["em_periodo_cura"] = False
        
        # Valores default para colunas opcionais
        if col_amortizacao not in df_resultado.columns:
            df_resultado[col_amortizacao] = 0.0
        if col_reestruturacao not in df_resultado.columns:
            df_resultado[col_reestruturacao] = False
        
        # Processar cada contrato
        for idx, row in df_resultado.iterrows():
            contrato_id = str(row[col_contrato])
            estagio = int(row[col_estagio])
            
            if estagio == 1:
                continue  # Stage 1 não precisa de cura
            
            dias_atraso = int(row.get(col_dias_atraso, 0))
            pd_atual = float(row.get(col_pd, 0.0))
            amortizacao = float(row.get(col_amortizacao, 0.0))
            eh_reestr = bool(row.get(col_reestruturacao, False))
            
            resultado = self.avaliar_elegibilidade_cura(
                contrato_id=contrato_id,
                estagio_atual=estagio,
                dias_atraso=dias_atraso,
                pd_atual=pd_atual,
                percentual_amortizacao=amortizacao,
                eh_reestruturacao_flag=eh_reestr
            )
            
            df_resultado.at[idx, "cura_status"] = resultado.status.value
            df_resultado.at[idx, "cura_elegivel"] = resultado.elegivel_cura
            df_resultado.at[idx, "cura_meses_observacao"] = resultado.meses_em_observacao
            df_resultado.at[idx, "cura_meses_necessarios"] = resultado.meses_necessarios
            df_resultado.at[idx, "cura_progresso"] = resultado.percentual_progresso
            df_resultado.at[idx, "cura_motivo"] = resultado.motivo
            df_resultado.at[idx, "em_periodo_cura"] = (
                resultado.status == StatusCura.EM_OBSERVACAO
            )
            
            # Aplicar cura se solicitado e elegível
            if aplicar_cura and resultado.elegivel_cura:
                sucesso, novo_estagio, _ = self.aplicar_cura(
                    contrato_id=contrato_id,
                    estagio_atual=estagio,
                    dias_atraso=dias_atraso,
                    pd_atual=pd_atual,
                    percentual_amortizacao=amortizacao
                )
                if sucesso:
                    df_resultado.at[idx, col_estagio] = novo_estagio
                    df_resultado.at[idx, "cura_status"] = StatusCura.APROVADO.value
        
        # Estatísticas
        total = len(df_resultado[df_resultado[col_estagio] > 1])
        em_observacao = (df_resultado["cura_status"] == StatusCura.EM_OBSERVACAO.value).sum()
        elegiveis = df_resultado["cura_elegivel"].sum()
        
        logger.info(
            f"Processamento concluído: {total} em Stage 2/3, "
            f"{em_observacao} em observação, {elegiveis} elegíveis"
        )
        
        return df_resultado
    
    def obter_historico(self, contrato_id: str) -> List[Dict[str, Any]]:
        """
        Obtém o histórico de estágios de um contrato.
        
        Args:
            contrato_id: ID do contrato
            
        Returns:
            Lista de registros históricos
        """
        if contrato_id not in self._historico:
            return []
        
        return [h.to_dict() for h in self._historico[contrato_id]]
    
    def limpar_cache(self) -> None:
        """Limpa o cache de resultados."""
        self._cache_cura.clear()
        logger.info("Cache de cura limpo")


# Instância global
_sistema_cura: Optional[SistemaCura] = None


def get_sistema_cura() -> SistemaCura:
    """Obtém ou cria instância global do sistema de cura."""
    global _sistema_cura
    if _sistema_cura is None:
        _sistema_cura = SistemaCura()
    return _sistema_cura


def avaliar_cura(
    contrato_id: str,
    estagio_atual: int,
    dias_atraso: int,
    pd_atual: float,
    percentual_amortizacao: float = 0.0
) -> ResultadoCura:
    """
    Função de conveniência para avaliar cura.
    
    Args:
        contrato_id: ID do contrato
        estagio_atual: Estágio atual
        dias_atraso: Dias em atraso
        pd_atual: PD atual
        percentual_amortizacao: Percentual amortizado
        
    Returns:
        ResultadoCura
    """
    sistema = get_sistema_cura()
    return sistema.avaliar_elegibilidade_cura(
        contrato_id=contrato_id,
        estagio_atual=estagio_atual,
        dias_atraso=dias_atraso,
        pd_atual=pd_atual,
        percentual_amortizacao=percentual_amortizacao
    )


if __name__ == "__main__":
    # Configurar logging para teste
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("TESTE DO SISTEMA DE CURA FORMAL")
    print("=" * 60)
    
    # Criar sistema
    sistema = SistemaCura()
    
    # Simular contratos
    contratos_teste = [
        {
            "id": "CTR001",
            "estagio": 2,
            "dias_atraso": 0,
            "pd_atual": 0.08,
            "amortizacao": 0.0,
            "reestruturacao": False,
            "meses_adimplente": 7  # Mais de 6 meses
        },
        {
            "id": "CTR002",
            "estagio": 2,
            "dias_atraso": 0,
            "pd_atual": 0.08,
            "amortizacao": 0.0,
            "reestruturacao": False,
            "meses_adimplente": 3  # Apenas 3 meses
        },
        {
            "id": "CTR003",
            "estagio": 3,
            "dias_atraso": 0,
            "pd_atual": 0.12,
            "amortizacao": 0.35,  # 35% amortizado
            "reestruturacao": False,
            "meses_adimplente": 14  # Mais de 12 meses
        },
        {
            "id": "CTR004",
            "estagio": 3,
            "dias_atraso": 45,  # Em atraso
            "pd_atual": 0.20,
            "amortizacao": 0.10,
            "reestruturacao": True,  # Reestruturação
            "meses_adimplente": 0
        }
    ]
    
    print("\n1. Registrando histórico de migrações...")
    
    # Simular histórico
    for contrato in contratos_teste:
        # Registrar migração inicial
        data_migracao = datetime.now() - timedelta(days=contrato["meses_adimplente"] * 30)
        
        sistema.registrar_migracao(
            contrato_id=contrato["id"],
            estagio_anterior=1,
            estagio_novo=contrato["estagio"],
            motivo=MotivoMigracao.REESTRUTURACAO if contrato["reestruturacao"] 
                   else MotivoMigracao.ATRASO_30_DIAS,
            dias_atraso=35,
            pd_atual=0.15,
            data=data_migracao
        )
        
        # Iniciar período de cura
        if contrato["meses_adimplente"] > 0:
            sistema.iniciar_periodo_cura(contrato["id"], data_migracao)
    
    print("\n2. Avaliando elegibilidade para cura...")
    
    for contrato in contratos_teste:
        resultado = sistema.avaliar_elegibilidade_cura(
            contrato_id=contrato["id"],
            estagio_atual=contrato["estagio"],
            dias_atraso=contrato["dias_atraso"],
            pd_atual=contrato["pd_atual"],
            percentual_amortizacao=contrato["amortizacao"]
        )
        
        print(f"\n   Contrato: {contrato['id']}")
        print(f"   - Estágio atual: {resultado.estagio_atual}")
        print(f"   - Estágio alvo: {resultado.estagio_alvo}")
        print(f"   - Status: {resultado.status.value}")
        print(f"   - Meses em observação: {resultado.meses_em_observacao}/{resultado.meses_necessarios}")
        print(f"   - Progresso: {resultado.percentual_progresso:.0f}%")
        print(f"   - Elegível: {'✅ SIM' if resultado.elegivel_cura else '❌ NÃO'}")
        print(f"   - Motivo: {resultado.motivo}")
    
    print("\n3. Processando DataFrame...")
    
    df_teste = pd.DataFrame([
        {
            "ID_Contrato": "CTR001",
            "estagio": 2,
            "dias_atraso": 0,
            "pd_atual": 0.08,
            "percentual_amortizacao": 0.0,
            "flag_reestruturacao": False
        },
        {
            "ID_Contrato": "CTR002",
            "estagio": 2,
            "dias_atraso": 0,
            "pd_atual": 0.08,
            "percentual_amortizacao": 0.0,
            "flag_reestruturacao": False
        },
        {
            "ID_Contrato": "CTR003",
            "estagio": 3,
            "dias_atraso": 0,
            "pd_atual": 0.12,
            "percentual_amortizacao": 0.35,
            "flag_reestruturacao": False
        }
    ])
    
    df_resultado = sistema.processar_dataframe(df_teste, aplicar_cura=True)
    
    print("\n   Resultado do processamento:")
    for _, row in df_resultado.iterrows():
        print(f"\n   {row['ID_Contrato']}:")
        print(f"   - Estágio: {row['estagio']}")
        print(f"   - Status cura: {row['cura_status']}")
        print(f"   - Elegível: {row['cura_elegivel']}")
        print(f"   - Em período de cura: {row['em_periodo_cura']}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
