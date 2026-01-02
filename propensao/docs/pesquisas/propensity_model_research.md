
## Modelo de Propensão de Uso de Crédito: Otimização de Limites Alinhado à ECL (Resolução 4966/2021)

Sua questão toca em uma das fronteiras mais sofisticadas da gestão de risco de crédito moderno: como alocar limites dinamicamente com base na **probabilidade real de uso** de cada produto, otimizando simultaneamente a **perda esperada (ECL)** que o banco precisa provisionar. Este é o diferencial competitivo de bancos de primeiro mundo. Vou estruturar uma resposta detalhada sobre a implementação integrada.

***

### 1. Por Que Propensity Models São Críticos na Era da ECL

#### 1.1 O Problema de Limites Não Utilizados

Sob a Resolução 4966/2021, o banco deve reconhecer ECL (Expected Credit Loss) conforme:[1][2]

```
ECL = PD × LGD × EAD
```

**A questão crítica**: O EAD é baseado no **limite aprovado**, não no saldo utilizado. Isto significa:[1]

- Cliente tem limite de R$10.000 em crédito pessoal
- Cliente **não usa** nada (saldo = R$0)
- Banco ainda provisiona: ECL = PD × LGD × R$10.000

Este limite não utilizado consome **capital do banco** (capital regulatório alocado) sem gerar receita. Se o banco tem 1 milhão de clientes com limite médio de R$5.000 cada, e 40% **nunca usam**, está alocando capital de forma ineficiente em ~R$2 bilhões de limites inutilizados.[3][4]

#### 1.2 A Solução: Propensity-Based Limit Optimization

Um **propensity model** prediz: "*Qual é a probabilidade de este cliente consumir crédito pessoal nos próximos 12 meses?*"[5][6][7]

**Aplicação prática**:

| Cliente | Propensão Pessoal | Recomendação | Limite Novo | ECL Antigo | ECL Novo | Capital Liberado |
|---------|------------------|--------------|------------|-----------|----------|-----------------|
| A | 85% | Aumentar | R$5.000 | R$30 | R$50 | -R$36 (alocado) |
| B | 15% | Reduzir | R$500 | R$30 | R$3 | +R$48.60 (liberado) |
| C | 50% | Manter | R$2.000 | R$30 | R$30 | R$0 |

**Agregado para 1 MM de clientes**:
- Capital liberado: ~R$500 MM
- Este capital pode ser redeployado para novos empréstimos
- Aumento de receita potencial: R$500MM × 10% (spread) = +R$50MM/ano

***

### 2. Propensity Models por Produto: Características e Features

#### 2.1 Crédito Pessoal Sem Garantias

**O que é propensão alta?**[8][9][10]

Um cliente com propensão alta para pessoal típicamente:
- Já tomou pessoal antes (comportamento comprovado)
- Tem transações frequentes (atividade bancária > 10/mês)
- Utiliza débito/crédito regularmente (não usa só dinheiro)
- Tem score interno > 600 (capacity mínimo)
- Ainda tem "espaço" de endividamento (DTI < 70%)

**Features principais**:[11][9][12][8]
- `credit_score_internal` (0-850): Core predictor
- `transaction_frequency_12m` (0-500): Quanto usa o banco
- `discretionary_spending_ratio` (0-100%): Gasta em lazer? (cartão, restaurante)
- `revolving_credit_utilization` (0-100%): Que % do cartão usa
- `historical_personal_loan_usage` (count): Quantos pessoais tomou antes
- `months_since_last_transaction` (0-1000): Quanto tempo parado
- `payment_history_score` (0-100): % pagamentos em dia
- `debt_to_income_ratio` (0-500%): Quanto já deve vs. renda

**Padrão Comportamental**: 
- Pessoal é produto de necessidade/impulso → frequência de transação ALTA é preditor forte
- Clientes que gastam discretionário frequente tendem a pedir pessoal para "cobrir"[9]

#### 2.2 Crédito Consignado (INSS/Servidores)

**Elegibilidade vs. Propensão**:[8][9]

Aqui a elegibilidade é **booleana** (é INSS/Servidor SIM/NÃO). Mas propensão varia:
- Cliente INSS elegível, 65 anos, margem já 90% utilizada → propensão BAIXA (não tem espaço)
- Cliente INSS elegível, 55 anos, margem 20% utilizada → propensão ALTA

**Features principais**:
- `is_inss_or_public_servant` (booleano): Filtro de elegibilidade
- `margem_consignavel_remaining_pct` (0-100%): % margem livre (45% da renda)
- `age` (25-100): Janela de vida útil (mais velho = menor tempo payoff)
- `margem_utilization_ratio` (0-100%): Quanto da margem já usa
- `months_employed` (0-600): Estabilidade no setor público
- `history_refinancing` (count): Quantas vezes refinanciou (indicador de comportamento cíclico)
- `consigned_arrears_historical` (0-100%): Histórico de atrasos em consignado específico

**Padrão Comportamental**:
- Consignado é **muito previsível** (renda garantida, retenção automática) → AUC em modelos muito alto (90%+)
- Cliente refinancia periodicamente (a cada 12-24 meses) quando termina contrato anterior

#### 2.3 Crédito Imobiliário

**Complexidade**: Baixa frequência (cada cliente toma 1-2× na vida), mas alto valor[10][9][8]

**Features principais**:
- `credit_score_internal` (700+ ideal): Risco deve ser baixo
- `has_property_registered` (booleano): Já é proprietário? (interesse)
- `estimated_property_value` (R$): Colateral disponível
- `annual_income` (R$): Capacity verificada
- `mortgage_prepayment_pattern` (0-100%): Se tem imobiliário anterior, paga antecipado?
- `website_visits_real_estate_category` (count): Comportamento de busca
- `income_stability_cv_12m` (0-100): Variação de renda
- `employment_sector` (categorizado): Alguns setores têm acesso melhor

**Padrão Comportamental**:
- Imobiliário é o produto com **menor propensão** (2-15% ao ano para população PF)
- Decisão é planejada (13-24 meses de antecedência): WebSite visits, simuladores são preditores
- Momento da vida importa: casamento, novo emprego (mudança para capital)

