-- =============================================================================
-- Schema do Agente de IA - PostgreSQL + PGVector
-- Sistema de Gestão de Risco Bancário
-- =============================================================================

-- Criar schema agente
CREATE SCHEMA IF NOT EXISTS agente;

-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS vector;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =============================================================================
-- TABELA: Sessões de Chat
-- =============================================================================
CREATE TABLE IF NOT EXISTS agente.sessoes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    usuario_id VARCHAR(50) NOT NULL,
    usuario_role VARCHAR(20) NOT NULL, -- ANALISTA, GESTOR, AUDITOR, ADMIN
    titulo VARCHAR(255) DEFAULT 'Nova Conversa',
    resumo TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessoes_usuario ON agente.sessoes (usuario_id);

CREATE INDEX IF NOT EXISTS idx_sessoes_created ON agente.sessoes (created_at DESC);

COMMENT ON
TABLE agente.sessoes IS 'Sessões de chat do Agente IA por usuário';

-- =============================================================================
-- TABELA: Mensagens
-- =============================================================================
CREATE TABLE IF NOT EXISTS agente.mensagens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    sessao_id UUID NOT NULL REFERENCES agente.sessoes (id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant, tool, system
    content TEXT,
    tool_name VARCHAR(100),
    tool_calls JSONB, -- Para chamadas de ferramentas
    tool_result JSONB, -- Resultado da ferramenta
    tokens_input INTEGER,
    tokens_output INTEGER,
    latency_ms INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mensagens_sessao ON agente.mensagens (sessao_id);

CREATE INDEX IF NOT EXISTS idx_mensagens_created ON agente.mensagens (created_at);

CREATE INDEX IF NOT EXISTS idx_mensagens_role ON agente.mensagens (role);

COMMENT ON
TABLE agente.mensagens IS 'Mensagens trocadas nas sessões de chat';

-- =============================================================================
-- TABELA: Artefatos Gerados
-- =============================================================================
CREATE TABLE IF NOT EXISTS agente.artefatos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    sessao_id UUID REFERENCES agente.sessoes (id) ON DELETE SET NULL,
    mensagem_id UUID REFERENCES agente.mensagens (id) ON DELETE SET NULL,
    usuario_id VARCHAR(50) NOT NULL,
    tipo VARCHAR(50) NOT NULL, -- chart, excel, pdf, code, report, image
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    mime_type VARCHAR(100),
    tamanho_bytes INTEGER,
    conteudo_path TEXT, -- Caminho no filesystem
    conteudo_base64 TEXT, -- Ou conteúdo inline (para pequenos)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_artefatos_sessao ON agente.artefatos (sessao_id);

CREATE INDEX IF NOT EXISTS idx_artefatos_usuario ON agente.artefatos (usuario_id);

CREATE INDEX IF NOT EXISTS idx_artefatos_tipo ON agente.artefatos (tipo);

COMMENT ON
TABLE agente.artefatos IS 'Artefatos gerados pelo Agente (gráficos, relatórios, etc)';

-- =============================================================================
-- TABELA: Document Chunks (RAG)
-- =============================================================================
CREATE TABLE IF NOT EXISTS agente.document_chunks (
    id TEXT PRIMARY KEY,
    document_id INTEGER,
    tenant_id TEXT NOT NULL DEFAULT 'risco_bancario',
    content TEXT NOT NULL,
    content_tsv TSVECTOR GENERATED ALWAYS AS (
        to_tsvector ('portuguese', content)
    ) STORED,
    embedding VECTOR (1024), -- multilingual-e5-large-instruct = 1024 dims
    source_file TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_tenant ON agente.document_chunks (tenant_id);

CREATE INDEX IF NOT EXISTS idx_chunks_source ON agente.document_chunks (source_file);

CREATE INDEX IF NOT EXISTS idx_chunks_tsv ON agente.document_chunks USING GIN (content_tsv);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON agente.document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

COMMENT ON
TABLE agente.document_chunks IS 'Chunks de documentos para RAG com embeddings vetoriais';

-- =============================================================================
-- TABELA: Log de Uso de Ferramentas
-- =============================================================================
CREATE TABLE IF NOT EXISTS agente.tool_usage_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4 (),
    sessao_id UUID REFERENCES agente.sessoes (id) ON DELETE SET NULL,
    usuario_id VARCHAR(50) NOT NULL,
    usuario_role VARCHAR(20) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    tool_input JSONB,
    tool_output JSONB,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    execution_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tool_usage_usuario ON agente.tool_usage_log (usuario_id);

CREATE INDEX IF NOT EXISTS idx_tool_usage_tool ON agente.tool_usage_log (tool_name);

CREATE INDEX IF NOT EXISTS idx_tool_usage_created ON agente.tool_usage_log (created_at DESC);

COMMENT ON
TABLE agente.tool_usage_log IS 'Log de uso de ferramentas pelo Agente para auditoria';

-- =============================================================================
-- FUNÇÃO: Hybrid Search (Vector + Full-Text)
-- =============================================================================
CREATE OR REPLACE FUNCTION agente.hybrid_search(
    query_text TEXT,
    query_embedding VECTOR(1024),
    tenant_filter TEXT DEFAULT 'risco_bancario',
    match_count INT DEFAULT 10,
    rrf_k INT DEFAULT 60
) 
RETURNS TABLE (
    chunk_id TEXT,
    chunk_content TEXT,
    source_file TEXT,
    chunk_index INTEGER,
    token_count INTEGER,
    metadata JSONB,
    vector_score FLOAT,
    text_score FLOAT,
    rrf_score FLOAT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH 
    -- Vector search
    vector_search AS (
        SELECT 
            dc.id,
            dc.content,
            dc.source_file,
            dc.chunk_index,
            dc.token_count,
            dc.metadata,
            1 - (dc.embedding <=> query_embedding) AS v_score,
            ROW_NUMBER() OVER (ORDER BY dc.embedding <=> query_embedding) AS v_rank
        FROM agente.document_chunks dc
        WHERE dc.tenant_id = tenant_filter
        ORDER BY dc.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    -- Full-text search
    text_search AS (
        SELECT 
            dc.id,
            dc.content,
            dc.source_file,
            dc.chunk_index,
            dc.token_count,
            dc.metadata,
            ts_rank_cd(dc.content_tsv, plainto_tsquery('portuguese', query_text)) AS t_score,
            ROW_NUMBER() OVER (
                ORDER BY ts_rank_cd(dc.content_tsv, plainto_tsquery('portuguese', query_text)) DESC
            ) AS t_rank
        FROM agente.document_chunks dc
        WHERE dc.tenant_id = tenant_filter
        AND dc.content_tsv @@ plainto_tsquery('portuguese', query_text)
        LIMIT match_count * 2
    ),
    -- RRF Fusion
    combined AS (
        SELECT 
            COALESCE(v.id, t.id) AS id,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.source_file, t.source_file) AS src_file,
            COALESCE(v.chunk_index, t.chunk_index) AS c_index,
            COALESCE(v.token_count, t.token_count) AS t_count,
            COALESCE(v.metadata, t.metadata) AS meta,
            COALESCE(v.v_score, 0)::FLOAT AS v_score,
            COALESCE(t.t_score, 0)::FLOAT AS t_score,
            (
                COALESCE(1.0 / (rrf_k + v.v_rank), 0) +
                COALESCE(1.0 / (rrf_k + t.t_rank), 0)
            )::FLOAT AS rrf
        FROM vector_search v
        FULL OUTER JOIN text_search t ON v.id = t.id
    )
    SELECT 
        c.id,
        c.content,
        c.src_file,
        c.c_index,
        c.t_count,
        c.meta,
        c.v_score,
        c.t_score,
        c.rrf
    FROM combined c
    ORDER BY c.rrf DESC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION agente.hybrid_search IS 'Busca híbrida combinando similaridade vetorial e full-text com RRF fusion';

-- =============================================================================
-- FUNÇÃO: Estatísticas do RAG
-- =============================================================================
CREATE OR REPLACE FUNCTION agente.get_rag_stats(
    tenant_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    total_chunks BIGINT,
    total_documents BIGINT,
    total_tokens BIGINT,
    avg_chunk_size FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT,
        COUNT(DISTINCT source_file)::BIGINT,
        COALESCE(SUM(token_count), 0)::BIGINT,
        COALESCE(AVG(token_count), 0)::FLOAT
    FROM agente.document_chunks
    WHERE tenant_filter IS NULL OR tenant_id = tenant_filter;
END;
$$;

-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================
GRANT USAGE ON SCHEMA agente TO PUBLIC;

GRANT ALL ON ALL TABLES IN SCHEMA agente TO PUBLIC;

GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA agente TO PUBLIC;

-- =============================================================================
-- VERIFICAÇÃO
-- =============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Schema agente criado com sucesso!';
    RAISE NOTICE '📊 Tabelas: sessoes, mensagens, artefatos, document_chunks, tool_usage_log';
    RAISE NOTICE '🔍 Funções: hybrid_search, get_rag_stats';
END $$;