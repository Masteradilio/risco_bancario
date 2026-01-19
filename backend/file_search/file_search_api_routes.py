"""
File Search API Routes

Provides REST endpoints for the new File Search Hybrid system:
- Upload documents with intelligent chunking
- Hybrid search with reranking
- Statistics and management
"""

import os
import shutil
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Documento
from core.embeddings import get_embeddings
from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# =============================================================================
# Pydantic Models
# =============================================================================

class SearchRequest(BaseModel):
    """Request model for hybrid search."""
    query: str = Field(..., min_length=1, description="Search query text")
    tenant_id: str = Field(default="default", description="Tenant identifier")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    use_rerank: bool = Field(default=True, description="Whether to use reranking")
    exact_match: bool = Field(default=False, description="Somente termo exato no conteúdo")
    source_filter: Optional[List[str]] = Field(default=None, description="Filtrar por arquivos/fonte")


class SearchResult(BaseModel):
    """Single search result."""
    content: str
    source_file: str
    chunk_index: int
    score: float
    preview: str


class SearchResponse(BaseModel):
    """Response model for hybrid search."""
    query: str
    results: List[SearchResult]
    context: str
    grounding_metadata: List[Dict[str, Any]]
    total_results: int
    search_type: str = "hybrid"


class UploadResponse(BaseModel):
    """Response model for document upload."""
    message: str
    document_id: Optional[int]
    source_file: str
    chunks_created: int
    total_tokens: int
    backend: str = "file_search"


class StatsResponse(BaseModel):
    """Response model for store statistics."""
    chunk_count: int
    document_count: int
    total_tokens: int
    tenant_count: int
    backend: str = "file_search"


# =============================================================================
# Helper Functions
# =============================================================================