#### 2.4 Financiamento de Veículo

**Features principais**:
- `historical_vehicle_financing` (count): Tomou antes? (repeat buyer)
- `transportation_spending_pattern` (R$): Gasta com Uber, combustível, manutenção?
- `vehicle_ownership` (booleano, idade): Tem carro? De que ano?
- `geographic_region` (categorizado): Urbano (precisa carro mais)
- `credit_score_internal` (600-750): Veículo aceita risco médio
- `driving_record_proxy` (booleano): Seguro de auto ativo? (comportamento cuidadoso)
- `monthly_income_pct_transportation` (0-30%): Quanto da renda gasta

**Padrão Comportamental**:
- Veículo é sazonal (Black Friday, fim ano, bônus)
- Repeat buyers (troca a cada 4-5 anos) são altamente propensos

#### 2.5 Cartão de Crédito

**O contrário de pessoal**: Cartão é **contínuo e recorrente**[12][11][8]

**Features principais**:
- `transaction_frequency_30d` (0-1000): # transações/mês (forte predictor)
- `credit_card_utilization_ratio` (0-100%): Que % do limite usa (if has card)
- `discretionary_spending_pct` (0-100%): Compras não-essenciais
- `spending_volatility_cv` (0-200%): Padrão estável ou errático?
- `payment_consistency_score` (0-100%): Paga sempre integral ou revolving?
- `months_active_on_platform` (0-200): Quanto tempo cliente de banco
- `app_engagement_score` (0-100): Usa app frequentemente? (behavioral)
- `online_shopping_ratio` (0-100%): Que % de compras é online (card-heavy)

**Padrão Comportamental**:
- Cartão é **behavioral heavy**: Como cliente interage com app, frequência de compra online importa mais que renda
- Utilization stable (~30%) = propensão ALTA (cliente "treina-se")
- Utilization 0% = propensão BAIXA (aversão a revolving ou vive poupando)

#### 2.6 Antecipação 13º Salário / Restituição IR

**O produto MAIS previsível**[5][9][8]

**Features principais**:
- `employment_type` (CLT, PJ, autônomo): CLT = 13º garantido
- `is_income_tax_filer` (booleano): Declara IR = potencial restituição
- `historical_13th_advances` (count): Quantas vezes antecipou antes
- `current_month` (1-12): Não faz sentido antecipar em jan/fev (ainda falta meses)
- `bonus_reception_pattern` (booleano): Empresa paga bônus ao 13º?
- `debt_repayment_behavior_seasonal` (0-100%): Paga antecipado em nov/dez?
- `income_level` (faixas): Renda > 2SM = mais interesse

**Padrão Comportamental**:
- 13º é **ultra-sazonal**: Pico nov/dez (antecipação), zero jan/fev
- Comportamento muitíssimo previsível (AUC pode chegar a 95%+)
- Eligibilidade é 99% por profile da população

#### 2.7 Financiamento Energia Solar

**O produto MENOS propensa** (penetração < 3% população)[9][10][8]

**Features principais**:
- `property_ownership` (booleano): Deve ser proprietário (restrição técnica)
- `monthly_electricity_bill` (R$): > R$200 = economia justificável
- `geographic_sunshine_index` (por CEP): RJ no inverno = 40% menos sol (reduz ROI)
- `credit_score_internal` (650+): Investimento verde, risco baixo
- `environmental_spending_pattern` (0-100%): Compra orgânico, reciclado? (proxy)
- `income_tier` (categorizado): Classe média (R$4-10k) = target
- `home_improvement_history` (count): Fez reforma antes? (willingness to invest)
- `digital_maturity_score` (0-100%): Tipo que lê sobre ESG?

**Padrão Comportamental**:
- Solar é **investimento**, não consumo imediato → cliente precisa ser educado (digital high)
- Propensão muito baixa: modelo pode ter acurácia menor (dados esparsos)

***

### 3. Arquitetura de Machine Learning: Algoritmos e Técnicas

#### 3.1 Algoritmo Primário: LightGBM

**Por que LightGBM é melhor que XGBoost para propensidade?**[13][14][15][5]

LightGBM (Light Gradient Boosting Machine) é o algoritmo mais efetivo na prática bancária global para modelos de propensão:[14][15][5]

| Métrica | XGBoost | LightGBM | Vencedor |
|---------|---------|----------|----------|
| **Tempo treino (500k registros)** | 120s | 45s | LightGBM (2.7x mais rápido) |
| **Memória** | 4.2GB | 1.8GB | LightGBM (57% menos) |
| **AUC-ROC (baseline)** | 0.916 | 0.919 | LightGBM (tie) |
| **AUC com SMOTEENN** | 0.935 | 0.952 | LightGBM (+17bps) |
| **Feature Importance Estabilidade** | Boa | Excelente | LightGBM (interpretável) |
| **Handling Missing Values** | Bom | Excelente | LightGBM (nativo) |

**Hyperparâmetros recomendados**:[15][14]

```python
LGBMClassifier(
    num_leaves=31,               # Leaf-wise growth (profundidade)
    learning_rate=0.05,          # Conservador (evita overfit)
    n_estimators=100,            # Iterações boosting
    max_depth=7,                 # Limite profundidade (regularização)
    subsample=0.8,               # 80% amostras por iteração
    colsample_bytree=0.8,        # 80% features por árvore
    lambda_l1=0.1,               # L1 regularization
    lambda_l2=0.1,               # L2 regularization
    min_child_samples=20,        # Mínimo samples por folha
    objective='binary',          # Classificação binária (propensão sim/não)
    metric='auc',                # Otimiza AUC
    verbose=10
)
```

**Performance esperada por produto**:[15]

```
Crédito Pessoal: AUC 0.87-0.92 (dados abundantes)
Consignado: AUC 0.89-0.94 (população homogênea)
Imobiliário: AUC 0.80-0.88 (dados esparsos, mas sinais claros)
Cartão: AUC 0.88-0.93 (comportamento transacional previsível)
13º/IR: AUC 0.92-0.96 (ultra-sazonal, muito previsível)
Solar: AUC 0.70-0.82 (dados muito esparsos, ruído)
```

