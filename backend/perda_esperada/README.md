# Módulo Perda Esperada (ECL) - BACEN 4966/IFRS 9

Sistema completo para cálculo de **Expected Credit Loss (ECL)** em conformidade com a **Resolução CMN 4.966/2021** e **IFRS 9**.

## 🎯 Visão Geral

Este módulo **CONSOME** os resultados do módulo **PRINAD** e adiciona funcionalidades específicas para o cálculo completo de ECL:

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUXO DE DADOS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRINAD (Módulo Anterior)                                       │
│  ├── PRINAD Score (0-100%)                                      │
│  ├── Rating (A1 → DEFAULT)                                      │
│  ├── PD_12m (calibrado)         ──────┐                         │
│  ├── PD_lifetime (fórmula sobrevivência)│                       │
│  └── Stage IFRS 9 (1, 2, 3)            │                        │
│                                        ▼                        │
│  ╔═══════════════════════════════════════════════════╗         │
│  ║        PERDA ESPERADA (Este Módulo)               ║         │
│  ╠═══════════════════════════════════════════════════╣         │
│  ║  ┌─────────────────┐    ┌─────────────────┐       ║         │
│  ║  │ Grupos          │    │ Forward Looking │       ║         │
│  ║  │ Homogêneos (GH) │───▶│ K_PD_FL        │       ║         │
│  ║  └─────────────────┘    └────────┬────────┘       ║         │
│  ║                                  │                ║         │
│  ║  ┌─────────────────┐    ┌───────▼────────┐       ║         │
│  ║  │ LGD Segmentado  │    │ EAD + CCF      │       ║         │
│  ║  │ (Árvore Decisão)│    │ Específico     │       ║         │
│  ║  └────────┬────────┘    └────────┬───────┘       ║         │
│  ║           │                      │               ║         │
│  ║           └──────────┬───────────┘               ║         │
│  ║                      ▼                           ║         │
│  ║         ┌─────────────────────────┐              ║         │
│  ║         │ ECL = PD × LGD × EAD    │              ║         │
│  ║         │ + Pisos Mínimos (St. 3) │              ║         │
│  ║         └─────────────────────────┘              ║         │
│  ╚═══════════════════════════════════════════════════╝         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Componentes

### Herdados do PRINAD (NÃO duplicados aqui)
- ✅ PD_12m - Calculado pelo PRINAD
- ✅ PD_lifetime - Calculado pelo PRINAD
- ✅ Rating - Calculado pelo PRINAD
- ✅ Stage IFRS 9 - Calculado pelo PRINAD

### Funcionalidades deste módulo
| Componente | Arquivo | Descrição |
|------------|---------|-----------|
| **Grupos Homogêneos** | `modulo_grupos_homogeneos.py` | Agrupamento por PD usando K-means, percentis ou densidade. Inclui cálculo de WOE. |
| **Forward Looking** | `modulo_forward_looking.py` | Integração com API BACEN SGS, equações FL por produto, fatores K_PD_FL e K_LGD_FL. |
| **LGD Segmentado** | `modulo_lgd_segmentado.py` | LGD por árvore de decisão: Produto × Atraso × Valor × Prazo × Ocupação. |
| **EAD + CCF** | `modulo_ead_ccf_especifico.py` | Credit Conversion Factor específico por produto e cenário. |
| **Pisos Mínimos** | `pisos_minimos.py` | Pisos de provisão para Stage 3 conforme BCB 352. |
| **Triggers** | `modulo_triggers_estagios.py` | Triggers de migração entre estágios, arrasto de contraparte. |
| **Pipeline Integrado** | `pipeline_ecl.py` | Orquestra todos os componentes, consome PRINAD. |

## 🚀 Uso

### Uso Básico (com dados do PRINAD)

```python
from prinad.src.classifier import PRINADClassifier
from perda_esperada.src.pipeline_ecl import ECLPipeline

# 1. Classificar cliente com PRINAD (módulo anterior)
classifier = PRINADClassifier()
prinad_result = classifier.classify({
    'cpf': '12345678901',
    'dados_cadastrais': {...},
    'dados_comportamentais': {...}
})

# 2. Calcular ECL usando resultado do PRINAD
pipeline = ECLPipeline()
ecl = pipeline.calcular_ecl_de_prinad_result(
    prinad_result=prinad_result,
    produto='consignado',
    saldo_utilizado=5000,
    limite_total=10000,
    dias_atraso=0
)

print(f"ECL: R$ {ecl.ecl_final:,.2f}")
print(f"Stage: {ecl.stage}")
print(f"Grupo Homogêneo: {ecl.grupo_homogeneo}")
```

