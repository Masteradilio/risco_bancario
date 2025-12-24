# PRINAD - Modelo de Probabilidade de Inadimplência

Sistema de classificação de risco de crédito baseado em Machine Learning, alinhado com as práticas internacionais do **Basel III**.

## 📋 Visão Geral

O PRINAD (Probabilidade de Inadimplência) é um modelo de scoring de crédito que avalia o risco de default de clientes de um banco comercial, combinando:

- **Modelo de Machine Learning** (XGBoost + LightGBM ensemble)
- **Componente Histórico** (penalidade baseada em comportamento passado)
- **Interpretabilidade** (SHAP para explicação de decisões)

### Fórmula do Score

```
PRINAD = PD_Base × (1 + Penalidade_Histórica)
```

- `PD_Base`: Probabilidade de default do modelo ML (0-100%)
- `Penalidade_Histórica`: Multiplicador de 0.0 a 1.5 baseado nos últimos 24 meses

## 🎯 Escala de Rating

| Rating | Faixa PD | Descrição | Ação Sugerida |
|--------|----------|-----------|---------------|
| A1 | 0-2% | Risco Mínimo | Aprovação automática |
| A2 | 2-5% | Risco Muito Baixo | Aprovação automática |
| A3 | 5-10% | Risco Baixo | Análise simplificada |
| B1 | 10-20% | Risco Baixo-Moderado | Análise padrão |
| B2 | 20-35% | Risco Moderado | Análise detalhada |
| B3 | 35-50% | Risco Moderado-Alto | Possíveis garantias |
| C1 | 50-70% | Risco Alto | Exige garantias |
| C2 | 70-90% | Risco Muito Alto | Condições especiais |
| D | 90-100% | Default/Iminente | Negação |

## 🛠️ Instalação

### Requisitos

- Python 3.10+
- pip

### Instalação

```bash
# Clone o repositório
cd novo_prinad

# Crie um ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instale as dependências
pip install -r requirements.txt
```

## 🚀 Uso

### 1. Treinar o Modelo

```bash
cd src
python train_model.py
```

Isso irá:
- Carregar dados de `dados/base_cadastro.csv` e `dados/base_3040.csv`
- Aplicar feature engineering
- Balancear com SMOTE-Tomek
- Treinar ensemble XGBoost + LightGBM
- Calibrar probabilidades
- Salvar artefatos em `modelo/`

### 2. Iniciar a API

```bash
cd src
python api.py
```

A API estará disponível em `http://localhost:8000`

- Documentação: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 3. Iniciar o Dashboard

Em outro terminal:

```bash
cd app
streamlit run dashboard.py
```

O dashboard abrirá em `http://localhost:8501`

### 4. Simular Classificações (Demo)

Para demonstrar o sistema em tempo real:

```bash
cd app
python streaming_sender.py --interval 1.0
```

Isso enviará classificações simuladas para a API, que aparecerão no dashboard.

## 📡 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/health` | GET | Status da API |
| `/predict` | POST | Classificar um cliente |
| `/batch` | POST | Classificar múltiplos clientes |
| `/metrics` | GET | Métricas de uso |
| `/ws/stream` | WebSocket | Stream em tempo real |

### Exemplo de Requisição

```python
import requests

response = requests.post("http://localhost:8000/predict", json={
    "cpf": "12345678901",
    "dados_cadastrais": {
        "IDADE_CLIENTE": 35,
        "RENDA_BRUTA": 5000.0,
        "RENDA_LIQUIDA": 4200.0,
        "OCUPACAO": "ASSALARIADO",
        "ESCOLARIDADE": "SUPERIOR",
        "QT_DEPENDENTES": 2,
        "TEMPO_RELAC": 48.0
    },
    "dados_comportamentais": {
        "v205": 0.0, "v210": 0.0, "v220": 0.0, "v230": 0.0,
        "v240": 0.0, "v245": 0.0, "v250": 0.0, "v255": 0.0,
        "v260": 0.0, "v270": 0.0, "v280": 0.0, "v290": 0.0
    }
})

result = response.json()
print(f"PRINAD: {result['prinad']}% - Rating: {result['rating']}")
```

## 📁 Estrutura do Projeto

```
novo_prinad/
├── src/                          # Código-fonte principal
│   ├── data_pipeline.py          # Carregamento e merge de dados
│   ├── feature_engineering.py    # Criação de features derivadas
│   ├── historical_penalty.py     # Cálculo de penalidade histórica
│   ├── train_model.py            # Treinamento do modelo
│   ├── classifier.py             # Pipeline de classificação
│   └── api.py                    # API FastAPI
├── app/                          # Aplicativos
│   ├── dashboard.py              # Dashboard Streamlit
│   └── streaming_sender.py       # Simulador de dados
├── modelo/                       # Artefatos de modelo
│   ├── ensemble_model.joblib     # Modelo treinado
│   ├── preprocessor.joblib       # Preprocessador
│   └── shap_explainer.joblib     # Explainer SHAP
├── dados/                        # Dados de entrada
│   ├── base_cadastro.csv         # Dados cadastrais
│   └── base_3040.csv             # Dados comportamentais
├── docs/                         # Documentação
│   ├── modelo_prinad_basel3.md   # Metodologia Basel III
│   └── api_documentation.md      # Documentação da API
├── modelo_antigo/                # Modelo anterior (referência)
├── requirements.txt              # Dependências Python
└── README.md                     # Este arquivo
```

## 📊 Métricas de Performance

O modelo é avaliado com as seguintes métricas mínimas:

| Métrica | Mínimo | Target |
|---------|--------|--------|
| AUC-ROC | 0.75 | 0.82+ |
| Gini | 0.50 | 0.64+ |
| KS | 0.35 | 0.45+ |
| Precision (Default) | 0.60 | 0.75+ |
| Recall (Default) | 0.55 | 0.70+ |

## 🔒 Conformidade e Regulação

Este modelo foi desenvolvido em conformidade com:

- **Basel III**: Requisitos de modelo interno (IRB)
- **LGPD Art. 20**: Direito à explicação de decisões automatizadas
- **BCB Circular 3.648**: Cálculo de risco de crédito

## 📝 Licença

Uso interno do Banco - Todos os direitos reservados.

## 👥 Equipe

Desenvolvido pela equipe de Data Science / Risco de Crédito.