#### 3.2 Ensemble com XGBoost e Random Forest

Prática bancária padrão é **ensemble**:[14][8][15]

```
Propensão Final = 0.70 × LightGBM_score 
                + 0.20 × XGBoost_score 
                + 0.10 × RandomForest_score
```

**Vantagens do ensemble**:
- LightGBM captura relações não-lineares complexas
- XGBoost valida (segundo vote, previne overfitting)
- Random Forest fornece robustez (menos sensível a outliers)
- Resultado: AUC melhora +1-2% vs. LightGBM standalone

#### 3.3 Técnicas de Balanceamento: SMOTEENN

Dados de propensão são **desbalanceados** (exemplo: 70% nunca usa pessoal, 30% usa):[14][15]

```
SMOTEENN = SMOTE + ENN
├─ SMOTE: Synthetic Minority Oversampling
│  └─ Gera sintéticos de "propensão alta" (minoria)
├─ ENN: Edited Nearest Neighbors
│  └─ Remove outliers/ruído de "propensão baixa" (maioria)
└─ Resultado: Dataset balanceado 50-50

Impacto:
├─ Sem SMOTEENN: AUC 85.5%, F1 0.72
└─ Com SMOTEENN: AUC 92.0%, F1 0.85 (+6.5% AUC, +13% F1)
```

#### 3.4 Redução de Dimensionalidade: PCA

Com 100+ features, risco de overfitting é alto:[15]

```
PCA (Principal Component Analysis):
├─ Reduz 100 features → 50 componentes (variância 95%)
├─ Remove multicolinearidade
├─ Acelera treino (-40% tempo)
└─ Melhora generalização (+1-2% AUC em teste)

Tradeoff:
├─ Perde interpretabilidade (componentes são combinações)
└─ Solução: Usar PCA para treino, features orig. para SHAP explanability
```

***

### 4. Features Críticas de Treinamento

#### 4.1 Top 15 Features Globais (Ranking por Importância)

Baseado em estudos de bancos global:[16][17][12][8][9]

| Rank | Feature | Tipo | Categoria | Por Quê? |
|------|---------|------|-----------|----------|
| 1 | `credit_score_internal` | Numérico | Scoring | Core predictor (0-850 capta risco geral) |
| 2 | `credit_utilization_ratio_current` | % | Comportamento | Proxy de appetite (alto uso = mais refinanciamento) |
| 3 | `annual_income` | R$ | Financeiro | Capacity absoluto |
| 4 | `transaction_frequency_12m` | Count | Comportamento | Engagement com banco (atividade alta = propositividade) |
| 5 | `revolving_utilization_ratio` | % | Comportamento | "Treino" em crédito revolving |
| 6 | `payment_history_score` | 0-100 | Comportamento | Confiabilidade (se paga cartão, paga pessoal) |
| 7 | `months_customer_tenure` | Meses | Histórico | Cliente antigo = estável |
| 8 | `delinquency_rate_12m` | % | Comportamento | Red flag (atrasos predizem padrão futuro) |
| 9 | `discretionary_spending_ratio` | % | Comportamento | "Estilo" consumidor (impulsivo = cartão/pessoal user) |
| 10 | `debt_to_income_ratio` | % | Financeiro | Espaço de endividamento (> 80% = não pode pedir mais) |
| 11 | `employment_stability_proxy` | 0-1 | Financeiro | Retenção de renda (CLT > Autônomo) |
| 12 | `product_holding_diversity` | Count | Comportamento | Multi-produto (customer vale mais) |
| 13 | `months_since_last_transaction` | Meses | Recência | Inatividade (sinal negativo) |
| 14 | `historical_product_usage_count` | Count | Histórico | Experiência prévia (conhece produto = propensão +) |
| 15 | `app_engagement_score` | 0-100 | Comportamento | Digital maturity (alta = receptivo a ofertas) |

#### 4.2 Features Específicas por Produto (Top 3 por tipo)

**Pessoal**:
1. `transaction_frequency` (atividade = propensão)
2. `discretionary_spending_ratio` (estilo vida)
3. `months_since_last_txn` (recência)

**Consignado**:
1. `margem_consignavel_remaining_pct` (espaço disponível)
2. `is_inss_eligible` (booleano elegibilidade)
3. `historical_consigned_refinance_count` (comportamento cíclico)

**Imobiliário**:
1. `has_property_registered` (interesse indicado)
2. `website_visit_real_estate_count` (comportamento busca)
3. `income_stability_cv` (capacity estável necessária)

**Cartão**:
1. `transaction_frequency_30d` (uso contínuo)
2. `online_shopping_ratio` (channel preference)
3. `credit_utilization_ratio` (se tem card, usa quanto?)

**13º/IR**:
1. `is_clt_employee` (elegibilidade 13º)
2. `current_month` (sazonalidade)
3. `historical_advance_count` (comportamento seasonal repeat)

**Solar**:
1. `property_ownership` (elegibilidade técnica)
2. `monthly_electricity_bill` (ROI da solar)
3. `environmental_spending_pattern` (proxy sustainability interest)

#### 4.3 Feature Engineering Específica

**Derived Features (Síntese)**:[12][9][14]

```python
# Para Pessoal
df['spare_debt_capacity'] = (df['annual_income'] * 0.30) - df['current_debt']
df['activity_engagement'] = df['transaction_frequency_12m'] / 365

# Para Consignado
df['margem_remaining_pct'] = (0.45 * df['renda']) - df['margem_utilizada']
df['age_to_retirement'] = 70 - df['age']  # Para INSS

# Para Cartão
df['card_maturity_score'] = df['months_with_card'] * df['utilization_ratio']
df['discretionary_intensity'] = df['discretionary_spend_12m'] / df['total_spend_12m']

# Para Imobiliário
df['ltv_capacity'] = df['estimated_property_value'] * 0.80
df['monthly_housing_budget'] = df['annual_income'] * 0.30

# Para 13º/IR
df['seasonal_advance_pattern'] = df['month'] in [11, 12]  # Nov/Dec
df['eligible_advance'] = df['is_clt_employee'] | df['is_ir_filer']
```

