# 🏦 Sistema de Gestão de Risco Bancário

**Solução Enterprise para Crédito, Perda Esperada (ECL) e Otimização de Limites**

[![BACEN 4966](https://img.shields.io/badge/Compliance-BACEN%204966-blue.svg)]()
[![IFRS 9](https://img.shields.io/badge/Standard-IFRS%209-green.svg)]()
[![Basel III](https://img.shields.io/badge/Standard-Basel%20III-orange.svg)]()
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-black.svg)]()
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)]()
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)]()

Este projeto é uma plataforma integrada de gestão de risco de crédito, desenvolvida para instituições financeiras brasileiras, focada em conformidade regulatória, automação de decisões e otimização de rentabilidade.

---

## 🚀 Módulos do Sistema

### 1. 🔍 PRINAD (Probabilidade de Inadimplência)

Motor de classificação de risco baseado em Machine Learning (XGBoost/LightGBM) e histórico comportamental.

| Funcionalidade | Descrição |
|----------------|-----------|
| **PRINAD Score** | Probabilidade de inadimplência (0-100%) |
| **Rating** | 11 níveis (A1 → DEFAULT) conforme BACEN 4966 |
| **PD 12 meses** | Probabilidade calibrada para horizonte de 1 ano |
| **PD Lifetime** | Probabilidade para vida útil do instrumento |
| **Stage IFRS 9** | Classificação automática em Estágio 1, 2 ou 3 |

**Métricas do Modelo:**
| Métrica | Valor | Status |
|---------|-------|--------|
| AUC-ROC | 0.9986 | ✅ Excelente |
| Gini | 0.9972 | ✅ Excelente |
| Precision | 0.9535 | ✅ Meta atingida |
| Recall | 0.9713 | ✅ Meta atingida |

**Escala de Rating:**
| Rating | Faixa PRINAD | Descrição | Ação |
|--------|--------------|-----------|------|
| A1 | 0-4.99% | Risco Mínimo | Aprovação automática |
| A2 | 5-14.99% | Risco Muito Baixo | Aprovação automática |
| A3 | 15-24.99% | Risco Baixo | Análise simplificada |
| B1 | 25-34.99% | Risco Baixo-Moderado | Análise padrão |
| B2 | 35-44.99% | Risco Moderado | Análise detalhada |
| B3 | 45-54.99% | Risco Moderado-Alto | Análise rigorosa |
| C1 | 55-64.99% | Risco Alto | Exige garantias |
| C2 | 65-74.99% | Risco Muito Alto | Condições especiais |
| C3 | 75-84.99% | Risco Crítico | Negação ou garantias sólidas |
| D | 85-94.99% | Pré-Default | Negação, monitoramento |
| DEFAULT | 95-100% | Default | Negação, cobrança |


### 2. 📉 ECL (Perda Esperada / Expected Credit Loss)

Calculador de provisionamento conforme normas contábeis internacionais e locais, com fluxo de trabalho completo desde o cálculo até o reporte regulatório.

| Componente | Descrição |
|------------|-----------|
| **Fórmula Central** | `ECL = PD × LGD × EAD` |
| **Pipeline Integrado** | Execução sequencial de estágios, LGD, EAD e cálculo final |
| **Workflow Guiado** | Integração lógica: Pipeline -> Validação -> Exportação XML |
| **Transparência Legal** | Cards explicativos com referência direta aos artigos da CMN 4966 |
| **Grupos Homogêneos** | Agrupamento por PD usando K-means, percentis ou densidade |
| **Forward Looking** | Integração com API BACEN SGS, fatores K_PD_FL e K_LGD_FL |
| **LGD Segmentado** | LGD por árvore de decisão: Produto × Atraso × Valor × Prazo |
| **Sistema de Cura** | Regras de carência e período probatório para retorno de estágio |
| **Rastreamento Write-off** | Controle de baixas e recuperações (5 anos) |

