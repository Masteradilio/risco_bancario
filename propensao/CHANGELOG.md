# PROLIMITE Changelog

Todas as alterações notáveis do módulo de propensão serão documentadas neste arquivo.

## [1.0.0] - 2025-12-30

### ✨ Adicionado

#### Estrutura do Projeto
- Reorganização do projeto em diretórios isolados:
  - `prinad/` - Módulo de risco de crédito existente
  - `propensao/` - Novo módulo de propensão e alocação de limites
  - `shared/` - Utilitários compartilhados entre módulos

#### Módulos Core (propensao/src/)
- **data_consolidator.py** (15KB) - Integração de dados 3040 + limites
  - Leitura de 12 meses de CSVs
  - Cálculo de taxa de utilização
  - Consolidação por cliente/produto
  
- **lgd_calculator.py** (7KB) - Cálculo de LGD Basel III
  - LGD por tipo de produto/garantia
  - Ajuste Downturn (×1.25) para cenário de estresse
  - Custos de workout incluídos
  
- **ecl_engine.py** (11KB) - Motor ECL IFRS 9
  - Fórmula: ECL = PD × LGD × EAD
  - Classificação por Stage (1, 2, 3)
  - Cálculo de portfolio agregado
  
- **propensity_model.py** (13KB) - Modelo multi-produto
  - 6 modelos (um por produto)
  - XGBoost/LightGBM ensemble
  - Integração com PRINAD
  - SHAP para explicabilidade
  
- **limit_optimizer.py** (13KB) - Otimizador de limites
  - Regra: mínimo 30% do limite original
  - Regra: máximo 70% comprometimento de renda
  - Regra: PRINAD D = zerar limite
  - Caso especial: max-debt (≥65%) reduz limites não utilizados
  
- **limit_predictor.py** (12KB) - Previsão de limites
  - Análise de tendência temporal
  - Horizonte 60/30/0 dias
  - Cancelamento automático se cliente usar limite
  
- **notification_engine.py** (14KB) - Sistema de notificações
  - Push notification
  - SMS
  - Banner in-app
  - Templates por tipo de notificação

#### Utilitários Compartilhados (shared/)
- **utils.py** - Constantes e funções comuns
  - 6 produtos de crédito configurados
  - LGD por produto (Basel III)
  - Limites máximos por salário
  - Funções: calcular_ecl, get_ifrs9_stage, etc.

### 📚 Documentação
- `propensao/README.md` - Documentação principal com exemplos de uso
- `propensao/docs/walkthrough.md` - Walkthrough técnico da arquitetura

### ✅ Testes Unitários

**91 testes passando** em 1.39s

| Arquivo | Testes |
|---------|--------|
| test_shared_utils.py | 17 testes |
| test_lgd_calculator.py | 15 testes |
| test_ecl_engine.py | 16 testes |
| test_limit_optimizer.py | 13 testes |
| test_limit_predictor.py | 16 testes |
| test_notification_engine.py | 14 testes |

Resultado:
```
=============================== 91 passed in 1.39s ===============================
```

### 📊 Valores de LGD Implementados (Basel III)

| Produto | LGD Base | LGD Downturn |
|---------|----------|--------------|
| consignado | 35% | 44% |
| banparacard | 45% | 56% |
| cartao_credito | 70% | 88% |
| imobiliario | 12% | 15% |
| antecipacao_13_sal | 20% | 25% |
| cred_veiculo | 30% | 38% |

### 📈 Exemplo de Cálculo ECL
```
Produto: consignado
PRINAD: 15% (Stage 1)
EAD: R$ 50.000
LGD: 48,75% (com downturn + workout)
ECL = 0.15 × 0.4875 × 50000 = R$ 3.656,25
```

### ⏳ Pendente
- Dashboard de propensão (`dashboard_propensao.py`)
- API de propensão (`api_propensao.py`)
- Backtesting com dados históricos
