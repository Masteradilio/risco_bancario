#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Logs de Auditoria Estruturados para ECL
===================================================

Implementa logging estruturado para conformidade com Art. 40, §1º da 
Resolução CMN 4.966/2021 que exige documentação verificável de todas 
as decisões de estadiamento, classificação e cálculo de ECL.

Eventos Auditáveis:
- STAGE_MIGRATION: Mudança de estágio (1→2, 2→3, cura)
- ECL_CALCULATION: Cálculo de perda esperada
- CURE_EVALUATION: Avaliação de elegibilidade para cura
- PD_ADJUSTMENT: Ajuste de PD (TTC→PIT, Forward Looking)
- LGD_CALCULATION: Cálculo de LGD
- TRIGGER_ACTIVATION: Ativação de gatilhos de estágio
- RESTRUCTURE_DETECTION: Detecção de reestruturação
- BACKTESTING_RESULT: Resultado de validação de modelo

Autor: Sistema ECL
Data: Janeiro 2025
"""

import os
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional, Dict, List, Union
from enum import Enum
import hashlib
import uuid
from pathlib import Path

# Configurar logger base
logger = logging.getLogger(__name__)


class EventoAuditoria(Enum):
    """Tipos de eventos auditáveis no sistema ECL."""
    STAGE_MIGRATION = "STAGE_MIGRATION"
    ECL_CALCULATION = "ECL_CALCULATION"
    CURE_EVALUATION = "CURE_EVALUATION"
    PD_ADJUSTMENT = "PD_ADJUSTMENT"
    LGD_CALCULATION = "LGD_CALCULATION"
    EAD_CALCULATION = "EAD_CALCULATION"
    TRIGGER_ACTIVATION = "TRIGGER_ACTIVATION"
    RESTRUCTURE_DETECTION = "RESTRUCTURE_DETECTION"
    BACKTESTING_RESULT = "BACKTESTING_RESULT"
    PISO_REGULAMENTAR = "PISO_REGULAMENTAR"
    FORWARD_LOOKING = "FORWARD_LOOKING"
    WOE_CALCULATION = "WOE_CALCULATION"
    GRUPO_HOMOGENEO = "GRUPO_HOMOGENEO"
    WRITE_OFF = "WRITE_OFF"
    MODEL_VERSION_CHANGE = "MODEL_VERSION_CHANGE"
    DATA_LOAD = "DATA_LOAD"
    PIPELINE_START = "PIPELINE_START"
    PIPELINE_END = "PIPELINE_END"


@dataclass
class AuditLog:
    """
    Registro estruturado de auditoria para eventos ECL.
    
    Conforme Art. 40, §1º da Resolução CMN 4.966/2021, todos os 
    eventos relevantes devem ser documentados de forma verificável.
    
    Attributes:
        timestamp: Data/hora do evento
        evento: Tipo de evento (EventoAuditoria)
        cliente_id: Identificador do cliente/contrato
        de_valor: Valor anterior (antes da mudança)
        para_valor: Valor novo (depois da mudança)
        justificativa: Razão técnica/regulatória para a decisão
        modelo_versao: Versão do modelo utilizado
        usuario: Usuário/sistema que executou
        trace_id: ID único para rastreamento
        metadata: Informações adicionais
    """
    timestamp: datetime
    evento: str
    cliente_id: str
    de_valor: Any
    para_valor: Any
    justificativa: str
    modelo_versao: str = "1.0.0"
    usuario: str = "SISTEMA_ECL"
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        # Converter valores complexos para string
        if not isinstance(data['de_valor'], (str, int, float, bool, type(None))):
            data['de_valor'] = str(data['de_valor'])
        if not isinstance(data['para_valor'], (str, int, float, bool, type(None))):
            data['para_valor'] = str(data['para_valor'])
        return data
    
    def to_json(self) -> str:
        """Serializa para JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def get_hash(self) -> str:
        """Gera hash único para verificação de integridade."""
        content = f"{self.timestamp.isoformat()}|{self.evento}|{self.cliente_id}|{self.de_valor}|{self.para_valor}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class AuditLogger:
    """
    Sistema de logging de auditoria para ECL.
    
    Implementa:
    - Logs estruturados em JSON
    - Armazenamento em arquivo com rotação
    - Índice de busca rápida
    - Verificação de integridade
    """
    
    # Versão atual do sistema de auditoria
    AUDIT_VERSION = "1.0.0"
    
    def __init__(self, 
                 log_dir: Optional[str] = None,
                 modelo_versao: str = "1.0.0",
                 max_file_size_mb: int = 10,
                 retention_days: int = 365):
        """
        Inicializa o sistema de auditoria.
        
        Args:
            log_dir: Diretório para salvar logs
            modelo_versao: Versão do modelo ECL
            max_file_size_mb: Tamanho máximo do arquivo antes de rotação
            retention_days: Dias de retenção dos logs
        """
        self.modelo_versao = modelo_versao
        self.max_file_size_mb = max_file_size_mb
        self.retention_days = retention_days
        
        # Definir diretório de logs
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            # Usar diretório padrão
            base_dir = Path(__file__).parent.parent
            self.log_dir = base_dir / "logs" / "audit"
        
        # Criar diretório se não existir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Buffer de logs em memória
        self._buffer: List[AuditLog] = []
        self._buffer_size = 100  # Flush a cada 100 registros
        
        # Arquivo de log atual
        self._current_file = self._get_log_filename()
        
        # Sessão atual
        self._session_id = str(uuid.uuid4())[:8]
        self._session_start = datetime.now()
        
        logger.info(f"AuditLogger inicializado - Session: {self._session_id}")
    
    def _get_log_filename(self) -> Path:
        """Gera nome do arquivo de log baseado na data."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"ecl_audit_{today}.jsonl"
    
    def _should_rotate(self) -> bool:
        """Verifica se deve rotacionar o arquivo."""
        if not self._current_file.exists():
            return False
        size_mb = self._current_file.stat().st_size / (1024 * 1024)
        return size_mb >= self.max_file_size_mb
    
    def _rotate_if_needed(self):
        """Rotaciona arquivo se necessário."""
        if self._should_rotate():
            timestamp = datetime.now().strftime("%H%M%S")
            rotated_name = self._current_file.with_suffix(f".{timestamp}.jsonl")
            self._current_file.rename(rotated_name)
            logger.info(f"Log rotacionado: {rotated_name}")
    
    def log(self,
            evento: Union[EventoAuditoria, str],
            cliente_id: str,
            de_valor: Any,
            para_valor: Any,
            justificativa: str,
            metadata: Optional[Dict[str, Any]] = None) -> AuditLog:
        """
        Registra um evento de auditoria.
        
        Args:
            evento: Tipo de evento
            cliente_id: ID do cliente/contrato
            de_valor: Valor anterior
            para_valor: Valor novo
            justificativa: Razão da mudança
            metadata: Dados adicionais
            
        Returns:
            AuditLog criado
        """
        # Converter enum para string se necessário
        if isinstance(evento, EventoAuditoria):
            evento = evento.value
        
        # Criar registro
        audit_log = AuditLog(
            timestamp=datetime.now(),
            evento=evento,
            cliente_id=str(cliente_id),
            de_valor=de_valor,
            para_valor=para_valor,
            justificativa=justificativa,
            modelo_versao=self.modelo_versao,
            metadata=metadata or {}
        )
        
        # Adicionar ao buffer
        self._buffer.append(audit_log)
        
        # Flush se buffer cheio
        if len(self._buffer) >= self._buffer_size:
            self.flush()
        
        return audit_log
    
    def log_stage_migration(self,
                            cliente_id: str,
                            estagio_anterior: int,
                            estagio_novo: int,
                            motivo: str,
                            dias_atraso: Optional[int] = None,
                            pd_variacao: Optional[float] = None) -> AuditLog:
        """
        Registra migração de estágio.
        
        Args:
            cliente_id: ID do contrato
            estagio_anterior: Estágio antes (1, 2, 3)
            estagio_novo: Estágio depois (1, 2, 3)
            motivo: ATRASO_90D, PD_INCREASE, CURE, TRIGGER, etc.
            dias_atraso: Dias de atraso atuais
            pd_variacao: Variação de PD se aplicável
        """
        direcao = "DOWNGRADE" if estagio_novo > estagio_anterior else "UPGRADE"
        
        return self.log(
            evento=EventoAuditoria.STAGE_MIGRATION,
            cliente_id=cliente_id,
            de_valor=f"Estágio {estagio_anterior}",
            para_valor=f"Estágio {estagio_novo}",
            justificativa=f"{direcao}: {motivo}",
            metadata={
                "estagio_anterior": estagio_anterior,
                "estagio_novo": estagio_novo,
                "direcao": direcao,
                "motivo_detalhado": motivo,
                "dias_atraso": dias_atraso,
                "pd_variacao_pct": pd_variacao
            }
        )
    
    def log_ecl_calculation(self,
                            cliente_id: str,
                            pd: float,
                            lgd: float,
                            ead: float,
                            ecl: float,
                            estagio: int,
                            produto: Optional[str] = None) -> AuditLog:
        """
        Registra cálculo de ECL.
        
        Args:
            cliente_id: ID do contrato
            pd: Probability of Default
            lgd: Loss Given Default
            ead: Exposure at Default
            ecl: Expected Credit Loss calculado
            estagio: Estágio IFRS 9
            produto: Tipo de produto
        """
        return self.log(
            evento=EventoAuditoria.ECL_CALCULATION,
            cliente_id=cliente_id,
            de_valor=f"PD={pd:.4f}, LGD={lgd:.4f}, EAD={ead:.2f}",
            para_valor=f"ECL={ecl:.2f}",
            justificativa=f"Cálculo ECL Estágio {estagio}: PD×LGD×EAD",
            metadata={
                "pd": pd,
                "lgd": lgd,
                "ead": ead,
                "ecl": ecl,
                "estagio": estagio,
                "produto": produto,
                "formula": "ECL = PD × LGD × EAD"
            }
        )
    
    def log_cure_evaluation(self,
                            cliente_id: str,
                            elegivel: bool,
                            meses_em_dia: int,
                            periodo_necessario: int,
                            modalidade: str) -> AuditLog:
        """
        Registra avaliação de cura.
        
        Args:
            cliente_id: ID do contrato
            elegivel: Se é elegível para cura
            meses_em_dia: Meses consecutivos em dia
            periodo_necessario: Período necessário para cura
            modalidade: Modalidade do crédito
        """
        resultado = "ELEGÍVEL" if elegivel else "NÃO ELEGÍVEL"
        
        return self.log(
            evento=EventoAuditoria.CURE_EVALUATION,
            cliente_id=cliente_id,
            de_valor=f"{meses_em_dia} meses em dia",
            para_valor=resultado,
            justificativa=f"Cura {modalidade}: necessário {periodo_necessario} meses",
            metadata={
                "elegivel": elegivel,
                "meses_em_dia": meses_em_dia,
                "periodo_necessario": periodo_necessario,
                "modalidade": modalidade,
                "faltam_meses": max(0, periodo_necessario - meses_em_dia)
            }
        )
    
    def log_pd_adjustment(self,
                          cliente_id: str,
                          pd_original: float,
                          pd_ajustado: float,
                          tipo_ajuste: str,
                          fator_macro: Optional[float] = None) -> AuditLog:
        """
        Registra ajuste de PD.
        
        Args:
            cliente_id: ID do contrato
            pd_original: PD antes do ajuste
            pd_ajustado: PD após ajuste
            tipo_ajuste: TTC_TO_PIT, FORWARD_LOOKING, WOE, etc.
            fator_macro: Fator macroeconômico se aplicável
        """
        variacao = ((pd_ajustado - pd_original) / pd_original * 100) if pd_original > 0 else 0
        
        return self.log(
            evento=EventoAuditoria.PD_ADJUSTMENT,
            cliente_id=cliente_id,
            de_valor=f"PD={pd_original:.4f}",
            para_valor=f"PD={pd_ajustado:.4f}",
            justificativa=f"Ajuste {tipo_ajuste}: {variacao:+.1f}%",
            metadata={
                "pd_original": pd_original,
                "pd_ajustado": pd_ajustado,
                "tipo_ajuste": tipo_ajuste,
                "variacao_percentual": variacao,
                "fator_macro": fator_macro
            }
        )
    
    def log_trigger_activation(self,
                               cliente_id: str,
                               trigger_tipo: str,
                               trigger_valor: Any,
                               acao_tomada: str) -> AuditLog:
        """
        Registra ativação de gatilho.
        
        Args:
            cliente_id: ID do contrato
            trigger_tipo: Tipo do gatilho
            trigger_valor: Valor que ativou
            acao_tomada: Ação resultante
        """
        return self.log(
            evento=EventoAuditoria.TRIGGER_ACTIVATION,
            cliente_id=cliente_id,
            de_valor=f"Trigger: {trigger_tipo}",
            para_valor=acao_tomada,
            justificativa=f"Gatilho ativado: {trigger_tipo}={trigger_valor}",
            metadata={
                "trigger_tipo": trigger_tipo,
                "trigger_valor": trigger_valor,
                "acao": acao_tomada
            }
        )
    
    def log_piso_regulamentar(self,
                              cliente_id: str,
                              ecl_original: float,
                              ecl_com_piso: float,
                              piso_aplicado: float,
                              carteira: str,
                              dias_atraso: int) -> AuditLog:
        """
        Registra aplicação de piso regulamentar.
        
        Args:
            cliente_id: ID do contrato
            ecl_original: ECL antes do piso
            ecl_com_piso: ECL após aplicar piso
            piso_aplicado: Valor do piso
            carteira: Carteira regulatória (C1-C5)
            dias_atraso: Dias de atraso
        """
        aplicou = ecl_com_piso > ecl_original
        
        return self.log(
            evento=EventoAuditoria.PISO_REGULAMENTAR,
            cliente_id=cliente_id,
            de_valor=f"ECL={ecl_original:.2f}",
            para_valor=f"ECL={ecl_com_piso:.2f}" + (" (PISO)" if aplicou else ""),
            justificativa=f"Piso BCB 352: {carteira}, atraso {dias_atraso}d, piso={piso_aplicado*100:.1f}%",
            metadata={
                "ecl_original": ecl_original,
                "ecl_com_piso": ecl_com_piso,
                "piso_percentual": piso_aplicado,
                "carteira": carteira,
                "dias_atraso": dias_atraso,
                "piso_aplicado": aplicou
            }
        )
    
    def log_pipeline(self,
                     evento_tipo: str,
                     total_contratos: int,
                     ecl_total: Optional[float] = None,
                     duracao_segundos: Optional[float] = None) -> AuditLog:
        """
        Registra eventos de pipeline.
        
        Args:
            evento_tipo: START ou END
            total_contratos: Total de contratos processados
            ecl_total: ECL total calculado (apenas para END)
            duracao_segundos: Duração do processamento
        """
        evento = EventoAuditoria.PIPELINE_START if evento_tipo == "START" else EventoAuditoria.PIPELINE_END
        
        return self.log(
            evento=evento,
            cliente_id="PIPELINE",
            de_valor=f"Contratos: {total_contratos:,}",
            para_valor=f"ECL Total: R$ {ecl_total:,.2f}" if ecl_total else "Iniciado",
            justificativa=f"Pipeline ECL {evento_tipo}",
            metadata={
                "total_contratos": total_contratos,
                "ecl_total": ecl_total,
                "duracao_segundos": duracao_segundos,
                "session_id": self._session_id
            }
        )
    
    def flush(self):
        """Escreve buffer em disco."""
        if not self._buffer:
            return
        
        self._rotate_if_needed()
        self._current_file = self._get_log_filename()
        
        with open(self._current_file, 'a', encoding='utf-8') as f:
            for log in self._buffer:
                f.write(log.to_json().replace('\n', ' ') + '\n')
        
        logger.debug(f"Flush: {len(self._buffer)} registros escritos")
        self._buffer.clear()
    
    def get_session_logs(self) -> List[AuditLog]:
        """Retorna todos os logs da sessão atual."""
        return list(self._buffer)
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo estatístico da sessão."""
        events_count = {}
        for log in self._buffer:
            events_count[log.evento] = events_count.get(log.evento, 0) + 1
        
        return {
            "session_id": self._session_id,
            "session_start": self._session_start.isoformat(),
            "total_events": len(self._buffer),
            "events_by_type": events_count,
            "log_file": str(self._current_file)
        }
    
    def __enter__(self):
        """Suporte a context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Flush ao sair do context."""
        self.flush()