***

### 5. Dados de Treinamento: Requisitos Técnicos

#### 5.1 Volume e Composição Ideais

**Mínimo aceitável**:[16][9][15]
- **50.000 registros por produto** (para LightGBM com dados tabulares)
- **Período de 24 meses** de histórico (captura ciclos econômicos)
- **Atualização mensal** (retraining com dados novos)

**Ideal**:[16][9][15]
- **100.000-500.000 registros** (melhor performance, mais generalização)
- **36 meses** de histórico (3 ciclos econômicos)
- **Mensalmente** ou até **semanalmente** (bancos grandes)

**Para banco médio brasileiro** (2-3 MM clientes PF):
- Pessoal: 300-400k elegíveis → 100-150k amostra treino ✓ Adequado
- Consignado: 400-500k elegíveis (INSS + Serv. Púb.) → 150-200k amostra ✓ Excelente
- Imobiliário: 50-80k potenciais → 15-25k amostra (marginal, mas usável)
- Cartão: 1-1.5MM (maioria tem) → 300-500k amostra ✓ Excelente
- 13º: ~500-700k elegíveis (CLT) → 150-250k amostra ✓ Excelente
- Solar: 20-30k potenciais → 5-10k amostra (dados esparsos, modelos terão AUC ~75%)

#### 5.2 Estrutura Temporal de Dados

**Timeline recomendada**:[9][16][15]

```
Período Observação: T-24 a T-13 (treinamento histórico)
  │
  ├─ T-24 a T-18: Baseline (6 meses iniciais)
  │  └─ Coleta features demográficas, scoring, saldos iniciais
  │
  ├─ T-18 a T-13: Período estável (6 meses)
  │  └─ Observa padrões comportamentais, transações
  │
  Período Alvo: T-12 a T-1 (12 meses de observação)
  │
  ├─ T-12 a T-1:
  │  ├─ DID CUSTOMER CONSUME PRODUCT? SIM/NÃO
  │  ├─ Variável-target para treino do modelo
  │  └─ 1 = tomou algum pessoal / 0 = não tomou
  │
  T+0: Hoje (dia da scoring)
  │
  └─ Modelo prediz:
     "Qual é a chance de tomar pessoal nos próximos 12 meses?"
```

**Exemplo para Crédito Pessoal**:
```
Treino: Clientes com dados completos jan/2021-dez/2022
Target: Tomou pessoal em jan/2023-dez/2023? SIM/NÃO
Deploy: jan/2024 em diante (score nova propensão)
Retraining: Monthly (jan/2024 data, predict feb-2024 propensão)
```

#### 5.3 Balanceamento de Classes (Solução SMOTEENN)

**Desbalanceamento típico** (% que usa produto):[14][15]

```
Pessoal: 35% usou, 65% não usou (Desbalanceamento 65:35)
Consignado: 45% usou, 55% não usou (Menos desbalanceado)
Imobiliário: 8% usou, 92% não usou (Severamente desbalanceado)
Cartão: 70% usou, 30% não usou (Invertido, menos é problema)
Solar: 2% usou, 98% não usou (Extremo)
```

**Problema**: Modelo treina em dados desbalanceados tende a predizer sempre "não usou" (maioria).

**Solução: SMOTEENN**:[15][14]

```python
from imblearn.combine import SMOTEENN

smoteenn = SMOTEENN(random_state=42)
X_resampled, y_resampled = smoteenn.fit_resample(X_train, y_train)

# Resultado:
# Antes: 35% positivo, 65% negativo
# Depois: 50% positivo, 50% negativo (ou 60-40 conforme config)

# Impacto em AUC:
# Sem SMOTEENN: 0.80
# Com SMOTEENN: 0.87 (+7% AUC)
```

#### 5.4 Validação e Backtesting

**Holdout Testing**:[16][9][15]

```
Dataset Original: 100.000 registros
├─ Train: 70% (70.000) → Treina LightGBM
├─ Validation: 15% (15.000) → Tuning hiperparâmetros
└─ Test: 15% (15.000) → Avalia performance final (NUNCA VER DURANTE TREINO)

Métricas Esperadas (Test Set):
├─ Pessoal: AUC 0.87-0.92, F1 0.78-0.84
├─ Consignado: AUC 0.89-0.94, F1 0.80-0.86
├─ Cartão: AUC 0.88-0.93, F1 0.77-0.83
├─ 13º/IR: AUC 0.92-0.96, F1 0.84-0.90
└─ Solar: AUC 0.70-0.82, F1 0.55-0.68 (dados esparsos)

Se AUC < 0.75: Modelo não é confiável, volte ao drawing board
```

**Backtesting Prospectivo** (validação contínua em produção):[16]

```
Mês 1 (jan/2024):
├─ Modelo prediz propensão em jan
├─ Recomenda limites
└─ Registra: "Propensão pessoal 75% → AUMENTAR limite"

Mês 2 (fev/2024):
├─ Observa: Cliente realmente tomou pessoal em jan? SIM/NÃO
├─ Se SIM: Modelo acertou (positivo predito, positivo observado)
├─ Se NÃO: Modelo errou (falso positivo)
└─ Calcula accuracy, precision, recall no período

Métrica de Performance em Produção:
├─ Accuracy em Produção deve estar > 80%
├─ Se cair abaixo 75%, model drift detectado → retrain
├─ Feedback loop contínuo: Model v2, v3, v4...
```

***

### 6. Integração Propensão + ECL: O Fluxo Operacional

#### 6.1 Pipeline Completo (Diário/Real-time)

