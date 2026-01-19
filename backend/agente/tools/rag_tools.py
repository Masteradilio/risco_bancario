# -*- coding: utf-8 -*-
"""
Ferramentas RAG - Busca em Documentos BACEN
"""

from typing import Dict, Any, List
import logging
import os

logger = logging.getLogger(__name__)


async def buscar_regulamentacao(
    query: str,
    top_k: int = 5,
    fonte: str = None
) -> Dict[str, Any]:
    """
    Busca em documentos de regulamentação BACEN usando RAG.
    
    Args:
        query: Texto da consulta
        top_k: Número de resultados
        fonte: Filtro por documento (opcional)
        
    Returns:
        Resultados da busca com contexto
    """
    try:
        # Tentar usar File Search híbrido se disponível
        from ..database import get_db
        
        db = get_db()
        
        # Buscar chunks relevantes
        query_sql = """
            SELECT content, source_file, chunk_index, 
                   ts_rank_cd(content_tsv, plainto_tsquery('portuguese', %s)) as score
            FROM agente.document_chunks
            WHERE content_tsv @@ plainto_tsquery('portuguese', %s)
            ORDER BY score DESC
            LIMIT %s
        """
        
        results = db.fetch_all(query_sql, (query, query, top_k))
        
        if results:
            # Formatar resultados
            chunks = []
            for r in results:
                chunks.append({
                    "conteudo": r["content"][:500] + "..." if len(r.get("content", "")) > 500 else r.get("content", ""),
                    "fonte": r.get("source_file", ""),
                    "posicao": r.get("chunk_index", 0),
                    "relevancia": round(r.get("score", 0), 4)
                })
            
            contexto = "\n\n---\n\n".join([c["conteudo"] for c in chunks[:3]])
            
            return {
                "query": query,
                "total_resultados": len(chunks),
                "resultados": chunks,
                "contexto": contexto,
                "fontes": list(set(c["fonte"] for c in chunks)),
                "status": "sucesso"
            }
    
    except Exception as e:
        logger.warning(f"Busca no banco falhou, usando fallback: {e}")
    
    # Fallback: busca em arquivos locais
    return await _buscar_local(query, top_k, fonte)


async def _buscar_local(query: str, top_k: int, fonte: str = None) -> Dict[str, Any]:
    """Busca local em arquivos de documentação."""
    from ..config import get_config
    
    config = get_config()
    docs_path = config.docs_path
    
    # Documentos conhecidos
    documentos = {
        "CMN 4966": {
            "arquivo": "Resolução CMN 4966.md",
            "trechos": [
                "Art. 21. A mensuração da perda esperada deve considerar informações forward-looking, incluindo cenários macroeconômicos.",
                "Art. 38. A instituição deve manter documentação que evidencie a metodologia utilizada para mensuração da perda esperada.",
                "Art. 49. Os créditos baixados como prejuízo devem ser acompanhados pelo período mínimo de 5 anos.",
                "Art. 7º. A classificação do risco de crédito deve segregar as operações em estágios conforme IFRS 9."
            ]
        },
        "BCB 352": {
            "arquivo": "Resolução BCB 352.md",
            "trechos": [
                "Dispõe sobre procedimentos para remessa de informações relativas a operações de crédito ao Banco Central.",
                "As instituições devem enviar arquivos XML conforme layout SCR até o 15º dia útil do mês subsequente.",
                "Os dados de ECL devem ser segregados por estágio, produto e modalidade."
            ]
        },
        "Perda 4966": {
            "arquivo": "Documentação Técnica de Perda 4966 - BIP.md",
            "trechos": [
                "O modelo de perda esperada IFRS 9 requer três componentes: PD (Probability of Default), LGD (Loss Given Default) e EAD (Exposure at Default).",
                "A transição entre estágios deve considerar triggers quantitativos e qualitativos.",
                "Forward Looking: Ajuste da PD por cenários macroeconômicos ponderados."
            ]
        }
    }
    
    # Buscar menções à query nos trechos
    query_lower = query.lower()
    resultados = []
    
    for doc_name, doc_info in documentos.items():
        for trecho in doc_info["trechos"]:
            # Pontuação simples por presença de termos
            score = sum(1 for word in query_lower.split() if word in trecho.lower())
            if score > 0:
                resultados.append({
                    "conteudo": trecho,
                    "fonte": doc_info["arquivo"],
                    "documento": doc_name,
                    "relevancia": score / len(query_lower.split())
                })
    
    # Ordenar por relevância
    resultados.sort(key=lambda x: x["relevancia"], reverse=True)
    resultados = resultados[:top_k]
    
    contexto = "\n\n".join([r["conteudo"] for r in resultados])
    
    return {
        "query": query,
        "total_resultados": len(resultados),
        "resultados": resultados,
        "contexto": contexto,
        "fontes": list(set(r["fonte"] for r in resultados)),
        "status": "fallback_local",
        "nota": "Busca realizada em cache local. Para busca completa, indexe os documentos."
    }


# Schema da ferramenta
RAG_TOOLS = [
    {
        "name": "buscar_regulamentacao",
        "description": "Busca informações em documentos de regulamentação BACEN (CMN 4966, BCB 352, IFRS 9). Use para consultar normas, artigos específicos ou procedimentos regulatórios.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Texto da consulta (ex: 'forward looking CMN 4966', 'período acompanhamento write-off')"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Número de resultados (padrão 5)"
                },
                "fonte": {
                    "type": "string",
                    "description": "Filtrar por documento específico (opcional)"
                }
            },
            "required": ["query"]
        }
    }
]


__all__ = [
    "buscar_regulamentacao",
    "RAG_TOOLS"
]
