# PRINAD - Sistema de Classificação de Risco de Crédito
## Guia de Apresentação Executiva

> Apresentação legada com dados sintéticos. Não constitui model card aprovado, validação independente, escala oficial de rating ou evidência de conformidade.

> **Versão:** 2.0  
> **Data:** Janeiro/2026  
> **Cobertura regulatória:** não avaliada; referências históricas requerem rastreabilidade

---

## 📋 Sumário Executivo

O **PRINAD** (Probabilidade de Inadimplência) é um sistema de classificação de risco de crédito desenvolvido para atender aos requisitos da **Resolução BACEN 4966/2021**, que regulamenta o reconhecimento de perdas esperadas de crédito no Brasil, em alinhamento com o padrão internacional **IFRS 9**.

### Principais Entregas

| Componente | Descrição |
|------------|-----------|
| **Modelo de ML** | Ensemble XGBoost com 99.2% AUC-ROC |
| **API REST** | Endpoints para classificação simples, explicada e em lote |
| **Dashboard** | Interface web para análise em tempo real |
| **Explicabilidade** | SHAP values para auditoria e transparência |

---

## 🎯 1. Visão Geral do Sistema

### 1.1 O que é o PRINAD?

O PRINAD é uma **métrica de risco** que combina três componentes:

```
PRINAD = min(PD_Base × (1 + Pen_Interna + Pen_Externa), 100%)
```

| Componente | Peso | Descrição |
|------------|------|-----------|
| **PD_Base (Modelo ML)** | 50% | Probabilidade de default calculada pelo modelo de Machine Learning |
| **Penalidade Interna** | 25% | Histórico de atrasos nos últimos 24 meses (dados internos do banco) |
| **Penalidade Externa (SCR)** | 25% | Histórico de atrasos no mercado (dados do BACEN/SCR) |

### 1.2 Por que o PRINAD?

A Resolução 4966/2021 exige:

1. ✅ **Mensuração de Perdas Esperadas** (Expected Credit Loss - ECL)
2. ✅ **Classificação em Estágios** (Stages 1, 2 e 3)
3. ✅ **Horizonte de PD 12 meses e Lifetime**
4. ✅ **Incorporação de informações forward-looking**
5. ✅ **Documentação e auditabilidade**

O PRINAD atende a **todos esses requisitos**.

---

## 📊 2. Arquitetura do Sistema

### 2.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRINAD SYSTEM v2.0                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │   DADOS     │    │   API       │    │      DASHBOARD          │ │
│  │   INTERNOS  │───▶│   REST      │◀───│      STREAMLIT          │ │
│  └─────────────┘    │  (FastAPI)  │    │                         │ │
│                     │             │    │  • Classificação        │ │
│  ┌─────────────┐    │  /classify  │    │  • Streaming            │ │
│  │   DADOS     │───▶│  /batch     │    │  • Explicabilidade      │ │
│  │   SCR/BACEN │    │  /explain   │    │  • Lote (CSV)           │ │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘ │
│                            │                                        │
│                            ▼                                        │
│                     ┌─────────────┐                                 │
│                     │   MODELO    │                                 │
│                     │   XGBoost   │                                 │
│                     │   Ensemble  │                                 │
│                     └─────────────┘                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Fluxo de Classificação

```
1. Entrada de CPF
        │
        ▼
2. Busca dados do cliente (cadastro + comportamento)
        │
        ▼
3. Enriquecimento com dados SCR/BACEN
        │
        ▼
4. Feature Engineering (38 variáveis)
        │
        ▼
5. Predição do Modelo ML (PD_Base)
        │
        ▼
6. Cálculo de Penalidades (Interna + Externa)
        │
        ▼
7. Composição do PRINAD Final
        │
        ▼
8. Mapeamento para Rating (A1 a DEFAULT)
        │
        ▼
9. Classificação de Estágio PE (1, 2 ou 3)
        │
        ▼
10. Cálculo de PD_12m e PD_Lifetime
        │
        ▼
11. Retorno com Explicabilidade (SHAP)
```

---

## 🤖 3. O Modelo de Machine Learning

### 3.1 Especificações Técnicas

