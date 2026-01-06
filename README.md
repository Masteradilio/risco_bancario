# 🏦 Sistema de Gestão de Risco Bancário

**Solução Enterprise para Crédito, Perda Esperada (ECL) e Otimização de Limites**

[![BACEN 4966](https://img.shields.io/badge/Compliance-BACEN%204966-blue.svg)]()
[![IFRS 9](https://img.shields.io/badge/Standard-IFRS%209-green.svg)]()
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-black.svg)]()
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)]()

Este projeto é uma plataforma integrada de gestão de risco de crédito, desenvolvida para instituições financeiras brasileiras, focada em conformidade regulatória, automação de decisões e otimização de rentabilidade.

---

## 🚀 Módulos do Sistema

### 1. 🔍 PRINAD (Probabilidade de Inadimplência)
Motor de classificação de risco baseado em Machine Learning (XGBoost/LightGBM) e histórico comportamental.
- **Output**: Rating (A1 a DEFAULT), PD 12 meses, PD Lifetime e Estágios IFRS 9.
- **Conformidade**: Basel III e Resolução 4966.
- **Portal**: [backend/prinad](backend/prinad/README.md)

### 2. 📉 ECL (Expected Credit Loss)
Calculador de provisionamento conforme normas contábeis internacionais e locais.
- **Funcionalidades**: Grupos Homogêneos, Forward Looking (dados macro), LGD Segmentada e EAD com CCF.
- **Pisos Mínimos**: Aplicação automática conforme Res. BCB 352.
- **Portal**: [backend/perda_esperada](backend/perda_esperada/README.md)

### 3. 🎯 PROLIMITE (Otimização de Limites)
Sistema de propensão e realocação dinâmica de limites de crédito.
- **Objetivo**: Minimizar ECL de limites não utilizados e aumentar exposição em perfis de alta propensão e baixo risco.
- **Portal**: [backend/propensao](backend/propensao/README.md)

### 4. 🤖 Assistente de IA (Em breve)
Agente inteligente baseado em LangGraph para análise qualitativa e suporte à decisão.

---

## 🏗️ Arquitetura Técnica

O sistema utiliza uma arquitetura de microserviços containerizados:

- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, Shadcn/UI, Recharts.
- **Backend APIs**: 3 instâncias de FastAPI (Python 3.11) isoladas por responsabilidade.
- **Orquestração**: Docker Compose para ambiente local e desenvolvimento.

---

## 📂 Estrutura do Projeto

```bash
risco_bancario/
├── backend/            # APIs em Python
│   ├── prinad/         # Classificação de Risco
│   ├── perda_esperada/ # Motor de ECL
│   └── propensao/      # Otimização de Limites (Prolimite)
├── frontend/           # Web App Next.js
├── docker/             # Dockerfiles de Produção
├── dados/              # Datasets e Bases Históricas
└── docker-compose.yml  # Orquestração Unificada
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
Acesse o portal em: [http://localhost:3000](http://localhost:3000)

---

## 📋 Changelog e Roadmap
- Confira o [changelog.md](changelog.md) para ver o que foi entregue hoje.
- Veja o [TODO.md](TODO.md) para as próximas funcionalidades planejadas.

---

## 👥 Autores e Contato
Desenvolvido por **Masteradilio** - Arquiteto de Soluções de Risco.
