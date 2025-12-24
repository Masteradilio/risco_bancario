# PRINAD - Script de Inicialização do Sistema
# Este script inicia a API e o Dashboard em terminais separados

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   PRINAD - Sistema de Risco de Crédito    " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Get the directory where the script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[1/3] Verificando ambiente virtual..." -ForegroundColor Yellow

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "      Ambiente virtual não encontrado!" -ForegroundColor Red
    Write-Host "      Execute primeiro: python -m venv venv" -ForegroundColor Red
    Write-Host "      E depois: .\venv\Scripts\activate; pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host "      Ambiente virtual encontrado!" -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] Iniciando API FastAPI..." -ForegroundColor Yellow
# Start API in new terminal
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
    Set-Location '$ScriptDir'
    Write-Host 'Ativando ambiente virtual...' -ForegroundColor Cyan
    & '.\venv\Scripts\Activate.ps1'
    Write-Host 'Iniciando API PRINAD na porta 8000...' -ForegroundColor Green
    Write-Host 'Documentação: http://localhost:8000/docs' -ForegroundColor Cyan
    Write-Host ''
    python src/api.py
"@

Write-Host "      API iniciando em http://localhost:8000" -ForegroundColor Green
Write-Host ""

# Wait a bit for API to start
Start-Sleep -Seconds 3

Write-Host "[3/3] Iniciando Dashboard Streamlit..." -ForegroundColor Yellow
# Start Dashboard in new terminal
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
    Set-Location '$ScriptDir'
    Write-Host 'Ativando ambiente virtual...' -ForegroundColor Cyan
    & '.\venv\Scripts\Activate.ps1'
    Write-Host 'Iniciando Dashboard PRINAD...' -ForegroundColor Green
    Write-Host ''
    streamlit run app/dashboard.py --server.port 8501
"@

Write-Host "      Dashboard iniciando em http://localhost:8501" -ForegroundColor Green
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Sistema iniciado com sucesso!           " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URLs de acesso:" -ForegroundColor White
Write-Host "  - API:       http://localhost:8000" -ForegroundColor Cyan
Write-Host "  - API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  - Dashboard: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Instruções:" -ForegroundColor White
Write-Host "  1. Aguarde os terminais iniciarem completamente" -ForegroundColor Gray
Write-Host "  2. Abra o Dashboard no navegador" -ForegroundColor Gray
Write-Host "  3. Clique em 'Iniciar Streaming' para começar a simulação" -ForegroundColor Gray
Write-Host ""
Write-Host "Para parar: feche os terminais da API e Dashboard" -ForegroundColor Yellow
Write-Host ""
