# Modelo PRINAD - Documentação Técnica

> Documento legado sobre um modelo treinado com dados sintéticos/demonstrativos. Não é model card aprovado, validação independente ou evidência de conformidade com Basileia.

## Alinhamento com Práticas Internacionais Basel III

Este documento descreve a metodologia histórica do protótipo PRINAD. Alegações anteriores de conformidade foram retiradas; metodologia, dados e métricas exigem reconstrução e validação.

---

## 1. Fundamentação Regulatória

### 1.1 Basel III e a Abordagem IRB

O Comitê de Supervisão Bancária de Basileia (BCBS) estabelece que bancos podem utilizar a abordagem **Internal Ratings-Based (IRB)** para cálculo de requisitos de capital. Os componentes principais são:

| Componente | Descrição | Requisito Basel III |
|------------|-----------|---------------------|
| **PD** (Probability of Default) | Probabilidade de inadimplência em 12 meses | Floor de 0.05% (5 bps) |
| **LGD** (Loss Given Default) | Perda esperada em caso de default | Definido por classe de ativo |
| **EAD** (Exposure at Default) | Exposição no momento do default | Calculado por produto |

### 1.2 Conformidade do Modelo PRINAD

O modelo PRINAD atende aos seguintes requisitos regulatórios:

- ✅ **Horizonte de predição**: 12 meses (padrão Basel III)
- ✅ **Floor de PD**: Mínimo de 0.05% para clientes não-default
- ✅ **Diferenciação de risco**: 11 níveis de rating (granularidade adequada)
- ✅ **Componente histórico**: Considera comportamento passado (24 meses)
- ✅ **Interpretabilidade**: SHAP values para explicação de decisões
- ✅ **Documentação**: Metodologia documentada e auditável

---

## 2. Arquitetura do Modelo

### 2.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE PRINAD v2.0                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────┐ │
│  │ Dados        │    │ Dados        │    │ Histórico    │    │ Dados  │ │
│  │ Cadastrais   │    │ Comportament.│    │ Interno      │    │ SCR    │ │
│  │ (15 feat.)   │    │ (12 feat.)   │    │ 24 meses     │    │ (BCB)  │ │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └───┬────┘ │
│         │                   │                   │                │      │
│         └─────────┬─────────┘                   │                │      │
│                   ▼                             ▼                ▼      │
│         ┌─────────────────┐           ┌─────────────────────────────┐   │
│         │ Feature         │           │ Penalidades Históricas      │   │
│         │ Engineering     │           │ ┌───────────┬─────────────┐ │   │
│         │ + SCR Features  │           │ │ Interna   │ Externa     │ │   │
│         └────────┬────────┘           │ │ (25%)     │ SCR (25%)   │ │   │
│                  │                    │ └───────────┴─────────────┘ │   │
│                  ▼                    └──────────────┬──────────────┘   │
│         ┌─────────────────┐                          │                  │
│         │ Ensemble ML     │                          │                  │
│         │ XGBoost+LightGBM│                          │                  │
│         └────────┬────────┘                          │                  │
│                  │                                   │                  │
│                  ▼                                   ▼                  │
│         ┌───────────────────────────────────────────────────────────┐   │
│         │                   PRINAD FINAL                             │   │
│         │  = PD_Base × (1 + Pen_Interna + Pen_Externa)              │   │
│         │  Pesos: 50% atual / 25% hist. interno / 25% hist. SCR    │   │
│         └────────────────────────┬──────────────────────────────────┘   │
│                                  │                                      │
│                                  ▼                                      │
│         ┌─────────────────────────────────────────┐                     │
│         │        RATING (A1 → D)                  │                     │
│         │        + SHAP Explanation               │                     │
│         └─────────────────────────────────────────┘                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Componentes do Score

#### Componente 1: PD Base (50% do peso)

O PD Base é calculado pelo modelo de machine learning ensemble:

```python
PD_Base = Ensemble.predict_proba(features_cliente)
```

**Modelos utilizados**:
- XGBoost (Gradient Boosting otimizado)
- LightGBM (Gradient Boosting eficiente)

**Meta-learner**: Voting Classifier com pesos otimizados

#### Componente 2: Penalidade Histórica Interna (25% do peso)

A penalidade histórica interna considera o comportamento do cliente **dentro do banco** nos últimos **24 meses** (vértices v* do atraso interno):

A penalidade histórica considera o comportamento do cliente nos últimos **24 meses**:

