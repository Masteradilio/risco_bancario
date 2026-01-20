# -*- coding: utf-8 -*-
"""
Script para indexar documentação do sistema no PGVector

Este script processa os documentos regulatórios e de documentação
do sistema e os indexa no sistema de File Search Hybrid.

Diretórios indexados:
- backend/perda_esperada/docs/
- backend/prinad/docs/
- backend/propensao/docs/
- README.md (raiz)

Uso:
    python backend/scripts/index_all_docs.py
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
project_root = backend_path.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def index_documents():
    """
    Indexa todos os documentos do sistema no PGVector.
    """
    from file_search.file_search import FileSearchHybrid, FileSearchConfig
    
    logger.info("=" * 60)
    logger.info("🚀 Iniciando indexação de documentos no PGVector")
    logger.info("=" * 60)
    
    # Inicializar File Search
    try:
        config = FileSearchConfig.from_env()
        file_search = FileSearchHybrid(config)
        logger.info(f"✅ File Search inicializado com modelo: {config.embedding_model}")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar File Search: {e}")
        return False
    
    # Diretórios para indexar
    docs_directories = [
        {
            "path": project_root / "backend" / "perda_esperada" / "docs",
            "category": "regulatorio",
            "description": "Documentação regulatória ECL/BACEN"
        },
        {
            "path": project_root / "backend" / "prinad" / "docs",
            "category": "modelo",
            "description": "Documentação do modelo PRINAD"
        },
        {
            "path": project_root / "backend" / "propensao" / "docs",
            "category": "relatorios",
            "description": "Relatórios trimestrais e documentação Propensão"
        },
    ]
    
    # Arquivos individuais
    individual_files = [
        {
            "path": project_root / "README.md",
            "category": "sistema",
            "description": "Documentação principal do sistema"
        }
    ]
    
    total_indexed = 0
    total_errors = 0
    
    # Indexar diretórios
    for doc_dir in docs_directories:
        dir_path = doc_dir["path"]
        
        logger.info(f"\n📂 Processando: {dir_path.name}")
        logger.info(f"   {doc_dir['description']}")
        
        if not dir_path.exists():
            logger.warning(f"   ⚠️ Diretório não encontrado: {dir_path}")
            continue
        
        # Encontrar arquivos markdown e SQL
        files = list(dir_path.glob("*.md")) + list(dir_path.glob("*.sql"))
        
        if not files:
            logger.warning(f"   ⚠️ Nenhum arquivo .md ou .sql encontrado")
            continue
        
        logger.info(f"   Encontrados {len(files)} arquivos")
        
        for file_path in files:
            try:
                result = file_search.ingest_document(
                    file_path=str(file_path),
                    tenant_id="system",
                    metadata={
                        "category": doc_dir["category"],
                        "source_directory": dir_path.name,
                        "filename": file_path.name,
                        "type": "documentation"
                    }
                )
                
                if result:
                    logger.info(f"   ✅ {file_path.name} ({result.get('chunks', '?')} chunks)")
                    total_indexed += 1
                else:
                    logger.warning(f"   ⚠️ {file_path.name} - sem chunks gerados")
                    
            except Exception as e:
                logger.error(f"   ❌ {file_path.name}: {str(e)[:50]}")
                total_errors += 1
    
    # Indexar arquivos individuais
    logger.info("\n📄 Processando arquivos individuais")
    
    for file_info in individual_files:
        file_path = file_info["path"]
        
        if not file_path.exists():
            logger.warning(f"   ⚠️ Arquivo não encontrado: {file_path}")
            continue
        
        try:
            result = file_search.ingest_document(
                file_path=str(file_path),
                tenant_id="system",
                metadata={
                    "category": file_info["category"],
                    "filename": file_path.name,
                    "type": "documentation"
                }
            )
            
            if result:
                logger.info(f"   ✅ {file_path.name} ({result.get('chunks', '?')} chunks)")
                total_indexed += 1
            else:
                logger.warning(f"   ⚠️ {file_path.name} - sem chunks gerados")
                
        except Exception as e:
            logger.error(f"   ❌ {file_path.name}: {str(e)[:50]}")
            total_errors += 1
    
    # Fechar conexão
    file_search.close()
    
    # Resumo
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMO DA INDEXAÇÃO")
    logger.info("=" * 60)
    logger.info(f"   ✅ Arquivos indexados: {total_indexed}")
    logger.info(f"   ❌ Erros: {total_errors}")
    logger.info("=" * 60)
    
    return total_errors == 0


def check_indexed_documents():
    """
    Verifica quantos documentos estão indexados no sistema.
    """
    from file_search.file_search import FileSearchHybrid, FileSearchConfig
    
    logger.info("\n📊 Verificando documentos indexados...")
    
    try:
        config = FileSearchConfig.from_env()
        file_search = FileSearchHybrid(config)
        
        stats = file_search.get_stats(tenant_id="system")
        
        logger.info(f"   Total de chunks: {stats.get('total_chunks', 0)}")
        logger.info(f"   Total de documentos: {stats.get('total_documents', 0)}")
        logger.info(f"   Total de tokens: {stats.get('total_tokens', 0)}")
        
        file_search.close()
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar: {e}")


def test_search(query: str = "CMN 4966"):
    """
    Testa uma busca no sistema.
    """
    from file_search.file_search import FileSearchHybrid, FileSearchConfig
    
    logger.info(f"\n🔍 Testando busca: '{query}'")
    
    try:
        config = FileSearchConfig.from_env()
        file_search = FileSearchHybrid(config)
        
        results = file_search.search(
            query=query,
            tenant_id="system",
            top_k=3,
            use_rerank=True
        )
        
        if results:
            logger.info(f"   Encontrados {len(results)} resultados:")
            for i, r in enumerate(results[:3], 1):
                logger.info(f"   {i}. {r.get('source_file', 'N/A')} (score: {r.get('rerank_score', 0):.3f})")
                content_preview = r.get('content', '')[:100]
                logger.info(f"      {content_preview}...")
        else:
            logger.warning("   Nenhum resultado encontrado")
        
        file_search.close()
        
    except Exception as e:
        logger.error(f"❌ Erro na busca: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Indexar documentos no PGVector")
    parser.add_argument("--check", "-c", action="store_true", help="Apenas verificar documentos indexados")
    parser.add_argument("--test", "-t", type=str, help="Testar busca com a query fornecida")
    
    args = parser.parse_args()
    
    if args.check:
        check_indexed_documents()
    elif args.test:
        test_search(args.test)
    else:
        success = index_documents()
        if success:
            print("\n✅ Indexação concluída com sucesso!")
            check_indexed_documents()
        else:
            print("\n❌ Houve erros na indexação")
            sys.exit(1)
