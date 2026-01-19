# -*- coding: utf-8 -*-
"""
Módulo de Autenticação NTLM/SSO para Active Directory
======================================================

Middleware FastAPI para autenticação via Windows NTLM/SSO.
Integra com Active Directory corporativo para Single Sign-On.

Requisitos:
- pip install pyspnego

Autor: Sistema ECL
Data: Janeiro 2026
"""

import base64
import logging
from typing import Optional, Tuple, Callable
from datetime import datetime

from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# Configurações NTLM (mover para .env em produção)
NTLM_ENABLED = False  # Desabilitado por padrão (habilitar em ambiente corporativo)
NTLM_REALM = "BANCO.LOCAL"
NTLM_EXCLUDED_PATHS = ["/health", "/docs", "/openapi.json", "/redoc"]


class NTLMContext:
    """Contexto de autenticação NTLM para uma requisição."""
    
    def __init__(self):
        self.authenticated = False
        self.username: Optional[str] = None
        self.domain: Optional[str] = None
        self.spn: Optional[str] = None
        self.timestamp = datetime.now()
    
    @property
    def full_username(self) -> Optional[str]:
        """Retorna username completo (DOMAIN\\user)."""
        if self.domain and self.username:
            return f"{self.domain}\\{self.username}"
        return self.username


def parse_authorization_header(auth_header: str) -> Tuple[str, bytes]:
    """
    Parseia o header Authorization para extrair scheme e token.
    
    Args:
        auth_header: Valor do header Authorization
        
    Returns:
        Tupla (scheme, token_bytes)
    """
    if not auth_header:
        return "", b""
    
    parts = auth_header.split(" ", 1)
    if len(parts) != 2:
        return "", b""
    
    scheme = parts[0].lower()
    try:
        token = base64.b64decode(parts[1])
    except Exception:
        token = b""
    
    return scheme, token


def extract_username_from_ntlm(token: bytes) -> Optional[str]:
    """
    Extrai username de um token NTLM Type 3.
    
    NOTA: Em produção, usar pyspnego para validação completa.
    
    Args:
        token: Token NTLM em bytes
        
    Returns:
        Username extraído ou None
    """
    try:
        # Token NTLM Type 3 tem estrutura específica
        # Esta é uma implementação simplificada para POC
        if len(token) < 60:
            return None
        
        # Verificar assinatura NTLMSSP
        if token[:8] != b"NTLMSSP\x00":
            return None
        
        # Type 3 tem código 3
        msg_type = int.from_bytes(token[8:12], "little")
        if msg_type != 3:
            return None
        
        # Extrair offsets e tamanhos do username
        # (estrutura NTLM Type 3 é complexa)
        # Em produção: usar pyspnego.negotiate
        
        logger.debug("NTLM Type 3 message detected")
        return None  # Retorna None para forçar uso de pyspnego
        
    except Exception as e:
        logger.error(f"Erro ao extrair username NTLM: {e}")
        return None


