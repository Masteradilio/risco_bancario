# -*- coding: utf-8 -*-
"""
Ferramentas do Agente de IA
Sistema de Gestão de Risco Bancário
"""

from .prinad_tools import (
    consultar_score_prinad,
    classificar_risco_cliente,
    PRINAD_TOOLS
)
from .ecl_tools import (
    calcular_ecl_individual,
    calcular_ecl_portfolio,
    consultar_ecl_contrato,
    simular_cenario_forward_looking,
    ECL_TOOLS
)
from .rag_tools import (
    buscar_regulamentacao,
    RAG_TOOLS
)
from .bacen_tools import (
    exportar_xml_bacen,
    validar_conformidade,
    BACEN_TOOLS
)
from .utils_tools import (
    ler_arquivo_excel,
    escrever_arquivo_excel,
    ler_arquivo_pdf,
    gerar_grafico,
    pesquisar_web,
    UTILS_TOOLS
)

# Combinar todas as ferramentas
ALL_TOOLS = PRINAD_TOOLS + ECL_TOOLS + RAG_TOOLS + BACEN_TOOLS + UTILS_TOOLS


def get_all_tools():
    """Retorna schema de todas as ferramentas."""
    return ALL_TOOLS


async def execute_tool(tool_name: str, args: dict) -> dict:
    """
    Executa uma ferramenta pelo nome.
    
    Args:
        tool_name: Nome da ferramenta
        args: Argumentos da ferramenta
        
    Returns:
        Resultado da execução
    """
    # Mapeamento de ferramentas
    TOOL_FUNCTIONS = {
        # PRINAD
        "consultar_score_prinad": consultar_score_prinad,
        "classificar_risco_cliente": classificar_risco_cliente,
        
        # ECL
        "calcular_ecl_individual": calcular_ecl_individual,
        "calcular_ecl_portfolio": calcular_ecl_portfolio,
        "consultar_ecl_contrato": consultar_ecl_contrato,
        "simular_cenario_forward_looking": simular_cenario_forward_looking,
        
        # RAG
        "buscar_regulamentacao": buscar_regulamentacao,
        
        # BACEN
        "exportar_xml_bacen": exportar_xml_bacen,
        "validar_conformidade": validar_conformidade,
        
        # Utils
        "ler_arquivo_excel": ler_arquivo_excel,
        "escrever_arquivo_excel": escrever_arquivo_excel,
        "ler_arquivo_pdf": ler_arquivo_pdf,
        "gerar_grafico": gerar_grafico,
        "pesquisar_web": pesquisar_web,
    }
    
    if tool_name not in TOOL_FUNCTIONS:
        raise ValueError(f"Ferramenta não encontrada: {tool_name}")
    
    func = TOOL_FUNCTIONS[tool_name]
    
    # Executar (async ou sync)
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return await func(**args)
    else:
        return func(**args)


__all__ = [
    "get_all_tools",
    "execute_tool",
    "ALL_TOOLS"
]
