# PROLIMITE - Walkthrough Técnico

## Visão Geral

O módulo PROLIMITE implementa propensão a crédito e alocação dinâmica de limites seguindo IFRS 9 e Basel III.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         DADOS                                    │
├─────────────────────────────────────────────────────────────────┤
│  3040 (Carteira) ──┬── data_consolidator.py ──► Base Analítica  │
│  Limites ──────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MODELAGEM                                  │
├─────────────────────────────────────────────────────────────────┤
│  propensity_model.py ──► Score por produto (XGBoost)            │
│  lgd_calculator.py ──► LGD Basel III                            │
│  ecl_engine.py ──► ECL = PD × LGD × EAD                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OTIMIZAÇÃO                                  │
├─────────────────────────────────────────────────────────────────┤
│  limit_optimizer.py ──► Regras de alocação                      │
│  limit_predictor.py ──► Previsão 60/30/0 dias                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     NOTIFICAÇÃO                                  │
├─────────────────────────────────────────────────────────────────┤
│  notification_engine.py ──► Push/SMS/Banner                     │
└─────────────────────────────────────────────────────────────────┘
```

## Módulos

### 1. data_consolidator.py
- Lê CSVs de 3040 e limites (12 meses)
- Calcula taxa de utilização
- Gera features por cliente/produto

### 2. lgd_calculator.py
- LGD por tipo de garantia (Basel III Foundation IRB)
- Ajuste downturn (×1.25) para cenário de estresse
- Custos de workout incluídos

### 3. ecl_engine.py
- Fórmula: `ECL = PD × LGD × EAD`
- Classificação por Stage IFRS 9:
  - Stage 1: PRINAD < 20% (ECL 12m)
  - Stage 2: PRINAD 20-70% (ECL Lifetime)
  - Stage 3: PRINAD ≥ 70% (ECL Lifetime)

### 4. propensity_model.py
- 6 modelos (um por produto)
- XGBoost/LightGBM ensemble
- SHAP para explicabilidade
- Integração com PRINAD

### 5. limit_optimizer.py
Regras implementadas:
- Mínimo 30% do limite original
- Máximo 70% comprometimento de renda
- PRINAD D = zero limite
- Max-debt (≥65%): reduzir não utilizados

### 6. limit_predictor.py
- Análise de tendência temporal
- Previsão de utilização futura
- Horizonte 60/30/0 dias
- Cancelamento automático se usar

### 7. notification_engine.py
Canais:
- Push notification
- SMS
- Banner in-app

Templates por tipo de notificação.

## Verificação

Teste de ECL:
```
Produto: consignado
PRINAD: 15%
EAD: R$ 50.000
LGD: 48,75% (com downturn + workout)
ECL = 0.15 × 0.4875 × 50000 = R$ 3.656,25
```
