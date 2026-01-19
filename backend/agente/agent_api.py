# -*- coding: utf-8 -*-
"""
API do Agente de IA com Ferramentas
Sistema de Gestão de Risco Bancário
"""

import os
import logging
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Body, Response, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import httpx
import io
import pandas as pd

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Agente IA"])


# ============================================================================
# ARMAZENAMENTO EM MEMÓRIA (DEMO)
# ============================================================================

# Sessões: {session_id: {id, titulo, messages: [], artifacts: [], uploads: [], created_at}}
SESSIONS: dict = {}

# Artefatos: {artifact_id: {id, session_id, tipo, nome, descricao, conteudo, ...}}
ARTIFACTS: dict = {}

# Uploads: {upload_id: {id, session_id, nome, tipo, mime_type, conteudo, texto_extraido, created_at}}
UPLOADS: dict = {}

# Tipos de arquivo permitidos para upload
ALLOWED_UPLOAD_TYPES = {
    "text/csv": "csv",
    "application/vnd.ms-excel": "excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
    "text/plain": "txt",
    "text/markdown": "markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/png": "image",
    "image/jpeg": "image",
    "image/jpg": "image",
}


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensagem do usuário")
    session_id: Optional[str] = Field(None, description="ID da sessão (opcional)")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    timestamp: str
    artifact_id: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    titulo: str
    resumo: Optional[str] = None
    createdAt: str
    updatedAt: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    toolName: Optional[str] = None
    createdAt: str


class ArtifactResponse(BaseModel):
    id: str
    tipo: str
    nome: str
    descricao: Optional[str] = None
    mimeType: str
    tamanho: int
    createdAt: str
    temVersoes: bool = False


class ToolInfo(BaseModel):
    name: str
    description: str


# ============================================================================
# CONFIGURAÇÃO DO LLM
# ============================================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")

CURRENT_DATE = date.today().strftime("%d/%m/%Y")

SYSTEM_PROMPT = f"""Você é um assistente de IA especializado em gestão de risco bancário, integrado a um sistema que possui ferramentas de automação.
Data atual: {CURRENT_DATE}

## SUAS CAPACIDADES:
- Análise de ECL (Expected Credit Loss) conforme IFRS 9 e BACEN CMN 4966/2021
- Classificação PRINAD de risco de crédito
- Regulamentações bancárias do BACEN
- Geração de gráficos, planilhas e documentos

## REGRAS CRÍTICAS - SIGA RIGOROSAMENTE:

1. **VOCÊ NÃO GERA ARQUIVOS**: Você é uma IA de texto. Quem gera arquivos são as FERRAMENTAS do sistema.
   - NUNCA diga "Gerei o arquivo" ou "Segue o link" se a ferramenta não tiver sido executada.
   - NUNCA invente links de download como `[Relatorio.pdf]` ou `(clique aqui)`. 
   - Se a ferramenta rodar com sucesso, o sistema avisará "✅ Gerando...". Se você não ver isso, o arquivo NÃO existe.

2. **EXECUÇÃO DE FERRAMENTAS**:
   - Se o usuário pedir um gráfico/relatório, o sistema tentará interceptar o pedido.
   - Se o pedido chegar até você (significa que o sistema não interceptou), responda curto e direto para tentar acionar a ferramenta na próxima:
     "Entendi. Para gerar esse arquivo, por favor confirme: 'Gerar relatório PDF da ECL' ou 'Gerar planilha Excel'."

3. **USE DADOS DE DEMONSTRAÇÃO**: Ao analisar ou explicar, use os dados fictícios do sistema se o usuário não fornecer.

4. **SEJA HONESTO**: Se não conseguir gerar o artefato, diga: "Não consigo gerar esse arquivo diretamente. Tente usar o botão de ferramentas ou peça um formato específico (PDF, Excel, Gráfico)."

## RESPOSTAS PADRÃO:
- Ao confirmar uma ação: "Entendido. Iniciando análise..."
- Ao explicar dados: Use Markdown para tabelas e negrito para destaques.
"""




SEARCH_KEYWORDS = [
    "pesquisar", "pesquise", "buscar", "busque", "procurar", "procure",
    "internet", "web", "atualização", "atualizações", "notícias", "últimas"
]


def should_search_web(message: str) -> bool:
    """Verifica se a mensagem requer busca web."""
    return any(k in message.lower() for k in SEARCH_KEYWORDS)