### Uso Manual (sem objeto PRINAD)

```python
from perda_esperada.src.pipeline_ecl import ECLPipeline

pipeline = ECLPipeline()

ecl = pipeline.calcular_ecl_completo(
    cliente_id='12345678901',
    produto='cartao_credito_rotativo',
    saldo_utilizado=3000,
    limite_total=5000,
    dias_atraso=45,
    
    # Dados que viriam do PRINAD
    prinad=55.0,
    rating='B3',
    pd_12m=0.055,
    pd_lifetime=0.24,
    stage=2
)

print(f"ECL: R$ {ecl.ecl_final:,.2f}")
print(f"K_PD_FL: {ecl.k_pd_fl:.4f}")
print(f"LGD Final: {ecl.lgd_final:.2%}")
```

### Uso de Componentes Individuais

```python
# Grupos Homogêneos
from perda_esperada.src import GruposHomogeneosConsolidado

gh = GruposHomogeneosConsolidado()
grupos = gh.criar_grupos_homogeneos(df, df['pd_score'])

# Forward Looking
from perda_esperada.src import ModeloForwardLooking

fl = ModeloForwardLooking('consignado')
pd_fl = fl.aplicar_equacao_documentada(dados_macro, grupo=2)

# Pisos Mínimos
from perda_esperada.src.pisos_minimos import aplicar_piso_minimo

piso = aplicar_piso_minimo(
    ecl_calculado=1500,
    ead=10000,
    dias_atraso=120,
    produto='cartao_credito',
    stage=3
)
```

## 📊 Tabelas de Referência

### WOE Scores por Grupo Homogêneo

| Produto | GH 1 | GH 2 | GH 3 | GH 4 |
|---------|------|------|------|------|
| Parcelados | -1.919 | -0.700 | 0.696 | 2.213 |
| Consignado | -1.665 | -1.038 | 0.009 | 0.825 |
| Rotativos | -2.811 | -0.887 | 0.387 | 1.028 |

### CCF por Produto

| Produto | CCF |
|---------|-----|
| Consignado | 100% |
| Imobiliário | 100% |
| Veículo | 100% |
| Cartão Rotativo | 75% |
| Cheque Especial | 70% |
| Crédito Sazonal | 50% |

### Pisos Mínimos (Stage 3) - Amostra

| Faixa Atraso | Pessoal | Rotativo | Consignado | Imobiliário |
|--------------|---------|----------|------------|-------------|
| 91-120 dias | 30% | 50% | 25% | 10% |
| 121-150 dias | 50% | 70% | 40% | 20% |
| > 360 dias | 100% | 100% | 85% | 50% |

## 🔧 Configuração

### Estrutura de Diretórios

```
perda_esperada/
├── src/
│   ├── __init__.py
│   ├── pipeline_ecl.py           # Pipeline integrador
│   ├── pisos_minimos.py          # Pisos regulatórios
│   ├── modulo_grupos_homogeneos.py
│   ├── modulo_forward_looking.py
│   ├── modulo_lgd_segmentado.py
│   ├── modulo_ead_ccf_especifico.py
│   ├── modulo_triggers_estagios.py
│   ├── modulo_estadiamento.py
│   ├── modulo_analise_writeoff.py
│   ├── ecl_engine.py             # Motor legado
│   └── lgd_calculator.py         # LGD legado
├── docs/
│   └── Documentação Técnica de Perda 4966 - BIP.md
├── artefatos_modelos/
└── relatorios/
```

## 📚 Referências

- [Resolução CMN 4.966/2021](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolução%20CMN&numero=4966)
- [Resolução BCB 352/2023](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolução%20BCB&numero=352)
- [IFRS 9 - Instrumentos Financeiros](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/)
- Documentação Técnica BIP (interna)

## ⚠️ Dependências

- **Módulo PRINAD**: Fornece PD_12m, PD_lifetime, Rating, Stage
- **shared/utils.py**: Funções compartilhadas e constantes
- **pandas**, **numpy**, **scikit-learn**: Processamento de dados
- **requests**: API BACEN SGS