```
Cliente: João (PF)
Dados Atuais: Score 650, Renda R$4.000, DTI 60%, sem pessoal
│
└─ STEP 1: Feature Calculation
   └─ Compute 100 features para João
      ├─ credit_score_internal = 650
      ├─ annual_income = 48.000
      ├─ transaction_freq_12m = 145
      ├─ discretionary_ratio = 35%
      ├─ ... (100 features total)
      └─ Features prontas para LightGBM

     └─ STEP 2: Propensity Scoring (LightGBM)
        ├─ Input: 100 features
        ├─ Output: Probabilidades
        │  ├─ Propensão Pessoal = 0.76 (76%)
        │  ├─ Propensão Consignado = 0.05 (5%, não elegível)
        │  ├─ Propensão Cartão = 0.68 (68%)
        │  ├─ Propensão Imobiliário = 0.12 (12%)
        │  ├─ Propensão Veículo = 0.20 (20%)
        │  ├─ Propensão 13º = 0.80 (80%, é CLT + sazonalidade)
        │  └─ Propensão Solar = 0.02 (2%, muito baixa)
        │
        └─ STEP 3: Limit Recommendation Engine (Decision Tree)
           ├─ Pessoal: 76% > 70% → AUMENTAR
           │  └─ Novo limite: R$4.000 (era R$2.000)
           │
           ├─ Consignado: 5% < 40% + NÃO ELEGÍVEL → CANCELAR
           │  └─ Novo limite: R$0
           │
           ├─ Cartão: 68% > 40% → AUMENTAR
           │  └─ Novo limite: R$3.500 (era R$2.500)
           │
           ├─ Imobiliário: 12% < 40% → REDUZIR
           │  └─ Novo limite: R$25.000 (era R$100.000 pré-aprovado)
           │
           ├─ Veículo: 20% < 40% → REDUZIR
           │  └─ Novo limite: R$0 (cancelado)
           │
           ├─ 13º: 80% > 70% → AUMENTAR
           │  └─ Novo limite: R$3.000 (era R$1.000)
           │
           └─ Solar: 2% < 40% → CANCELAR
              └─ Novo limite: R$0

           └─ STEP 4: ECL Recalculation
              └─ Para cada produto, recalcula ECL
                 │
                 ├─ Pessoal (novo limit R$4.000):
                 │  ├─ PD₁₂ₘ = 3% (estimado modelo PD)
                 │  ├─ LGD = 40% (sem colateral)
                 │  ├─ EAD_novo = R$4.000
                 │  └─ ECL_novo = 3% × 40% × 4.000 = R$48
                 │  └─ ECL_antigo = 3% × 40% × 2.000 = R$24
                 │  └─ Δ ECL = +R$24 (alocado mais capital, +receita esperada)
                 │
                 ├─ Consignado (novo limit R$0):
                 │  └─ ECL_novo = R$0
                 │  └─ ECL_antigo (se tinha) = R$10
                 │  └─ Δ ECL = -R$10 (libera capital)
                 │
                 ├─ Cartão (novo limit R$3.500):
                 │  ├─ PD₁₂ₘ = 3.5% (cartão é mais arriscado que pessoal)
                 │  ├─ LGD = 45%
                 │  ├─ EAD_novo = R$3.500
                 │  └─ ECL_novo = 3.5% × 45% × 3.500 = R$55.125
                 │  └─ ECL_antigo = 3.5% × 45% × 2.500 = R$39.375
                 │  └─ Δ ECL = +R$15.75
                 │
                 ├─ Imobiliário (novo limit R$25.000):
                 │  ├─ PD_lifetime = 0.8% (baixo risco)
                 │  ├─ LGD = 20% (com colateral imóvel)
                 │  ├─ EAD_novo = R$25.000
                 │  └─ ECL_lifetime = 0.8% × 20% × 25.000 = R$40
                 │  └─ ECL_antigo (pré-aprovado) = 0.8% × 20% × 100.000 = R$160
                 │  └─ Δ ECL = -R$120 (libera MUITO capital)
                 │
                 ├─ Veículo (novo limit R$0):
                 │  └─ ECL_novo = R$0
                 │  └─ ECL_antigo = R$5
                 │  └─ Δ ECL = -R$5
                 │
                 ├─ 13º (novo limit R$3.000):
                 │  ├─ PD₁₂ₘ = 0.5% (muito baixo, renda garantida)
                 │  ├─ LGD = 30%
                 │  ├─ EAD_novo = R$3.000
                 │  └─ ECL_novo = 0.5% × 30% × 3.000 = R$4.50
                 │  └─ ECL_antigo = 0.5% × 30% × 1.000 = R$1.50
                 │  └─ Δ ECL = +R$3
                 │
                 └─ Solar (novo limit R$0):
                    └─ ECL_novo = R$0
                    └─ ECL_antigo = R$30
                    └─ Δ ECL = -R$30

              CONSOLIDADO:
              ├─ Pessoal: +R$24
              ├─ Consignado: -R$10
              ├─ Cartão: +R$15.75
              ├─ Imobiliário: -R$120  ← Capital liberado!!!
              ├─ Veículo: -R$5
              ├─ 13º: +R$3
              └─ Solar: -R$30
              
              ├─ ECL Total Delta = 24 + (-10) + 15.75 + (-120) + (-5) + 3 + (-30) = -R$122.25
              ├─ Capital Alocado Liberado = R$122.25 × 1.8 (fator conservador) = R$220/mês × 12 = R$2.640/ano
              └─ RESULTADO: Banco libera ~R$2.640 de capital para este cliente
                           (ao reduzir pré-aprovado imobiliário de R$100k → R$25k)

                └─ STEP 5: RAROC Check (Decision Gate)
                   └─ Para nova operação aprovada, valida:
                      │
                      ├─ Pessoal aumentado R$2.000:
                      │  ├─ Spread estimado: 2.5% = R$50/ano
                      │  ├─ ECL: R$24
                      │  ├─ Custos admin: R$15
                      │  ├─ Lucro ajustado: R$50 - R$24 - R$15 = R$11
                      │  ├─ Capital alocado: R$24 × 1.8 = R$43.20
                      │  ├─ RAROC: R$11 / R$43.20 = 25.5%
                      │  └─ RAROC mínimo = 10% → APROVADO ✓
                      │
                      └─ Imobiliário reduzido R$75.000:
                         ├─ Receita perdida: -R$30.375 (6 meses × 0.81% spread)
                         ├─ Mas capital liberado! Pode usar em pessoal (RAROC 25.5% >> imóvel)
                         └─ Decision: Sacrifica imóvel para ganho pessoal (melhor RAROC)

                   └─ STEP 6: Business Rules (Compliance)
                      └─ Validações:
                         ├─ NÃO reduzir limite se cliente está em Estágio 1 ECL (baixo risco)?
                         │  └─ João em Estágio 1 (score 650, adimplente) → OK reduzir solar
                         ├─ Máximo de 1 redução de limite por ano (friction)?
                         │  └─ Política: OK (não havia redução anterior)
                         └─ Notificar cliente antes de reduzir?
                            └─ Sim: SMS/Email → "Limit solar reduzido (não estava usando)"

                      └─ STEP 7: Comunicação ao Cliente
                         ├─ SMS: "Seu limite de pessoal ↑ para R$4.000! Aproveite."
                         ├─ Email: "Atualizamos seus limites (propensão + ECL optimization)"
                         ├─ App: "Limite de cartão aumentado: R$3.500 disponível!"
                         └─ App: "Limite de solar cancelado (não estava usando)"

                         └─ STEP 8: Logging / Auditoria
                            ├─ Registro: João | Pessoal | R$2k→R$4k | Propensão 76% | Data XX/XX
                            ├─ Registro: João | Solar | R$5k→R$0 | Propensão 2% | Data XX/XX
                            ├─ Auditoria: Quem fez? (Sistema Automático)
                            ├─ Rastreabilidade: Por quê? (Propensão modelo v12)
                            └─ Conformidade: Res. 4966 ECL recalculada? SIM ✓
```

