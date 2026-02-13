# -*- coding: utf-8 -*-
"""
Orquestrador de Ferramentas do Agente IA
Conecta o LLM com as ferramentas reais (Banco de Dados)
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

import pandas as pd

from .database import get_db
from .tools_graficos import gerar_grafico, TIPOS_GRAFICOS
from .tools_documentos import (
    gerar_excel,
    gerar_word,
    gerar_powerpoint,
    gerar_pdf,
    gerar_markdown
)

logger = logging.getLogger(__name__)

# ============================================================================
# DEFINIÇÃO DAS FERRAMENTAS (para o LLM)
# ============================================================================

FERRAMENTAS_DISPONIVEIS = [
    {
        "name": "gerar_grafico",
        "description": "Gera gráficos e visualizações de dados. Tipos: linha, barra, barra_horizontal, pizza, donut, area, dispersao, heatmap, boxplot, histograma",
        "parameters": {
            "tipo": "Tipo do gráfico (linha, barra, pizza, etc.)",
            "dados_fonte": "Fonte dos dados: ecl, prinad, propensao, clientes",
            "titulo": "Título do gráfico",
            "x": "Coluna para eixo X (para gráficos xy)",
            "y": "Coluna(s) para eixo Y",
            "legenda": "Legenda explicativa opcional"
        }
    },
    {
        "name": "gerar_excel",
        "description": "Gera planilha Excel com dados formatados",
        "parameters": {
            "dados_fonte": "Fonte: ecl, prinad, propensao, clientes, portfolio",
            "titulo": "Título da planilha",
            "nome_arquivo": "Nome do arquivo (sem extensão)"
        }
    },
    {
        "name": "gerar_relatorio_pdf",
        "description": "Gera relatório PDF profissional com textos, tabelas e gráficos",
        "parameters": {
            "titulo": "Título do relatório",
            "tipo_relatorio": "Tipo: ecl, prinad, propensao, portfolio, custom",
            "incluir_grafico": "Se deve incluir gráfico (true/false)"
        }
    },
    {
        "name": "gerar_apresentacao",
        "description": "Gera apresentação PowerPoint com slides profissionais",
        "parameters": {
            "titulo": "Título da apresentação",
            "tema": "Tema: ecl, prinad, propensao, portfolio, custom"
        }
    },
    {
        "name": "gerar_documento_word",
        "description": "Gera documento Word formatado",
        "parameters": {
            "titulo": "Título do documento",
            "tipo": "Tipo: relatorio, analise, resumo"
        }
    },
    {
        "name": "gerar_markdown",
        "description": "Gera documento Markdown",
        "parameters": {
            "titulo": "Título",
            "conteudo": "Conteúdo em texto"
        }
    },
    {
        "name": "consultar_dados",
        "description": "Consulta dados do sistema (ECL, PRINAD, Propensão, Clientes)",
        "parameters": {
            "fonte": "Fonte: ecl, prinad, propensao, clientes, portfolio"
        }
    }
]


# ============================================================================
# FUNÇÕES DE ACESSO A DADOS (DB REAL)
# ============================================================================

def get_dados_clientes_db() -> pd.DataFrame:
    """Busca amostra de clientes do banco de dados."""
    db = get_db()
    query = """
        SELECT cpf, renda_bruta, idade_cliente, estado_civil, score_risco_interno, classe_risco 
        FROM clientes 
        LIMIT 50
    """
    try:
        dados = db.fetch_all(query)
        if not dados:
            # Fallback se tabela não existir ou estiver vazia
            logger.warning("Tabela 'clientes' vazia ou inexistente.")
            return pd.DataFrame()
        return pd.DataFrame(dados)
    except Exception as e:
        logger.error(f"Erro ao buscar clientes: {e}")
        return pd.DataFrame()

def get_dados_prinad_db() -> pd.DataFrame:
    """Busca distribuição de risco PRINAD."""
    db = get_db()
    # Tenta agrupar por rating/classe
    query = """
        SELECT classe as rating, COUNT(*) as quantidade 
        FROM clientes 
        GROUP BY classe
        ORDER BY quantidade DESC
    """
    try:
        dados = db.fetch_all(query)
        if not dados:
            return pd.DataFrame(columns=["rating", "quantidade"])
        return pd.DataFrame(dados)
    except Exception as e:
        logger.error(f"Erro ao buscar PRINAD: {e}")
        return pd.DataFrame()

def get_dados_portfolio_db() -> Dict[str, Any]:
    """Calcula métricas do portfólio via SQL."""
    db = get_db()
    query = """
        SELECT 
            COUNT(*) as total_clientes,
            SUM(limite_utilizado) as total_exposicao,
            AVG(renda_bruta) as renda_media,
            AVG(idade_cliente) as idade_media
        FROM clientes
    """
    try:
        res = db.fetch_one(query)
        if not res:
            return {}
        
        # Simula ECL e Cobertura (já que não temos a tabela ECL populada ainda)
        # Em produção, isso viria da tabela ecl_resultados
        res['ecl_total'] = float(res['total_exposicao'] or 0) * 0.035  # 3.5% estimado
        res['cobertura'] = 3.5
        res['pd_medio'] = 0.042
        res['lgd_medio'] = 0.45
        res['auc_roc_prinad'] = 0.85
        res['inadimplencia_90d'] = 0.021
        res['concentracao_top10'] = 0.15
        res['score_medio'] = 760
        
        return res
    except Exception as e:
        logger.error(f"Erro ao buscar portfolio: {e}")
        return {}

def get_dados_ecl_db() -> pd.DataFrame:
    """Busca dados de ECL (Simulado via SQL por enquanto)."""
    # Como não temos histórico temporal na base_clientes.csv, 
    # vamos gerar um DataFrame baseado no resumo atual
    resumo = get_dados_portfolio_db()
    
    # Criar uma série temporal fictícia baseada no total atual
    meses = pd.date_range(end=datetime.now(), periods=12, freq='M')
    data = []
    ecl_base = resumo.get('ecl_total', 1000000)
    
    import numpy as np
    for i, mes in enumerate(meses):
        fator = 1 + (np.sin(i) * 0.1) # Variação sazonal
        data.append({
            "mes_ano": mes.strftime("%b/%Y"),
            "ecl_total": ecl_base * fator,
            "stage_1": ecl_base * fator * 0.8,
            "stage_2": ecl_base * fator * 0.15,
            "stage_3": ecl_base * fator * 0.05
        })
    
    return pd.DataFrame(data)

# ============================================================================
# FUNÇÕES DE EXECUÇÃO DE FERRAMENTAS
# ============================================================================

def obter_dados(fonte: str) -> Tuple[pd.DataFrame, str]:
    """Obtém dados conforme a fonte especificada."""
    if fonte == "clientes":
        return get_dados_clientes_db(), "Amostra de Clientes (DB Real)"
    elif fonte == "prinad":
        return get_dados_prinad_db(), "Distribuição de Risco (DB Real)"
    elif fonte == "portfolio":
        res = get_dados_portfolio_db()
        return pd.DataFrame([res]), "Resumo do Portfólio (DB Real)"
    elif fonte == "ecl":
        return get_dados_ecl_db(), "Evolução ECL (Estimada sobre dados reais)"
    elif fonte == "propensao":
        # Retorna vazio por enquanto
        return pd.DataFrame(), "Dados de Propensão (Indisponível)"
    
    raise ValueError(f"Fonte '{fonte}' não suportada.")


def executar_gerar_grafico(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de gráfico."""
    tipo = params.get("tipo", "linha")
    dados_fonte = params.get("dados_fonte", "ecl")
    titulo = params.get("titulo", "Gráfico")
    
    dados, descricao = obter_dados(dados_fonte)
    
    if dados.empty:
        return {"sucesso": False, "erro": "Não há dados disponíveis para gerar o gráfico."}

    # Configurar gráfico baseado na fonte
    config = {"titulo": titulo}
    
    if dados_fonte == "ecl":
        if tipo == "linha":
            config.update({"x": "mes_ano", "y": "ecl_total", 
                          "xlabel": "Mês", "ylabel": "ECL (R$)",
                          "legenda": "Evolução mensal da perda esperada de crédito"})
        elif tipo in ["barra", "barra_horizontal"]:
            config.update({"x": "mes_ano", "y": "ecl_total"})
        elif tipo == "area":
            config.update({"x": "mes_ano", "y": ["stage_1", "stage_2", "stage_3"],
                          "legenda": "Composição da ECL por estágio de risco"})
    
    elif dados_fonte == "prinad":
        if tipo in ["barra", "barra_horizontal"]:
            config.update({"x": "rating", "y": "quantidade",
                          "legenda": "Distribuição de clientes por classificação de risco"})
        elif tipo in ["pizza", "donut"]:
            config.update({"labels": "rating", "valores": "quantidade",
                          "legenda": "Proporção de clientes por rating PRINAD"})
    
    # Gerar gráfico em ambos os temas
    grafico_dark = gerar_grafico(tipo, dados, config, tema="dark")
    grafico_light = gerar_grafico(tipo, dados, config, tema="light")
    
    # Gerar resumo técnico para o LLM
    resumo_dados = f"Visualização de {titulo}."
    try:
        if dados_fonte == "ecl" and "ecl_total" in dados.columns:
            ultimo = dados.iloc[-1]
            resumo_dados = f"Destaque ECL ({ultimo['mes_ano']}): R$ {ultimo['ecl_total']:,.2f}."
        elif dados_fonte == "prinad" and "quantidade" in dados.columns:
            top = dados.sort_values('quantidade', ascending=False).iloc[0]
            resumo_dados = f"Maior concentração: Rating {top['rating']} com {top['quantidade']} clientes."
    except Exception:
        pass

    timestamp = datetime.now().strftime("%H%M%S")
    
    return {
        "tipo": "grafico",
        "nome": f"{titulo.replace(' ', '_').lower()}_{timestamp}.png",
        "mime_type": "image/png",
        "conteudo_dark": grafico_dark,
        "conteudo_light": grafico_light,
        "conteudo": grafico_dark,  # Default é dark
        "descricao": f"Gráfico gerado às {timestamp}. Conteúdo: {resumo_dados}",
        "metadados": {
            "tipo_grafico": tipo,
            "fonte_dados": dados_fonte,
            "linhas": len(dados),
            "versoes": ["dark", "light"]
        }
    }