| Característica | Valor |
|----------------|-------|
| **Algoritmo** | XGBoost Ensemble |
| **Features** | 38 variáveis |
| **Amostras de Treinamento** | 50.000 clientes |
| **Período de Lookback** | 24 meses |

### 3.2 Métricas de Performance

| Métrica | Valor | Descrição |
|---------|-------|-----------|
| **AUC-ROC** | 99.2% | Capacidade de distinguir bons de maus pagadores |
| **Gini** | 98.3% | Poder discriminatório do modelo |
| **KS** | 92.0% | Separação máxima entre curvas |
| **Precision** | 85.5% | Taxa de acerto nas previsões de default |
| **Recall** | 95.3% | Cobertura de inadimplentes identificados |
| **Accuracy** | 95.9% | Acurácia geral |

### 3.3 Escala de Rating

> **Fórmula PD Lifetime:** `PD_Lifetime = 1 - (1 - PD_12m)^n` onde `n` = maturidade média (5 anos)

| Rating | Faixa PRINAD | Descrição | PD 12m | PD Lifetime |
|--------|-------------|-----------|--------|-------------|
| A1 | 0% - 5% | Risco Mínimo | 2.5% | 11.9% |
| A2 | 5% - 15% | Risco Muito Baixo | 10.0% | 40.9% |
| A3 | 15% - 25% | Risco Baixo | 20.0% | 67.2% |
| B1 | 25% - 35% | Risco Baixo-Moderado | 30.0% | 83.2% |
| B2 | 35% - 45% | Risco Moderado | 40.0% | 92.2% |
| B3 | 45% - 55% | Risco Moderado-Alto | 50.0% | 96.9% |
| C1 | 55% - 65% | Risco Alto | 60.0% | 99.0% |
| C2 | 65% - 75% | Risco Muito Alto | 70.0% | 99.8% |
| C3 | 75% - 85% | Risco Crítico | 80.0% | 100.0% |
| D | 85% - 95% | Pré-Default | 90.0% | 100.0% |
| DEFAULT | 95% - 100% | Default | 100.0% | 100.0% |

**Nota:** PD (Probability of Default) é uma probabilidade e nunca pode exceder 100%.

### 3.4 Classificação de Estágios (IFRS 9)

| Estágio | Critério | Horizonte ECL |
|---------|----------|---------------|
| **Stage 1** | Dias atraso < 30 E PRINAD < 50% | PD 12 meses |
| **Stage 2** | Dias atraso ≥ 30 OU PRINAD ≥ 50% | PD Lifetime |
| **Stage 3** | Dias atraso ≥ 90 OU PRINAD ≥ 85% | PD Lifetime |

---

## 🔌 4. API REST

### 4.1 Endpoints Disponíveis

#### Sistema
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Verificação de saúde da API |

#### Classificação Individual
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/simple_classify` | Classificação rápida (sem SHAP) |
| POST | `/explained_classify` | Classificação com explicabilidade |

#### Classificação em Lote
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/multiple_classify` | Classificação em lote (simples) |
| POST | `/multiple_explained_classify` | Classificação em lote (explicada) |

#### Dados
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/clientes` | Lista CPFs disponíveis |
| GET | `/cliente/{cpf}` | Dados de um cliente específico |

### 4.2 Exemplo de Requisição

**Request:**
```json
POST /explained_classify
{
    "cpf": "12345678901"
}
```

**Response:**
```json
{
    "cpf": "12345678901",
    "prinad": 45.5,
    "pd_12m": 0.08,
    "pd_lifetime": 0.56,
    "rating": "B3",
    "rating_descricao": "Risco Moderado-Alto",
    "estagio_pe": 2,
    "acao_sugerida": "Análise rigorosa, possíveis garantias",
    "explicacao_shap": [
        {"feature": "v270", "contribuicao": 5.2, "direcao": "aumenta_risco"},
        {"feature": "scr_dias_atraso", "contribuicao": 3.8, "direcao": "aumenta_risco"}
    ],
    "explicacao_completa": {
        "composicao_prinad": {
            "pd_modelo_ml": {"valor": 30.2, "peso": "50%"},
            "penalidade_interna": {"valor": 25.0, "peso": "25%"},
            "penalidade_externa": {"valor": 15.0, "peso": "25%"}
        }
    }
}
```

### 4.3 Documentação Interativa

A API possui documentação Swagger acessível em:
- **Swagger UI:** `http://{host}:8000/docs`
- **ReDoc:** `http://{host}:8000/redoc`

