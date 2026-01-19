"""
File Search Hybrid - A modern RAG implementation using PostgreSQL + pgvector
Inspired by Google Gemini File Search with hybrid search and reranking.

Features:
- Hybrid Search: Combines vector search (pgvector) + Full-Text Search (PostgreSQL)
- Reciprocal Rank Fusion (RRF) for combining search results
- FlashRank reranking for improved relevance
- Smart chunking with overlap for better context
- Multi-format document support (PDF, DOCX, TXT, MD, JSON, code)
- Grounding with citations for traceability
"""

import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)


@dataclass
class FileSearchConfig:
    """Central configuration for File Search Hybrid system."""
    
    # Embedding settings
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    embedding_dimension: int = 768
    
    # Chunking settings
    chunk_size: int = 1500  # tokens
    chunk_overlap: int = 200  # tokens
    
    # Search settings
    top_k: int = 20  # Initial retrieval count
    final_k: int = 5  # Final results after reranking
    rrf_k: int = 60  # RRF constant (typically 60)
    
    # Reranking settings
    rerank_model: str = "ms-marco-MiniLM-L-12-v2"
    use_rerank: bool = True
    rerank_threshold: float = 0.1  # Minimum score to include
    
    # Database settings
    db_host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    db_port: str = field(default_factory=lambda: os.getenv("POSTGRES_PORT", "5432"))
    db_name: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "eao_db"))
    db_user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    db_password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "postgres"))
    connect_timeout: int = field(default_factory=lambda: int(os.getenv("FILE_SEARCH_CONNECT_TIMEOUT", "7")))
    statement_timeout_ms: int = field(default_factory=lambda: int(os.getenv("FILE_SEARCH_STATEMENT_TIMEOUT_MS", "6000")))
    
    @classmethod
    def from_env(cls) -> "FileSearchConfig":
        """Create configuration from environment variables."""
        return cls(
            embedding_model=os.getenv(
                "FILE_SEARCH_EMBEDDING_MODEL",
                "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
            ),
            chunk_size=int(os.getenv("FILE_SEARCH_CHUNK_SIZE", "1500")),
            chunk_overlap=int(os.getenv("FILE_SEARCH_CHUNK_OVERLAP", "200")),
            rerank_model=os.getenv("FILE_SEARCH_RERANK_MODEL", "ms-marco-MiniLM-L-12-v2"),
        )


