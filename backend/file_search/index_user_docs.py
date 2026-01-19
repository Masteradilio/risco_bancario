"""
Script para indexar documentação do usuário no File Search

Este script processa os documentos do diretório docs/user_guide/
e os indexa no sistema de File Search Hybrid para uso pelo Agente Construtor.

Uso:
    python -m backend.scripts.index_user_docs
    
Ou diretamente:
    python backend/scripts/index_user_docs.py
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pathlib import Path


def index_user_documentation():
    """
    Indexa os documentos do user_guide no sistema de File Search.
    """
    # Define paths
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    project_root = backend_dir.parent
    docs_dir = project_root / "docs" / "user_guide"
    
    print(f"📂 Diretório de documentos: {docs_dir}")
    
    if not docs_dir.exists():
        print(f"❌ Diretório não encontrado: {docs_dir}")
        return False
    
    # List all markdown files
    md_files = list(docs_dir.glob("*.md"))
    
    if not md_files:
        print("❌ Nenhum arquivo .md encontrado no diretório")
        return False
    
    print(f"📄 Encontrados {len(md_files)} arquivos para indexar:")
    for f in md_files:
        print(f"   - {f.name}")
    
    # Try to use File Search Hybrid if available
    try:
        from core.file_search import FileSearchHybrid, FileSearchConfig
        
        print("\n🔧 Inicializando File Search Hybrid...")
        config = FileSearchConfig.from_env()
        file_search = FileSearchHybrid(config)
        
        indexed_count = 0
        
        for file_path in md_files:
            try:
                print(f"\n📥 Indexando: {file_path.name}")
                
                result = file_search.ingest_document(
                    file_path=str(file_path),
                    tenant_id="system_docs",
                    metadata={
                        "type": "user_guide",
                        "category": "documentation",
                        "filename": file_path.name
                    }
                )
                
                if result:
                    print(f"   ✅ Sucesso: {result}")
                    indexed_count += 1
                else:
                    print(f"   ⚠️ Sem resultado de indexação")
                    
            except Exception as e:
                print(f"   ❌ Erro ao indexar {file_path.name}: {str(e)}")
        
        file_search.close()
        
        print(f"\n📊 Resumo: {indexed_count}/{len(md_files)} arquivos indexados com sucesso")
        return indexed_count > 0
        
    except ImportError as e:
        print(f"\n⚠️ File Search Hybrid não disponível: {e}")
        print("   Os documentos serão usados via busca local (fallback)")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na inicialização do File Search: {str(e)}")
        print("   Os documentos serão usados via busca local (fallback)")
        return True


def list_user_documentation():
    """
    Lista os documentos disponíveis no user_guide.
    Útil para verificar o que está disponível sem indexar.
    """
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    project_root = backend_dir.parent
    docs_dir = project_root / "docs" / "user_guide"
    
    print(f"📂 Documentação do Usuário ({docs_dir})")
    print("=" * 60)
    
    if not docs_dir.exists():
        print("❌ Diretório não encontrado")
        return
    
    md_files = sorted(docs_dir.glob("*.md"))
    
    if not md_files:
        print("❌ Nenhum arquivo encontrado")
        return
    
    total_size = 0
    for f in md_files:
        size = f.stat().st_size
        total_size += size
        print(f"  {f.name:<35} {size:>8} bytes")
    
    print("=" * 60)
    print(f"  Total: {len(md_files)} arquivos, {total_size:,} bytes")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Indexar documentação do usuário para File Search"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Apenas listar documentos sem indexar"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_user_documentation()
    else:
        print("🚀 Iniciando indexação de documentos do User Guide...")
        print("-" * 60)
        success = index_user_documentation()
        print("-" * 60)
        
        if success:
            print("✅ Indexação concluída com sucesso!")
        else:
            print("❌ Falha na indexação")
            sys.exit(1)