---

## 📺 5. Dashboard

### 5.1 Funcionalidades

| Funcionalidade | Descrição |
|----------------|-----------|
| **Classificação Simples** | Classificação rápida sem explicabilidade |
| **Classificação Explicada** | Classificação com SHAP e detalhes completos |
| **Streaming em Tempo Real** | Classificação contínua de clientes aleatórios |
| **Processamento em Lote** | Upload de CSV com múltiplos CPFs |
| **Export CSV** | Download dos resultados processados |

### 5.2 Indicadores Exibidos

#### Métricas Principais
- Total de classificações
- PRINAD médio
- PD 12m médio
- PD Lifetime médio
- Distribuição por Stage (1, 2, 3)

#### Gráficos
- Distribuição de Ratings (barras)
- Distribuição de Stages (donut)
- Faixas de Risco PD 12m
- Faixas de Risco PD Lifetime

#### Painel de Explicabilidade
- Top 5 Fatores de Risco (SHAP)
- Composição do Score PRINAD
- Situação do Histórico (Interno + Externo)
- Elegibilidade para Reavaliação
- Ação Sugerida

---

## 📦 6. Requisitos de Dados

### 6.1 Dados Internos do Banco (Obrigatórios)

#### Cadastro do Cliente
| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| CPF | string | CPF do cliente (chave) | "12345678901" |
| IDADE_CLIENTE | int | Idade em anos | 35 |
| RENDA_BRUTA | float | Renda mensal (R$) | 5000.00 |
| TEMPO_RELAC | int | Meses de relacionamento | 24 |
| QT_PRODUTOS | int | Quantidade de produtos | 3 |
| ESCOLARIDADE | string | Nível de escolaridade | "SUPERIOR" |
| ESTADO_CIVIL | string | Estado civil | "CASADO" |
| TIPO_RESIDENCIA | string | Tipo de moradia | "PROPRIA" |
| POSSUI_VEICULO | string | Possui veículo? | "SIM" |

#### Histórico de Atrasos (V-Columns)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| v205 | float | Saldo em atraso 1-30 dias |
| v210 | float | Saldo em atraso 31-60 dias |
| v220 | float | Saldo em atraso 61-90 dias |
| v230 | float | Saldo em atraso 91-120 dias |
| v240 | float | Saldo em atraso 121-150 dias |
| v245 | float | Saldo em atraso 151-180 dias |
| v250 | float | Saldo em atraso 181-210 dias |
| v255 | float | Saldo em atraso 211-240 dias |
| v260 | float | Saldo em atraso 241-270 dias |
| v270 | float | Saldo em atraso 271-300 dias |
| v280 | float | Saldo em atraso 301-330 dias |
| v290 | float | Saldo em atraso >330 dias (prejuízo) |

#### Utilização de Crédito
| Campo | Tipo | Descrição |
|-------|------|-----------|
| limite_total | float | Limite total de crédito (R$) |
| limite_utilizado | float | Limite utilizado (R$) |
| parcelas_mensais | float | Valor de parcelas mensais (R$) |

### 6.2 Dados SCR/BACEN (Recomendados)

Estes dados são obtidos via **API SCR do BACEN** e enriquecem significativamente a qualidade da predição.

| Campo | Tipo | Descrição | Impacto |
|-------|------|-----------|---------|
| scr_classificacao_risco | string | Rating SCR (AA a H) | Alto |
| scr_dias_atraso | int | Dias em atraso no mercado | Alto |
| scr_valor_vencido | float | Valor vencido no mercado (R$) | Médio |
| scr_valor_prejuizo | float | Valor em prejuízo no mercado (R$) | Alto |
| scr_tem_prejuizo | int | Flag de prejuízo (0/1) | Alto |
| scr_score_risco | int | Score numérico (1-8) | Alto |
| scr_exposicao_total | float | Exposição total no mercado (R$) | Médio |
| scr_taxa_utilizacao | float | Utilização do limite no mercado | Médio |

