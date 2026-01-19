# Sistema de File Search Híbrido

Este documento descreve detalhadamente o funcionamento do sistema de **File Search Híbrido** implementado no projeto. O sistema utiliza uma arquitetura RAG (Retrieval-Augmented Generation) moderna, combinando busca vetorial (semântica) e busca textual (palavras-chave), refinada por um processo de reclassificação (reranking).

## Visão Geral

O objetivo do sistema é permitir a indexação e recuperação eficiente de informações a partir de documentos de diversos formatos (PDF, DOCX, TXT, etc.). Ele foi projetado para superar as limitações da busca vetorial pura, integrando busca por palavras-chave e reclassificação para alta precisão.

### Principais Características
- **Busca Híbrida**: Combina `pgvector` (vetorial) + PostgreSQL Full-Text Search.
- **Fusão de Resultados**: Utiliza o algoritmo **RRF (Reciprocal Rank Fusion)** para combinar os resultados das duas buscas de forma equilibrada.
- **Reranking**: Aplica um modelo de Cross-Encoder (via `FlashRank`) para reordenar os resultados finais, garantindo que o contexto mais relevante esteja no topo.
- **Chunking Inteligente**: Divide os documentos respeitando parágrafos e frases, com sobreposição (overlap) para manter o contexto.
- **Multilíngue**: Suporta documentos e consultas em diversos idiomas, com otimização para Português.

---

## Arquitetura e Fluxo de Dados

### 1. Ingestão de Documentos (Upload)
O processo inicia quando um documento é enviado para a API.

1.  **Carregamento (`DocumentLoader`)**:
    - O arquivo é salvo temporariamente.
    - O `DocumentLoader` identifica o formato e extrai o texto.
    - Suporta: PDF (via `pypdf`), DOCX (`python-docx`), JSON, Código Fonte, Markdown, TXT.

2.  **Chunking (`SmartChunker`)**:
    - O texto extraído é dividido em pedaços menores ("chunks").
    - **Estratégia**: Tenta manter parágrafos inteiros. Se um parágrafo for muito grande, divide por frases.
    - **Configuração Padrão**: Chunks de ~1500 tokens com sobreposição de 200 tokens.

3.  **Embedding (`EmbeddingModel`)**:
    - Cada chunk é convertido em um vetor numérico (embedding) que representa seu significado semântico.
    - **Modelo**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (Dimensão: 768).

4.  **Armazenamento (`PostgresVectorStore`)**:
    - Os chunks, embeddings e metadados são salvos na tabela `base.document_chunks`.
    - O PostgreSQL gera automaticamente um índice de texto (`tsvector`) para busca full-text.

### 2. Recuperação de Informação (Search)
Quando o usuário realiza uma busca:

1.  **Expansão de Query**:
    - O sistema pode expandir termos da busca (ex: "conduta" -> "ética", "regras") para aumentar o alcance (implementado no `HttpFileSearch`).

2.  **Busca Paralela (Híbrida)**:
    - **Vetorial**: Busca os chunks semanticamente mais próximos da query.
    - **Textual**: Busca chunks que contêm as palavras-chave exatas.

3.  **Fusão (RRF)**:
    - Os resultados das duas buscas são combinados usando a fórmula RRF:
      $$ Score = \frac{1}{k + rank_{vetorial}} + \frac{1}{k + rank_{textual}} $$
    - Isso garante que documentos relevantes em *ambas* as estratégias subam no ranking.

4.  **Reranking (`Reranker`)**:
    - Os Top-N resultados da fusão passam por um modelo de reranking (`ms-marco-MiniLM-L-12-v2`).
    - O reranker analisa o par (Query, Documento) profundamente e atribui um score de relevância mais preciso.

5.  **Resultado Final**:
    - Os chunks mais relevantes são retornados, juntamente com metadados e score de confiança.

---

## Estrutura do Banco de Dados

A tabela central é a `base.document_chunks`.

```sql
CREATE TABLE base.document_chunks (
    id TEXT PRIMARY KEY,
    document_id INTEGER REFERENCES base.documentos(...),
    tenant_id TEXT NOT NULL,
    content TEXT NOT NULL,            -- Texto do chunk
    content_tsv TSVECTOR,             -- Índice Full-Text (Gerado auto.)
    embedding VECTOR(768),            -- Vetor semântico
    source_file TEXT,                 -- Nome do arquivo origem
    chunk_index INTEGER,              -- Ordem no documento
    metadata JSONB                    -- Metadados extras
);
```

### Índices
- **IVFFlat**: Para busca vetorial rápida (`idx_chunks_embedding`).
- **GIN**: Para busca full-text (`idx_chunks_tsv`) e busca em metadados JSON (`idx_chunks_metadata`).

---

## Scripts e Arquivos Python

Os componentes do sistema estão distribuídos nos seguintes arquivos:

### Core (Lógica Principal)
- **[backend/core/file_search.py](file:///e:/Projetos/orquestrador_agentes/backend/core/file_search.py)**:
    - `FileSearchConfig`: Configurações (modelos, dimensões, chunks).
    - `DocumentLoader`: Carregamento e extração de texto de arquivos.
    - `SmartChunker`: Lógica de divisão de texto.
    - `EmbeddingModel`: Wrapper para geração de embeddings.
    - `Reranker`: Implementação do FlashRank.
    - `PostgresVectorStore`: Gerenciamento de conexão e tabelas no DB.

### API (Interface)
- **[backend/api/routes/file_search.py](file:///e:/Projetos/orquestrador_agentes/backend/api/routes/file_search.py)**:
    - Define as rotas `/upload`, `/search`, `/stats`.
    - `HttpFileSearch`: Classe adaptadora que orquestra a busca se o modo direto via banco não estiver ativo (ou como fallback).
    - Implementa a lógica de expansão de sinônimos.

### Banco de Dados
- **[backend/migrations/file_search_tables.sql](file:///e:/Projetos/orquestrador_agentes/backend/migrations/file_search_tables.sql)**:
    - Script SQL que cria as tabelas, índices e a função `base.hybrid_search`.

### Scripts Auxiliares
- **[backend/scripts/index_user_docs.py](file:///e:/Projetos/orquestrador_agentes/backend/scripts/index_user_docs.py)**:
    - Script utilitário para indexar documentos em lote (batch).

## Como Utilizar

### Exemplo de Busca via Código (Python)

```python
from core.file_search import FileSearchHybrid, FileSearchConfig

# Inicializar
config = FileSearchConfig.from_env()
search_engine = FileSearchHybrid(config)

# Realizar busca
results = search_engine.search(
    query="Quais são as regras de compliance?",
    tenant_id="default",
    use_rerank=True,
    top_k=5
)

for result in results:
    print(f"Score: {result['rerank_score']}")
    print(f"Conteúdo: {result['content'][:100]}...")
```
