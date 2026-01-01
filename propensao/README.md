# 📊 PROLIMITE - Propensão a Crédito e Alocação Dinâmica de Limites

Módulo de propensão a crédito para otimização de limites e minimização de ECL (Expected Credit Loss).

## 🎯 Objetivo

Identificar clientes com propensão a consumir crédito por produto e realocar dinamicamente os limites para:
- **Reduzir ECL** para limites não utilizados
- **Aumentar limites** para clientes com alta propensão e baixo risco
- **Notificar clientes** sobre mudanças com antecedência

## 📁 Estrutura

```
propensao/
├── src/
│   ├── data_consolidator.py    # Integração 3040 + limites
│   ├── lgd_calculator.py       # LGD por produto (Basel III)
│   ├── ecl_engine.py           # Cálculo ECL = PD × LGD × EAD
│   ├── propensity_model.py     # Modelo multi-produto
│   ├── limit_optimizer.py      # Otimização com regras
│   ├── limit_predictor.py      # Previsão 60/30/0 dias
│   └── notification_engine.py  # Push/SMS/Banner
├── app/
│   └── dashboard_propensao.py  # Interface visual
├── tests/
│   └── test_*.py               # Testes unitários
├── modelo/
│   └── *.joblib                # Modelos treinados
└── docs/
    └── walkthrough.md          # Documentação técnica
```

## 🚀 Uso Rápido

### Calcular ECL

```python
from propensao.src.ecl_engine import ECLEngine

engine = ECLEngine()
result = engine.calcular_ecl_individual(
    cliente_id="12345678901",
    produto="consignado",
    prinad=15.0,  # PRINAD %
    ead=50000     # Limite
)
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

## 📋 Regras de Negócio (v1.0)

### Ações de Limite

| Ação | Condição | Novo Limite | Horizonte |
|------|----------|-------------|-----------|
| **ZERAR** | PRINAD = 100 (default completo) | 0 | Imediato |
| **REDUZIR 25%** | PRINAD 90-99 (Rating D) | 25% do atual | Imediato |
| **REDUZIR 50%** | PRINAD 80-89 (Rating C2) | 50% do atual | 30 dias |
| **REDUZIR 50%** | Propensão < 45 E Utilização < 30% | 50% do atual | 60 dias |
| **AUMENTAR** | PRINAD < 80 + Propensão > 55 + Margem + Comprometimento < 65% | +25% | Imediato |
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