***

### 7. Comparação com Bancos Internacionais e Práticas Globais

#### 7.1 Moody's Analytics: Markov Decision Process

Moody's desenvolveu um modelo mais sofisticado baseado em **programação dinâmica** para cartão de crédito:[18]

```
MDP (Markov Decision Process) Model:
├─ Estado: (Behavioral_Score, Balance)
│  └─ Exemplo: Estado (Score=650, Balance=R$1.500)
│
├─ Ação: Qual limite atribuir? (R$1.000, R$2.000, R$3.000, R$5.000...)
│
├─ Transição: Como cliente muda estado (Bellman equation)
│  └─ P(Score sobe para 700) = f(score, balance, payment_history)
│
└─ Reward (Objetivo a Maximizar):
   └─ E[Profit | action, state] = E[Interest + Fees - Losses]

Solução: Política ótima de limite por (score, balance)

Resultado: Rentabilidade +12-18% vs. limite estático
```

**Por que é mais sofisticado que propensity simples?**
- Propensity prediz: "Vai usar pessoal?"
- MDP otimiza: "Qual limite gera máximo RAROC?"
- Diferença: Propensity é binário (sim/não); MDP é contínuo (limite ótimo)

#### 7.2 Experian/FICO: Credit Limit Optimization (CLO)

Experian oferece solução "Ascend Intelligence Services Limit":[19]

```
CLO Stack:
├─ Data Input: Bureau data (Serasa, SPC) + Internal bank data
├─ ML Model: Prediz comportamento cliente para diferentes limites
├─ Optimization Engine: Testa 50+ cenários de limite em tempo real
│  └─ Prediz: "Se limite = R$1.000 → default prob = 2.5%, profit = R$50"
│  └─ Prediz: "Se limite = R$3.000 → default prob = 3.2%, profit = R$75"
│  └─ Prediz: "Se limite = R$5.000 → default prob = 4.8%, profit = R$80"
│  └─ Recomenda: R$5.000 (máximo profit)
│
└─ Output: Limit recommendation + confidence

Benefício: Reduz trial-and-error em 60-70% (vs. manual tuning)
```

#### 7.3 Akbank (Turquia): FICO Decision Optimizer

Akbank implementou otimização de limite em larga escala:[20]

```
Estratégia:
├─ Initial Credit Line (ICL): Novos clientes
│  └─ Usa propensity + scoring para atribuir limite inicial
│
├─ Credit Line Increase (CLI): Clientes existentes com histórico
│  └─ Usa comportamento histórico + propensity para aumentar limite
│
└─ Credit Line Decrease (CLD): Clientes de alto risco
   └─ Usa churn risk + default risk para reduzir limite

Resultado:
├─ Portfolio default rate: -15% (melhoria)
├─ Net interest margin: +25bps (mais ganho)
└─ Customer satisfaction: +8% (percebe "reconhecimento")
```

#### 7.4 AWS Personalize / GCP Recommender: Next Best Action

Amazon e Google oferecem plataformas de "Next Best Action" (NBA) para bancos:[21][22]

```
NBA = "Qual é a melhor ação para este cliente neste momento?"

Exemplo:
├─ Cliente acessa app
├─ Sistema calcula: propensão pessoal, cartão, 13º...
├─ Resultado: "Pessoal = 76% (alta)"
├─ NBA recomenda: "Ofereça pessoal AGORA no app"
│  └─ Timing: Quinta-feira 14h (história de interação)
│  └─ Canal: Push notification (taxa de conversão +32%)
│  └─ Mensagem: "João, sua propensão para pessoal é alta! R$4k disponível"
│
└─ Resultado: Conversão +15-25% vs. offer estático

Integração com ECL:
├─ Se cliente recebe oferta pessoal (propensão 76%)
├─ E aceita: limite é definido via propensity + ECL
├─ Else (não aceita): limite reduzido (propensão não validou)
```

#### 7.5 Práticas de Bancos Brasileiros

**Observações da pesquisa**:[4][23]

- **Dock (Fintech)**: Implementou "Smart Limit" aderente a Res. 4966 (jan/2025)
  - Ajusta limite dinamicamente sem customer friction
  - Comunicação proativa

- **Bancos Grandes (Itaú, Bradesco, Caixa)**: 
  - Implementando propensity via terceiros (Experian, SAS, FICO)
  - Maior foco em cartão/pessoal (volumes maiores)
  - Imobiliário ainda manual/lento

- **Gap detectado**: Integração explícita propensão + ECL é rara
  - Maioria calcula propensão E ecl separados
  - Falta automação de "reduza limite solar se ECL > threshold"

***

