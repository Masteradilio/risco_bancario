# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-12-26

### Fixed

#### Pipeline de Inferência
- **Colunas Obrigatórias**: Adicionado método `_ensure_base_columns()` no classifier que preenche automaticamente colunas faltantes (SCR, v-columns, cadastrais) com valores default sensíveis
- **Fallback 25%**: Corrigido problema onde falta de colunas causava exceções silenciosas que retornavam sempre 25% como fallback
- **Atributo penalidade_total**: Corrigido acesso ao atributo correto no `HistoricalAnalysis`

#### Performance
- **Latência Reduzida**: De ~1000ms para ~45ms por requisição (22x mais rápido)
- **SHAP Desabilitado**: Cálculo SHAP desabilitado temporariamente (causava ~5s de latência adicional e erros)
- **Mínimo PRINAD**: Adicionado floor de 0.5% - nenhum cliente tem risco zero

### Changed

#### Dashboard v2.0 (`dashboard.py`)
- **Timeline no Topo**: Gráfico de timeline movido para topo da página principal
- **Controles na Sidebar**: Botões de streaming movidos para sidebar esquerda
- **Intervalo Configurável**: Seletor de intervalo de 1-10 segundos (padrão: 2s)
- **Streaming Integrado**: Dashboard envia requisições diretamente à API (não precisa mais do streaming_sender.py externo)

#### Perfis de Simulação
- **7 Perfis Graduais**: Substituídos 4 perfis extremos por 7 perfis realistas:
  - `excelente` (25%): PRINAD 0.5-2% → Rating A1
  - `muito_bom` (20%): PRINAD 2-5% → Rating A2
  - `bom` (20%): PRINAD 5-10% → Rating A3
  - `moderado` (15%): PRINAD 10-20% → Rating B1
  - `atencao` (10%): PRINAD 20-35% → Rating B2
  - `risco` (7%): PRINAD 35-70% → Rating B3/C1
  - `alto_risco` (3%): PRINAD 70-100% → Rating C2/D
- **SCR Variável**: Dados SCR agora variam conforme perfil (AA até G)
- **V-Columns Graduais**: Exposição em atraso progride gradualmente entre perfis

### Added
- **test_diagnosis.py**: Script de diagnóstico para testar variação de PRINAD e latência

## [1.1.0] - 2025-12-24

### Added

#### Sistema de Streaming Integrado
- **Simulação de Sistemas Bancários**: Adicionada simulação de origem das solicitações com proporções realistas:
  - `app_mobile` (50%), `sis_agencia` (30%), `terminal_eletronico` (15%), `central_cliente` (5%)
  
- **Produtos de Crédito**: Implementada seleção ponderada de produtos:
  - `consignado` (40%), `banparacard` (20%), `cartao_credito` (20%), `imobiliario` (10%), `antecipacao_13_sal` (5%), `cred_veiculo` (3%), `energia_solar` (2%)

- **Tipo de Solicitação**: Adicionado campo para tipo de solicitação:
  - `Proposta` (70%), `Contratacao` (30%)

#### API FastAPI
- **Persistência em CSV**: Novo arquivo `dados/avaliacoes_risco.csv` que armazena todas as avaliações realizadas
- **Endpoint `/avaliacoes`**: GET para recuperar as últimas N avaliações persistidas
- **Endpoint `/stats`**: GET para estatísticas agregadas por sistema, produto e tipo
- **Endpoint `/avaliacoes` DELETE**: Para limpar dados de avaliações

#### Dashboard Streamlit
- **Botão de Streaming**: Controles para iniciar/parar o streaming diretamente do Dashboard
- **Métricas por Sistema**: Visualização de distribuição de solicitações por sistema de origem
- **Métricas por Produto**: Gráfico horizontal de produtos de crédito mais solicitados
- **Métricas por Tipo**: Contadores de Propostas vs Contratações
- **Tabela de Avaliações**: Tabela em tempo real com todas as colunas da avaliação de risco
- **Auto-refresh**: Atualização automática a cada 5 segundos

#### Scripts de Inicialização
- **start_system.ps1**: Script PowerShell para Windows que inicia API e Dashboard em terminais separados
- **start_system.sh**: Script Bash para Linux/Mac com mesma funcionalidade

### Changed
- **streaming_sender.py**: Refatorado para incluir campos de simulação bancária e usar intervalo padrão de 5 segundos
- **api.py**: Estendido com modelos Pydantic para novos campos e lógica de persistência
- **dashboard.py**: Redesenhado com novas visualizações e controles de streaming
- **classifier.py**: Corrigida inicialização do `HistoricalPenaltyCalculator` para usar parâmetros corretos (`max_penalty_internal`, `max_penalty_external`)

### Fixed
- Correção do atributo `penalidade` para `penalidade_total` no `HistoricalAnalysis`
- Correção dos parâmetros do `HistoricalPenaltyCalculator` no classifier

## [1.0.0] - 2024-12-23

### Added
- Lançamento inicial do PRINAD
- Modelo ensemble XGBoost + LightGBM para classificação de risco
- API FastAPI com endpoints `/health`, `/predict`, `/batch`, `/ws/stream`, `/metrics`
- Dashboard Streamlit para monitoramento em tempo real
- Integração com dados mockados do SCR do Banco Central
- Explicabilidade via SHAP
- Sistema de ratings A1 → D em conformidade com Basel III