```python
def calcular_penalidade_historica(dados_24_meses):
    """
    Retorna multiplicador entre 0.0 (sem penalidade) e 1.5 (máxima penalidade)
    """
    penalidade = 0.0
    
    # Inadimplência recente (peso maior)
    if inadimplencia_ultimos_6_meses:
        penalidade += 0.8
    elif inadimplencia_ultimos_12_meses:
        penalidade += 0.5
    elif inadimplencia_ultimos_24_meses:
        penalidade += 0.3
    
    # Duração da inadimplência
    if meses_inadimplente > 12:
        penalidade += 0.5
    elif meses_inadimplente > 6:
        penalidade += 0.3
    elif meses_inadimplente > 3:
        penalidade += 0.2
    
    # Recência da regularização
    if meses_desde_regularizacao < 3:
        penalidade += 0.2
    
    return min(0.75, penalidade)  # Máximo 75% pois divide peso com externa
```

#### Componente 3: Penalidade Histórica Externa - SCR (25% do peso)

A penalidade externa considera o histórico do cliente **no Sistema Financeiro Nacional** via consulta ao SCR (Sistema de Informações de Crédito do Banco Central):

```python
def calcular_penalidade_scr(dados_scr):
    """
    Retorna multiplicador entre 0.0 (sem penalidade) e 0.75 (máxima penalidade)
    Baseado nos dados do SCR do Banco Central
    """
    penalidade = 0.0
    
    # Classificação de Risco BCB (AA a H)
    risco_map = {'AA': 0, 'A': 0, 'B': 0.1, 'C': 0.2, 
                 'D': 0.35, 'E': 0.5, 'F': 0.6, 'G': 0.7, 'H': 0.75}
    penalidade += risco_map.get(classificacao_risco, 0)
    
    # Valor vencido em outras instituições
    if valor_vencido_scr > 0:
        if valor_vencido_scr > 10000:
            penalidade += 0.4
        elif valor_vencido_scr > 5000:
            penalidade += 0.3
        elif valor_vencido_scr > 1000:
            penalidade += 0.2
        else:
            penalidade += 0.1
    
    # Dias de atraso em outras instituições
    if dias_atraso_scr > 90:
        penalidade += 0.3
    elif dias_atraso_scr > 60:
        penalidade += 0.2
    elif dias_atraso_scr > 30:
        penalidade += 0.1
    
    # Possui prejuízo em outras instituições
    if valor_prejuizo_scr > 0:
        penalidade += 0.5
    
    # Taxa de utilização do limite (> 90% indica stress financeiro)
    if taxa_utilizacao_scr > 0.9:
        penalidade += 0.15
    elif taxa_utilizacao_scr > 0.7:
        penalidade += 0.05
    
    return min(0.75, penalidade)
```

### 2.3 Fórmula Final

```
PRINAD_Final = min(100%, PD_Base × (1 + Pen_Interna + Pen_Externa))
```

Onde:
- **PD_Base**: Probabilidade do modelo ML (50% do peso)
- **Pen_Interna**: Penalidade por histórico interno no banco (25% do peso, máx 0.75)
- **Pen_Externa**: Penalidade por histórico SCR externo (25% do peso, máx 0.75)

**Exemplo de cálculo**:

| Cliente | PD_Base | Histórico Interno | Histórico SCR | Pen_Int | Pen_Ext | PRINAD |
|---------|---------|-------------------|---------------|---------|---------|--------|
| João | 8% | Sem histórico | Limpo | 0.0 | 0.0 | **8%** |
| Maria | 8% | Atraso 6m atrás | Limpo | 0.5 | 0.0 | **12%** |
| Pedro | 15% | Quitou há 2m | Vencido R$2k | 0.7 | 0.2 | **28.5%** |
| Ana | 10% | Limpo | Rating F, 60d atraso | 0.0 | 0.8 | **18%** |
| Carlos | 20% | Inadimplente 12m | Prejuízo R$5k | 0.75 | 0.75 | **50%** |

---

## 3. Escala de Rating

### 3.1 Mapeamento PD → Rating

A escala de rating segue as melhores práticas internacionais, com faixas customizadas para o perfil de risco do banco:

| Rating | Faixa PD | Descrição | Cor | Ação Sugerida |
|--------|----------|-----------|-----|---------------|
| **A1** | 0.00% - 4.99% | Risco Mínimo | 🟢 | Aprovação automática, melhores taxas |
| **A2** | 5.00% - 14.99% | Risco Muito Baixo | 🟢 | Aprovação automática |
| **A3** | 15.00% - 24.99% | Risco Baixo | 🟢 | Aprovação com análise simplificada |
| **B1** | 25.00% - 34.99% | Risco Baixo-Moderado | 🟡 | Análise padrão |
| **B2** | 35.00% - 44.99% | Risco Moderado | 🟡 | Análise detalhada |
| **B3** | 45.00% - 54.99% | Risco Moderado-Alto | 🟠 | Análise rigorosa, possíveis garantias |
| **C1** | 55.00% - 64.99% | Risco Alto | 🔴 | Exige garantias ou fiador |
| **C2** | 65.00% - 74.99% | Risco Muito Alto | 🔴 | Negação ou condições especiais |
| **C3** | 75.00% - 84.99% | Risco Crítico | 🔴 | Negação, exige garantias sólidas |
| **D** | 85.00% - 94.99% | Pré-Default | ⚫ | Negação, monitoramento intensivo |
| **DEFAULT** | 95.00% - 100.00% | Default | ⚫ | Negação, encaminhar para cobrança |

