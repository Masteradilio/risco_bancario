-- File Search Hybrid Tables Migration
-- Creates tables and functions for PostgreSQL + pgvector based hybrid search
-- 
-- This migration enables the new File Search system that combines:
-- - Vector search (pgvector) for semantic similarity
-- - Full-Text Search (PostgreSQL) for keyword matching
-- - Reciprocal Rank Fusion (RRF) for combining results

-- =============================================================================
-- STEP 1: Enable required extensions
-- =============================================================================

-- pgvector for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_trgm for trigram similarity (optional, for fuzzy matching)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =============================================================================
-- STEP 2: Create document_chunks table
-- =============================================================================

CREATE TABLE IF NOT EXISTS base.document_chunks (
    -- Primary key
    id TEXT PRIMARY KEY,
    
    -- Reference to original document in base.documentos
    document_id INTEGER REFERENCES base.documentos(cd_documento) ON DELETE CASCADE,
    
    -- Multi-tenant support
    tenant_id TEXT NOT NULL,
    
    -- Chunk content
    content TEXT NOT NULL,
    
    -- Auto-generated tsvector for full-text search (Portuguese)
    content_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('portuguese', content)) STORED,
    
    -- Embedding vector
    -- NOTE: Dimension (768) must match the embedding model used:
    -- - paraphrase-multilingual-mpnet-base-v2: 768 dimensions
    -- - all-MiniLM-L6-v2: 384 dimensions
    -- - text-embedding-3-small: 1536 dimensions
    -- Change this value if using a different embedding model
    embedding VECTOR(768),
    
    -- Source file information
    source_file TEXT,
    
    -- Position within document
    chunk_index INTEGER,
    
    -- Token count for context window management
    token_count INTEGER,
    
    -- Flexible metadata storage
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comment for documentation
COMMENT ON TABLE base.document_chunks IS 
    'Stores document chunks with embeddings for hybrid search (vector + full-text)';

-- =============================================================================
-- STEP 3: Create indexes for optimal query performance
-- =============================================================================

-- Index for tenant filtering (B-tree)
CREATE INDEX IF NOT EXISTS idx_chunks_tenant 
ON base.document_chunks(tenant_id);

-- Index for document filtering (B-tree)
CREATE INDEX IF NOT EXISTS idx_chunks_document 
ON base.document_chunks(document_id);

-- Index for source file lookup (B-tree)
CREATE INDEX IF NOT EXISTS idx_chunks_source 
ON base.document_chunks(source_file);

-- Vector similarity index (IVFFlat with cosine distance)
-- Note: lists = 100 is good for up to ~100k vectors
-- For larger datasets, increase lists (sqrt(n) is a good rule)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
ON base.document_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Full-text search index (GIN)
CREATE INDEX IF NOT EXISTS idx_chunks_tsv 
ON base.document_chunks 
USING GIN(content_tsv);

-- JSONB metadata index (GIN for containment queries)
CREATE INDEX IF NOT EXISTS idx_chunks_metadata 
ON base.document_chunks 
USING GIN(metadata);

-- =============================================================================
-- STEP 4: Create hybrid search function with Reciprocal Rank Fusion (RRF)
-- =============================================================================

CREATE OR REPLACE FUNCTION base.hybrid_search(
    query_text TEXT,
    query_embedding VECTOR(768),
    tenant_filter TEXT,
    match_count INT DEFAULT 20,
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
    -- Vector search: find similar chunks by embedding
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
        FROM base.document_chunks dc
        WHERE dc.tenant_id = tenant_filter
        ORDER BY dc.embedding <=> query_embedding
        LIMIT match_count * 2  -- Fetch more for fusion
    ),
    
    -- Full-text search: find chunks matching keywords
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
        FROM base.document_chunks dc
        WHERE dc.tenant_id = tenant_filter
        AND dc.content_tsv @@ plainto_tsquery('portuguese', query_text)
        LIMIT match_count * 2  -- Fetch more for fusion
    ),
    
    -- Combine results with Reciprocal Rank Fusion
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

COMMENT ON FUNCTION base.hybrid_search IS 
    'Performs hybrid search combining vector similarity and full-text search with RRF fusion';

-- =============================================================================
-- STEP 5: Create helper functions
-- =============================================================================

-- Function to get document statistics
CREATE OR REPLACE FUNCTION base.get_file_search_stats(
    tenant_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    total_chunks BIGINT,
    total_documents BIGINT,
    total_tokens BIGINT,
    avg_chunk_size FLOAT,
    tenant_count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT,
        COUNT(DISTINCT source_file)::BIGINT,
        COALESCE(SUM(token_count), 0)::BIGINT,
        COALESCE(AVG(token_count), 0)::FLOAT,
        COUNT(DISTINCT tenant_id)::BIGINT
    FROM base.document_chunks
    WHERE tenant_filter IS NULL OR tenant_id = tenant_filter;
END;
$$;

-- Function to delete chunks by source file
CREATE OR REPLACE FUNCTION base.delete_chunks_by_source(
    source TEXT,
    tenant TEXT
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM base.document_chunks
    WHERE source_file = source AND tenant_id = tenant;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- =============================================================================
-- STEP 6: Create RLS policies for multi-tenant security (optional)
-- =============================================================================

-- Enable RLS on document_chunks table
ALTER TABLE base.document_chunks ENABLE ROW LEVEL SECURITY;

-- Policy for reading chunks (tenants can only read their own data)
CREATE POLICY chunks_tenant_read ON base.document_chunks
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant', true));

-- Policy for inserting chunks
CREATE POLICY chunks_tenant_insert ON base.document_chunks
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant', true));

-- Policy for deleting chunks
CREATE POLICY chunks_tenant_delete ON base.document_chunks
    FOR DELETE
    USING (tenant_id = current_setting('app.current_tenant', true));

-- Note: For application users, set the tenant context with:
-- SET app.current_tenant = 'your_tenant_id';
-- Or use BYPASSRLS role for admin operations

-- =============================================================================
-- STEP 7: Grant permissions
-- =============================================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA base TO PUBLIC;

-- Grant permissions on table
GRANT SELECT, INSERT, UPDATE, DELETE ON base.document_chunks TO PUBLIC;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION base.hybrid_search TO PUBLIC;
GRANT EXECUTE ON FUNCTION base.get_file_search_stats TO PUBLIC;
GRANT EXECUTE ON FUNCTION base.delete_chunks_by_source TO PUBLIC;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

-- Verify installation
DO $$
BEGIN
    RAISE NOTICE 'File Search Hybrid migration completed successfully!';
    RAISE NOTICE 'Tables created: base.document_chunks';
    RAISE NOTICE 'Functions created: base.hybrid_search, base.get_file_search_stats, base.delete_chunks_by_source';
    RAISE NOTICE 'Indexes created: 5 indexes for optimal performance';
END $$;