async def authenticate_ntlm(
    request: Request,
    use_pyspnego: bool = True
) -> NTLMContext:
    """
    Autentica uma requisição via NTLM.
    
    O fluxo NTLM é:
    1. Cliente envia requisição sem auth
    2. Servidor responde 401 + WWW-Authenticate: Negotiate
    3. Cliente envia Auth header com Type 1 (Negotiation)
    4. Servidor responde com Type 2 (Challenge)
    5. Cliente envia Type 3 (Authentication) com credenciais
    6. Servidor valida e responde 200
    
    Args:
        request: Request FastAPI
        use_pyspnego: Se True, usa pyspnego para validação
        
    Returns:
        NTLMContext com resultado da autenticação
    """
    ctx = NTLMContext()
    
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header:
        return ctx
    
    scheme, token = parse_authorization_header(auth_header)
    
    if scheme not in ["negotiate", "ntlm"]:
        return ctx
    
    if len(token) == 0:
        return ctx
    
    # Tentar usar pyspnego se disponível
    if use_pyspnego:
        try:
            import spnego
            
            # Criar contexto de servidor
            server_ctx = spnego.server(
                hostname=request.headers.get("Host", "localhost"),
            )
            
            # Processar token do cliente
            out_token = server_ctx.step(token)
            
            if server_ctx.complete:
                ctx.authenticated = True
                ctx.username = server_ctx.client_principal
                
                # Separar domínio do username
                if ctx.username and "\\" in ctx.username:
                    ctx.domain, ctx.username = ctx.username.split("\\", 1)
                elif ctx.username and "@" in ctx.username:
                    ctx.username, ctx.domain = ctx.username.split("@", 1)
                
                logger.info(f"NTLM auth successful: {ctx.full_username}")
            
            return ctx
            
        except ImportError:
            logger.warning("pyspnego não instalado. Usando fallback.")
        except Exception as e:
            logger.error(f"Erro NTLM: {e}")
    
    # Fallback: extrair username do token (não valida contra AD)
    username = extract_username_from_ntlm(token)
    if username:
        ctx.username = username
        ctx.authenticated = True
        logger.warning(f"NTLM fallback auth (não validado): {username}")
    
    return ctx


def create_ntlm_challenge_response() -> Response:
    """
    Cria resposta 401 com challenge NTLM.
    
    Returns:
        Response 401 com header WWW-Authenticate
    """
    return Response(
        content="NTLM authentication required",
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={
            "WWW-Authenticate": "Negotiate",
        }
    )


class NTLMMiddleware(BaseHTTPMiddleware):
    """
    Middleware FastAPI para autenticação NTLM/SSO.
    
    Usage:
        app.add_middleware(NTLMMiddleware)
    
    Ou com callback customizado:
        app.add_middleware(
            NTLMMiddleware,
            on_authenticated=lambda ctx, req: process_user(ctx)
        )
    """
    
    def __init__(
        self, 
        app,
        enabled: bool = NTLM_ENABLED,
        excluded_paths: list = None,
        on_authenticated: Callable = None
    ):
        super().__init__(app)
        self.enabled = enabled
        self.excluded_paths = excluded_paths or NTLM_EXCLUDED_PATHS
        self.on_authenticated = on_authenticated
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Processa a requisição."""
        
        # Se desabilitado, passar adiante
        if not self.enabled:
            return await call_next(request)
        
        # Excluir paths específicos
        for path in self.excluded_paths:
            if request.url.path.startswith(path):
                return await call_next(request)
        
        # Verificar auth header
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header:
            # Primeiro passo: solicitar autenticação
            return create_ntlm_challenge_response()
        
        # Autenticar via NTLM
        ctx = await authenticate_ntlm(request)
        
        if not ctx.authenticated:
            # Falha na autenticação
            logger.warning(f"NTLM auth failed for {request.client.host}")
            return create_ntlm_challenge_response()
        
        # Callback customizado
        if self.on_authenticated:
            try:
                await self.on_authenticated(ctx, request)
            except Exception as e:
                logger.error(f"Erro no callback de autenticação: {e}")
        
        # Armazenar contexto na requisição
        request.state.ntlm_context = ctx
        
        # Prosseguir com a requisição
        response = await call_next(request)
        
        return response


# Função helper para extrair usuário NTLM da requisição
def get_ntlm_user(request: Request) -> Optional[str]:
    """
    Obtém o username NTLM autenticado da requisição.
    
    Args:
        request: Request FastAPI
        
    Returns:
        Username ou None
    """
    ctx: NTLMContext = getattr(request.state, "ntlm_context", None)
    if ctx and ctx.authenticated:
        return ctx.full_username
    return None


__all__ = [
    "NTLMContext",
    "NTLMMiddleware",
    "authenticate_ntlm",
    "get_ntlm_user",
    "NTLM_ENABLED",
    "NTLM_REALM"
]
