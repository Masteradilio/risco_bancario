# -*- coding: utf-8 -*-
"""
Controle de Permissões por Ferramenta
Sistema de Gestão de Risco Bancário

Mapeamento de ferramentas para roles permitidos,
seguindo princípio de Least Privilege.
"""

from enum import Enum
from typing import List, Set
import logging

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """Perfis de acesso do sistema."""
    ANALISTA = "ANALISTA"
    GESTOR = "GESTOR"
    AUDITOR = "AUDITOR"
    ADMIN = "ADMIN"


# ============================================================================
# MAPEAMENTO DE PERMISSÕES POR FERRAMENTA
# ============================================================================

TOOL_PERMISSIONS = {
    # -------------------------------------------------------------------------
    # Ferramentas de Consulta (Todas as roles)
    # -------------------------------------------------------------------------
    "consultar_score_prinad": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
    "buscar_cliente": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
    "buscar_regulamentacao": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
    "consultar_ecl_contrato": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
    "listar_grupos_homogeneos": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
    "consultar_taxa_recuperacao": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
    
    # -------------------------------------------------------------------------
    # Ferramentas de Cálculo/Simulação (Analista+)
    # -------------------------------------------------------------------------
    "calcular_ecl_individual": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.ADMIN],
    "calcular_ecl_portfolio": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.ADMIN],
    "simular_cenario_forward_looking": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.ADMIN],
    "classificar_estagio": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.ADMIN],
    "analisar_cura": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.ADMIN],
    
    # -------------------------------------------------------------------------
    # Ferramentas de Exportação/Relatório (Gestor+)
    # -------------------------------------------------------------------------
    "exportar_xml_bacen": [UserRole.GESTOR, UserRole.ADMIN],
    "aprovar_exportacao_bacen": [UserRole.GESTOR, UserRole.ADMIN],
    "gerar_relatorio_ecl": [UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
    "executar_pipeline_ecl": [UserRole.GESTOR, UserRole.ADMIN],
    
    # -------------------------------------------------------------------------
    # Ferramentas de Auditoria (Auditor+)
    # -------------------------------------------------------------------------
    "gerar_relatorio_auditoria": [UserRole.AUDITOR, UserRole.ADMIN],
    "consultar_logs_atividade": [UserRole.AUDITOR, UserRole.ADMIN],
    "exportar_evidencias_bacen": [UserRole.AUDITOR, UserRole.ADMIN],
    "validar_conformidade": [UserRole.AUDITOR, UserRole.ADMIN],
    
    # -------------------------------------------------------------------------
    # Ferramentas Administrativas (Admin only)
    # -------------------------------------------------------------------------
    "gerenciar_usuarios": [UserRole.ADMIN],
    "configurar_sistema": [UserRole.ADMIN],
    "visualizar_logs_sistema": [UserRole.ADMIN],
    
    # -------------------------------------------------------------------------
    # Ferramentas Auxiliares (Todas as roles)
    # -------------------------------------------------------------------------
    "ler_arquivo_excel": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
    "escrever_arquivo_excel": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.ADMIN],
    "ler_arquivo_pdf": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
    "gerar_grafico": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
    "pesquisar_web": [UserRole.ANALISTA, UserRole.GESTOR, UserRole.AUDITOR, UserRole.ADMIN],
}


def check_tool_permission(user_role: str, tool_name: str) -> bool:
    """
    Verifica se o usuário tem permissão para usar a ferramenta.
    
    Args:
        user_role: Role do usuário (ANALISTA, GESTOR, AUDITOR, ADMIN)
        tool_name: Nome da ferramenta
        
    Returns:
        True se tem permissão, False caso contrário
    """
    # Converter string para enum se necessário
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role.upper())
        except ValueError:
            logger.warning(f"Role inválida: {user_role}")
            return False
    
    # Verificar se a ferramenta existe
    if tool_name not in TOOL_PERMISSIONS:
        logger.warning(f"Ferramenta não mapeada: {tool_name}")
        # Por segurança, negar acesso a ferramentas não mapeadas
        return False
    
    # Verificar permissão
    allowed_roles = TOOL_PERMISSIONS[tool_name]
    has_permission = user_role in allowed_roles
    
    if not has_permission:
        logger.info(f"Acesso negado: {user_role} não pode usar {tool_name}")
    
    return has_permission


def get_allowed_tools(user_role: str) -> List[str]:
    """
    Retorna lista de ferramentas permitidas para o role.
    
    Args:
        user_role: Role do usuário
        
    Returns:
        Lista de nomes de ferramentas permitidas
    """
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role.upper())
        except ValueError:
            return []
    
    allowed = []
    for tool_name, roles in TOOL_PERMISSIONS.items():
        if user_role in roles:
            allowed.append(tool_name)
    
    return sorted(allowed)


def get_tool_roles(tool_name: str) -> List[str]:
    """
    Retorna lista de roles que podem usar a ferramenta.
    
    Args:
        tool_name: Nome da ferramenta
        
    Returns:
        Lista de roles permitidos
    """
    if tool_name not in TOOL_PERMISSIONS:
        return []
    
    return [role.value for role in TOOL_PERMISSIONS[tool_name]]


# Descrições das ferramentas para o LLM
TOOL_DESCRIPTIONS = {
    "consultar_score_prinad": "Consulta score de risco PRINAD de um cliente por CPF/CNPJ",
    "buscar_cliente": "Busca informações cadastrais de um cliente",
    "buscar_regulamentacao": "Busca em documentos de regulamentação BACEN (CMN 4966, BCB 352)",
    "consultar_ecl_contrato": "Consulta ECL calculado de um contrato específico",
    "calcular_ecl_individual": "Calcula ECL para um contrato individual",
    "calcular_ecl_portfolio": "Calcula ECL agregado do portfólio",
    "simular_cenario_forward_looking": "Simula impacto de cenário macroeconômico no ECL",
    "exportar_xml_bacen": "Gera arquivo XML para envio ao BACEN",
    "gerar_relatorio_auditoria": "Gera relatório de auditoria de operações",
    "ler_arquivo_excel": "Lê e analisa dados de arquivos Excel",
    "ler_arquivo_pdf": "Extrai texto de arquivos PDF",
    "gerar_grafico": "Gera gráficos e visualizações de dados",
    "pesquisar_web": "Realiza pesquisa na web e retorna resultados",
}


__all__ = [
    "UserRole",
    "TOOL_PERMISSIONS",
    "TOOL_DESCRIPTIONS",
    "check_tool_permission",
    "get_allowed_tools",
    "get_tool_roles"
]