# =============================================================================
# INSTÂNCIA GLOBAL
# =============================================================================

# Singleton para uso global
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(reinit: bool = False, **kwargs) -> AuditLogger:
    """
    Obtém instância global do AuditLogger.
    
    Args:
        reinit: Se True, reinicializa o logger
        **kwargs: Argumentos para inicialização
        
    Returns:
        Instância do AuditLogger
    """
    global _audit_logger
    
    if _audit_logger is None or reinit:
        _audit_logger = AuditLogger(**kwargs)
    
    return _audit_logger


# =============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# =============================================================================

def audit_stage_migration(cliente_id: str, de: int, para: int, motivo: str, **kwargs) -> AuditLog:
    """Atalho para log de migração de estágio."""
    return get_audit_logger().log_stage_migration(cliente_id, de, para, motivo, **kwargs)


def audit_ecl(cliente_id: str, pd: float, lgd: float, ead: float, ecl: float, estagio: int, **kwargs) -> AuditLog:
    """Atalho para log de cálculo ECL."""
    return get_audit_logger().log_ecl_calculation(cliente_id, pd, lgd, ead, ecl, estagio, **kwargs)


def audit_cure(cliente_id: str, elegivel: bool, meses: int, necessario: int, modalidade: str) -> AuditLog:
    """Atalho para log de avaliação de cura."""
    return get_audit_logger().log_cure_evaluation(cliente_id, elegivel, meses, necessario, modalidade)