### 3.2 Comparação com Escalas Internacionais

| Nosso Rating | S&P Equiv. | Moody's Equiv. | Fitch Equiv. |
|--------------|------------|----------------|--------------|
| A1 | AAA/AA+ | Aaa/Aa1 | AAA/AA+ |
| A2 | AA/AA- | Aa2/Aa3 | AA/AA- |
| A3 | A+/A | A1/A2 | A+/A |
| B1 | A-/BBB+ | A3/Baa1 | A-/BBB+ |
| B2 | BBB/BBB- | Baa2/Baa3 | BBB/BBB- |
| B3 | BB+/BB | Ba1/Ba2 | BB+/BB |
| C1 | BB-/B+ | Ba3/B1 | BB-/B+ |
| C2 | B/B- | B2/B3 | B/B- |
| C3 | CCC/CCC- | Caa1/Caa2 | CCC/CCC- |
| D | CC/C | Caa3/Ca | CC/C |
| DEFAULT | D | C | D |

---

## 4. Janela de Observação e Perdão

### 4.1 Lookback Period: 24 Meses

O período de observação de **24 meses** foi escolhido por:

1. **Alinhamento regulatório**: IFRS 9 requer análise de 12 meses + lifetime PD
2. **Ciclo econômico**: Captura pelo menos 2 anos de comportamento
3. **Prática de mercado**: Bureaus de crédito internacionais usam 7 anos, mas modelos internos tipicamente 12-24 meses
4. **Equilíbrio**: Suficiente para identificar padrões, sem penalizar excessivamente

### 4.2 Período de Cura (Perdão): 6 Meses

Após **6 meses consecutivos** sem nenhum evento negativo **interno E externo**:
- As penalidades históricas são **zeradas**
- Cliente passa a ser avaliado apenas pela situação atual
- Incentiva comportamento positivo e reabilitação do cliente

**Requisitos para cura:**

| Condição | Requisito |
|----------|-----------|
| Histórico Interno | 6 meses sem atraso no banco |
| Histórico SCR | 6 meses sem atraso em outras instituições |
| Ambos devem ser atendidos | ✅ |

```python
def verificar_cura(cliente):
    """
    Verifica se cliente atingiu período de cura (6 meses limpo interno E externo)
    """
    meses_limpo_interno = calcular_meses_sem_atraso_interno(cliente)
    meses_limpo_scr = calcular_meses_sem_atraso_scr(cliente)
    
    if meses_limpo_interno >= 6 and meses_limpo_scr >= 6:
        return True  # Perdão concedido
    return False

if verificar_cura(cliente):
    penalidade_interna = 0.0
    penalidade_externa = 0.0
```

---

## 5. Integração com SCR do Banco Central

### 5.1 O que é o SCR?

O **Sistema de Informações de Crédito (SCR)** é um banco de dados mantido pelo Banco Central do Brasil que contém informações sobre operações de crédito de pessoas físicas e jurídicas em todo o Sistema Financeiro Nacional.

### 5.2 Campos da API SCR para Produção

A tabela abaixo lista os campos que **devem ser consumidos da API SCR** em ambiente de produção:

| Campo API | Tipo | Descrição | Uso no Modelo |
|-----------|------|-----------|---------------|
| `valorVencer` | R$ | Valor total a vencer em todas operações | Feature + Taxa utilização |
| `valorVencido` | R$ | Valor em atraso (não pago na data) | **Penalidade externa** |
| `valorPrejuizo` | R$ | Valor baixado como prejuízo | **Penalidade máxima** |
| `limCredito` | R$ | Limite de crédito total concedido | Feature |
| `limCreditoUtilizado` | R$ | Valor utilizado do limite | Taxa de utilização |
| `qtdOperacoes` | Int | Quantidade de operações ativas | Feature de exposição |
| `qtdInstituicoes` | Int | Nº de instituições com operações | Feature de dispersão |
| `diasAtraso` | Int | Dias de atraso da parcela mais atrasada | **Penalidade por severidade** |
| `classificacaoRisco` | Char | Rating de risco BCB (AA a H) | **Penalidade por rating** |
| `modalidade` | Cod | Código da modalidade de operação | Feature categórica |