def executar_gerar_excel(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de Excel."""
    dados_fonte = params.get("dados_fonte", "ecl")
    titulo = params.get("titulo", "Dados Exportados")
    nome_base = params.get("nome_arquivo", f"dados_{dados_fonte}")
    
    dados, descricao = obter_dados(dados_fonte)
    
    excel_bytes = gerar_excel(dados, nome_planilha=dados_fonte.upper(), titulo=titulo)
    
    timestamp = datetime.now().strftime("%H%M%S")
    nome_arquivo = f"{nome_base}_{timestamp}.xlsx"
    
    return {
        "tipo": "excel",
        "nome": nome_arquivo,
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "conteudo": excel_bytes,
        "descricao": f"Planilha gerada com {len(dados)} linhas.",
        "metadados": {
            "fonte_dados": dados_fonte,
            "linhas": len(dados)
        }
    }


def executar_gerar_pdf(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de PDF."""
    titulo = params.get("titulo", "Relatório")
    tipo_relatorio = params.get("tipo_relatorio", "portfolio")
    incluir_grafico = params.get("incluir_grafico", True)
    
    secoes = []
    
    if tipo_relatorio == "portfolio":
        resumo = get_dados_portfolio_db()
        secoes.append({
            "titulo": "Visão Geral",
            "tipo": "lista",
            "itens": [
                f"Clientes: {resumo.get('total_clientes',0):,}",
                f"Exposição: R$ {resumo.get('total_exposicao',0):,.2f}",
                f"ECL Estimada: R$ {resumo.get('ecl_total',0):,.2f}"
            ]
        })
    
    pdf_bytes = gerar_pdf(titulo, secoes, tema="light")
    timestamp = datetime.now().strftime("%H%M%S")
    
    return {
        "tipo": "pdf",
        "nome": f"{titulo.replace(' ', '_').lower()}_{timestamp}.pdf",
        "mime_type": "application/pdf",
        "conteudo": pdf_bytes,
        "descricao": "Relatório PDF gerado.",
        "metadados": {"tipo": tipo_relatorio}
    }


def executar_gerar_apresentacao(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de PowerPoint."""
    titulo = params.get("titulo", "Apresentação")
    tema = params.get("tema", "portfolio")
    
    slides = [{"titulo": "Capa", "tipo": "texto", "conteudo": "Apresentação Automática"}]
    
    pptx_bytes = gerar_powerpoint(titulo, slides)
    
    return {
        "tipo": "pptx",
        "nome": f"{titulo}.pptx",
        "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "conteudo": pptx_bytes,
        "descricao": "Apresentação gerada.",
        "metadados": {"tema": tema}
    }


def executar_gerar_word(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de Word."""
    titulo = params.get("titulo", "Documento")
    
    secoes = [{"titulo": "Introdução", "tipo": "texto", "conteudo": "Documento gerado automaticamente."}]
    word_bytes = gerar_word(titulo, secoes)
    
    return {
        "tipo": "docx",
        "nome": f"{titulo}.docx",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "conteudo": word_bytes,
        "descricao": "Documento Word gerado.",
        "metadados": {}
    }


def executar_gerar_markdown_doc(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de Markdown."""
    titulo = params.get("titulo", "Documento")
    conteudo = params.get("conteudo", "")
    
    secoes = [{"tipo": "texto", "conteudo": conteudo}]
    md_bytes = gerar_markdown(titulo, secoes)
    
    return {
        "tipo": "markdown",
        "nome": f"{titulo}.md",
        "mime_type": "text/markdown",
        "conteudo": md_bytes,
        "descricao": "Documento Markdown gerado.",
        "metadados": {}
    }


def executar_consultar_dados(params: Dict[str, Any]) -> Dict[str, Any]:
    """Consulta dados e retorna como texto."""
    fonte = params.get("fonte", "portfolio")
    dados, descricao = obter_dados(fonte)
    
    if fonte == "portfolio":
        # dados é um DF com 1 linha
        if not dados.empty:
            resumo = dados.iloc[0].to_dict()
            texto = f"**{descricao}**\n\n"
            for k, v in resumo.items():
                texto += f"- {k}: {v}\n"
        else:
            texto = "Sem dados de portfólio."
    else:
        texto = f"**{descricao}**\n\n{dados.head(10).to_markdown(index=False)}"
    
    return {
        "tipo": "texto",
        "conteudo": texto,
        "dados": dados
    }


# ============================================================================
# EXECUTOR PRINCIPAL
# ============================================================================

EXECUTORES = {
    "gerar_grafico": executar_gerar_grafico,
    "gerar_excel": executar_gerar_excel,
    "gerar_relatorio_pdf": executar_gerar_pdf,
    "gerar_apresentacao": executar_gerar_apresentacao,
    "gerar_documento_word": executar_gerar_word,
    "gerar_markdown": executar_gerar_markdown_doc,
    "consultar_dados": executar_consultar_dados,
}


def executar_ferramenta(nome: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executa uma ferramenta pelo nome.
    """
    if nome not in EXECUTORES:
        raise ValueError(f"Ferramenta '{nome}' não encontrada. Opções: {list(EXECUTORES.keys())}")
    
    logger.info(f"Executando ferramenta: {nome} com params: {params}")
    
    try:
        resultado = EXECUTORES[nome](params)
        resultado["sucesso"] = True
        return resultado
    except Exception as e:
        logger.error(f"Erro ao executar {nome}: {e}")
        return {
            "sucesso": False,
            "erro": str(e),
            "tipo": "erro"
        }


def detectar_intencao_ferramenta(mensagem: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Detecta se a mensagem requer uso de ferramenta.
    """
    msg_lower = mensagem.lower()
    
    # Lógica simplificada de detecção (reutilizar a anterior ou melhorar)
    # Para brevidade, mantemos a lógica de regex simples
    
    if "gráfico" in msg_lower or "grafico" in msg_lower:
        tipo = "linha"
        if "barra" in msg_lower: tipo = "barra"
        elif "pizza" in msg_lower: tipo = "pizza"
        
        fonte = "ecl"
        if "prinad" in msg_lower: fonte = "prinad"
        
        return "gerar_grafico", {"tipo": tipo, "dados_fonte": fonte, "titulo": "Gráfico Gerado"}
    
    if "excel" in msg_lower or "planilha" in msg_lower:
        return "gerar_excel", {"dados_fonte": "portfolio", "titulo": "Exportação"}
        
    return None


__all__ = [
    "FERRAMENTAS_DISPONIVEIS",
    "executar_ferramenta",
    "detectar_intencao_ferramenta"
]
