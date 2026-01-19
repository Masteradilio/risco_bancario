# -*- coding: utf-8 -*-
"""
Módulo de Relatórios de Auditoria
=================================

Gera relatórios de acessos, operações críticas e conformidade
para evidências regulatórias.

Autor: Sistema ECL
Data: Janeiro 2026
"""

import csv
import io
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TipoRelatorio(str, Enum):
    """Tipos de relatórios de auditoria disponíveis."""
    ACESSOS = "acessos"
    OPERACOES_CRITICAS = "operacoes_criticas"
    CONFORMIDADE_BACEN = "conformidade_bacen"
    ATIVIDADE_USUARIO = "atividade_usuario"


class GeradorRelatoriosAuditoria:
    """
    Gerador de relatórios de auditoria para conformidade regulatória.
    
    Fornece relatórios em CSV e JSON para evidências de auditoria.
    """
    
    def __init__(self, logs_store: List[Dict] = None, errors_store: List[Dict] = None):
        """
        Inicializa o gerador.
        
        Args:
            logs_store: Lista de logs de atividade
            errors_store: Lista de erros do sistema
        """
        self._logs = logs_store or []
        self._errors = errors_store or []
    
    def gerar_relatorio_acessos(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        formato: str = "json"
    ) -> Dict[str, Any]:
        """
        Gera relatório de acessos ao sistema por período.
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            formato: "json" ou "csv"
            
        Returns:
            Dict com dados do relatório e conteúdo
        """
        # Filtrar logs de login/logout
        acessos = [
            log for log in self._logs
            if log.get("acao") in ["LOGIN", "LOGOUT", "LOGIN_FALHA"]
            and self._dentro_periodo(log, data_inicio, data_fim)
        ]
        
        # Estatísticas
        total_logins = sum(1 for a in acessos if a.get("acao") == "LOGIN")
        total_logouts = sum(1 for a in acessos if a.get("acao") == "LOGOUT")
        total_falhas = sum(1 for a in acessos if a.get("acao") == "LOGIN_FALHA")
        
        # Agrupar por usuário
        por_usuario = {}
        for acesso in acessos:
            usuario = acesso.get("usuario_nome", "Desconhecido")
            if usuario not in por_usuario:
                por_usuario[usuario] = {"logins": 0, "logouts": 0, "falhas": 0}
            if acesso.get("acao") == "LOGIN":
                por_usuario[usuario]["logins"] += 1
            elif acesso.get("acao") == "LOGOUT":
                por_usuario[usuario]["logouts"] += 1
            elif acesso.get("acao") == "LOGIN_FALHA":
                por_usuario[usuario]["falhas"] += 1
        
        relatorio = {
            "tipo": TipoRelatorio.ACESSOS.value,
            "data_geracao": datetime.now().isoformat(),
            "periodo": {
                "inicio": data_inicio.isoformat(),
                "fim": data_fim.isoformat()
            },
            "estatisticas": {
                "total_logins": total_logins,
                "total_logouts": total_logouts,
                "total_falhas": total_falhas,
                "usuarios_ativos": len(por_usuario)
            },
            "por_usuario": por_usuario,
            "detalhes": acessos if formato == "json" else None
        }
        
        if formato == "csv":
            relatorio["csv_content"] = self._to_csv(acessos)
        
        logger.info(f"Relatório de acessos gerado: {total_logins} logins, {total_falhas} falhas")
        return relatorio
    
    def gerar_relatorio_operacoes_criticas(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        formato: str = "json"
    ) -> Dict[str, Any]:
        """
        Gera relatório de operações críticas (exportações BACEN, etc).
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            formato: "json" ou "csv"
            
        Returns:
            Dict com dados do relatório
        """
        # Ações consideradas críticas
        acoes_criticas = [
            "EXPORT_BACEN", "GENERATE_XML", "EXPORT_PDF",
            "DELETE_USER", "UPDATE_USER_ROLE", "RESET_PASSWORD",
            "EXECUTE_PIPELINE", "CALCULATE_ECL_BATCH"
        ]
        
        operacoes = [
            log for log in self._logs
            if log.get("acao") in acoes_criticas
            and self._dentro_periodo(log, data_inicio, data_fim)
        ]
        
        # Agrupar por tipo de operação
        por_tipo = {}
        for op in operacoes:
            acao = op.get("acao")
            if acao not in por_tipo:
                por_tipo[acao] = {"total": 0, "sucesso": 0, "falha": 0}
            por_tipo[acao]["total"] += 1
            if op.get("status") == "SUCESSO":
                por_tipo[acao]["sucesso"] += 1
            else:
                por_tipo[acao]["falha"] += 1
        
        relatorio = {
            "tipo": TipoRelatorio.OPERACOES_CRITICAS.value,
            "data_geracao": datetime.now().isoformat(),
            "periodo": {
                "inicio": data_inicio.isoformat(),
                "fim": data_fim.isoformat()
            },
            "total_operacoes": len(operacoes),
            "por_tipo_operacao": por_tipo,
            "detalhes": operacoes if formato == "json" else None
        }
        
        if formato == "csv":
            relatorio["csv_content"] = self._to_csv(operacoes)
        
        logger.info(f"Relatório de operações críticas gerado: {len(operacoes)} operações")
        return relatorio
    
    def gerar_relatorio_conformidade_bacen(
        self,
        data_inicio: datetime,
        data_fim: datetime
    ) -> Dict[str, Any]:
        """
        Gera relatório de conformidade para auditoria BACEN.
        
        Inclui todos os envios Doc3040, validações e operações regulatórias.
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            
        Returns:
            Dict com relatório de conformidade
        """
        # Filtrar operações relacionadas ao BACEN
        operacoes_bacen = [
            log for log in self._logs
            if any(termo in str(log.get("acao", "")).upper() 
                   for termo in ["BACEN", "XML", "DOC3040", "PIPELINE", "ECL"])
            and self._dentro_periodo(log, data_inicio, data_fim)
        ]
        
        # Separar por categoria
        envios_xml = [op for op in operacoes_bacen if "XML" in str(op.get("acao", "")).upper()]
        calculos_ecl = [op for op in operacoes_bacen if "ECL" in str(op.get("acao", "")).upper()]
        pipelines = [op for op in operacoes_bacen if "PIPELINE" in str(op.get("acao", "")).upper()]
        
        relatorio = {
            "tipo": TipoRelatorio.CONFORMIDADE_BACEN.value,
            "data_geracao": datetime.now().isoformat(),
            "periodo": {
                "inicio": data_inicio.isoformat(),
                "fim": data_fim.isoformat()
            },
            "resumo": {
                "total_operacoes_regulatorias": len(operacoes_bacen),
                "envios_xml_doc3040": len(envios_xml),
                "calculos_ecl": len(calculos_ecl),
                "execucoes_pipeline": len(pipelines)
            },
            "conformidade_status": {
                "cmn_4966": "CONFORME" if len(calculos_ecl) > 0 else "PENDENTE",
                "doc_3040": "CONFORME" if len(envios_xml) > 0 else "PENDENTE"
            },
            "detalhes_envios_xml": envios_xml,
            "detalhes_calculos_ecl": calculos_ecl[-10:] if calculos_ecl else []  # últimos 10
        }
        
        logger.info(f"Relatório de conformidade BACEN gerado: {len(operacoes_bacen)} operações")
        return relatorio
    
    def gerar_relatorio_atividade_usuario(
        self,
        usuario_id: str,
        data_inicio: datetime,
        data_fim: datetime,
        formato: str = "json"
    ) -> Dict[str, Any]:
        """
        Gera relatório de atividade de um usuário específico.
        
        Args:
            usuario_id: ID do usuário
            data_inicio: Data inicial do período
            data_fim: Data final do período
            formato: "json" ou "csv"
            
        Returns:
            Dict com relatório de atividade
        """
        atividades = [
            log for log in self._logs
            if log.get("usuario_id") == usuario_id
            and self._dentro_periodo(log, data_inicio, data_fim)
        ]
        
        # Agrupar por tipo de ação
        por_acao = {}
        for ativ in atividades:
            acao = ativ.get("acao")
            por_acao[acao] = por_acao.get(acao, 0) + 1
        
        # Encontrar info do usuário
        usuario_nome = atividades[0].get("usuario_nome") if atividades else "Desconhecido"
        
        relatorio = {
            "tipo": TipoRelatorio.ATIVIDADE_USUARIO.value,
            "data_geracao": datetime.now().isoformat(),
            "usuario": {
                "id": usuario_id,
                "nome": usuario_nome
            },
            "periodo": {
                "inicio": data_inicio.isoformat(),
                "fim": data_fim.isoformat()
            },
            "total_atividades": len(atividades),
            "por_tipo_acao": por_acao,
            "detalhes": atividades if formato == "json" else None
        }
        
        if formato == "csv":
            relatorio["csv_content"] = self._to_csv(atividades)
        
        logger.info(f"Relatório de atividade do usuário {usuario_id}: {len(atividades)} atividades")
        return relatorio
    
    def _dentro_periodo(self, log: Dict, inicio: datetime, fim: datetime) -> bool:
        """Verifica se o log está dentro do período especificado."""
        try:
            timestamp = datetime.fromisoformat(log.get("timestamp", ""))
            return inicio <= timestamp <= fim
        except (ValueError, TypeError):
            return False
    
    def _to_csv(self, dados: List[Dict]) -> str:
        """Converte lista de dicts para CSV."""
        if not dados:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=dados[0].keys())
        writer.writeheader()
        for row in dados:
            writer.writerow({k: str(v) for k, v in row.items()})
        return output.getvalue()


def exportar_relatorio_pdf(relatorio: Dict[str, Any]) -> bytes:
    """
    Exporta relatório em formato PDF.
    
    NOTA: Implementação simplificada - em produção usar reportlab ou weasyprint.
    
    Args:
        relatorio: Dict com dados do relatório
        
    Returns:
        Bytes do PDF gerado
    """
    # Placeholder - retorna JSON formatado como bytes
    # Em produção, usar biblioteca de geração de PDF
    content = json.dumps(relatorio, indent=2, ensure_ascii=False, default=str)
    return content.encode("utf-8")


# Instância global
_gerador_relatorios: Optional[GeradorRelatoriosAuditoria] = None


def get_gerador_relatorios(logs: List[Dict] = None, errors: List[Dict] = None) -> GeradorRelatoriosAuditoria:
    """Obtém ou cria instância do gerador de relatórios."""
    global _gerador_relatorios
    if _gerador_relatorios is None or logs is not None:
        _gerador_relatorios = GeradorRelatoriosAuditoria(logs, errors)
    return _gerador_relatorios


__all__ = [
    "TipoRelatorio",
    "GeradorRelatoriosAuditoria",
    "exportar_relatorio_pdf",
    "get_gerador_relatorios"
]
