# -*- coding: utf-8 -*-
"""
Core do Agente de IA
Sistema de Gestão de Risco Bancário

Implementação usando OpenAI-compatible API (OpenRouter)
com ferramentas nativas Python.
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass

import httpx

from .config import get_config
from .database import (
    criar_sessao, obter_sessao, listar_mensagens, 
    adicionar_mensagem, atualizar_sessao, registrar_uso_ferramenta
)
from .permissions import check_tool_permission, get_allowed_tools, TOOL_DESCRIPTIONS
from .tools import get_all_tools, execute_tool

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Mensagem do agente."""
    role: str  # user, assistant, tool, system
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_name: Optional[str] = None
    tool_result: Optional[Dict] = None


class BankingAgent:
    """
    Agente de IA para Sistema de Risco Bancário.
    
    Features:
    - Integração com OpenRouter (LLM)
    - RAG para documentos BACEN
    - Ferramentas de cálculo ECL, PRINAD, etc
    - Controle de acesso RBAC
    """
    
    SYSTEM_PROMPT = """Você é um assistente especializado em Gestão de Risco Bancário.
Você ajuda analistas, gestores e auditores com:
- Cálculos de ECL (Expected Credit Loss) conforme IFRS 9
- Classificação de risco PRINAD
- Análise de conformidade com CMN 4966 e BCB 352
- Exportação regulatória para BACEN
- Análise de portfólio e cenários forward-looking

REGRAS IMPORTANTES:
1. Sempre cite regulamentações quando aplicável (CMN 4966, IFRS 9)
2. Use as ferramentas disponíveis para consultas e cálculos
3. Seja preciso com números e percentuais
4. Para operações sensíveis, confirme antes de executar
5. Respeite o perfil de acesso do usuário

FERRAMENTAS DISPONÍVEIS:
{tools_description}

Responda em português brasileiro, de forma clara e profissional."""

    def __init__(
        self,
        user_id: str,
        user_role: str,
        session_id: Optional[str] = None
    ):
        """
        Inicializa o agente.
        
        Args:
            user_id: ID do usuário
            user_role: Role do usuário (ANALISTA, GESTOR, AUDITOR, ADMIN)
            session_id: ID de sessão existente (opcional)
        """
        self.config = get_config()
        self.user_id = user_id
        self.user_role = user_role
        self.session_id = session_id
        
        # Obter ferramentas permitidas para o usuário
        self.allowed_tools = get_allowed_tools(user_role)
        self.tools = self._build_tools_schema()
        
        # Histórico de mensagens da sessão
        self.messages: List[Dict[str, Any]] = []
        
        # Carregar histórico se sessão existente
        if session_id:
            self._load_session_history()
    
    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        """Constrói schema de ferramentas para o LLM."""
        all_tools = get_all_tools()
        allowed_schemas = []
        
        for tool in all_tools:
            if tool["name"] in self.allowed_tools:
                allowed_schemas.append({
                    "type": "function",
                    "function": tool
                })
        
        return allowed_schemas
    
    def _get_tools_description(self) -> str:
        """Gera descrição das ferramentas para o system prompt."""
        descriptions = []
        for tool_name in self.allowed_tools:
            if tool_name in TOOL_DESCRIPTIONS:
                descriptions.append(f"- {tool_name}: {TOOL_DESCRIPTIONS[tool_name]}")
        return "\n".join(descriptions) if descriptions else "Nenhuma ferramenta disponível."
    
    def _load_session_history(self):
        """Carrega histórico de mensagens da sessão."""
        if not self.session_id:
            return
        
        messages = listar_mensagens(self.session_id)
        for msg in messages:
            self.messages.append({
                "role": msg["role"],
                "content": msg["content"] or ""
            })
    
    def _create_session(self) -> str:
        """Cria nova sessão."""
        session = criar_sessao(self.user_id, self.user_role)
        self.session_id = str(session["id"])
        return self.session_id
    
    def _get_system_message(self) -> Dict[str, str]:
        """Retorna mensagem de sistema."""
        return {
            "role": "system",
            "content": self.SYSTEM_PROMPT.format(
                tools_description=self._get_tools_description()
            )
        }
    
    async def chat(
        self,
        message: str,
        stream: bool = False
    ) -> str:
        """
        Envia mensagem e obtém resposta.
        
        Args:
            message: Mensagem do usuário
            stream: Se True, retorna generator para streaming
            
        Returns:
            Resposta do agente
        """
        # Criar sessão se necessário
        if not self.session_id:
            self._create_session()
        
        # Adicionar mensagem do usuário
        self.messages.append({"role": "user", "content": message})
        adicionar_mensagem(self.session_id, "user", message)
        
        # Construir request
        messages = [self._get_system_message()] + self.messages
        
        # Chamar LLM
        response = await self._call_llm(messages)
        
        # Processar resposta
        assistant_message = response["choices"][0]["message"]
        
        # Verificar se há tool calls
        if assistant_message.get("tool_calls"):
            response_content = await self._handle_tool_calls(
                assistant_message["tool_calls"]
            )
        else:
            response_content = assistant_message.get("content", "")
        
        # Salvar resposta
        self.messages.append({"role": "assistant", "content": response_content})
        adicionar_mensagem(self.session_id, "assistant", response_content)
        
        # Atualizar resumo da sessão
        if len(self.messages) == 2:
            # Primeira interação, usar mensagem como título
            atualizar_sessao(self.session_id, titulo=message[:100])
        
        return response_content
    
    async def _call_llm(self, messages: List[Dict]) -> Dict:
        """Chama a API do LLM."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.config.llm.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.llm.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://risco-bancario.app",
                    "X-Title": "Sistema Risco Bancario"
                },
                json={
                    "model": self.config.llm.model,
                    "messages": messages,
                    "tools": self.tools if self.tools else None,
                    "temperature": self.config.llm.temperature,
                    "max_tokens": self.config.llm.max_tokens
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Erro LLM: {response.status_code} - {response.text}")
                raise Exception(f"Erro ao chamar LLM: {response.status_code}")
            
            return response.json()
    
    async def _handle_tool_calls(self, tool_calls: List[Dict]) -> str:
        """Processa chamadas de ferramentas."""
        results = []
        
        for call in tool_calls:
            tool_name = call["function"]["name"]
            tool_args = json.loads(call["function"]["arguments"])
            
            # Verificar permissão
            if not check_tool_permission(self.user_role, tool_name):
                result = {
                    "error": f"Acesso negado: você não tem permissão para usar {tool_name}"
                }
                results.append(f"❌ {tool_name}: Acesso negado para seu perfil ({self.user_role})")
                continue
            
            # Executar ferramenta
            start_time = time.time()
            try:
                result = await execute_tool(tool_name, tool_args)
                success = True
                error_msg = None
            except Exception as e:
                result = {"error": str(e)}
                success = False
                error_msg = str(e)
                logger.error(f"Erro ao executar {tool_name}: {e}")
            
            execution_ms = int((time.time() - start_time) * 1000)
            
            # Registrar uso
            registrar_uso_ferramenta(
                usuario_id=self.user_id,
                usuario_role=self.user_role,
                tool_name=tool_name,
                tool_input=tool_args,
                tool_output=result,
                success=success,
                error_message=error_msg,
                execution_ms=execution_ms,
                sessao_id=self.session_id
            )
            
            # Salvar mensagem da ferramenta
            adicionar_mensagem(
                self.session_id, "tool", 
                json.dumps(result, ensure_ascii=False),
                tool_name=tool_name,
                tool_result=result
            )
            
            # Formatar resultado
            if success:
                results.append(f"✅ **{tool_name}**: {json.dumps(result, ensure_ascii=False, indent=2)}")
            else:
                results.append(f"❌ **{tool_name}**: {error_msg}")
        
        # Fazer segunda chamada com resultados
        tool_results_msg = "\n\n".join(results)
        self.messages.append({"role": "assistant", "content": f"Resultados das ferramentas:\n{tool_results_msg}"})
        
        # Chamar LLM novamente para gerar resposta final
        messages = [self._get_system_message()] + self.messages
        messages.append({
            "role": "user",
            "content": "Com base nos resultados das ferramentas acima, forneça uma resposta clara e completa."
        })
        
        final_response = await self._call_llm(messages)
        return final_response["choices"][0]["message"].get("content", "")


async def create_agent(
    user_id: str,
    user_role: str,
    session_id: Optional[str] = None
) -> BankingAgent:
    """Factory function para criar agente."""
    return BankingAgent(
        user_id=user_id,
        user_role=user_role,
        session_id=session_id
    )


__all__ = [
    "BankingAgent",
    "AgentMessage",
    "create_agent"
]