def get_file_search():
    """Get File Search implementation."""
    mode = os.getenv("FILE_SEARCH_DIRECT_PG", "false").lower()
    if mode == "true":
        try:
            from core.file_search import FileSearchHybrid, FileSearchConfig
            from core.config import settings
            config = FileSearchConfig.from_env()
            return FileSearchHybrid(config, huggingface_token=settings.HUGGINGFACE_TOKEN)
        except Exception as e:
            logger.error(f"Failed to initialize File Search: {e}")
            raise HTTPException(status_code=503, detail=f"File Search service unavailable: {str(e)}")
    class HttpFileSearch:
        def __init__(self):
            self.client = get_supabase()
            self.embedder = get_embeddings()
        def search(self, query: str, tenant_id: str, use_rerank: bool, final_k: int, exact_match: bool = False, source_filter: Optional[List[str]] = None):
            try:
                def expand_terms(qs: str) -> list[str]:
                    base = (qs or "").lower().strip()
                    syn = {
                        "conduta": ["conduta", "código de conduta", "codigo de conduta", "ética", "comportamento", "normas", "política", "regulamento"],
                        "ética": ["ética", "etica", "conduta"],
                        "compliance": ["compliance", "conformidade", "regras", "políticas", "regulamentos"],
                        "disciplina": ["disciplina", "regras", "comportamento"],
                        "política": ["política", "politica", "norma", "regra", "diretriz"],
                        "regulamento": ["regulamento", "normas", "políticas"],
                        "segurança": ["segurança", "security", "proteção", "guardrails"],
                        "privacidade": ["privacidade", "lgpd", "gdpr", "dados pessoais"],
                        "lgpd": ["lgpd", "lei geral de proteção de dados", "privacidade"],
                        "gdpr": ["gdpr", "general data protection regulation", "privacidade"],
                        "guardrail": ["guardrail", "guardrails", "proteções", "validações"],
                        "ferramenta": ["ferramenta", "tool", "tools", "mcp", "api"],
                        # English mappings
                        "conduct": ["conduct", "code of conduct", "ethics", "behavior", "norms", "policy", "rules"],
                        "ethics": ["ethics", "ethical", "code of ethics", "conduct"],
                        "compliance_en": ["compliance", "conformance", "policies", "regulations", "standards"],
                        "discipline_en": ["discipline", "rules", "behavior"],
                        "policy": ["policy", "guideline", "rule", "standard", "directive"],
                        "regulation": ["regulation", "regulations", "rules"],
                        "security": ["security", "protection", "guardrails", "safety"],
                        "privacy": ["privacy", "gdpr", "personal data", "data protection"],
                        "gdpr_en": ["gdpr", "general data protection regulation", "privacy"],
                        "guardrails": ["guardrail", "guardrails", "protections", "validations"],
                        "tool": ["tool", "tools", "mcp", "api"],
                    }
                    terms = set([base])
                    for key, arr in syn.items():
                        if key in base:
                            for a in arr:
                                terms.add(a)
                    # Remover vazios e normalizar
                    return [t for t in terms if t]
                terms = expand_terms(query)
                data = []
                for t in terms:
                    q = self.client.schema("public").from_("document_chunks").select("id,content,source_file,chunk_index,token_count,metadata,embedding").eq("tenant_id", tenant_id)
                    if source_filter:
                        try:
                            q = q.in_("source_file", source_filter)
                        except Exception:
                            pass
                    if exact_match:
                        q = q.ilike("content", f"%{query}%")
                    else:
                        q = q.ilike("content", f"%{t}%")
                    q = q.limit(max(final_k*10, 30))
                    part = q.execute().data or []
                    if part:
                        data.extend(part)
                if not data:
                    q = self.client.schema("public").from_("document_chunks").select("id,content,source_file,chunk_index,token_count,metadata,embedding").eq("tenant_id", tenant_id)
                    if source_filter:
                        try:
                            q = q.in_("source_file", source_filter)
                        except Exception:
                            pass
                    data = q.limit(max(final_k*20, 50)).execute().data or []
                qe = self.embedder.embed_query(query)
                def cos(a,b):
                    import math
                    da = sum(x*y for x,y in zip(a,b))
                    na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
                    return da/(na*nb) if na and nb else 0.0
                scored = []
                for row in data:
                    emb = row.get("embedding") or []
                    if isinstance(emb, str):
                        try:
                            import json as _json
                            emb = _json.loads(emb)
                        except Exception:
                            emb = []
                    if not isinstance(emb, (list, tuple)):
                        emb = []
                    content = row.get("content") or ""
                    # Text score: boost if exact match or any expanded term present
                    lc = content.lower()
                    if exact_match and (query.lower() in lc):
                        text_score = 0.95
                    elif any((t in lc) for t in terms):
                        text_score = 0.85
                    else:
                        text_score = 0.0
                    emb_score = cos(qe, list(emb)) if emb else 0.0
                    final_score = max(text_score, emb_score)
                    scored.append({
                        "content": row.get("content") or "",
                        "source_file": row.get("source_file") or "unknown",
                        "chunk_index": row.get("chunk_index") or 0,
                        "token_count": row.get("token_count") or 0,
                        "metadata": row.get("metadata") or {},
                        "rrf_score": final_score,
                    })
                # Se houve termos expandidos, prioriza textos que contém algum termo
                def contains_any(content: str) -> bool:
                    lc = (content or "").lower()
                    return any((t in lc) for t in terms)
                scored.sort(key=lambda x: (
                    1 if contains_any(x.get("content","")) else 0,
                    x.get("rrf_score", 0.0)
                ), reverse=True)
                return scored[:final_k]
            except Exception:
                return []
        def generate_context(self, results):
            parts = []; meta = []; total = 0
            for i,r in enumerate(results):
                tk = r.get("token_count",0)
                if total + tk > 4000:
                    break
                parts.append(f"[{i+1}] {r.get('source_file','unknown')}:\n{r.get('content','')}")
                meta.append({"citation_id": i+1, "source": r.get("source_file","unknown"), "chunk_index": r.get("chunk_index",0), "score": r.get("rrf_score",0.0), "preview": (r.get("content","")[:200] + ("..." if len(r.get("content",""))>200 else ""))})
                total += tk
            return "\n\n".join(parts), meta
        def get_stats(self, tenant_id=None):
            if tenant_id:
                res = self.client.schema("public").from_("document_chunks").select("source_file,token_count").eq("tenant_id", tenant_id).execute().data or []
            else:
                res = self.client.schema("public").from_("document_chunks").select("source_file,token_count").execute().data or []
            return {
                "chunk_count": len(res),
                "document_count": len({r.get("source_file") for r in res if r.get("source_file")}),
                "total_tokens": sum([(r.get("token_count") or 0) for r in res]),
                "tenant_count": 0,
            }
        def close(self):
            return None
    return HttpFileSearch()


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Form(default="default"),
    agent_id: Optional[int] = Form(default=None),
    db: Session = Depends(get_db)
):
    """
    Upload and index a document using File Search Hybrid.
    
    Supports: PDF, DOCX, TXT, MD, JSON, and code files.
    
    The document will be:
    1. Saved locally
    2. Chunked intelligently with overlap
    3. Embedded using multilingual model
    4. Stored in PostgreSQL with pgvector
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Get file size for storage limit check
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to beginning
    
    # Check storage limits
    from core.subscription_limits import check_storage_limit, update_storage_usage
    can_upload, message = check_storage_limit(db, tenant_id, file_size)
    if not can_upload:
        raise HTTPException(status_code=403, detail=message)
    
    # Get file extension
    ext = os.path.splitext(file.filename)[1].lower()
    supported_extensions = {
        '.pdf', '.txt', '.md', '.json', '.docx',
        '.py', '.js', '.ts', '.java', '.go', '.rs',
        '.cpp', '.c', '.h', '.html', '.css', '.sql',
        '.yaml', '.yml', '.xml'
    }
    
    if ext not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(sorted(supported_extensions))}"
        )
    
    file_search = None
    try:
        # 1. Save file locally
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Save metadata to database first
        new_doc = Documento(
            no_documento=file.filename,
            no_vector_db="file_search",
            cd_agente=agent_id,
            no_agente=str(agent_id) if agent_id else None,
            cd_vector=file.filename,
            dt_criacao=datetime.utcnow()
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        # 3. Index document with File Search
        file_search = get_file_search()
        result = file_search.ingest_document(
            file_path=file_path,
            tenant_id=tenant_id,
            document_id=new_doc.cd_documento,
            metadata={
                "agent_id": agent_id,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        )
        
        if result.get("status") == "error":
            # Rollback database entry
            db.delete(new_doc)
            db.commit()
            raise HTTPException(status_code=500, detail=result.get("message", "Ingestion failed"))
        
        # Update storage usage after successful upload
        update_storage_usage(db, tenant_id, file_size)
        
        return UploadResponse(
            message="Document uploaded and indexed successfully",
            document_id=new_doc.cd_documento,
            source_file=result.get("source_file", file.filename),
            chunks_created=result.get("chunks_created", 0),
            total_tokens=result.get("total_tokens", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file_search:
            file_search.close()


@router.post("/search", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest):
    """
    Perform hybrid search combining vector and full-text search.
    
    Uses Reciprocal Rank Fusion (RRF) to combine results and
    FlashRank for reranking to improve relevance.
    """
    file_search = None
    try:
        file_search = get_file_search()
        try:
            if hasattr(file_search, "vector_store") and hasattr(file_search.vector_store, "get_connection"):
                _ = file_search.vector_store.get_connection()
            else:
                _ = file_search.get_stats(request.tenant_id)
        except Exception:
            return SearchResponse(
                query=request.query,
                results=[],
                context="File Search indisponível (timeout de conexão)",
                grounding_metadata=[],
                total_results=0,
                search_type="unavailable"
            )
        # Perform search
        try:
            results = file_search.search(
                query=request.query,
                tenant_id=request.tenant_id,
                use_rerank=request.use_rerank,
                final_k=request.top_k,
                exact_match=request.exact_match,
                source_filter=request.source_filter
            )
        except TypeError:
            # Backward compatibility: retry without new parameters
            results = file_search.search(
                query=request.query,
                tenant_id=request.tenant_id,
                use_rerank=request.use_rerank,
                final_k=request.top_k,
            )
        
        # Generate context with grounding
        context, grounding_metadata = file_search.generate_context(results)
        
        # Format results
        formatted_results = []
        for r in results:
            content = r.get("content", "")
            score_raw = r.get("rerank_score", r.get("rrf_score", 0))
            try:
                score_val = round(float(score_raw or 0.0), 4)
            except Exception:
                score_val = 0.0
            try:
                chunk_idx = int(r.get("chunk_index", 0) or 0)
            except Exception:
                chunk_idx = 0
            formatted_results.append(SearchResult(
                content=content,
                source_file=r.get("source_file", "unknown"),
                chunk_index=chunk_idx,
                score=score_val,
                preview=content[:200] + "..." if len(content) > 200 else content
            ))
        
        return SearchResponse(
            query=request.query,
            results=formatted_results,
            context=context,
            grounding_metadata=grounding_metadata,
            total_results=len(formatted_results),
            search_type="hybrid_with_rerank" if request.use_rerank else "hybrid"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
        return SearchResponse(
            query=request.query,
            results=[],
            context="File Search indisponível (erro: " + str(e) + ")",
            grounding_metadata=[],
            total_results=0,
            search_type="unavailable"
        )
    finally:
        if file_search:
            file_search.close()


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    tenant_id: Optional[str] = Query(default=None, description="Filter by tenant ID")
):
    """
    Get statistics about the File Search vector store.
    
    Returns counts of chunks, documents, tokens, and tenants.
    """
    file_search = None
    try:
        file_search = get_file_search()
        stats = file_search.get_stats(tenant_id)
        
        return StatsResponse(
            chunk_count=stats.get("chunk_count", 0),
            document_count=stats.get("document_count", 0),
            total_tokens=stats.get("total_tokens", 0),
            tenant_count=stats.get("tenant_count", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file_search:
            file_search.close()


@router.delete("/{filename}")
async def delete_document(
    filename: str,
    tenant_id: str = Query(default="default"),
    db: Session = Depends(get_db)
):
    """
    Delete a document from the File Search store.
    
    Removes all chunks associated with the document.
    """
    file_search = None
    try:
        file_search = get_file_search()
        
        # Delete from vector store
        deleted_count = file_search.delete_document(filename, tenant_id)
        
        # Delete from database
        doc = db.query(Documento).filter(Documento.no_documento == filename).first()
        if doc:
            db.delete(doc)
            db.commit()
        
        # Delete file if exists
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "message": "Document deleted successfully",
            "filename": filename,
            "chunks_deleted": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file_search:
            file_search.close()


@router.get("/health")
async def health_check():
    """
    Check if File Search service is healthy.
    
    Verifies database connectivity and extension availability.
    """
    file_search = None
    try:
        file_search = get_file_search()
        stats = file_search.get_stats()
        mode = os.getenv("FILE_SEARCH_DIRECT_PG", "false").lower()
        backend = "postgresql_pgvector" if mode == "true" else "supabase_postgrest"
        return {
            "status": "healthy",
            "service": "file_search_hybrid",
            "backend": backend,
            "stats": stats
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "file_search_hybrid",
            "error": str(e)
        }
    finally:
        if file_search:
            file_search.close()
