# -*- coding: utf-8 -*-
"""
Script Standalone para Indexar Documentação no PostgreSQL/PGVector

Este script processa os documentos e os indexa diretamente no PostgreSQL
usando psycopg2 para conexão e sentence-transformers para embeddings.

Uso:
    python backend/scripts/index_docs_standalone.py
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Adicionar paths
script_dir = Path(__file__).parent
backend_path = script_dir.parent
project_root = backend_path.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURAÇÃO DO BANCO
# ============================================================================

DB_CONFIG = {
    "host": os.getenv("DATABASE_HOST", "localhost"),
    "port": int(os.getenv("DATABASE_PORT", "5432")),
    "dbname": os.getenv("DATABASE_NAME", "dbrisco"),
    "user": os.getenv("DATABASE_USER", "postgres"),
    "password": os.getenv("DATABASE_PASSWORD", "12345678"),
}

EMBEDDING_MODEL = os.getenv("FILE_SEARCH_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
EMBEDDING_DIM = int(os.getenv("FILE_SEARCH_EMBEDDING_DIMENSION", "768"))
CHUNK_SIZE = int(os.getenv("FILE_SEARCH_CHUNK_SIZE", "1500"))


# ============================================================================
# CLASSES AUXILIARES
# ============================================================================

class SimpleChunker:
    """Chunker simples para dividir texto em partes."""
    
    def __init__(self, chunk_size: int = 1500, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """Divide texto em chunks."""
        if not text or not text.strip():
            return []
        
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_len = 0
        
        for para in paragraphs:
            para_len = len(para.split())
            
            if current_len + para_len > self.chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'token_count': len(chunk_text.split()),
                    'chunk_index': len(chunks)
                })
                # Overlap: manter últimos parágrafos
                overlap_len = 0
                overlap_paras = []
                for p in reversed(current_chunk):
                    p_len = len(p.split())
                    if overlap_len + p_len <= self.overlap:
                        overlap_paras.insert(0, p)
                        overlap_len += p_len
                    else:
                        break
                current_chunk = overlap_paras
                current_len = overlap_len
            
            current_chunk.append(para)
            current_len += para_len
        
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'content': chunk_text,
                'token_count': len(chunk_text.split()),
                'chunk_index': len(chunks)
            })
        
        return chunks


class EmbeddingGenerator:
    """Gerador de embeddings usando sentence-transformers."""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        if self._model is None:
            logger.info(f"Carregando modelo de embeddings: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Modelo carregado. Dimensão: {self._model.get_sentence_embedding_dimension()}")
        return self._model
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para uma lista de textos."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()


# ============================================================================
# FUNÇÕES DE BANCO DE DADOS
# ============================================================================

def get_connection():
    """Obtém conexão com o banco."""
    import psycopg2
    return psycopg2.connect(**DB_CONFIG)


def ensure_table_exists(conn):
    """Garante que a tabela de chunks existe."""
    with conn.cursor() as cur:
        # Verificar se extensão vector existe
        cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        if not cur.fetchone():
            logger.warning("⚠️ Extensão 'vector' não encontrada. Tentando criar...")
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
                logger.info("✅ Extensão 'vector' criada")
            except Exception as e:
                logger.error(f"❌ Erro ao criar extensão vector: {e}")
                return False
        
        # Criar schema se não existir
        cur.execute("CREATE SCHEMA IF NOT EXISTS base")
        
        # Criar tabela
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS base.document_chunks (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding VECTOR({EMBEDDING_DIM}),
                source_file TEXT,
                chunk_index INTEGER,
                token_count INTEGER,
                metadata JSONB DEFAULT '{{}}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Criar índices
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_doc_chunks_tenant 
            ON base.document_chunks(tenant_id)
        """)
        
        try:
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_doc_chunks_embedding 
                ON base.document_chunks 
                USING ivfflat (embedding vector_cosine_ops)
            """)
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível criar índice IVFFlat: {e}")
        
        # Adicionar coluna tsvector para busca full-text
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_schema = 'base' 
                    AND table_name = 'document_chunks' 
                    AND column_name = 'content_tsv'
                ) THEN
                    ALTER TABLE base.document_chunks 
                    ADD COLUMN content_tsv TSVECTOR 
                    GENERATED ALWAYS AS (to_tsvector('portuguese', content)) STORED;
                END IF;
            END $$;
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_doc_chunks_tsv 
            ON base.document_chunks 
            USING GIN(content_tsv)
        """)
        
        conn.commit()
        logger.info("✅ Tabela base.document_chunks criada/verificada")
        return True


def insert_chunks(conn, chunks: List[Dict], embeddings: List[List[float]], 
                  source_file: str, tenant_id: str = "system") -> int:
    """Insere chunks no banco."""
    inserted = 0
    with conn.cursor() as cur:
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = hashlib.md5(
                f"{tenant_id}:{source_file}:{chunk['chunk_index']}:{chunk['content'][:100]}".encode()
            ).hexdigest()
            
            embedding_str = f"[{','.join(map(str, embedding))}]"
            
            try:
                cur.execute("""
                    INSERT INTO base.document_chunks 
                    (id, tenant_id, content, embedding, source_file, chunk_index, token_count, metadata)
                    VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                """, (
                    chunk_id,
                    tenant_id,
                    chunk['content'],
                    embedding_str,
                    source_file,
                    chunk['chunk_index'],
                    chunk['token_count'],
                    json.dumps({"indexed_at": datetime.now().isoformat()})
                ))
                inserted += 1
            except Exception as e:
                logger.error(f"Erro ao inserir chunk: {e}")
        
        conn.commit()
    return inserted