### 8. Exemplo Prático Completo: Pipeline para Banco Médio

#### 8.1 Cronograma de Implementação (6 meses)

```
Mês 1: Preparação Dados & Feature Engineering
├─ Extrair 36 meses histórico de clientes
├─ Computar 100 features por produto
├─ Validar qualidade dados (missing values, outliers)
└─ Dataset pronto: 300k registros/produto

Mês 2: Treino de Modelos
├─ LightGBM + XGBoost + Random Forest
├─ SMOTEENN balanceamento
├─ PCA redução dimensionalidade
├─ Tuning hiperparâmetros
└─ Modelos v1 prontos (AUC 85-93% esperado)

Mês 3: Validação & Backtesting
├─ Hold-out test (15% dataset)
├─ Backtesting prospectivo (6 meses históricos)
├─ Feature importance analysis
├─ SHAP explainability (interpretability)
└─ Modelos finalizados v1.0

Mês 4: Integração ECL
├─ Mapear propensão → recomendação limite
├─ Conectar à calculadora ECL (PD × LGD × EAD_novo)
├─ Validar regras (RAROC > 10%, DTI < 80%)
├─ Teste integração com Core Banking
└─ Pipeline pronto para produção

Mês 5: Piloto (1-5% clientes)
├─ Rodar modelo em 50-250k clientes
├─ Coletar feedback (customer churn? satisfaction?)
├─ Monitorar performance (accuracy, AUC)
├─ Ajustar thresholds se necessário
└─ Piloto validado

Mês 6: Full Rollout
├─ Deploy em 100% da base (2-3 MM clientes)
├─ Automação daily scoring
├─ Monitoramento contínuo (model drift detection)
├─ Retraining mensal
└─ Produção em regime

Resultado Esperado:
├─ ECL reduction: 10-15%
├─ Capital liberado: R$200-500MM (dependendo tamanho banco)
├─ Cross-sell rate: +5-8% (melhores limites aumentam compra)
└─ Customer satisfaction: +3-5% (reconhecimento personalizado)
```

#### 8.2 Equipe & Tecnologia Necessária

**People**:
- 1 Data Science Lead (propensity models)
- 2 ML Engineers (LightGBM, pipeline)
- 1 Risk Engineer (ECL integration)
- 1 Data Engineer (ETL, Big Data)
- 1 Product Manager (requirements, rollout)

**Tech Stack**:
- **ML Framework**: LightGBM, XGBoost (Python scikit-learn)
- **Big Data**: Spark (processamento 1MM+ clientes)
- **Database**: Hadoop/Redshift para feature store
- **Orquestração**: Airflow (daily retraining)
- **Monitoring**: Evidently AI, WhyLabs (model monitoring)
- **Explainability**: SHAP, Lime (interpretability)
- **Cloud**: AWS (SageMaker), Google Cloud (Vertex AI), ou On-premise

**Cost**:
- Software licenses (FICO/Experian): R$500k-2MM/ano
- Cloud infrastructure: R$100-300k/ano
- Personnel (6 pessoas): R$1.5-3MM/ano
- **Total**: R$2-5MM/ano (ROI em 2-3 meses com banco médio)

***

### 9. Conclusão Executiva

Um modelo robusto de **propensão de uso de crédito** integrado com **ECL (Resolução 4966)** fornece:

1. **Otimização de Capital**: Libera 15-25% de capital alocado em limites não utilizados
2. **Aumento de Rentabilidade**: +50-100bps RAROC (foco em clientes realmente interessados)
3. **Redução de Defaults**: Melhor seleção (aumenta limite para propensão alta, reduz para baixa)
4. **Customer Experience**: Ofertas personalizadas (aumenta satisfação +3-5%)

**Algoritmos recomendados** (ordem de preferência):
1. **LightGBM** (primário) - AUC 87-94%, velocidade
2. **XGBoost** (validação) - AUC 85-92%, robustez
3. **Random Forest** (ensemble) - AUC 80-88%, interpretabilidade

**Features críticas** (top 5):
1. Credit score interno
2. Credit utilization ratio
3. Annual income
4. Transaction frequency
5. Payment history score

**Dados necessários**:
- 50k-500k registros por produto
- 24-36 meses histórico
- Balanceamento SMOTEENN (dados desbalanceados)

**Integração ECL**: Propensão → Recomendação de Limite → Novo EAD → Novo ECL → Capital Liberado

