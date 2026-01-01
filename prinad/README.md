# 🏦 PRINAD - Sistema de Risco de Crédito Bancário

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AUC-ROC: 0.9986](https://img.shields.io/badge/AUC--ROC-0.9986-brightgreen.svg)]()
[![Precision: 0.95](https://img.shields.io/badge/Precision-0.95-brightgreen.svg)]()
[![Recall: 0.97](https://img.shields.io/badge/Recall-0.97-brightgreen.svg)]()

Sistema de **Probabilidade de Inadimplência (PRINAD)** para instituições financeiras, em conformidade com as diretrizes **Basel III** e integração com o **SCR do Banco Central**.

## 📊 Métricas do Modelo

| Métrica | Valor | Status |
|---------|-------|--------|
| **AUC-ROC** | 0.9986 | ✅ Excelente |
| **Gini** | 0.9972 | ✅ Excelente |
| **KS** | 0.9595 | ✅ Excelente |
| **Precision** | 0.9535 | ✅ Meta atingida |
| **Recall** | 0.9713 | ✅ Meta atingida |

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PIPELINE PRINAD v2.0                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ Cadastro   │  │ Comportam. │  │ Histórico  │  │ SCR (BCB)  │    │
│  │ (15 feat.) │  │ (12 feat.) │  │ Interno    │  │ (16 feat.) │    │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘    │
│        │               │               │               │           │
│        └───────┬───────┴───────┬───────┴───────┬───────┘           │
│                ▼               ▼               ▼                    │
│        ┌───────────────────────────────────────────────────┐       │
│        │              Ensemble ML (XGBoost + LightGBM)     │       │
│        │              + Penalidades Históricas             │       │
│        │              50% ML | 25% Interno | 25% SCR       │       │
│        └──────────────────────┬────────────────────────────┘       │
│                               ▼                                     │
│        ┌───────────────────────────────────────────────────┐       │
│        │              PRINAD + Rating (A1 → D)             │       │
│        │              + Explicação SHAP                    │       │
│        └───────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

## 📂 Estrutura do Projeto

```
risco_bancario/
├── 📁 app/                    # Dashboard Streamlit
│   ├── dashboard.py           # Interface visual
│   └── streaming_sender.py    # Envio de dados em tempo real
├── 📁 dados/                  # Datasets
│   ├── base_cadastro.csv      # Dados cadastrais
│   ├── base_3040.csv          # Dados comportamentais
│   └── scr_mock_data.csv      # Dados SCR mockados
├── 📁 docs/                   # Documentação
│   ├── modelo_prinad_basel3.md # Metodologia Basel III
│   └── api_documentation.md   # Documentação da API
├── 📁 modelo/                 # Artefatos treinados
│   ├── ensemble_model.joblib  # Modelo ensemble
│   ├── preprocessor.joblib    # Preprocessador
│   └── shap_explainer.joblib  # Explicador SHAP
├── 📁 src/                    # Código-fonte
│   ├── train_model.py         # Treinamento do modelo
│   ├── classifier.py          # Classificador PRINAD
│   ├── data_pipeline.py       # Pipeline de dados
│   ├── feature_engineering.py # Engenharia de features
│   ├── historical_penalty.py  # Penalidades históricas
│   ├── scr_data_generator.py  # Gerador de dados SCR
│   └── api.py                 # API FastAPI
├── 📁 tests/                  # Testes unitários
├── requirements.txt           # Dependências
└── README.md                  # Este arquivo
```

## 🚀 Instalação

### Pré-requisitos
- Python 3.10+
- Git

### Setup

```bash
# Clone o repositório
git clone https://github.com/Masteradilio/risco_bancario.git
cd risco_bancario

# Crie o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt
```

## 💻 Uso

### Treinar o Modelo

```bash
python src/train_model.py
```

### Executar a API

```bash
python src/api.py
# API disponível em http://localhost:8000
```

### Executar o Dashboard

```bash
streamlit run app/dashboard.py
# Dashboard disponível em http://localhost:8501
```

### Classificar um Cliente

```python
from src.classifier import PRINADClassifier

classifier = PRINADClassifier()
result = classifier.classify({
    'IDADE_CLIENTE': 35,
    'RENDA_LIQUIDA': 5000,
    'v205': 0,
    'v210': 0,
    'scr_classificacao_risco': 'A',
    'scr_dias_atraso': 0
})

print(f"PRINAD: {result['prinad']:.2f}%")
print(f"Rating: {result['rating']}")
```

## 📋 Componentes do Score

### 1. PD Base (50%)
Modelo de machine learning ensemble (XGBoost + LightGBM) calibrado.

### 2. Penalidade Histórica Interna (25%)
Baseada nos vértices v* de atraso interno dos últimos 24 meses.

### 3. Penalidade Histórica Externa - SCR (25%)
Baseada nos dados do Sistema de Informações de Crédito do Banco Central:
- Classificação de risco (AA a H)
- Valor vencido em outras instituições
- Dias de atraso
- Valores em prejuízo

### 🔄 Período de Cura
Cliente é "perdoado" após **6 meses consecutivos** sem nenhum evento negativo **interno E externo**.

## 📈 Escala de Rating

| Rating | Faixa PD | Descrição | Ação |
|--------|----------|-----------|------|
| **A1** | 0-4.99% | Risco Mínimo | Aprovação automática |
| **A2** | 5-14.99% | Risco Muito Baixo | Aprovação automática |
| **A3** | 15-24.99% | Risco Baixo | Análise simplificada |
| **B1** | 25-34.99% | Risco Baixo-Moderado | Análise padrão |
| **B2** | 35-44.99% | Risco Moderado | Análise detalhada |
| **B3** | 45-54.99% | Risco Moderado-Alto | Análise rigorosa |
| **C1** | 55-64.99% | Risco Alto | Exige garantias |
| **C2** | 65-74.99% | Risco Muito Alto | Condições especiais |
| **C3** | 75-84.99% | Risco Crítico | Negação ou garantias sólidas |
| **D** | 85-94.99% | Pré-Default | Negação, monitoramento |
| **DEFAULT** | 95-100% | Default | Negação, cobrança |

## 🧪 Testes

```bash
pytest tests/ -v
```

## 📚 Documentação

- [Metodologia Basel III](docs/modelo_prinad_basel3.md)
- [Documentação da API](docs/api_documentation.md)

## 🔐 Integração com SCR

Em produção, substitua o `scr_mock_data.csv` pela integração real com a API do SCR:

**Endpoint:** `https://www9.bcb.gov.br/wsscr2n/api/`

Campos necessários:
- `valorVencer`, `valorVencido`, `valorPrejuizo`
- `limCredito`, `limCreditoUtilizado`
- `diasAtraso`, `classificacaoRisco`
- `qtdOperacoes`, `qtdInstituicoes`

> ⚠️ A consulta ao SCR requer autorização prévia do cliente (Res. BCB 4.571/2017).

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Autor

Desenvolvido para análise de risco de crédito em conformidade com as melhores práticas internacionais Basel III.

---

**⭐ Se este projeto foi útil, considere dar uma estrela!**
