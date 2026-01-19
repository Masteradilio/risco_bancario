# -*- coding: utf-8 -*-
"""
Ferramenta de Pesquisa Web para o Agente IA
Usa DuckDuckGo para buscas (sem necessidade de API key)
"""

import logging
from typing import List, Dict, Optional
import httpx
from urllib.parse import quote_plus
import re

logger = logging.getLogger(__name__)


async def web_search(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Realiza pesquisa web usando DuckDuckGo.
    
    Args:
        query: Termo de busca
        limit: Número máximo de resultados (1-10)
        
    Returns:
        Lista de resultados com title, url e description
    """
    limit = min(max(limit, 1), 10)
    results = []
    
    try:
        # Usar DuckDuckGo HTML
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
        
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(search_url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Erro na busca: {response.status_code}")
                return []
            
            html = response.text
            
            # Extrair resultados usando regex (simples e eficaz)
            # Padrão para links de resultado
            result_pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
            snippet_pattern = r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>'
            
            # Encontrar todos os resultados
            links = re.findall(result_pattern, html, re.DOTALL)
            snippets = re.findall(snippet_pattern, html, re.DOTALL)
            
            for i, (url, title) in enumerate(links[:limit]):
                # Limpar HTML do título
                title_clean = re.sub(r'<[^>]+>', '', title).strip()
                
                # Pegar snippet correspondente se existir
                description = ""
                if i < len(snippets):
                    description = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                
                # Decodificar URL do DuckDuckGo
                if url.startswith("//duckduckgo.com/l/?uddg="):
                    # Extrair URL real
                    url_match = re.search(r'uddg=([^&]+)', url)
                    if url_match:
                        from urllib.parse import unquote
                        url = unquote(url_match.group(1))
                
                if title_clean and url:
                    results.append({
                        "title": title_clean,
                        "url": url,
                        "description": description
                    })
        
        logger.info(f"Busca web '{query}': {len(results)} resultados")
        return results
        
    except Exception as e:
        logger.error(f"Erro na busca web: {e}")
        return []


async def format_search_results(query: str, limit: int = 5) -> str:
    """
    Realiza busca e formata resultados para exibição.
    
    Returns:
        String formatada em Markdown com os resultados
    """
    results = await web_search(query, limit)
    
    if not results:
        return f"Não foi possível encontrar resultados para: **{query}**"
    
    output = f"### 🔍 Resultados da pesquisa: \"{query}\"\n\n"
    
    for i, result in enumerate(results, 1):
        output += f"**{i}. [{result['title']}]({result['url']})**\n"
        if result['description']:
            output += f"   {result['description']}\n"
        output += "\n"
    
    return output


# Teste local
if __name__ == "__main__":
    import asyncio
    
    async def test():
        results = await format_search_results("Resolução BACEN 4966 2024 atualizações")
        print(results)
    
    asyncio.run(test())