def get_stats(conn, tenant_id: str = "system") -> Dict[str, int]:
    """Obtém estatísticas de indexação."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(DISTINCT source_file) as total_documents,
                COALESCE(SUM(token_count), 0) as total_tokens
            FROM base.document_chunks
            WHERE tenant_id = %s
        """, (tenant_id,))
        row = cur.fetchone()
        return {
            "total_chunks": row[0] or 0,
            "total_documents": row[1] or 0,
            "total_tokens": row[2] or 0
        }


# ============================================================================
# FUNÇÃO PRINCIPAL DE INDEXAÇÃO
# ============================================================================

def load_document(file_path: Path) -> str:
    """Carrega conteúdo de um documento."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def index_all_documents():
    """Indexa todos os documentos do sistema."""
    logger.info("=" * 60)
    logger.info("🚀 INDEXAÇÃO DE DOCUMENTOS NO PGVECTOR")
    logger.info("=" * 60)
    
    # Diretórios para indexar
    docs_to_index = [
        {"path": project_root / "backend" / "perda_esperada" / "docs", "category": "ecl"},
        {"path": project_root / "backend" / "prinad" / "docs", "category": "prinad"},
        {"path": project_root / "backend" / "propensao" / "docs", "category": "propensao"},
    ]
    
    # Arquivos individuais
    files_to_index = [
        {"path": project_root / "README.md", "category": "sistema"},
    ]
    
    # Conectar ao banco
    logger.info(f"\n📊 Conectando ao banco: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    try:
        conn = get_connection()
        logger.info("✅ Conexão estabelecida")
    except Exception as e:
        logger.error(f"❌ Erro ao conectar: {e}")
        return False
    
    # Garantir tabela existe
    if not ensure_table_exists(conn):
        return False
    
    # Inicializar componentes
    chunker = SimpleChunker(chunk_size=CHUNK_SIZE)
    embedder = EmbeddingGenerator()
    
    total_indexed = 0
    total_errors = 0
    
    # Indexar diretórios
    for doc_info in docs_to_index:
        dir_path = doc_info["path"]
        logger.info(f"\n📂 Processando: {dir_path.name}")
        
        if not dir_path.exists():
            logger.warning(f"   ⚠️ Diretório não encontrado")
            continue
        
        files = list(dir_path.glob("*.md")) + list(dir_path.glob("*.sql"))
        logger.info(f"   Encontrados {len(files)} arquivos")
        
        for file_path in files:
            try:
                content = load_document(file_path)
                chunks = chunker.chunk(content)
                
                if not chunks:
                    logger.warning(f"   ⚠️ {file_path.name} - sem chunks")
                    continue
                
                texts = [c['content'] for c in chunks]
                embeddings = embedder.embed(texts)
                
                inserted = insert_chunks(conn, chunks, embeddings, file_path.name)
                logger.info(f"   ✅ {file_path.name}: {inserted} chunks")
                total_indexed += 1
                
            except Exception as e:
                logger.error(f"   ❌ {file_path.name}: {str(e)[:50]}")
                total_errors += 1
    
    # Indexar arquivos individuais
    logger.info("\n📄 Processando arquivos individuais")
    for file_info in files_to_index:
        file_path = file_info["path"]
        
        if not file_path.exists():
            logger.warning(f"   ⚠️ {file_path.name} não encontrado")
            continue
        
        try:
            content = load_document(file_path)
            chunks = chunker.chunk(content)
            
            if chunks:
                texts = [c['content'] for c in chunks]
                embeddings = embedder.embed(texts)
                inserted = insert_chunks(conn, chunks, embeddings, file_path.name)
                logger.info(f"   ✅ {file_path.name}: {inserted} chunks")
                total_indexed += 1
        except Exception as e:
            logger.error(f"   ❌ {file_path.name}: {str(e)[:50]}")
            total_errors += 1
    
    # Estatísticas finais
    stats = get_stats(conn)
    conn.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMO DA INDEXAÇÃO")
    logger.info("=" * 60)
    logger.info(f"   ✅ Arquivos processados: {total_indexed}")
    logger.info(f"   ❌ Erros: {total_errors}")
    logger.info(f"   📄 Total de chunks no banco: {stats['total_chunks']}")
    logger.info(f"   📚 Total de documentos: {stats['total_documents']}")
    logger.info(f"   📝 Total de tokens: {stats['total_tokens']}")
    logger.info("=" * 60)
    
    return total_errors == 0


if __name__ == "__main__":
    success = index_all_documents()
    if success:
        print("\n✅ Indexação concluída com sucesso!")
    else:
        print("\n❌ Houve erros na indexação")
        sys.exit(1)