**3 Estágios IFRS 9:**
| Estágio | Horizonte ECL | Condição |
|---------|---------------|----------|
| Stage 1 | 12 meses | Risco não aumentou significativamente |
| Stage 2 | Lifetime | Aumento significativo do risco (Trigger SICR) |
| Stage 3 | Lifetime + LGD máxima | Ativo com problema de recuperação (Default) |

**CCF por Produto:**
| Produto | CCF |
|---------|-----|
| Consignado | 100% |
| Imobiliário | 100% |
| Veículo | 100% |
| Cartão Rotativo | 75% |
| Cheque Especial | 70% |
| Crédito Sazonal | 50% |

### 3. 🎯 PROLIMITE (Otimização de Limites)

Sistema de propensão e realocação dinâmica de limites de crédito.

| Funcionalidade | Descrição |
|----------------|-----------|
| **Modelo Multi-Produto** | 6 modelos XGBoost/LightGBM (1 por produto) |
| **Propensão a Consumo** | Score de probabilidade de uso do limite |
| **Realocação Dinâmica** | Redistribuição de limites entre produtos |
| **Notificações** | Push, SMS e Banner in-app com antecedência |

**Regras de Otimização:**
| Ação | Condição | Novo Limite |
|------|----------|-------------|
| ZERAR | Rating DEFAULT | 0 |
| REDUZIR 25% | Rating D (PRINAD 85-94%) | 25% do atual |
| REDUZIR 50% | Rating C3 OU Propensão < 45% + Utilização < 30% | 50% do atual |
| AUMENTAR | PRINAD < 75% + Propensão > 55% + Margem + Comprometimento < 65% | +25% |
| MANTER | Demais casos | Sem alteração |

**LGD por Produto (Basel III):**
| Produto | LGD Base | LGD Downturn |
|---------|----------|--------------|
| Consignado | 35% | 44% |
| Banparacard | 45% | 56% |
| Cartão de Crédito | 70% | 88% |
| Imobiliário | 12% | 15% |
| Antecipação 13º | 20% | 25% |
| Crédito Veículo | 30% | 38% |

### 4. 📤 Exportação Regulatória BACEN

Suite completa de conformidade para geração e validação de arquivos regulatórios.

| Funcionalidade | Descrição |
|----------------|-----------|
| **Documento 3040** | XML conforme leiaute SCR3040 v5.0+ |
| **Validador BACEN** | Simulador integrado de validação (Sintática + Semântica) |
| **Etapas de Validação** | Checagem de Estrutura, COSIF, Regras CMN 4966 e Totais |
| **Tag Res4966** | Geração automática da seção `<ContInstFinRes4966>` |
| **Histórico de Envios** | Controle de remessas, status e protocolos |
| **Bloqueio de Segurança** | Impede geração sem execução prévia de pipeline validado |

### 5. 🤖 Assistente de IA (Em breve)

Agente inteligente baseado em LangGraph para análise qualitativa e suporte à decisão.

---

## 🏗️ Arquitetura Técnica

O sistema utiliza uma arquitetura de microserviços containerizados:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ARQUITETURA DO SISTEMA                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      FRONTEND (Next.js 15)                      │   │
│  │  ├── Dashboard PRINAD (Classificação de Risco)                  │   │
│  │  ├── Dashboard ECL (Perda Esperada)                             │   │
│  │  ├── Dashboard Propensão (Otimização de Limites)                │   │
│  │  ├── Relatórios PDF (@react-pdf/renderer)                       │   │
│  │  └── Autenticação RBAC (Analista, Gestor, Auditor, Admin)       │   │
│  └────────────────────────────┬────────────────────────────────────┘   │
│                               │                                         │
│                               ▼                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │   API       │  │   API       │  │   API       │                     │
│  │  PRINAD     │  │   ECL       │  │ PROPENSÃO   │                     │
│  │ :8000       │  │  :8001      │  │  :8002      │                     │
│  │  (FastAPI)  │  │  (FastAPI)  │  │  (FastAPI)  │                     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                     │
│         │                │                │                             │
│         └────────────────┼────────────────┘                             │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    SHARED UTILS (Python)                        │   │
│  │  ├── PD_POR_RATING (11 ratings calibrados)                      │   │
│  │  ├── CCF_POR_PRODUTO (Credit Conversion Factors)                │   │
│  │  ├── LGD_POR_PRODUTO (Basel III)                                │   │
│  │  └── Funções: calcular_ecl, get_ifrs9_stage, etc.               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Stack Tecnológico:**
- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, Shadcn/UI, Recharts
- **Backend APIs**: 3 instâncias de FastAPI (Python 3.11) isoladas por responsabilidade
- **ML/AI**: XGBoost, LightGBM, SHAP para explicabilidade
- **Orquestração**: Docker Compose para ambiente local e desenvolvimento