async def call_llm(messages: List[dict]) -> str:
    """Chama o LLM via OpenRouter."""
    if not OPENROUTER_API_KEY:
        return "⚠️ **API Key não configurada.**"
    
    logger.info(f"Chamando LLM: {MODEL_NAME}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL_NAME,
                    "messages": messages,
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"Erro: {response.status_code}")
                return f"⚠️ Erro ao chamar LLM: {response.status_code}"
                
    except httpx.TimeoutException:
        return "⚠️ **Tempo limite excedido.** Tente novamente."
    except Exception as e:
        logger.error(f"Erro: {e}")
        return f"⚠️ Erro: {str(e)}"


# ============================================================================
# DETECÇÃO E EXECUÇÃO DE FERRAMENTAS
# ============================================================================

def detectar_e_executar_ferramenta(mensagem: str, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Detecta se a mensagem requer ferramenta e executa.
    
    Returns:
        Dict com informações do artefato gerado ou None
    """
    try:
        from .tools_orquestrador import detectar_intencao_ferramenta, executar_ferramenta
        
        logger.info(f"Detectando ferramenta para: {mensagem[:50]}...")
        intencao = detectar_intencao_ferramenta(mensagem)
        logger.info(f"Intenção detectada: {intencao}")
        
        if intencao:
            nome_ferramenta, params = intencao
            logger.info(f"Ferramenta detectada: {nome_ferramenta} com params: {params}")
            
            resultado = executar_ferramenta(nome_ferramenta, params)
            logger.info(f"Resultado da ferramenta: sucesso={resultado.get('sucesso')}, tipo={resultado.get('tipo')}, erro={resultado.get('erro')}")
            
            if resultado.get("sucesso") and resultado.get("tipo") != "texto":
                # Salvar artefato
                artifact_id = str(uuid4())
                
                artefato = {
                    "id": artifact_id,
                    "session_id": session_id,
                    "tipo": resultado["tipo"],
                    "nome": resultado["nome"],
                    "descricao": resultado.get("descricao", ""),
                    "mime_type": resultado["mime_type"],
                    "conteudo": resultado["conteudo"],
                    "conteudo_dark": resultado.get("conteudo_dark"),
                    "conteudo_light": resultado.get("conteudo_light"),
                    "tamanho": len(resultado["conteudo"]),
                    "metadados": resultado.get("metadados", {}),
                    "created_at": datetime.now()
                }
                
                ARTIFACTS[artifact_id] = artefato
                
                # Adicionar à sessão
                if session_id in SESSIONS:
                    if "artifacts" not in SESSIONS[session_id]:
                        SESSIONS[session_id]["artifacts"] = []
                    SESSIONS[session_id]["artifacts"].append(artifact_id)
                
                logger.info(f"Artefato criado: {artifact_id} ({resultado['tipo']})")
                
                return {
                    "artifact_id": artifact_id,
                    "tipo": resultado["tipo"],
                    "nome": resultado["nome"],
                    "descricao": resultado.get("descricao", ""),
                    "ferramenta": nome_ferramenta
                }
            
            elif resultado.get("tipo") == "texto":
                return {
                    "tipo": "texto",
                    "conteudo": resultado.get("conteudo", "")
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao executar ferramenta: {e}")
        return None


# ============================================================================
# ENDPOINTS DE CHAT
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Envia mensagem para o agente e obtém resposta."""
    try:
        # Criar ou obter sessão
        session_id = request.session_id
        if not session_id or session_id not in SESSIONS:
            session_id = str(uuid4())
            SESSIONS[session_id] = {
                "id": session_id,
                "titulo": request.message[:50] + "..." if len(request.message) > 50 else request.message,
                "messages": [],
                "artifacts": [],
                "created_at": datetime.now()
            }
        
        session = SESSIONS[session_id]
        
        # Adicionar mensagem do usuário
        session["messages"].append({
            "id": str(uuid4()),
            "role": "user",
            "content": request.message,
            "created_at": datetime.now()
        })
        
        # Tentar executar ferramenta
        resultado_ferramenta = detectar_e_executar_ferramenta(request.message, session_id)
        
        artifact_id = None
        tool_context = ""
        
        if resultado_ferramenta:
            if resultado_ferramenta.get("artifact_id"):
                artifact_id = resultado_ferramenta["artifact_id"]
                # Injetar contexto para o LLM saber que a ferramenta rodou
                tool_context = f"""
[SISTEMA - AÇÃO AUTOMÁTICA EXECUTADA]
Ferramenta '{resultado_ferramenta.get('ferramenta', 'desconhecida')}' executada com SUCESSO.
Artefato gerado: {resultado_ferramenta['nome']} ({resultado_ferramenta['tipo']})
Descrição: {resultado_ferramenta.get('descricao', '')}
ID do Artefato: {artifact_id}

INSTRUÇÃO PARA O ASSISTENTE:
O artefato JÁ FOI CRIADO e está disponível na sidebar do usuário.
NÃO diga "Vou gerar" ou "Estou gerando". Diga "Gerei" ou "Aqui está".
Analise o pedido do usuário e descreva o que contém no artefato que acabou de ser criado (use dados fictícios se necessário para enriquecer a explicação).
Seja cordial e profissional.
"""
            elif resultado_ferramenta.get("tipo") == "texto":
                 tool_context = f"\n\n[SISTEMA]: A ferramenta retornou o seguinte texto técnico:\n{resultado_ferramenta.get('conteudo', '')}\n\nUse essa informação para responder ao usuário."
        
        # Verificar busca web
        web_results = ""
        if should_search_web(request.message):
            try:
                from .web_search import format_search_results
                query = request.message.replace("pesquise", "").replace("busque", "").strip()
                web_results = await format_search_results(query, limit=5)
            except Exception as e:
                logger.error(f"Erro busca web: {e}")
        
        # Obter contexto de uploads da sessão
        uploads_context = ""
        session_uploads = session.get("uploads", [])
        if session_uploads:
            uploads_context = "\n\n## ARQUIVOS DO USUÁRIO:\n"
            for up_id in session_uploads[-5:]:  # Últimos 5 uploads
                if up_id in UPLOADS:
                    up = UPLOADS[up_id]
                    uploads_context += f"\n### Arquivo: {up['nome']}\n"
                    if up.get("texto_extraido"):
                        uploads_context += up["texto_extraido"][:2000]  # Limitar tamanho
        
        # Construir mensagens para o LLM
        llm_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        if tool_context:
            llm_messages.append({"role": "system", "content": tool_context})

        if uploads_context:
            llm_messages.append({
                "role": "system",
                "content": uploads_context
            })
        
        if web_results:
            llm_messages.append({
                "role": "system",
                "content": f"RESULTADOS DA PESQUISA WEB:\n\n{web_results}"
            })
        
        for msg in session["messages"][-10:]:
            llm_messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Chamar LLM
        response_text = await call_llm(llm_messages)
        
        # Adicionar aviso discreto sobre sidebar apenas se houver artefato
        if artifact_id:
             response_text += f"\n\n> *O arquivo **{resultado_ferramenta['nome']}** está disponível na aba 'Artefatos Gerados'.*"

        # Salvar resposta
        session["messages"].append({
            "id": str(uuid4()),
            "role": "assistant",
            "content": response_text,
            "artifact_id": artifact_id,
            "created_at": datetime.now()
        })
        
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            timestamp=datetime.now().isoformat(),
            artifact_id=artifact_id
        )
        
    except Exception as e:
        logger.error(f"Erro no chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE SESSÕES
# ============================================================================

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(limit: int = Query(50, ge=1, le=100)):
    """Lista sessões."""
    sessions = list(SESSIONS.values())[-limit:]
    sessions.reverse()
    
    return [
        SessionResponse(
            id=s["id"],
            titulo=s.get("titulo", "Nova Conversa"),
            resumo=None,
            createdAt=s["created_at"].isoformat(),
            updatedAt=s["created_at"].isoformat()
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=SessionResponse)
async def create_session(titulo: str = Body("Nova Conversa", embed=True)):
    """Cria nova sessão."""
    session_id = str(uuid4())
    now = datetime.now()
    
    SESSIONS[session_id] = {
        "id": session_id,
        "titulo": titulo,
        "messages": [],
        "artifacts": [],
        "created_at": now
    }
    
    return SessionResponse(
        id=session_id,
        titulo=titulo,
        resumo=None,
        createdAt=now.isoformat(),
        updatedAt=now.isoformat()
    )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str, limit: int = Query(100, ge=1, le=500)):
    """Obtém mensagens de uma sessão."""
    if session_id not in SESSIONS:
        return []
    
    messages = SESSIONS[session_id]["messages"][-limit:]
    
    return [
        MessageResponse(
            id=m["id"],
            role=m["role"],
            content=m["content"],
            toolName=m.get("tool_name"),
            createdAt=m["created_at"].isoformat()
        )
        for m in messages
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Exclui uma sessão."""
    if session_id in SESSIONS:
        # Excluir artefatos da sessão
        for art_id in SESSIONS[session_id].get("artifacts", []):
            if art_id in ARTIFACTS:
                del ARTIFACTS[art_id]
        del SESSIONS[session_id]
    return {"message": "Sessão excluída"}


# ============================================================================
# ENDPOINTS DE UPLOAD DE ARQUIVOS
# ============================================================================

def extrair_texto_arquivo(conteudo: bytes, mime_type: str, nome: str) -> str:
    """Extrai texto de um arquivo para contexto do LLM."""
    try:
        tipo = ALLOWED_UPLOAD_TYPES.get(mime_type, "")
        
        if tipo == "txt" or tipo == "markdown":
            return conteudo.decode("utf-8", errors="ignore")
        
        elif tipo == "csv":
            df = pd.read_csv(io.BytesIO(conteudo))
            return f"Dados CSV ({len(df)} linhas, {len(df.columns)} colunas):\n\n{df.head(20).to_markdown()}"
        
        elif tipo == "excel":
            df = pd.read_excel(io.BytesIO(conteudo))
            return f"Dados Excel ({len(df)} linhas, {len(df.columns)} colunas):\n\n{df.head(20).to_markdown()}"
        
        elif tipo == "image":
            return f"[Imagem anexada: {nome}]"
        
        elif tipo == "docx":
            try:
                from docx import Document
                doc = Document(io.BytesIO(conteudo))
                text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                return text[:3000]
            except:
                return f"[Documento Word: {nome}]"
        
        return f"[Arquivo: {nome}]"
    except Exception as e:
        logger.error(f"Erro ao extrair texto: {e}")
        return f"[Arquivo: {nome}]"


class UploadResponse(BaseModel):
    id: str
    nome: str
    tipo: str
    tamanho: int


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """Faz upload de arquivo para contexto do agente."""
    
    # Verificar tipo
    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo não permitido: {file.content_type}. Permitidos: CSV, Excel, TXT, Markdown, Word, PNG, JPEG"
        )
    
    # Ler conteúdo
    conteudo = await file.read()
    
    # Limite de 10MB
    if len(conteudo) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máx 10MB)")
    
    # Extrair texto para contexto
    texto_extraido = extrair_texto_arquivo(conteudo, file.content_type, file.filename)
    
    # Salvar upload
    upload_id = str(uuid4())
    UPLOADS[upload_id] = {
        "id": upload_id,
        "session_id": session_id,
        "nome": file.filename,
        "tipo": ALLOWED_UPLOAD_TYPES[file.content_type],
        "mime_type": file.content_type,
        "conteudo": conteudo,
        "texto_extraido": texto_extraido,
        "tamanho": len(conteudo),
        "created_at": datetime.now()
    }
    
    # Adicionar à sessão
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            "id": session_id,
            "titulo": "Nova Conversa",
            "messages": [],
            "artifacts": [],
            "uploads": [],
            "created_at": datetime.now()
        }
    
    if "uploads" not in SESSIONS[session_id]:
        SESSIONS[session_id]["uploads"] = []
    
    SESSIONS[session_id]["uploads"].append(upload_id)
    
    logger.info(f"Upload: {file.filename} ({len(conteudo)} bytes)")
    
    return UploadResponse(
        id=upload_id,
        nome=file.filename,
        tipo=ALLOWED_UPLOAD_TYPES[file.content_type],
        tamanho=len(conteudo)
    )


@router.get("/uploads")
async def list_uploads(session_id: str):
    """Lista uploads de uma sessão."""
    if session_id not in SESSIONS:
        return []
    
    upload_ids = SESSIONS[session_id].get("uploads", [])
    uploads = [UPLOADS[uid] for uid in upload_ids if uid in UPLOADS]
    
    return [
        {
            "id": u["id"],
            "nome": u["nome"],
            "tipo": u["tipo"],
            "tamanho": u["tamanho"],
            "createdAt": u["created_at"].isoformat()
        }
        for u in uploads
    ]


@router.delete("/uploads/{upload_id}")
async def delete_upload(upload_id: str):
    """Exclui um upload."""
    if upload_id in UPLOADS:
        session_id = UPLOADS[upload_id].get("session_id")
        if session_id and session_id in SESSIONS:
            SESSIONS[session_id]["uploads"] = [
                u for u in SESSIONS[session_id].get("uploads", []) if u != upload_id
            ]
        del UPLOADS[upload_id]
    return {"message": "Upload excluído"}


# ============================================================================
# ENDPOINTS DE ARTEFATOS
# ============================================================================

@router.get("/artifacts", response_model=List[ArtifactResponse])
async def list_artifacts(session_id: Optional[str] = None):
    """Lista artefatos de uma sessão."""
    if session_id and session_id in SESSIONS:
        art_ids = SESSIONS[session_id].get("artifacts", [])
        arts = [ARTIFACTS[aid] for aid in art_ids if aid in ARTIFACTS]
    else:
        arts = list(ARTIFACTS.values())
    
    return [
        ArtifactResponse(
            id=a["id"],
            tipo=a["tipo"],
            nome=a["nome"],
            descricao=a.get("descricao"),
            mimeType=a["mime_type"],
            tamanho=a["tamanho"],
            createdAt=a["created_at"].isoformat(),
            temVersoes=bool(a.get("conteudo_light"))
        )
        for a in arts
    ]


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str, versao: str = Query("dark", pattern="^(dark|light)$")):
    """Obtém conteúdo de um artefato para visualização."""
    if artifact_id not in ARTIFACTS:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    
    art = ARTIFACTS[artifact_id]
    
    # Selecionar versão apropriada
    if versao == "light" and art.get("conteudo_light"):
        conteudo = art["conteudo_light"]
    else:
        conteudo = art["conteudo"]
    
    return StreamingResponse(
        io.BytesIO(conteudo),
        media_type=art["mime_type"],
        headers={
            "Content-Disposition": f'inline; filename="{art["nome"]}"'
        }
    )


@router.get("/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: str, versao: str = Query("dark", pattern="^(dark|light)$")):
    """Download de um artefato."""
    if artifact_id not in ARTIFACTS:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    
    art = ARTIFACTS[artifact_id]
    
    # Adicionar sufixo para versão light
    nome = art["nome"]
    if versao == "light" and art.get("conteudo_light"):
        conteudo = art["conteudo_light"]
        nome_base, ext = nome.rsplit(".", 1) if "." in nome else (nome, "")
        nome = f"{nome_base}_impressao.{ext}" if ext else f"{nome}_impressao"
    else:
        conteudo = art["conteudo"]
    
    return StreamingResponse(
        io.BytesIO(conteudo),
        media_type=art["mime_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{nome}"'
        }
    )


@router.delete("/artifacts/{artifact_id}")
async def delete_artifact(artifact_id: str):
    """Exclui um artefato."""
    if artifact_id not in ARTIFACTS:
        raise HTTPException(status_code=404, detail="Artefato não encontrado")
    
    art = ARTIFACTS[artifact_id]
    session_id = art.get("session_id")
    
    # Remover da sessão
    if session_id and session_id in SESSIONS:
        SESSIONS[session_id]["artifacts"] = [
            a for a in SESSIONS[session_id].get("artifacts", []) if a != artifact_id
        ]
    
    del ARTIFACTS[artifact_id]
    
    return {"message": "Artefato excluído"}


# ============================================================================
# ENDPOINTS DE FERRAMENTAS
# ============================================================================

TOOLS = [
    {"name": "gerar_grafico", "description": "Gera gráficos (linha, barra, pizza, donut, área, dispersão, heatmap, boxplot, histograma)"},
    {"name": "gerar_excel", "description": "Gera planilhas Excel formatadas"},
    {"name": "gerar_relatorio_pdf", "description": "Gera relatórios PDF profissionais"},
    {"name": "gerar_apresentacao", "description": "Gera apresentações PowerPoint"},
    {"name": "gerar_documento_word", "description": "Gera documentos Word"},
    {"name": "gerar_markdown", "description": "Gera documentos Markdown"},
    {"name": "consultar_dados", "description": "Consulta dados (ECL, PRINAD, Propensão)"},
    {"name": "pesquisar_web", "description": "Pesquisa informações na web"},
]


@router.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    """Lista ferramentas disponíveis."""
    return [ToolInfo(**t) for t in TOOLS]


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check."""
    return {
        "status": "ok",
        "mode": "demo",
        "artifacts_count": len(ARTIFACTS),
        "sessions_count": len(SESSIONS)
    }


__all__ = ["router"]