Este é o padrão dos bancos globais líderes (Moody's, FICO, AWS, Experian, Akbank). Bancos brasileiros estão começando a implementar, com foco em 2025-2026.

[1](https://www.pwc.com/gx/en/audit-services/ifrs/publications/ifrs-9/revolving-credit-facilities-and-expected-credit%20losses.pdf)
[2](https://corporatefinanceinstitute.com/resources/career-map/sell-side/risk-management/expected-loss-definition-calculation-importance/)
[3](https://www.tdcommons.org/cgi/viewcontent.cgi?article=8000&context=dpubs_series)
[4](https://dock.tech/en/fluid/blog/cards-et-credit/smart-limit/)
[5](https://www.oajaiml.com/uploads/archivepdf/237151184.pdf)
[6](https://datamasters.ai/case-studies/propensity-to-buy-model/)
[7](https://www.datarobot.com/partner-solutions/propensity-to-buy-for-financial-services-customers/)
[8](https://www.linkedin.com/pulse/credit-limit-management-optimizing-limits-cardholders-gundala-osh9c)
[9](https://www.indebted.co/en-ae/blog/guides/what-is-the-behavioural-credit-scoring-model-and-how-does-it-work/)
[10](https://finezza.in/blog/behavioral-scoring-smart-approach-line-of-credit-risk/)
[11](https://support.sas.com/resources/papers/proceedings15/3328-2015.pdf)
[12](https://fastercapital.com/topics/key-factors-considered-in-behavioral-scoring-models.html)
[13](https://francis-press.com/uploads/papers/m8JsMRk3SRgwcchtnuAErYiCnp5YfFg8Ds8S6jJt.pdf)
[14](https://www.linkedin.com/posts/skphd_advanced-user-credit-risk-prediction-model-activity-7305647707396677633-3NWk)
[15](https://arxiv.org/pdf/2408.03497.pdf)
[16](https://www.tcmb.gov.tr/wps/wcm/connect/fbbf56d3-1427-48d9-92c3-446af0a7fef0/WP2508.pdf?MOD=AJPERES&CACHEID=ROOTWORKSPACE-fbbf56d3-1427-48d9-92c3-446af0a7fef0-pwn7z5i)
[17](https://dl.acm.org/doi/10.1145/3662739.3669913)
[18](https://www.moodys.com/web/en/us/insights/resources/Determining-the-Optimal-Dynamic-Credit-Card-Limit.pdf)
[19](https://www.experian.com/blogs/insights/credit-limit-optimization/)
[20](https://www.fico.com/blogs/credit-card-portfolio-optimization)
[21](https://www.wwt.com/article/the-next-best-action-for-banks-chapter-3-formulating-recommendations)
[22](https://www.leewayhertz.com/next-best-action-ai/)
[23](https://periodicos.unoesc.edu.br/race/article/view/32948/19362)
[24](https://dspace.mit.edu/bitstream/handle/1721.1/100614/932622145-MIT.pdf?sequence=1)
[25](https://pmc.ncbi.nlm.nih.gov/articles/PMC11389638/)
[26](https://www.linkedin.com/posts/cknichols_ai-machinelearning-treasurymanagement-activity-7326974162168700929-rIew)
[27](https://www.federalreserve.gov/econres/feds/files/2025088pap.pdf)
[28](https://pmc.ncbi.nlm.nih.gov/articles/PMC8898559/)
[29](https://www.sciencedirect.com/science/article/abs/pii/S037722172300975X)
[30](https://finance.unibocconi.eu/sites/default/files/files/media/attachments/DAydin_MPCL20160112112657.pdf)
[31](https://ifgeekthen.nttdata.com/s/post/modelos-de-propension-en-el-ambito-de-banca-digital-MCFK2R5FXWZFGVJPMYD5J2MOX4JA?language=en_US)
[32](https://arxiv.org/abs/2306.15585)
[33](https://www.sciencedirect.com/science/article/abs/pii/S0957417413001693)
[34](https://www.artefact.com/blog/scoring-customer-propensity-using-machine-learning-models-on-google-analytics-data/)
[35](https://www.fico.com/blogs/how-decision-optimization-improves-credit-line-management)
[36](https://arxiv.org/html/2509.03063v1)
[37](https://github.com/DiegoUsaiUK/Propensity_Modelling)
[38](https://github.com/mitalipatle/Credit-card-limit-prediction-in-python)
[39](https://assets.kpmg.com/content/dam/kpmgsites/in/pdf/2025/01/expected-credit-loss-ecl.pdf)
[40](https://www.aasb.gov.au/admin/file/content105/c9/IFRS9_IE_7-14.pdf)
[41](https://kpmg.com/in/en/insights/2025/01/expected-credit-loss-ecl.html)
[42](https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/ifrs-9-financial-instruments-disclosures)
[43](https://www.bis.org/bcbs/publ/d311.pdf)
[44](https://cfrr.worldbank.org/sites/default/files/2022-05/05_0.pdf)
[45](https://www.transorg.ai/case-study/optimizing-credit-limit-increase-for-a-leading-bank/)
[46](https://iongroup.com/blog/treasury/demystifying-cva-cecl-and-ecl-understanding-accounting-for-expected-credit-loss/)
[47](https://www.bis.org/fsi/fsisummaries/ifrs9.pdf)
[48](https://unitedfintech.com/cobaltfx/dynamic-credit/)
[49](https://www.pwc.ch/en/insights/accounting/IFRS9-understanding-expected-credit-losses.html)
[50](https://www.bankingsupervision.europa.eu/ecb/pub/pdf/ssm.IFRS9novelrisks_202407~5e0eb30b5c.en.pdf)
[51](https://web.stanford.edu/~glynn/papers/2018/ChehraziG18.pdf)
[52](https://www.elibrary.imf.org/downloadpdf/view/journals/001/2020/111/001.2020.issue-111-en.pdf)
[53](https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2021/issued/part-a/ifrs-9-financial-instruments.pdf)
[54](https://www.ijresonline.com/assets/year/volume-10-issue-2/IJRES-V10I2P107.pdf)
[55](https://revista.crcsc.org.br/index.php/CRCSC/article/download/3526/2734)
[56](https://www.nature.com/articles/s41599-025-05230-y)
[57](https://svitla.com/blog/machine-learning-for-credit-scoring/)
[58](https://www.credolab.com/blog/credit-scoring-models-how-to-create-a-model-that-works-best-for-you)
[59](https://ieeexplore.ieee.org/document/7585216/)
[60](https://www.nected.ai/blog/behavioral-credit-scoring)
[61](https://www.sciencedirect.com/science/article/abs/pii/S0032591025000774)
[62](https://www.sciencedirect.com/science/article/abs/pii/S1566014125001736)
[63](https://thedocs.worldbank.org/en/doc/935891585869698451-0130022020/original/CREDITSCORINGAPPROACHESGUIDELINESFINALWEB.pdf)
[64](https://arxiv.org/html/2402.17979v1)
[65](https://www.aimspress.com/article/id/678b834bba35de451fe3ccc5)
[66](https://www.pega.com/pt-br/next-best-action)
[67](https://onlinelibrary.wiley.com/doi/10.1155/2024/5585575)
[68](https://www.celent.com/insights/929146461)
[69](https://exacaster.com/6-steps-for-successful-telecom-next-best-action-next-best-offer-implementation/)
[70](https://www.braze.com/resources/articles/next-best-everything-ai-decisioning)
[71](https://www.legacycreditunion.com/learn/understanding-credit-utilization-maximizing-your-score-2)
[72](https://www.databricks.com/solutions/accelerators/next-best-action-healthcare-and-life-sciences)
[73](https://docs.aws.amazon.com/personalize/latest/dg/native-recipe-next-best-action.html)
[74](https://huntsman.usu.edu/qsps/files/documents/2017papers/Fulford.pdf)