---

## 📂 Estrutura do Projeto

```bash
risco_bancario/
├── backend/                    # APIs em Python
│   ├── prinad/                 # Classificação de Risco (PRINAD)
│   │   ├── src/                # Código-fonte
│   │   │   ├── classifier.py   # Classificador principal
│   │   │   ├── api.py          # API FastAPI
│   │   │   └── ...
│   │   ├── modelo/             # Artefatos treinados (.joblib)
│   │   ├── dados/              # Datasets e bases históricas
│   │   └── tests/              # Testes unitários
│   │
│   ├── perda_esperada/         # Motor de ECL
│   │   ├── src/
│   │   │   ├── pipeline_ecl.py          # Pipeline integrador
│   │   │   ├── modulo_grupos_homogeneos.py
│   │   │   ├── modulo_forward_looking.py
│   │   │   ├── modulo_lgd_segmentado.py
│   │   │   ├── modulo_ead_ccf_especifico.py
│   │   │   ├── modulo_triggers_estagios.py
│   │   │   ├── modulo_exportacao_bacen.py
│   │   │   └── pisos_minimos.py
│   │   └── docs/               # Documentação técnica e regulatória
│   │
│   ├── propensao/              # Otimização de Limites (PROLIMITE)
│   │   ├── src/
│   │   │   ├── ecl_engine.py           # Motor ECL v2.0
│   │   │   ├── stage_classifier.py     # Classificação IFRS 9
│   │   │   ├── limit_reallocation.py   # Realocação por propensão
│   │   │   ├── propensity_model.py     # Modelo multi-produto
│   │   │   └── pipeline_runner.py      # Pipeline completo
│   │   └── tests/              # Testes unitários
│   │
│   └── shared/                 # Utilitários compartilhados
│       └── utils.py            # Constantes e funções comuns
│
├── frontend/                   # Web App Next.js
│   ├── app/                    # Pages (App Router)
│   ├── components/             # Componentes React
│   └── lib/                    # Stores Zustand, utilidades
│
├── docker/                     # Dockerfiles de Produção
├── .env.example                # Variáveis de ambiente (template)
├── docker-compose.yml          # Orquestração Unificada
├── CHANGELOG.md                # Histórico de mudanças
├── TODO.md                     # Próximas funcionalidades
└── README.md                   # Este arquivo
```

---

## 🛠️ Como Iniciar

### 1. Requisitos
- Docker e Docker Compose
- Node.js 20+ (para desenvolvimento local do frontend)
- Python 3.11+ (para desenvolvimento local do backend)

### 2. Configuração (Variáveis de Ambiente)

Crie um arquivo `.env` na raiz baseado no `.env.example`:
```bash
cp .env.example .env
```

### 3. Execução com Docker (Recomendado)
```bash
docker-compose up --build
```