def audit_pd_adjust(cliente_id: str, pd_antes: float, pd_depois: float, tipo: str, **kwargs) -> AuditLog:
    """Atalho para log de ajuste de PD."""
    return get_audit_logger().log_pd_adjustment(cliente_id, pd_antes, pd_depois, tipo, **kwargs)


def audit_flush():
    """Força escrita dos logs em disco."""
    get_audit_logger().flush()


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("SISTEMA DE LOGS DE AUDITORIA ECL")
    print("=" * 60)
    
    # Criar logger
    with AuditLogger(modelo_versao="1.0.0-POC") as audit:
        
        # Log de início de pipeline
        audit.log_pipeline("START", total_contratos=1000)
        
        # Simular processamento de alguns contratos
        for i in range(5):
            cliente = f"CONT_{i:06d}"
            
            # Log de cálculo ECL
            audit.log_ecl_calculation(
                cliente_id=cliente,
                pd=0.05 + i*0.01,
                lgd=0.45,
                ead=10000 + i*1000,
                ecl=(0.05 + i*0.01) * 0.45 * (10000 + i*1000),
                estagio=1 if i < 3 else 2,
                produto="Consignado"
            )
            
            # Log de migração de estágio (apenas alguns)
            if i == 3:
                audit.log_stage_migration(
                    cliente_id=cliente,
                    estagio_anterior=1,
                    estagio_novo=2,
                    motivo="PD_INCREASE_50PCT",
                    pd_variacao=0.52
                )
            
            # Log de avaliação de cura
            if i == 4:
                audit.log_cure_evaluation(
                    cliente_id=cliente,
                    elegivel=True,
                    meses_em_dia=6,
                    periodo_necessario=5,
                    modalidade="parcelado"
                )
        
        # Log de piso regulamentar
        audit.log_piso_regulamentar(
            cliente_id="CONT_000003",
            ecl_original=200.0,
            ecl_com_piso=350.0,
            piso_aplicado=0.03,
            carteira="C1",
            dias_atraso=45
        )
        
        # Log de fim de pipeline
        audit.log_pipeline("END", total_contratos=1000, ecl_total=50000.0, duracao_segundos=2.5)
        
        # Mostrar resumo
        summary = audit.get_summary()
        print(f"\nResumo da Sessão: {summary['session_id']}")
        print(f"Total de eventos: {summary['total_events']}")
        print(f"Eventos por tipo:")
        for tipo, count in summary['events_by_type'].items():
            print(f"  - {tipo}: {count}")
        print(f"\nArquivo de log: {summary['log_file']}")
    
    print("\n✅ Logs de auditoria salvos com sucesso!")
