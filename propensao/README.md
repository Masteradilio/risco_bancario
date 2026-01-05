# 📊 PROLIMITE v2.0 - Propensão a Crédito e Alocação Dinâmica de Limites

**BACEN 4966 / IFRS 9 Compliant**

Módulo de propensão a crédito para otimização de limites e minimização de ECL (Expected Credit Loss).

## 🎯 Objetivo

Identificar clientes com propensão a consumir crédito por produto e realocar dinamicamente os limites para:
- **Reduzir ECL** para limites não utilizados (modelo de 3 stages IFRS 9)
- **Aumentar limites** para clientes com alta propensão e baixo risco
- **Realocar limites** entre produtos baseado em propensão
- **Notificar clientes** sobre mudanças com antecedência

## 🏛️ Conformidade BACEN 4966 (v2.0)

- **ECL = PD × LGD × EAD** (fórmula central)
- **3 Stages IFRS 9**: Stage 1 (12m), Stage 2 (lifetime), Stage 3 (lifetime + max LGD)
- **PD Calibrado** por rating band (A1 → DEFAULT)
- **EAD com CCF** (Credit Conversion Factor) por produto
- **Regra de Arrasto**: Todos produtos migram para Stage 3 juntos
- **Critérios de Cura**: Reversão de stage após período de observação

## 📁 Estrutura

```
propensao/
├── src/
│   ├── data_consolidator.py    # Integração + geração ECL/propensão
│   ├── stage_classifier.py     # 🆕 Classificação IFRS 9 (3 stages)
│   ├── ecl_engine.py           # 🔄 ECL v2.0 (BACEN 4966)
│   ├── lgd_calculator.py       # LGD por produto (Basel III)
│   ├── limit_reallocation.py   # 🆕 Realocação por propensão
│   ├── propensity_model.py     # Modelo multi-produto
│   ├── pipeline_runner.py      # 🔄 Pipeline v2.0 completo
│   ├── limit_optimizer.py      # Otimização com regras
│   └── notification_engine.py  # Push/SMS/Banner
├── app/
│   └── dashboard_propensao.py  # Interface visual
├── tests/
│   └── test_*.py               # 137 testes unitários
├── modelo/
│   └── *.joblib                # Modelos treinados
└── docs/
    ├── task_revamp.md          # 🆕 Plano de implementação BACEN 4966
    └── implementation_plan.md  # Documentação técnica
```

## 🚀 Uso Rápido

### Pipeline Completo (v2.0)

```python
from propensao.src.pipeline_runner import run_pipeline

# Executa pipeline completo BACEN 4966
df = run_pipeline()
# Gera: base_clientes_processada.csv com colunas ECL/propensão
```

### Calcular ECL (v2.0)

```python
from propensao.src.ecl_engine import ECLEngine

engine = ECLEngine()
result = engine.calcular_ecl_individual(
    cliente_id="12345678901",
    produto="consignado",
    prinad=15.0,           # PRINAD %
    limite_total=50000,    # Limite total
    saldo_utilizado=40000, # Saldo usado
    dias_atraso=0          # Dias de atraso
)
print(f"Stage: {result.stage}")
print(f"Rating: {result.rating}")
print(f"ECL: R$ {result.ecl:,.2f}")
```


### Otimizar Limites

```python
from propensao.src.limit_optimizer import LimitOptimizer

optimizer = LimitOptimizer()
cliente = optimizer.otimizar_cliente(
    cliente_id="12345678901",
    renda_bruta=10000,
    parcelas_mensais=5000,
    limites={'consignado': 100000, 'cartao_credito': 15000},
    propensoes={'consignado': 80, 'cartao_credito': 60},
    prinad=15.0,
    utilizacao_trimestral={'consignado': 0, 'cartao_credito': 0}
)

for rec in cliente.recomendacoes:
    print(f"{rec.produto}: {rec.acao.value} → R$ {rec.limite_recomendado:,.2f}")
```

## 📋 Regras de Negócio (v1.1)

### Ações de Limite

| Ação | Condição | Novo Limite | Horizonte |
|------|----------|-------------|-----------|
| **ZERAR** | Rating DEFAULT (PRINAD ≥ 95%) | 0 | Imediato |
| **REDUZIR 25%** | Rating D (PRINAD 85-94%) | 25% do atual | Imediato |
| **REDUZIR 50%** | Rating C3 (PRINAD 75-84%) | 50% do atual | 30 dias |
| **REDUZIR 50%** | Propensão < 45 E Utilização < 30% | 50% do atual | 60 dias |
| **AUMENTAR** | PRINAD < 75% + Propensão > 55 + Margem + Comprometimento < 65% | +25% | Imediato |
| **MANTER** | Todos os demais | Sem alteração | - |

### Parâmetros Gerais

| Parâmetro | Valor |
|-----------|-------|
| Comprometimento máximo | 65% da renda bruta |
| Avaliação completa | Mensal |
| Clientes novos | Diário |
| Notificação | 60/30/0 dias |

## 📊 LGD por Produto

| Produto | LGD Base | LGD Downturn |
|---------|----------|--------------|
| consignado | 35% | 44% |
| banparacard | 45% | 56% |
| cartao_credito | 70% | 88% |
| imobiliario | 12% | 15% |
| antecipacao_13_sal | 20% | 25% |
| cred_veiculo | 30% | 38% |

## 🧪 Testes

```bash
cd risco_bancario
python -m pytest propensao/tests/ -v
```

## 📚 Documentação

- [Walkthrough Técnico](docs/walkthrough.md)
- [Metodologia ECL IFRS 9](../docs/modelo_prolimite_ecl.md)
