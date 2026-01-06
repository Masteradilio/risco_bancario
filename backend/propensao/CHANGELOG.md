# PROLIMITE Changelog

Todas as alterações notáveis do módulo de propensão serão documentadas neste arquivo.

## [2.0.0] - 2026-01-02 (REVAMP BACEN 4966)

### 🏛️ Conformidade Regulatória

#### ECL / IFRS 9 / Resolução BACEN 4966
- **Fórmula Central**: `ECL = PD × LGD × EAD`
- **3 Estágios IFRS 9**:
  - Stage 1: ECL horizonte 12 meses (usa PD_12m)
  - Stage 2: ECL horizonte lifetime (usa PD_lifetime)
  - Stage 3: ECL lifetime com LGD máxima (LGD × 1.5)
- **Regra de Arrasto** (Drag Effect): Se um produto vai para Stage 3, TODOS os produtos do cliente migram
- **Critérios de Cura**: Reversão de stage após período de observação

### ✨ Novos Módulos

#### StageClassifier (`stage_classifier.py`)
- Classificação automática de exposições nos 3 stages IFRS 9
- Múltiplos gatilhos: dias_atraso, downgrade, evento_judicial, insolvência
- Regra de arrasto implementada (todos produtos migram juntos)
- Critérios de cura (Stage 2→1 requer 6 meses, Stage 3→2 requer 12 meses)

#### LimitReallocation (`limit_reallocation.py`)
- Cálculo do Limite Global FIXO (só muda quando renda muda)
- Grupos de produtos: A (35%), B (30%), C (5%)
- Realocação por propensão:
  - Produtos com propensão < 45% têm limite reduzido
  - Espaço liberado é redistribuído para produtos com propensão > 55%
- Limite legal do consignado (35%) nunca é reduzido

### 🔧 Refatorações

#### ECL Engine v2.0 (`ecl_engine.py`)
- **PD Calibrado**: Usa tabela PD_POR_RATING com PD_12m e PD_lifetime
- **EAD com CCF**: `EAD = saldo + (limite_disponível × CCF)`
- **Stage Integration**: Integração com StageClassifier
- **Drag Effect**: Suporte a arrasto no cálculo de portfólio
- Métodos:
  - `calcular_ecl_individual()` - Cálculo completo com todos parâmetros
  - `calcular_ecl_individual_simples()` - Retrocompatibilidade
  - `calcular_ecl_cliente()` - Múltiplos produtos com arrasto
  - `calcular_ecl_portfolio()` - Portfólio completo

#### Shared Utils (`shared/utils.py`) - +262 linhas
- `PD_POR_RATING`: 11 ratings calibrados (A1 → DEFAULT)
- `CCF_POR_PRODUTO`: 10 produtos com Credit Conversion Factor
- `PARAMS_LIMITE_GLOBAL`: Grupos A/B/C para limite global
- `CRITERIOS_STAGE`: Critérios de migração IFRS 9
- `CRITERIOS_CURA`: Critérios de reversão de stage
- Funções:
  - `get_rating_from_prinad()`
  - `calcular_pd_por_rating()`
  - `calcular_ead()`
  - `calcular_limite_global_fixo()`
  - `get_stage_from_criteria()`
  - `calcular_ecl_por_stage()`

#### Pipeline Runner
- `ECLCalculator` atualizado para usar ECL Engine v2.0
- Novas colunas de saída: pd_12m, pd_lifetime, stage, ecl_horizonte

### 📊 Valores Calibrados

#### PDs por Rating (12 meses)

| Rating | PD_min | PD_max | Mult. Lifetime |
|--------|--------|--------|----------------|
| A1 | 0.03% | 0.50% | 2.5x |
| A2 | 0.50% | 1.00% | 2.5x |
| A3 | 1.00% | 2.00% | 3.0x |
| B1 | 2.00% | 3.50% | 3.5x |
| B2 | 3.50% | 5.00% | 4.0x |
| B3 | 5.00% | 7.00% | 4.5x |
| C1 | 7.00% | 10.00% | 5.0x |
| C2 | 10.00% | 15.00% | 5.5x |
| C3 | 15.00% | 25.00% | 6.0x |
| D | 25.00% | 50.00% | 6.5x |
| DEFAULT | 50.00% | 100% | 7.0x |

#### CCF por Produto

| Produto | CCF |
|---------|-----|
| Consignado | 100% |
| Imobiliário | 100% |
| Veículo | 100% |
| Cartão Rotativo | 75% |
| Banparacard | 75% |
| Cheque Especial | 70% |
| Crédito Sazonal | 50% |

### ✅ Testes
- **27 novos testes** para ECL Engine v2.0
- Cobertura de todos os cenários: stages, arrasto, calibração PD

---

## [1.1.0] - 2026-01-01


### ✨ Adicionado

#### Data Consolidation Framework
- **data_consolidator.py** - Reescrito para criar base unificada:
  - Mescla dados reais (cadastro, limites, 3040) com sintéticos
  - Suporte a 9 produtos de crédito
  - Geração de 352.220 registros (156.891 clientes × produtos)
  - Regras de distribuição de produtos por cliente

#### Pipeline Runner
- **pipeline_runner.py** - Novo orquestrador do pipeline completo:
  - Enriquecimento PRINAD (score + rating)
  - Enriquecimento de Propensão
  - Cálculo de ECL
  - Otimização de limites
  - Geração de notificações por horizonte (D+0, D+30, D+60)

### 📋 Regras de Negócio Oficiais (v1.0)

| Ação | Condição | Novo Limite |
|------|----------|-------------|
| ZERAR | PRINAD = 100 | 0 |
| REDUZIR 25% | PRINAD 90-99 | 25% do atual |
| REDUZIR 50% | PRINAD 80-89 OU baixa propensão + baixa utilização | 50% do atual |
| AUMENTAR | PRINAD < 80 + propensão + margem + comprometimento < 65% | +25% |
| MANTER | Demais casos | Sem alteração |

### 📚 Documentação
- `propensao/docs/mysql_ddl.sql` - DDL MySQL para TI
- `propensao/docs/dicionario_dados.md` - Dicionário de dados
- `propensao/docs/requisitos_producao.md` - Requisitos de produção

### 🔧 Melhorias
- Adicionados campos `COMPROMETIMENTO_POR_PRODUTO` e `DISTRIBUICAO_PRODUTOS` em `shared/utils.py`
- 124 testes passando

---

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
