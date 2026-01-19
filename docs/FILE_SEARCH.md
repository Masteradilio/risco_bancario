# File Search - Sistema de Busca Híbrida

## 📋 Visão Geral

O **File Search** é o sistema RAG (Retrieval-Augmented Generation) do IAGPM que combina busca vetorial com busca de texto completo para encontrar informações relevantes em documentos de projeto.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        File Search Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Documento      ┌──────────┐    ┌──────────┐    ┌────────────┐  │
│  Upload    ──▶  │  Loader  │──▶ │ Chunker  │──▶ │ Embeddings │  │
│                 └──────────┘    └──────────┘    └─────┬──────┘  │
│                                                       │         │
│                                                       ▼         │
│                                               ┌────────────┐    │
│                                               │   Vector   │    │
│                                               │   Store    │    │
│                                               │ (pgvector) │    │
│                                               └─────┬──────┘    │
│                                                     │           │
│  ┌──────────────────────────────────────────────────┼─────────┐ │
│  │                    Query Pipeline                │         │ │
│  │                                                  ▼         │ │
│  │  Query   ┌──────────┐   ┌──────────┐   ┌────────────────┐  │ │
│  │   ───▶   │ Semantic │ + │   FTS    │ = │  RRF Fusion    │  │ │
│  │          │  Search  │   │  Search  │   │  (Reranking)   │  │ │
│  │          └──────────┘   └──────────┘   └───────┬────────┘  │ │
│  │                                                 │          │ │
│  │                                     ┌───────────▼────────┐ │ │
│  │                                     │   FlashRank        │ │ │
│  │                                     │   Cross-Encoder    │ │ │
│  │                                     └───────────┬────────┘ │ │
│  └─────────────────────────────────────────────────│──────────┘ │
│                                                    │            │
│                                                    ▼            │
│                                            ┌──────────────┐     │
│                                            │   Results    │     │
│                                            └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Componentes

### 1. Loader (`loader.py`)

Responsável por carregar e extrair texto de diversos formatos de arquivo:

| Formato | Biblioteca | Descrição |
|---------|------------|-----------|
| **PDF** | `pypdf` | Extração de texto de PDFs |
| **DOCX** | `python-docx` | Documentos Word |
| **XLSX/XLS** | `openpyxl` | Planilhas Excel |
| **CSV** | `pandas` | Arquivos CSV |
| **Markdown** | `markdown` | Arquivos .md |
| **JSON** | `json` | Dados estruturados |
| **Código** | `pygments` | Python, JS, SQL, etc. |

**Uso:**

```python
from app.file_search.loader import DocumentLoader

loader = DocumentLoader()
text = await loader.load("documento.pdf")
```

### 2. Chunker (`chunker.py`)

Divide documentos longos em chunks menores para indexação:

| Configuração | Valor Default | Descrição |
|--------------|---------------|-----------|
| `chunk_size` | 512 tokens | Tamanho máximo do chunk |
| `chunk_overlap` | 64 tokens | Sobreposição entre chunks |
| `tokenizer` | `tiktoken` | Contador de tokens preciso |

**Características:**

- **Semantic Chunking**: Respeita limites de parágrafo e frase
- **Overlap**: Garante contexto entre chunks adjacentes
- **Metadados**: Preserva informações de origem (página, seção)

### 3. Embeddings (`embeddings.py`)

Gera representações vetoriais dos textos:

| Modelo | Dimensão | Descrição |
|--------|----------|-----------|
| `intfloat/multilingual-e5-large-instruct` | 1024 | Modelo principal |
| Alternativas | Configurável | Suporte a outros modelos |

**Vantagens do E5:**

- Multilíngue (português, inglês, espanhol, etc.)
- Instruct-tuned (melhor para queries)
- Alta qualidade em similaridade semântica

### 4. Vector Store (`vector_store.py`)

Armazenamento e busca vetorial usando PostgreSQL + pgvector:

**Tabela `document_chunks`:**

```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    content TEXT NOT NULL,
    embedding VECTOR(1024),
    metadata JSONB,
    created_at TIMESTAMPTZ
);

CREATE INDEX ON document_chunks 
USING ivfflat (embedding vector_cosine_ops);
```

**Operações:**

- `upsert_chunks()` - Inserir/atualizar chunks
- `similarity_search()` - Busca por similaridade vetorial
- `hybrid_search()` - Busca combinada (vetor + FTS)

### 5. Reranker (`reranker.py`)

Refina resultados usando cross-encoder:

| Componente | Tecnologia | Descrição |
|------------|------------|-----------|
| **Modelo** | FlashRank | Cross-encoder rápido |
| **Função** | Reordenar top-K | Melhora precisão |

**Pipeline de Reranking:**

1. Busca inicial retorna 50 candidatos
2. Reranker pontua cada par (query, chunk)
3. Retorna top-10 reordenados

### 6. Hybrid Search (`hybrid_search.py`)

Orquestrador principal que combina todas as técnicas:

**RRF (Reciprocal Rank Fusion):**

```
score(d) = Σ 1 / (k + rank_i(d))
```

Onde:

- `k` = 60 (constante de suavização)
- `rank_i(d)` = posição do documento no ranking i

---

## 🔌 API Endpoints

### Upload de Documento

```http
POST /api/v1/file-search/upload
Content-Type: multipart/form-data

file: <arquivo>
project_id: <uuid>
```

**Response:**

```json
{
  "document_id": "uuid",
  "filename": "relatorio.pdf",
  "chunks_created": 15,
  "status": "indexed"
}
```

### Busca

```http
POST /api/v1/file-search/search
Content-Type: application/json

{
  "query": "orçamento do projeto Alpha",
  "project_id": "uuid",
  "top_k": 10,
  "use_rerank": true
}
```

**Response:**

```json
{
  "results": [
    {
      "chunk_id": "uuid",
      "content": "O orçamento aprovado...",
      "score": 0.89,
      "document": {
        "id": "uuid",
        "filename": "orcamento_alpha.xlsx"
      },
      "metadata": {
        "page": 2,
        "section": "Resumo Executivo"
      }
    }
  ],
  "query_time_ms": 120
}
```

### Estatísticas

```http
GET /api/v1/file-search/stats?project_id=<uuid>
```

**Response:**

```json
{
  "total_documents": 45,
  "total_chunks": 892,
  "index_size_mb": 156.4,
  "last_updated": "2026-01-16T10:30:00Z"
}
```

---

## ⚙️ Configuração

```bash
# .env

# Modelo de Embedding
FILE_SEARCH_EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct
FILE_SEARCH_EMBEDDING_DIMENSION=1024

# Chunking
FILE_SEARCH_CHUNK_SIZE=512
FILE_SEARCH_CHUNK_OVERLAP=64

# Busca
FILE_SEARCH_TOP_K=50
FILE_SEARCH_RERANK_TOP_K=10
FILE_SEARCH_USE_RERANK=true
```

---

## 🚀 Performance

| Métrica | Valor |
|---------|-------|
| Tempo de indexação | ~2s por página |
| Tempo de busca (sem rerank) | ~50ms |
| Tempo de busca (com rerank) | ~150ms |
| Precisão P@10 | ~0.85 |

---

## 🔗 Integrações

- **Document Intelligence Agent**: Usa File Search para RAG
- **Skills**: Skills podem buscar contexto automaticamente
- **Cowork**: Auto-indexa arquivos do workspace

---

*Documentação atualizada em 16/01/2026*
