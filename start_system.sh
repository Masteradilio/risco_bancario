#!/bin/bash
# PRINAD - Script de Inicialização do Sistema
# Este script inicia a API e o Dashboard em terminais separados

echo "============================================"
echo "   PRINAD - Sistema de Risco de Crédito    "
echo "============================================"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[1/3] Verificando ambiente virtual..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "      Ambiente virtual não encontrado!"
    echo "      Execute primeiro: python -m venv venv"
    echo "      E depois: source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "      Ambiente virtual encontrado!"
echo ""

echo "[2/3] Iniciando API FastAPI..."

# Determine the terminal emulator to use
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && source venv/bin/activate && echo 'Iniciando API PRINAD na porta 8000...' && python src/api.py; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -e "cd '$SCRIPT_DIR' && source venv/bin/activate && echo 'Iniciando API PRINAD na porta 8000...' && python src/api.py; exec bash" &
elif command -v osascript &> /dev/null; then
    # macOS
    osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && source venv/bin/activate && echo 'Iniciando API PRINAD na porta 8000...' && python src/api.py\""
else
    echo "      Nenhum terminal suportado encontrado. Iniciando em background..."
    source venv/bin/activate && python src/api.py &
fi

echo "      API iniciando em http://localhost:8000"
echo ""

# Wait a bit for API to start
sleep 3

echo "[3/3] Iniciando Dashboard Streamlit..."

if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && source venv/bin/activate && echo 'Iniciando Dashboard PRINAD...' && streamlit run app/dashboard.py --server.port 8501; exec bash"
elif command -v xterm &> /dev/null; then
    xterm -e "cd '$SCRIPT_DIR' && source venv/bin/activate && echo 'Iniciando Dashboard PRINAD...' && streamlit run app/dashboard.py --server.port 8501; exec bash" &
elif command -v osascript &> /dev/null; then
    # macOS
    osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && source venv/bin/activate && echo 'Iniciando Dashboard PRINAD...' && streamlit run app/dashboard.py --server.port 8501\""
else
    source venv/bin/activate && streamlit run app/dashboard.py --server.port 8501 &
fi

echo "      Dashboard iniciando em http://localhost:8501"
echo ""

echo "============================================"
echo "   Sistema iniciado com sucesso!           "
echo "============================================"
echo ""
echo "URLs de acesso:"
echo "  - API:       http://localhost:8000"
echo "  - API Docs:  http://localhost:8000/docs"
echo "  - Dashboard: http://localhost:8501"
echo ""
echo "Instruções:"
echo "  1. Aguarde os terminais iniciarem completamente"
echo "  2. Abra o Dashboard no navegador"
echo "  3. Clique em 'Iniciar Streaming' para começar a simulação"
echo ""
echo "Para parar: feche os terminais da API e Dashboard"
echo ""