### 5.3 Features Derivadas do SCR

| Feature Derivada | Fórmula | Descrição |
|------------------|---------|------------|
| `scr_taxa_utilizacao` | limCreditoUtilizado / limCredito | Percentual de limite usado |
| `scr_ratio_vencido` | valorVencido / (valorVencer + valorVencido) | Proporção em atraso |
| `scr_tem_prejuizo` | 1 se valorPrejuizo > 0 | Indicador de prejuízo |
| `scr_score_risco` | AA=0, A=1, B=2, ..., H=8 | Rating numérico |
| `scr_faixa_atraso` | Categorias 0/1-14/15-30/31-60/61-90/90+ | Faixas de atraso |
| `scr_exposicao_total` | valorVencer + valorVencido | Dívida total no SFN |
| `scr_concentracao` | 1/qtdInstituicoes | Índice de concentração |

### 5.4 Endpoint de Consulta SCR

Em produção, a consulta ao SCR deve ser feita via Web Service oficial:

**URL Base:** `https://www9.bcb.gov.br/wsscr2n/api/`

**Parâmetros de Requisição:**

```json
{
  "cdCliente": "12345678901",   // CPF (11 dígitos) ou CNPJ (14 dígitos)
  "tpCliente": "1",             // 1=PF, 2=PJ
  "databaseIni": "202301",      // AAAAMM início
  "databaseFim": "202312",      // AAAAMM fim
  "autorizacao": "S"            // Cliente autorizou consulta
}
```

> ⚠️ **IMPORTANTE**: A consulta ao SCR requer autorização prévia do cliente (Art. 1º, Res. BCB 4.571/2017).

---

## 5. Interpretabilidade (SHAP)

### 5.1 Por que SHAP?

O modelo utiliza **SHAP (SHapley Additive exPlanations)** para:

1. **Conformidade LGPD** (Art. 20): Direito à explicação de decisões automatizadas
2. **Auditoria interna**: Validação de que o modelo não discrimina
3. **Transparência**: Cliente pode entender por que teve crédito negado
4. **Regulatório Basel III**: Demonstração de governance adequada

### 5.2 Exemplo de Explicação

Para cada classificação, o modelo retorna:

```json
{
  "cpf": "12345678901",
  "prinad": 34.5,
  "rating": "B2",
  "pd_base": 15.0,
  "penalidade_historica": 1.3,
  "explicacao_shap": [
    {"feature": "historico_inadimplencia_18m", "contribuicao": +8.5},
    {"feature": "regularizacao_recente_2m", "contribuicao": +4.2},
    {"feature": "renda_liquida", "contribuicao": -3.1},
    {"feature": "tempo_relacionamento", "contribuicao": -2.8},
    {"feature": "ocupacao_autonomo", "contribuicao": +1.5}
  ]
}
```

---

## 6. Métricas de Performance Esperadas

### 6.1 Métricas Mínimas para Produção

| Métrica | Mínimo | Target | Descrição |
|---------|--------|--------|-----------|
| AUC-ROC | 0.75 | 0.82+ | Capacidade discriminatória |
| Gini | 0.50 | 0.64+ | 2×AUC - 1 |
| KS | 0.35 | 0.45+ | Kolmogorov-Smirnov |
| Precision (D) | 0.60 | 0.75+ | Acurácia em defaults |
| Recall (D) | 0.55 | 0.70+ | Cobertura de defaults |

### 6.2 Monitoramento Contínuo

O modelo deve ser reavaliado quando:
- KS cair abaixo de 0.30
- PSI (Population Stability Index) > 0.25
- Taxa de default real divergir >20% do previsto

---

## 7. Governança e Auditoria

### 7.1 Documentação Requerida

- ✅ Este documento de metodologia
- ✅ Código-fonte versionado
- ✅ Logs de treinamento e validação
- ✅ Relatórios de performance mensais
- ✅ Análise de fairness/viés

### 7.2 Ciclo de Revisão

| Frequência | Atividade |
|------------|-----------|
| Mensal | Monitoramento de métricas |
| Trimestral | Relatório de performance |
| Semestral | Backtesting completo |
| Anual | Revisão de metodologia e re-treinamento |

---

## 8. Referências

1. Basel Committee on Banking Supervision. (2017). *Basel III: Finalising post-crisis reforms*. BIS.
2. European Banking Authority. (2021). *Guidelines on PD estimation, LGD estimation and the treatment of defaulted exposures*. EBA.
3. Banco Central do Brasil. (2020). *Circular 3.648 - Cálculo do Risco de Crédito*. BCB.
4. Lundberg, S. M., & Lee, S. I. (2017). *A Unified Approach to Interpreting Model Predictions*. NeurIPS.
