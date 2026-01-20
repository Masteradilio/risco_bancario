# -*- coding: utf-8 -*-
"""
Orquestrador de Ferramentas do Agente IA
Conecta o LLM com as ferramentas reais
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

import pandas as pd

from .mock_data import (
    get_dados_ecl,
    get_dados_prinad,
    get_dados_propensao,
    get_resumo_portfolio,
    get_clientes_amostra
)
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
# FUNÇÕES DE EXECUÇÃO DE FERRAMENTAS
# ============================================================================

def obter_dados(fonte: str) -> Tuple[pd.DataFrame, str]:
    """Obtém dados conforme a fonte especificada."""
    fontes = {
        "ecl": (get_dados_ecl, "Dados de ECL (Expected Credit Loss) - últimos 12 meses"),
        "prinad": (get_dados_prinad, "Classificação PRINAD por rating"),
        "propensao": (get_dados_propensao, "Dados de Propensão por produto"),
        "clientes": (get_clientes_amostra, "Amostra de 50 clientes"),
        "portfolio": (lambda: pd.DataFrame([get_resumo_portfolio()]), "Resumo do portfólio")
    }
    
    if fonte not in fontes:
        raise ValueError(f"Fonte '{fonte}' não encontrada. Opções: {list(fontes.keys())}")
    
    func, descricao = fontes[fonte]
    return func(), descricao


def executar_gerar_grafico(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de gráfico."""
    tipo = params.get("tipo", "linha")
    dados_fonte = params.get("dados_fonte", "ecl")
    titulo = params.get("titulo", "Gráfico")
    
    dados, descricao = obter_dados(dados_fonte)
    
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
    
    elif dados_fonte == "propensao":
        df_pivot = dados.pivot_table(index="mes_ano", columns="produto", 
                                     values="propensao_media", aggfunc="mean").reset_index()
        dados = df_pivot
        if tipo == "linha":
            produtos = [c for c in dados.columns if c != "mes_ano"]
            config.update({"x": "mes_ano", "y": produtos[0] if len(produtos) == 1 else "propensao_media"})
    
    # Gerar gráfico em ambos os temas
    grafico_dark = gerar_grafico(tipo, dados, config, tema="dark")
    grafico_light = gerar_grafico(tipo, dados, config, tema="light")
    
    # Gerar resumo técnico para o LLM
    resumo_dados = f"Visualização de {titulo}."
    try:
        if dados_fonte == "ecl" and "ecl_total" in dados.columns:
            ultimo = dados.iloc[-1]
            resumo_dados = f"Destaque ECL ({ultimo['mes_ano']}): R$ {ultimo['ecl_total']:,.2f}."
            if "stage_1" in dados.columns:
                resumo_dados += f" S1: {ultimo['stage_1']:,.0f}, S2: {ultimo['stage_2']:,.0f}, S3: {ultimo['stage_3']:,.0f}."
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
    
    # Adicionar timestamp para nome único
    timestamp = datetime.now().strftime("%H%M%S")
    nome_arquivo = f"{nome_base}_{timestamp}.xlsx"
    
    # Gerar resumo para LLM
    resumo_dados = f"Contém {len(dados)} registros e {len(dados.columns)} colunas."
    if dados_fonte == "ecl" and "ecl_total" in dados.columns:
        ultimo = dados.iloc[-1] if len(dados) > 0 else None
        if ultimo is not None:
            resumo_dados = f"ECL último período: R$ {ultimo['ecl_total']:,.2f}. Total de {len(dados)} meses."
    elif dados_fonte == "prinad" and "quantidade" in dados.columns:
        total = dados['quantidade'].sum()
        resumo_dados = f"Total de {total:,} clientes distribuídos em {len(dados)} ratings."
    
    return {
        "tipo": "excel",
        "nome": nome_arquivo,
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "conteudo": excel_bytes,
        "descricao": f"Planilha gerada às {timestamp}. {titulo}: {resumo_dados}",
        "metadados": {
            "fonte_dados": dados_fonte,
            "linhas": len(dados),
            "colunas": len(dados.columns),
            "gerado_em": datetime.now().isoformat()
        }
    }