Acesse:
- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **API PRINAD**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API ECL**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **API Propensão**: [http://localhost:8002/docs](http://localhost:8002/docs)

### 4. Desenvolvimento Local

**Backend (cada módulo):**
```bash
cd backend/prinad
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
python src/api.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🔐 Integração com SCR (Sistema de Informações de Crédito)

Em produção, substitua os dados mockados pela integração real com a API do SCR:

**Endpoint:** `https://www9.bcb.gov.br/wsscr2n/api/`

**Campos necessários:**
- `valorVencer`, `valorVencido`, `valorPrejuizo`
- `limCredito`, `limCreditoUtilizado`
- `diasAtraso`, `classificacaoRisco`
- `qtdOperacoes`, `qtdInstituicoes`

> ⚠️ A consulta ao SCR requer autorização prévia do cliente (Res. BCB 4.571/2017).

---

## 📋 Fluxo de Dados

```
┌────────────────────────────────────────────────────────────────────────┐
│                          FLUXO DO PIPELINE                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  PRINAD (Módulo 1)                                                     │
│  ├── Dados Cadastrais (15 features)                                    │
│  ├── Dados Comportamentais (12 features)                               │
│  ├── Histórico Interno (v-columns)                                     │
│  └── SCR BACEN (16 features)                                           │
│              │                                                         │
│              ▼                                                         │
│  ┌───────────────────────────────────────────────────────────┐        │
│  │      Ensemble ML (XGBoost + LightGBM)                     │        │
│  │      + Penalidades Históricas (25% Int + 25% Ext)         │        │
│  │      = PRINAD Score + Rating + PD_12m + PD_lifetime       │        │
│  └──────────────────────────┬────────────────────────────────┘        │
│                             │                                          │
│                             ▼                                          │
│  ECL (Módulo 2)  ◄──────────┘                                          │
│  ├── Grupos Homogêneos (GH)                                            │
│  ├── Forward Looking (K_PD_FL)                                         │
│  ├── LGD Segmentado + EAD com CCF                                      │
│  ├── Pisos Mínimos (Stage 3)                                           │
│  └── Triggers e Arrasto                                                │
│              │                                                         │
│              ▼                                                         │
│  ╔═══════════════════════════════════════════════════════════╗        │
│  ║     ECL = PD × LGD × EAD (por estágio IFRS 9)             ║        │
│  ╚═══════════════════════════════════════════════════════════╝        │
│              │                                                         │
│              ▼                                                         │
│  PROLIMITE (Módulo 3)  ◄─────┘                                         │
│  ├── Propensão a Consumo por Produto                                   │
│  ├── Otimização de Limites                                             │
│  ├── Realocação por Propensão                                          │
│  └── Notificações (D+0, D+30, D+60)                                    │
│              │                                                         │
│              ▼                                                         │
│  ┌───────────────────────────────────────────────────────────┐        │
│  │     Exportação BACEN (Doc3040 / ContInstFinRes4966)       │        │
│  └───────────────────────────────────────────────────────────┘        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testes

```bash
# PRINAD
cd backend/prinad
pytest tests/ -v

# PROLIMITE
cd backend/propensao
pytest tests/ -v

# ECL
cd backend/perda_esperada
pytest tests/ -v
```

---

## 📚 Documentação

- **Changelog**: [CHANGELOG.md](CHANGELOG.md) - Histórico completo de mudanças
- **TODO**: [TODO.md](TODO.md) - Próximas funcionalidades planejadas
- **Documentação Técnica ECL**: [backend/perda_esperada/docs/](backend/perda_esperada/docs/)

### Referências Regulatórias

- [Resolução CMN 4.966/2021](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolução%20CMN&numero=4966)
- [Resolução BCB 352/2023](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Resolução%20BCB&numero=352)
- [IFRS 9 - Instrumentos Financeiros](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/)
- [Instrução Normativa BCB 414](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?tipo=Instrução+Normativa+BCB&numero=414)
- [Leiaute Doc3040](https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute_de_documentos/scrdoc3040/SCR3040_Leiaute.xls)

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Autores e Contato

Desenvolvido por **Masteradilio** - Arquiteto de Soluções de Risco.

---

**⭐ Se este projeto foi útil, considere dar uma estrela!**
