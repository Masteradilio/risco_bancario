
import sys
import os
from unittest.mock import MagicMock, patch
import pandas as pd
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

# Mock database before importing tools
sys.modules["backend.agente.database"] = MagicMock()
from backend.agente.database import get_db

# Mock the DB instance
mock_db = MagicMock()
get_db.return_value = mock_db

# Mock fetch_one result for portfolio
mock_db.fetch_one.return_value = {
    "total_clientes": 1500,
    "total_exposicao": 5000000.0,
    "renda_media": 4500.0,
    "idade_media": 35,
    "ecl_total": 175000.0,
    "cobertura": 3.5,
    "pd_medio": 0.04,
    "lgd_medio": 0.45,
    "auc_roc_prinad": 0.88,
    "inadimplencia_90d": 0.02
}

# Now import the orchestrator
from agente.tools_orquestrador import executar_ferramenta, detectar_intencao_ferramenta

def test_flow():
    print("Testing Agent Flow with Refactored DB Tools...")
    
    # 1. Test Detection
    msg = "Gere um gráfico de pizza do prinad"
    intent = detectar_intencao_ferramenta(msg)
    print(f"\nMessage: '{msg}'")
    print(f"Detected Intent: {intent}")
    
    if intent and intent[0] == "gerar_grafico":
        print("✅ Intent Detection: PASS")
    else:
        print("❌ Intent Detection: FAIL")

    # 2. Test Execution (Portfolio)
    print("\nExecuting 'consultar_dados' for 'portfolio'...")
    result = executar_ferramenta("consultar_dados", {"fonte": "portfolio"})
    
    if result["sucesso"]:
        print("✅ Execution: PASS")
        print("Result Preview:", result["conteudo"][:100] + "...")
    else:
        print("❌ Execution: FAIL", result.get("erro"))

    # 3. Test Execution (PRINAD - using fetch_all)
    print("\nExecuting 'consultar_dados' for 'prinad'...")
    # Mock fetch_all for PRINAD
    mock_db.fetch_all.return_value = [
        {"rating": "A1", "quantidade": 500},
        {"rating": "B1", "quantidade": 300},
        {"rating": "C1", "quantidade": 200}
    ]
    
    result = executar_ferramenta("consultar_dados", {"fonte": "prinad"})
    if result["sucesso"]:
        print("✅ Execution: PASS")
        # Check if it returned text with markdown
        if "A1" in result["conteudo"]:
            print("✅ Data Content: PASS")
        else:
            print("❌ Data Content: FAIL")
    else:
        print("❌ Execution: FAIL", result.get("erro"))

if __name__ == "__main__":
    test_flow()