class DocumentLoader:
    """Universal document loader supporting multiple formats."""
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'pdf',
        '.txt': 'text',
        '.md': 'markdown',
        '.json': 'json',
        '.docx': 'docx',
        '.py': 'code',
        '.js': 'code',
        '.ts': 'code',
        '.java': 'code',
        '.go': 'code',
        '.rs': 'code',
        '.cpp': 'code',
        '.c': 'code',
        '.h': 'code',
        '.html': 'code',
        '.css': 'code',
        '.sql': 'code',
        '.yaml': 'code',
        '.yml': 'code',
        '.xml': 'code',
    }
    
    @classmethod
    def load(cls, file_path: str) -> Dict[str, Any]:
        """
        Load a document from file path.
        
        Returns:
            Dict with 'content', 'metadata', and 'source_file'
        """
        ext = os.path.splitext(file_path)[1].lower()
        doc_type = cls.SUPPORTED_EXTENSIONS.get(ext, 'text')
        
        content = ""
        metadata = {
            "source_file": os.path.basename(file_path),
            "file_type": doc_type,
            "file_extension": ext,
            "loaded_at": datetime.utcnow().isoformat(),
        }
        
        try:
            if doc_type == 'pdf':
                content = cls._load_pdf(file_path)
            elif doc_type == 'docx':
                content = cls._load_docx(file_path)
            elif doc_type == 'json':
                content = cls._load_json(file_path)
            else:
                content = cls._load_text(file_path)
                
            metadata["char_count"] = len(content)
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            raise
            
        return {
            "content": content,
            "metadata": metadata,
            "source_file": file_path
        }
    
    @staticmethod
    def _load_pdf(file_path: str) -> str:
        """Load PDF document."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            return "\n\n".join(text_parts)
        except ImportError:
            logger.warning("pypdf not installed, falling back to langchain loader")
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            return "\n\n".join([doc.page_content for doc in docs])
    
    @staticmethod
    def _load_docx(file_path: str) -> str:
        """Load DOCX document."""
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n\n".join(paragraphs)
        except ImportError:
            logger.error("python-docx not installed")
            raise ImportError("python-docx is required for DOCX files. Install with: pip install python-docx")
    
    @staticmethod
    def _load_json(file_path: str) -> str:
        """Load JSON document as formatted text."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _load_text(file_path: str) -> str:
        """Load text-based document."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


class SmartChunker:
    """Intelligent text chunking with semantic overlap."""
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._tokenizer = None
    
    @property
    def tokenizer(self):
        """Lazy load tokenizer."""
        if self._tokenizer is None:
            try:
                import tiktoken
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                logger.warning("tiktoken not installed, using character-based chunking")
                self._tokenizer = None
        return self._tokenizer
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        # Fallback: approximate tokens as words
        return len(text.split())
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks with overlap.
        
        Returns:
            List of dicts with 'content', 'token_count', 'chunk_index', 'metadata'
        """
        if not text or not text.strip():
            return []
        
        # Split by paragraphs first to maintain semantic boundaries
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            
            # If single paragraph exceeds chunk size, split it
            if para_tokens > self.chunk_size:
                # Flush current chunk first
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append({
                        'content': chunk_text,
                        'token_count': self.count_tokens(chunk_text),
                        'chunk_index': len(chunks),
                        'metadata': metadata or {}
                    })
                    current_chunk = []
                    current_tokens = 0
                
                # Split large paragraph by sentences
                sentences = self._split_into_sentences(para)
                for sentence in sentences:
                    sent_tokens = self.count_tokens(sentence)
                    if current_tokens + sent_tokens > self.chunk_size and current_chunk:
                        chunk_text = ' '.join(current_chunk)
                        chunks.append({
                            'content': chunk_text,
                            'token_count': self.count_tokens(chunk_text),
                            'chunk_index': len(chunks),
                            'metadata': metadata or {}
                        })
                        # Keep overlap
                        overlap_text = ' '.join(current_chunk[-2:]) if len(current_chunk) > 2 else ' '.join(current_chunk)
                        current_chunk = [overlap_text] if overlap_text else []
                        current_tokens = self.count_tokens(overlap_text) if overlap_text else 0
                    
                    current_chunk.append(sentence)
                    current_tokens += sent_tokens
                continue
            
            # Check if adding this paragraph exceeds chunk size
            if current_tokens + para_tokens > self.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'token_count': self.count_tokens(chunk_text),
                    'chunk_index': len(chunks),
                    'metadata': metadata or {}
                })
                
                # Keep last paragraph(s) for overlap
                overlap_paras = []
                overlap_tokens = 0
                for p in reversed(current_chunk):
                    p_tokens = self.count_tokens(p)
                    if overlap_tokens + p_tokens <= self.chunk_overlap:
                        overlap_paras.insert(0, p)
                        overlap_tokens += p_tokens
                    else:
                        break
                
                current_chunk = overlap_paras
                current_tokens = overlap_tokens
            
            current_chunk.append(para)
            current_tokens += para_tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'content': chunk_text,
                'token_count': self.count_tokens(chunk_text),
                'chunk_index': len(chunks),
                'metadata': metadata or {}
            })
        
        return chunks
    
    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        import re
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