def executar_gerar_pdf(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de PDF."""
    titulo = params.get("titulo", "Relatório")
    tipo_relatorio = params.get("tipo_relatorio", "portfolio")
    incluir_grafico = params.get("incluir_grafico", True)
    
    secoes = []
    resumo_texto_llm = "Relatório gerado com sucesso."
    
    if tipo_relatorio == "ecl":
        dados, _ = obter_dados("ecl")
        resumo = get_resumo_portfolio()
        
        texto_resumo = f"""A análise da Expected Credit Loss (ECL) do portfólio apresenta os seguintes indicadores:

• ECL Total: R$ {resumo['ecl_total']:,.2f}
• Cobertura: {resumo['cobertura']:.1f}%
• PD Médio: {resumo['pd_medio']*100:.2f}%
• LGD Médio: {resumo['lgd_medio']*100:.1f}%

O portfólio demonstra adequação aos requisitos da Resolução BACEN CMN 4966/2021."""
        
        # Salvar para o LLM
        resumo_texto_llm = f"Dados do Relatório ECL: ECL Total R$ {resumo['ecl_total']:,.2f}, Cobertura {resumo['cobertura']:.1f}%, PD {resumo['pd_medio']*100:.2f}%."

        secoes.append({
            "titulo": "Resumo Executivo",
            "tipo": "texto",
            "conteudo": texto_resumo
        })
        
        secoes.append({
            "titulo": "Evolução Mensal da ECL",
            "tipo": "tabela",
            "dados": dados[["mes_ano", "ecl_total", "stage_1", "stage_2", "stage_3"]].tail(6)
        })
        
        if incluir_grafico:
            grafico = executar_gerar_grafico({
                "tipo": "linha",
                "dados_fonte": "ecl",
                "titulo": "Evolução da ECL"
            })
            secoes.append({
                "titulo": "Visualização",
                "tipo": "imagem",
                "imagem": grafico["conteudo_light"]
            })
    
    elif tipo_relatorio == "prinad":
        dados, _ = obter_dados("prinad")
        
        resumo_texto_llm = "Relatório PRINAD gerado com distribuição de ratings de crédito."

        secoes.append({
            "titulo": "Distribuição de Rating",
            "tipo": "texto",
            "conteudo": "Análise da classificação de risco dos clientes conforme metodologia PRINAD."
        })
        
        secoes.append({
            "titulo": "Classificação por Rating",
            "tipo": "tabela",
            "dados": dados
        })
    
    elif tipo_relatorio == "portfolio":
        resumo = get_resumo_portfolio()
        
        resumo_texto_llm = f"Resumo do Portfólio: Clientes {resumo['total_clientes']:,}, Exposição R$ {resumo['total_exposicao']:,.2f}, ECL R$ {resumo['ecl_total']:,.2f}, Score {resumo['score_medio']}."

        secoes.append({
            "titulo": "Visão Geral do Portfólio",
            "tipo": "lista",
            "itens": [
                f"Total de Clientes: {resumo['total_clientes']:,}",
                f"Exposição Total: R$ {resumo['total_exposicao']:,.2f}",
                f"ECL Total: R$ {resumo['ecl_total']:,.2f}",
                f"Score Médio: {resumo['score_medio']}",
                f"AUC-ROC PRINAD: {resumo['auc_roc_prinad']:.4f}",
                f"Inadimplência 90d: {resumo['inadimplencia_90d']*100:.2f}%"
            ]
        })
    
    pdf_bytes = gerar_pdf(titulo, secoes, tema="light")
    timestamp = datetime.now().strftime("%H%M%S")
    
    return {
        "tipo": "pdf",
        "nome": f"{titulo.replace(' ', '_').lower()}_{timestamp}.pdf",
        "mime_type": "application/pdf",
        "conteudo": pdf_bytes,
        "descricao": f"Relatório gerado às {timestamp}. {resumo_texto_llm}",
        "metadados": {
            "tipo_relatorio": tipo_relatorio,
            "secoes": len(secoes)
        }
    }


def executar_gerar_apresentacao(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de PowerPoint."""
    titulo = params.get("titulo", "Apresentação")
    tema = params.get("tema", "portfolio")
    
    slides = []
    
    if tema == "ecl":
        resumo = get_resumo_portfolio()
        
        slides.append({
            "titulo": "ECL - Expected Credit Loss",
            "tipo": "bullets",
            "itens": [
                f"ECL Total: R$ {resumo['ecl_total']:,.2f}",
                f"Cobertura de Provisão: {resumo['cobertura']:.1f}%",
                "Metodologia: IFRS 9 / CMN 4966",
                "Frequência: Cálculo mensal"
            ]
        })
        
        grafico = executar_gerar_grafico({
            "tipo": "linha", "dados_fonte": "ecl", "titulo": "Evolução ECL"
        })
        slides.append({
            "titulo": "Evolução da ECL",
            "tipo": "imagem",
            "imagem": grafico["conteudo"]
        })
    
    elif tema == "prinad":
        slides.append({
            "titulo": "PRINAD - Classificação de Risco",
            "tipo": "bullets",
            "itens": [
                "Modelo de credit scoring proprietário",
                "Classificação: A1-A3, B1-B3, C1-C3, D-H",
                f"AUC-ROC: {get_resumo_portfolio()['auc_roc_prinad']:.4f}",
                "Validação anual conforme BACEN"
            ]
        })
    
    elif tema == "portfolio":
        resumo = get_resumo_portfolio()
        
        slides.append({
            "titulo": "Indicadores do Portfólio",
            "tipo": "bullets",
            "itens": [
                f"Clientes: {resumo['total_clientes']:,}",
                f"Exposição: R$ {resumo['total_exposicao']/1e6:.1f}M",
                f"ECL: R$ {resumo['ecl_total']/1e6:.2f}M",
                f"Concentração Top 10: {resumo['concentracao_top10']*100:.0f}%"
            ]
        })
    
    pptx_bytes = gerar_powerpoint(titulo, slides)
    
    return {
        "tipo": "pptx",
        "nome": f"{titulo.replace(' ', '_').lower()}.pptx",
        "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "conteudo": pptx_bytes,
        "descricao": f"Apresentação: {titulo} ({len(slides)} slides)",
        "metadados": {
            "tema": tema,
            "slides": len(slides) + 1
        }
    }


def executar_gerar_word(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de Word."""
    titulo = params.get("titulo", "Documento")
    tipo = params.get("tipo", "relatorio")
    
    secoes = []
    resumo = get_resumo_portfolio()
    
    secoes.append({
        "titulo": "Resumo Executivo",
        "tipo": "texto",
        "conteudo": f"""Este documento apresenta uma análise do portfólio de crédito.

O portfólio conta com {resumo['total_clientes']:,} clientes, com exposição total de R$ {resumo['total_exposicao']:,.2f}.

A perda esperada de crédito (ECL) calculada é de R$ {resumo['ecl_total']:,.2f}, representando uma cobertura de {resumo['cobertura']:.1f}%."""
    })
    
    dados_ecl, _ = obter_dados("ecl")
    secoes.append({
        "titulo": "Dados de ECL",
        "tipo": "tabela",
        "dados": dados_ecl.tail(6)
    })
    
    word_bytes = gerar_word(titulo, secoes)
    
    return {
        "tipo": "docx",
        "nome": f"{titulo.replace(' ', '_').lower()}.docx",
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "conteudo": word_bytes,
        "descricao": f"Documento Word: {titulo}",
        "metadados": {
            "tipo": tipo,
            "secoes": len(secoes)
        }
    }


def executar_gerar_markdown_doc(params: Dict[str, Any]) -> Dict[str, Any]:
    """Executa geração de Markdown."""
    titulo = params.get("titulo", "Documento")
    conteudo = params.get("conteudo", "")
    
    secoes = [{"tipo": "texto", "conteudo": conteudo}]
    
    md_bytes = gerar_markdown(titulo, secoes)
    
    return {
        "tipo": "markdown",
        "nome": f"{titulo.replace(' ', '_').lower()}.md",
        "mime_type": "text/markdown",
        "conteudo": md_bytes,
        "descricao": f"Documento Markdown: {titulo}",
        "metadados": {}
    }


def executar_consultar_dados(params: Dict[str, Any]) -> Dict[str, Any]:
    """Consulta dados e retorna como texto."""
    fonte = params.get("fonte", "portfolio")
    
    dados, descricao = obter_dados(fonte)
    
    if fonte == "portfolio":
        resumo = dados.iloc[0].to_dict()
        texto = f"""**{descricao}**

| Indicador | Valor |
|-----------|-------|
| Total de Clientes | {resumo.get('total_clientes', 0):,} |
| Exposição Total | R$ {resumo.get('total_exposicao', 0):,.2f} |
| ECL Total | R$ {resumo.get('ecl_total', 0):,.2f} |
| Cobertura | {resumo.get('cobertura', 0):.1f}% |
| PD Médio | {resumo.get('pd_medio', 0)*100:.2f}% |
| LGD Médio | {resumo.get('lgd_medio', 0)*100:.1f}% |
| AUC-ROC PRINAD | {resumo.get('auc_roc_prinad', 0):.4f} |
| Inadimplência 90d | {resumo.get('inadimplencia_90d', 0)*100:.2f}% |
"""
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
    
    Args:
        nome: Nome da ferramenta
        params: Parâmetros da ferramenta
    
    Returns:
        Resultado da execução
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
    
    Returns:
        Tuple (nome_ferramenta, params) ou None
    """
    msg_lower = mensagem.lower()
    
    # Padrões de detecção para GRÁFICOS
    grafico_keywords = [
        "gere um grafico", "gerar grafico", "criar grafico", "crie um grafico",
        "gere um gráfico", "gerar gráfico", "criar gráfico", "crie um gráfico",
        "plote", "plotar", "visualização", "visualize", "visualizacao",
        "grafico de", "gráfico de", "faca um grafico", "faça um gráfico",
        "monte um grafico", "monte um gráfico"
    ]
    
    if any(p in msg_lower for p in grafico_keywords):
        # Detectar tipo de gráfico
        tipo = "linha"
        if "barra" in msg_lower:
            tipo = "barra_horizontal" if "horizontal" in msg_lower else "barra"
        elif any(p in msg_lower for p in ["pizza", "pie"]):
            tipo = "pizza"
        elif any(p in msg_lower for p in ["rosca", "donut"]):
            tipo = "donut"
        elif any(p in msg_lower for p in ["área", "area", "empilhad"]):
            tipo = "area"
        elif any(p in msg_lower for p in ["dispersão", "dispersao", "scatter"]):
            tipo = "dispersao"
        elif any(p in msg_lower for p in ["calor", "heatmap", "correlação", "correlacao"]):
            tipo = "heatmap"
        elif any(p in msg_lower for p in ["boxplot", "box plot"]):
            tipo = "boxplot"
        elif "histograma" in msg_lower:
            tipo = "histograma"
        
        # Detectar fonte de dados
        fonte = "ecl"
        if "prinad" in msg_lower:
            fonte = "prinad"
        elif any(p in msg_lower for p in ["propensão", "propensao"]):
            fonte = "propensao"
        elif "cliente" in msg_lower:
            fonte = "clientes"
        
        # Extrair título da mensagem
        titulo = f"Evolução da {fonte.upper()}" if tipo == "linha" else f"Distribuição {fonte.upper()}"
        if "ecl" in msg_lower.lower():
            titulo = "Evolução da ECL"
        
        return ("gerar_grafico", {
            "tipo": tipo,
            "dados_fonte": fonte,
            "titulo": titulo
        })
    
    # Detecção mais flexível para EXCEL
    excel_keywords = [
        "gerar excel", "gere um excel", "criar excel", "crie um excel",
        "gerar planilha", "gere uma planilha", "criar planilha", "crie uma planilha",
        "exportar excel", "exportar para excel", "exportar xlsx",
        "gerar xlsx", "gere um xlsx"
    ]
    if any(p in msg_lower for p in excel_keywords):
        fonte = "ecl"
        if "prinad" in msg_lower:
            fonte = "prinad"
        elif "propensão" in msg_lower or "propensao" in msg_lower:
            fonte = "propensao"
        
        return ("gerar_excel", {
            "dados_fonte": fonte,
            "titulo": f"Dados de {fonte.upper()}",
            "nome_arquivo": f"dados_{fonte}"
        })
    
    # Detecção mais flexível para PDF
    pdf_keywords = [
        "gerar pdf", "gere um pdf", "criar pdf", "crie um pdf",
        "gerar relatorio pdf", "gere um relatorio pdf", 
        "relatorio em pdf", "relatório em pdf",
        "exportar pdf", "exportar para pdf",
        "salvar como pdf", "gerar documento pdf"
    ]
    # Check especial para "relatório... em pdf" ou "gerar... pdf"
    is_pdf_intention = any(p in msg_lower for p in pdf_keywords)
    if not is_pdf_intention and "pdf" in msg_lower:
        if any(verb in msg_lower for verb in ["gerar", "gere", "criar", "crie", "fazer", "faça", "exportar"]):
            is_pdf_intention = True

    if is_pdf_intention:
        tipo_rel = "portfolio"
        if "ecl" in msg_lower:
            tipo_rel = "ecl"
        elif "prinad" in msg_lower:
            tipo_rel = "prinad"
        
        return ("gerar_relatorio_pdf", {
            "titulo": "Relatório de Análise",
            "tipo_relatorio": tipo_rel,
            "incluir_grafico": True
        })
    
    # Detecção Powerpoint
    pptx_keywords = [
        "apresentação", "apresentacao", "powerpoint", "pptx", "slides",
        "gerar apresentação", "gere uma apresentação", "criar slides"
    ]
    if any(p in msg_lower for p in pptx_keywords):
        tema = "portfolio"
        if "ecl" in msg_lower:
            tema = "ecl"
        elif "prinad" in msg_lower:
            tema = "prinad"
        
        return ("gerar_apresentacao", {
            "titulo": "Apresentação Executiva",
            "tema": tema
        })
    
    if any(p in msg_lower for p in ["documento word", "gerar word", "docx", "arquivo word", "relatorio word"]):
        return ("gerar_documento_word", {
            "titulo": "Relatório",
            "tipo": "relatorio"
        })
    
    return None


__all__ = [
    "FERRAMENTAS_DISPONIVEIS",
    "executar_ferramenta",
    "detectar_intencao_ferramenta"
]