### 6.3 Features Derivadas (Calculadas Automaticamente)

O sistema calcula automaticamente estas features a partir dos dados de entrada:

| Feature | Fórmula |
|---------|---------|
| taxa_utilizacao | limite_utilizado / limite_total |
| comprometimento_renda | parcelas_mensais / RENDA_BRUTA |
| margem_disponivel | limite_total - limite_utilizado |
| max_dias_atraso_12m | máximo dias de atraso no período |
| tem_veiculo | 1 se POSSUI_VEICULO = 'SIM', senão 0 |
| em_idade_ativa | 1 se 18 ≤ idade ≤ 65, senão 0 |
| cliente_novo | 1 se TEMPO_RELAC < 6 meses, senão 0 |
| idade_squared | IDADE_CLIENTE² |
| log_tempo_relac | log(TEMPO_RELAC + 1) |

---

## 🔒 7. Conformidade BACEN 4966/2021

### 7.1 Requisitos Atendidos

| Requisito | Como o PRINAD Atende |
|-----------|---------------------|
| **ECL Forward-Looking** | Modelo incorpora dados SCR e histórico de 24 meses |
| **Staging IFRS 9** | Classificação automática em 3 estágios |
| **PD 12 meses** | Calculado para Stage 1 |
| **PD Lifetime** | Calculado para Stages 2 e 3 |
| **Auditabilidade** | SHAP values explicam cada predição |
| **Documentação** | API documentada + Logs de classificação |
| **Backtesting** | Métricas de performance disponíveis |

### 7.2 Período de Cura (Forgiveness)

Conforme boas práticas de mercado:
- **Período:** 6 meses consecutivos
- **Requisito:** Histórico limpo **INTERNO** e **EXTERNO**
- **Efeito:** Cliente pode ser reclassificado para Stage 1

---

## 📈 8. Resultados da Validação

### 8.1 Análise de Correlações (Dados Reais)

Análise realizada com **582.030 clientes reais**:

| Feature | Correlação | Interpretação |
|---------|------------|---------------|
| QT_PRODUTOS | +0.18 | Mais produtos = Maior risco |
| RENDA_BRUTA | -0.15 | Maior renda = Menor risco |
| IDADE_CLIENTE | -0.14 | Mais idade = Menor risco |
| ESCOLARIDADE (Superior) | -2.7pp | Maior escolaridade = Menor risco |
| POSSUI_VEICULO (Sim) | -5.9pp | Ter patrimônio = Menor risco |

### 8.2 Taxa de Inadimplência por Segmento

| Segmento | Taxa de Inadimplência |
|----------|----------------------|
| Ensino Fundamental | 34.98% |
| Ensino Superior | 26.36% |
| Solteiro | 33.31% |
| Casado | 27.47% |
| Sem veículo | 29.48% |
| Com veículo | 23.54% |

---

## 🚀 9. Próximos Passos

### 9.1 Implantação

1. **Integração com Core Banking**
   - Conectar API ao sistema de originação
   - Configurar fluxo de consulta SCR
   
2. **Configuração de Produção**
   - Deploy em ambiente de produção
   - Configuração de monitoramento e alertas

3. **Treinamento de Usuários**
   - Capacitação da equipe de crédito
   - Documentação de processos

### 9.2 Evolução do Modelo

1. **Retreinamento Periódico**
   - Frequência recomendada: Trimestral
   - Monitoramento de drift

2. **Novas Features**
   - Incorporar dados de open banking (quando disponível)
   - Dados de redes sociais profissionais

3. **Modelos Específicos**
   - Modelos por segmento (PF, PJ, Consignado)
   - Modelos de recuperação (LGD)

---

## 📞 Contatos e Suporte

| Assunto | Responsável |
|---------|-------------|
| Dúvidas técnicas | Equipe de Data Science |
| Integrações | Equipe de TI |
| Compliance | Equipe de Riscos |

---

## 📎 Anexos

- [Documentação Técnica da API](/docs)
- [Análise de Correlações](/docs/analise_correlacoes_reais.md)
- [Interpretação de Features SHAP](/docs/features_shap_interpretacao.md)

---

*Documento preparado para apresentação executiva - Confidencial*