class EmbeddingModel:
    """Wrapper for sentence-transformers embeddings with multilingual support and Hugging Face integration."""
    
    def __init__(
        self, 
        model_name: str = "intfloat/multilingual-e5-large",
        huggingface_token: Optional[str] = None
    ):
        self.model_name = model_name
        self.huggingface_token = huggingface_token
        self._model = None
        self._dimension = None
    
    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                
                # Load model with Hugging Face token if provided
                if self.huggingface_token:
                    self._model = SentenceTransformer(
                        self.model_name,
                        use_auth_token=self.huggingface_token
                    )
                else:
                    self._model = SentenceTransformer(self.model_name)
                
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Embedding model loaded. Dimension: {self._dimension}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required. Install with: pip install sentence-transformers"
                )
        return self._model
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            _ = self.model  # Initialize model to get dimension
        return self._dimension or 768
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        embedding = self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True)
        return embedding[0].tolist()


class Reranker:
    """FlashRank-based reranker for improved search relevance."""
    
    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2"):
        self.model_name = model_name
        self._ranker = None
    
    @property
    def ranker(self):
        """Lazy load the reranker."""
        if self._ranker is None:
            try:
                from flashrank import Ranker, RerankRequest
                self._ranker = Ranker(model_name=self.model_name)
                logger.info(f"Reranker loaded: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "flashrank is required for reranking. Install with: pip install flashrank"
                )
        return self._ranker
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on query relevance.
        
        Args:
            query: Search query
            documents: List of documents with 'content' field
            top_k: Number of top results to return
            threshold: Minimum score threshold
            
        Returns:
            Reranked documents with 'rerank_score' added
        """
        if not documents:
            return []
        
        try:
            from flashrank import RerankRequest
            
            # Prepare passages for reranking
            passages = [{"id": i, "text": doc.get("content", "")} for i, doc in enumerate(documents)]
            
            rerank_request = RerankRequest(query=query, passages=passages)
            results = self.ranker.rerank(rerank_request)
            
            # Map scores back to documents
            reranked = []
            for result in results:
                doc_idx = result.get("id", 0)
                if doc_idx < len(documents):
                    doc = documents[doc_idx].copy()
                    doc["rerank_score"] = result.get("score", 0.0)
                    if doc["rerank_score"] >= threshold:
                        reranked.append(doc)
            
            # Sort by rerank score and limit
            reranked.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return original documents
            return documents[:top_k]


class PostgresVectorStore:
    """PostgreSQL vector store with pgvector for hybrid search."""
    
    def __init__(self, config: FileSearchConfig):
        self.config = config
        self._conn = None
    
    def get_connection(self):
        """Get database connection."""
        if self._conn is None or self._conn.closed:
            try:
                import psycopg
                self._conn = psycopg.connect(
                    host=self.config.db_host,
                    port=self.config.db_port,
                    dbname=self.config.db_name,
                    user=self.config.db_user,
                    password=self.config.db_password,
                    sslmode="require",
                    connect_timeout=self.config.connect_timeout,
                )
                try:
                    with self._conn.cursor() as cur:
                        cur.execute(f"SET statement_timeout = {self.config.statement_timeout_ms}")
                        self._conn.commit()
                except Exception:
                    pass
            except ImportError:
                # Fallback to psycopg2
                try:
                    import psycopg2
                    self._conn = psycopg2.connect(
                        host=self.config.db_host,
                        port=self.config.db_port,
                        dbname=self.config.db_name,
                        user=self.config.db_user,
                        password=self.config.db_password,
                        sslmode="require",
                        connect_timeout=self.config.connect_timeout,
                    )
                    try:
                        with self._conn.cursor() as cur:
                            cur.execute(f"SET statement_timeout = {self.config.statement_timeout_ms}")
                            self._conn.commit()
                    except Exception:
                        pass
                except ImportError:
                    raise ImportError(
                        "Neither psycopg nor psycopg2 is installed. "
                        "Install with: pip install 'psycopg[binary]>=3.1.0' or pip install psycopg2-binary"
                    )
        return self._conn
    
    def close(self):
        """Close database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None
    
    def ensure_tables(self):
        """Create tables if they don't exist."""
        conn = self.get_connection()
        with conn.cursor() as cur:
            # Enable extensions
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            
            # Create table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id INTEGER,
                    tenant_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding VECTOR(768),
                    source_file TEXT,
                    chunk_index INTEGER,
                    token_count INTEGER,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Add tsvector column for full-text search if not exists
            cur.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'document_chunks' 
                        AND column_name = 'content_tsv'
                    ) THEN
                        ALTER TABLE public.document_chunks 
                        ADD COLUMN content_tsv TSVECTOR 
                        GENERATED ALWAYS AS (to_tsvector('portuguese', content)) STORED;
                    END IF;
                END $$;
            """)
            
            # Create indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_tenant 
                ON public.document_chunks(tenant_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
                ON public.document_chunks 
                USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_tsv 
                ON public.document_chunks 
                USING GIN(content_tsv)
            """)
            
            conn.commit()
            logger.info("Database tables and indexes created successfully")
    
    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        document_id: Optional[int],
        tenant_id: str,
        source_file: str
    ) -> List[str]:
        """
        Add chunks with embeddings to the store.
        
        Returns:
            List of chunk IDs
        """
        conn = self.get_connection()
        chunk_ids = []
        
        with conn.cursor() as cur:
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Generate unique ID
                chunk_id = hashlib.md5(
                    f"{tenant_id}:{source_file}:{chunk.get('chunk_index', i)}:{chunk['content'][:100]}".encode()
                ).hexdigest()
                
                # Convert embedding to PostgreSQL vector format
                embedding_str = f"[{','.join(map(str, embedding))}]"
                
                cur.execute("""
                    INSERT INTO public.document_chunks 
                    (id, document_id, tenant_id, content, embedding, source_file, chunk_index, token_count, metadata)
                    VALUES (%s, %s, %s, %s, %s::vector, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                """, (
                    chunk_id,
                    document_id,
                    tenant_id,
                    chunk['content'],
                    embedding_str,
                    source_file,
                    chunk.get('chunk_index', i),
                    chunk.get('token_count', 0),
                    json.dumps(chunk.get('metadata', {}))
                ))
                chunk_ids.append(chunk_id)
            
            conn.commit()
        
        return chunk_ids
    
    def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        tenant_id: str,
        top_k: int = 20,
        rrf_k: int = 60,
        exact_match: bool = False,
        source_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector and full-text search with RRF.
        
        Args:
            query: Search query text
            query_embedding: Query embedding vector
            tenant_id: Tenant ID for filtering
            top_k: Number of results to return
            rrf_k: RRF constant (typically 60)
            
        Returns:
            List of search results with scores
        """
        conn = self.get_connection()
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        with conn.cursor() as cur:
            # Hybrid search with RRF
            text_fn = "phraseto_tsquery('portuguese', %s)" if exact_match else "plainto_tsquery('portuguese', %s)"
            src_cond_vec = " AND source_file = ANY(%s)" if source_filter else ""
            src_cond_txt = " AND source_file = ANY(%s)" if source_filter else ""
            sql = f"""
                WITH vector_search AS (
                    SELECT 
                        id,
                        content,
                        source_file,
                        chunk_index,
                        token_count,
                        metadata,
                        1 - (embedding <=> %s::vector) AS vector_score,
                        ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) AS vector_rank
                    FROM public.document_chunks
                    WHERE tenant_id = %s{src_cond_vec}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                ),
                text_search AS (
                    SELECT 
                        id,
                        content,
                        source_file,
                        chunk_index,
                        token_count,
                        metadata,
                        ts_rank_cd(content_tsv, {text_fn}) AS text_score,
                        ROW_NUMBER() OVER (
                            ORDER BY ts_rank_cd(content_tsv, {text_fn}) DESC
                        ) AS text_rank
                    FROM public.document_chunks
                    WHERE tenant_id = %s{src_cond_txt}
                    AND content_tsv @@ {text_fn}
                    LIMIT %s
                ),
                combined AS (
                    SELECT 
                        COALESCE(v.id, t.id) AS id,
                        COALESCE(v.content, t.content) AS content,
                        COALESCE(v.source_file, t.source_file) AS source_file,
                        COALESCE(v.chunk_index, t.chunk_index) AS chunk_index,
                        COALESCE(v.token_count, t.token_count) AS token_count,
                        COALESCE(v.metadata, t.metadata) AS metadata,
                        COALESCE(v.vector_score, 0) AS vector_score,
                        COALESCE(t.text_score, 0) AS text_score,
                        (
                            COALESCE(1.0 / (%s + v.vector_rank), 0) +
                            COALESCE(1.0 / (%s + t.text_rank), 0)
                        ) AS rrf_score
                    FROM vector_search v
                    FULL OUTER JOIN text_search t ON v.id = t.id
                )
                SELECT id, content, source_file, chunk_index, token_count, metadata, 
                       vector_score, text_score, rrf_score
                FROM combined
                ORDER BY rrf_score DESC
                LIMIT %s
            """
            params: List[Any] = [
                embedding_str, embedding_str, tenant_id
            ]
            if source_filter:
                params.append(source_filter)
            params += [embedding_str, top_k]
            # text_search params (query used twice)
            params += [query, query, tenant_id]
            if source_filter:
                params.append(source_filter)
            params += [query, top_k, rrf_k, rrf_k, top_k]
            cur.execute(sql, tuple(params))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "id": row[0],
                    "content": row[1],
                    "source_file": row[2],
                    "chunk_index": row[3],
                    "token_count": row[4],
                    "metadata": row[5] if isinstance(row[5], dict) else json.loads(row[5] or "{}"),
                    "vector_score": float(row[6]) if row[6] else 0.0,
                    "text_score": float(row[7]) if row[7] else 0.0,
                    "rrf_score": float(row[8]) if row[8] else 0.0,
                })
        
        return results
    
    def delete_by_document(self, document_id: int, tenant_id: str) -> int:
        """Delete all chunks for a document."""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM public.document_chunks
                WHERE document_id = %s AND tenant_id = %s
            """, (document_id, tenant_id))
            deleted = cur.rowcount
            conn.commit()
        return deleted
    
    def delete_by_source(self, source_file: str, tenant_id: str) -> int:
        """Delete all chunks for a source file."""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM public.document_chunks
                WHERE source_file = %s AND tenant_id = %s
            """, (source_file, tenant_id))
            deleted = cur.rowcount
            conn.commit()
        return deleted
    
    def get_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        conn = self.get_connection()
        with conn.cursor() as cur:
            if tenant_id:
                cur.execute("""
                    SELECT 
                        COUNT(*) as chunk_count,
                        COUNT(DISTINCT source_file) as document_count,
                        SUM(token_count) as total_tokens,
                        COUNT(DISTINCT tenant_id) as tenant_count
                    FROM public.document_chunks
                    WHERE tenant_id = %s
                """, (tenant_id,))
            else:
                cur.execute("""
                    SELECT 
                        COUNT(*) as chunk_count,
                        COUNT(DISTINCT source_file) as document_count,
                        SUM(token_count) as total_tokens,
                        COUNT(DISTINCT tenant_id) as tenant_count
                    FROM public.document_chunks
                """)
            
            row = cur.fetchone()
            return {
                "chunk_count": row[0] or 0,
                "document_count": row[1] or 0,
                "total_tokens": row[2] or 0,
                "tenant_count": row[3] or 0
            }


class FileSearchHybrid:
    """
    Main orchestrator class for the File Search Hybrid system.
    
    This class combines all components to provide a complete
    hybrid search solution with intelligent chunking and reranking.
    """
    
    def __init__(self, config: Optional[FileSearchConfig] = None, huggingface_token: Optional[str] = None):
        self.config = config or FileSearchConfig.from_env()
        self.chunker = SmartChunker(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        # Pass Hugging Face token to embedding model
        self.embedding_model = EmbeddingModel(
            self.config.embedding_model,
            huggingface_token=huggingface_token
        )
        self.reranker = Reranker(self.config.rerank_model) if self.config.use_rerank else None
        self.vector_store = PostgresVectorStore(self.config)
        
        pass
    
    def ingest_document(
        self,
        file_path: str,
        tenant_id: str,
        document_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a document into the vector store.
        
        Args:
            file_path: Path to the document file
            tenant_id: Tenant identifier for multi-tenancy
            document_id: Optional database document ID
            metadata: Additional metadata to store
            
        Returns:
            Dict with ingestion results
        """
        logger.info(f"Ingesting document: {file_path} for tenant: {tenant_id}")
        
        # 1. Load document
        doc = DocumentLoader.load(file_path)
        doc_metadata = doc['metadata']
        if metadata:
            doc_metadata.update(metadata)
        
        # 2. Chunk document
        chunks = self.chunker.chunk(doc['content'], doc_metadata)
        logger.info(f"Created {len(chunks)} chunks from document")
        
        if not chunks:
            return {
                "status": "error",
                "message": "No content to index",
                "chunks_created": 0
            }
        
        # 3. Generate embeddings
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self.embedding_model.embed(texts)
        
        # 4. Store in vector store
        source_file = os.path.basename(file_path)
        chunk_ids = self.vector_store.add_chunks(
            chunks=chunks,
            embeddings=embeddings,
            document_id=document_id,
            tenant_id=tenant_id,
            source_file=source_file
        )
        
        return {
            "status": "success",
            "source_file": source_file,
            "chunks_created": len(chunk_ids),
            "chunk_ids": chunk_ids,
            "total_tokens": sum(c.get('token_count', 0) for c in chunks)
        }
    
    def search(
        self,
        query: str,
        tenant_id: str,
        use_rerank: Optional[bool] = None,
        top_k: Optional[int] = None,
        final_k: Optional[int] = None,
        exact_match: Optional[bool] = None,
        source_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using hybrid search + reranking.
        
        Args:
            query: Search query
            tenant_id: Tenant identifier
            use_rerank: Override config setting for reranking
            top_k: Override initial retrieval count
            final_k: Override final result count
            
        Returns:
            List of relevant document chunks with scores
        """
        top_k = top_k or self.config.top_k
        final_k = final_k or self.config.final_k
        use_rerank = use_rerank if use_rerank is not None else self.config.use_rerank
        
        # 1. Generate query embedding
        query_embedding = self.embedding_model.embed_query(query)
        
        # 2. Hybrid search
        try:
            results = self.vector_store.hybrid_search(
                query=query,
                query_embedding=query_embedding,
                tenant_id=tenant_id,
                top_k=top_k,
                rrf_k=self.config.rrf_k,
                exact_match=bool(exact_match),
                source_filter=source_filter,
            )
        except Exception as e:
            logger.warning(f"Vector search unavailable, falling back to Supabase HTTP: {e}")
            results = self._fallback_supabase_search(query, query_embedding, tenant_id, top_k)
        
        if not results:
            return []
        
        # 3. Rerank if enabled
        if use_rerank and self.reranker:
            results = self.reranker.rerank(
                query=query,
                documents=results,
                top_k=final_k,
                threshold=self.config.rerank_threshold
            )
        else:
            results = results[:final_k]
        
        return results

    def _cosine(self, a: List[float], b: List[float]) -> float:
        try:
            import math
            dot = sum(x*y for x, y in zip(a, b))
            na = math.sqrt(sum(x*x for x in a))
            nb = math.sqrt(sum(y*y for y in b))
            if na == 0 or nb == 0:
                return 0.0
            return dot / (na * nb)
        except Exception:
            return 0.0

    def _fallback_supabase_search(self, query: str, query_embedding: List[float], tenant_id: str, top_k: int) -> List[Dict[str, Any]]:
        try:
            client = get_supabase()
            # Fetch a reasonable candidate set via text match; if none, fetch some recent chunks
            q = client.schema("public").from_("document_chunks").select("id,content,source_file,chunk_index,token_count,metadata,embedding").eq("tenant_id", tenant_id).ilike("content", f"%{query}%").limit(max(top_k*20, 50))
            data = q.execute().data or []
            if not data:
                data = client.schema("public").from_("document_chunks").select("id,content,source_file,chunk_index,token_count,metadata,embedding").eq("tenant_id", tenant_id).limit(max(top_k*20, 50)).execute().data or []
            scored: List[Dict[str, Any]] = []
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
                score = self._cosine(query_embedding, list(emb))
                scored.append({
                    "id": row.get("id"),
                    "content": row.get("content") or "",
                    "source_file": row.get("source_file") or "unknown",
                    "chunk_index": row.get("chunk_index") or 0,
                    "token_count": row.get("token_count") or 0,
                    "metadata": row.get("metadata") or {},
                    "rrf_score": float(score),
                })
            scored.sort(key=lambda x: x.get("rrf_score", 0.0), reverse=True)
            return scored[:top_k]
        except Exception as e:
            logger.error(f"Supabase fallback failed: {e}")
            return []
    
    def generate_context(
        self,
        results: List[Dict[str, Any]],
        max_tokens: int = 4000
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate context string from search results for LLM.
        
        Args:
            results: Search results from search()
            max_tokens: Maximum tokens for context
            
        Returns:
            Tuple of (context_string, grounding_metadata)
        """
        if not results:
            return "", []
        
        context_parts = []
        grounding_metadata = []
        total_tokens = 0
        
        for i, result in enumerate(results):
            chunk_tokens = result.get('token_count', 0)
            if chunk_tokens == 0:
                chunk_tokens = self.chunker.count_tokens(result.get('content', ''))
            
            if total_tokens + chunk_tokens > max_tokens:
                break
            
            source = result.get('source_file', f'Source {i+1}')
            content = result.get('content', '')
            
            context_parts.append(f"[{i+1}] {source}:\n{content}")
            
            try:
                score_val = float(result.get('rerank_score', result.get('rrf_score', 0)) or 0.0)
            except Exception:
                score_val = 0.0
            try:
                chunk_idx = int(result.get('chunk_index', 0) or 0)
            except Exception:
                chunk_idx = 0
            grounding_metadata.append({
                "citation_id": i + 1,
                "source": source,
                "chunk_index": chunk_idx,
                "score": score_val,
                "preview": content[:200] + "..." if len(content) > 200 else content
            })
            
            total_tokens += chunk_tokens
        
        context = "\n\n".join(context_parts)
        return context, grounding_metadata
    
    def delete_document(self, source_file: str, tenant_id: str) -> int:
        """Delete a document from the store."""
        return self.vector_store.delete_by_source(source_file, tenant_id)
    
    def get_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get store statistics."""
        return self.vector_store.get_stats(tenant_id)
    
    def close(self):
        """Clean up resources."""
        self.vector_store.close()


# Factory function for easy initialization
def create_file_search(
    use_file_search: bool = True,
    config: Optional[FileSearchConfig] = None
) -> Optional[FileSearchHybrid]:
    """
    Factory function to create FileSearchHybrid instance.
    
    Args:
        use_file_search: If False, returns None (for ChromaDB fallback)
        config: Optional configuration
        
    Returns:
        FileSearchHybrid instance or None
    """
    if not use_file_search:
        return None
    
    enabled = os.getenv("FILE_SEARCH_ENABLED", "true").lower() == "true"
    if not enabled:
        return None
    
    return FileSearchHybrid(config)
