# Avaliação histórica de cobertura - módulos perda_esperada e PRINAD

> **Documento legado, não normativo.** Esta avaliação de 8 de janeiro de 2026 não constitui certificação, validação independente ou parecer de conformidade. Percentuais e selos autodeclarados foram removidos. Citações de artigos e parâmetros abaixo ainda precisam ser conferidas contra fontes oficiais vigentes e vinculadas à matriz de rastreabilidade. Dados, métricas e exemplos do protótipo são sintéticos ou demonstrativos.

**Data da Análise:** 2026-01-08  
**Versão do Sistema:** v2.1  
**Documentos de Referência:**
- Resolução CMN nº 4.966/2021
- Resolução BCB nº 352/2023
- Documentação Técnica de Perda 4966 - BIP
- Leiaute do Documento 3040 (ContInstFinRes4966)

---

## 📊 Resumo Executivo

| Aspecto | Evidência histórica | Situação para modernização |
|---------|---------------------|----------------------------|
| **PRINAD (PD)** | Código e testes estruturais | Requer dados longitudinais, calibração e OOT |
| **ECL (Perda Esperada)** | Produto escalar demonstrativo | Requer motor por período, cenário e desconto |
| **Estágios** | Regras heurísticas | Requer política única relativa à originação |
| **Grupos Homogêneos** | Agrupamentos implementados | Requer validação estatística |
| **Forward Looking** | Multiplicadores fixos | Requer trajetórias e relações macro-risco |
| **LGD Segmentado** | Tabelas e heurísticas | Requer workout LGD descontada |
| **Triggers de Migração** | Regras distribuídas | Requer consolidação e evidência |
| **Reestruturações** | Fluxos parciais | Requer golden cases e rastreabilidade |
| **Exportação regulatória** | XML demonstrativo | Requer leiaute, XSD e críticas versionadas |
| **Write-off e Cura** | Funções e testes estruturais | Requer validação de fonte e integração |

---

## Implementações históricas a verificar

### 1. Classificação em 3 Estágios IFRS 9 (Art. 37, 38, 40 da CMN 4966)

**Interpretação histórica a confirmar:**
> Art. 37: Os instrumentos financeiros devem ser alocados em três estágios para fins de mensuração da provisão para perdas esperadas:
> - Estágio 1: ECL 12 meses
> - Estágio 2: ECL lifetime (aumento significativo de risco)
> - Estágio 3: ECL lifetime (ativo com problema de recuperação)

**Implementação Atual:**
```python
# classifier.py (PRINAD)
ClassificationResult:
    estagio_pe: int = 1  # IFRS 9 Stage (1, 2 ou 3)

# RatingMapper.get_rating()
# - Stage 1: Rating A1-B2 (PRINAD 0-44.99%)
# - Stage 2: Rating B3-C3 (PRINAD 45-84.99%)  
# - Stage 3: Rating D-DEFAULT (PRINAD 85-100%)
```

**Status:** implementação histórica sem validação regulatória independente.

---

### 2. Provisão por Estágio (Art. 47 da CMN 4966)

**Requisito Legal:**
> - Estágio 1: ECL 12 meses
> - Estágio 2: ECL lifetime
> - Estágio 3: ECL lifetime + ativo com problema

**Implementação Atual:**
```python
# pipeline_ecl.py
ECLCompleteResult:
    pd_12m: float        # Para Stage 1
    pd_lifetime: float   # Para Stage 2/3
    horizonte_ecl: str   # "12_meses" ou "lifetime"
```

**Status:** implementação histórica sem validação regulatória independente.

---

### 3. Critérios de Migração para Estágio 2 (Art. 38 da CMN 4966)

**Requisito Legal:**
> Art. 38: A migração para o segundo estágio deve ocorrer quando houver aumento significativo do risco de crédito desde o reconhecimento inicial.

**Critérios avaliados (§1º do Art. 38):**
- ✅ Atraso superior a 30 dias (presunção relativa)
- ✅ Variação significativa da PD desde a concessão
- ✅ Alteração adversa em condições econômicas

**Implementação Atual:**
```python
# modulo_triggers_estagios.py
REGRAS_AUMENTO_RISCO_POR_CLASSIFICACAO = {
    "Parcelado": {
        "pd_concessao_min": 0.0186,
        "pd_atual_min": 0.1112,
        "novo_estagio": 2
    },
    "Rotativo": {
        "pd_atual_threshold": 0.45,
        "novo_estagio": 2
    },
    "Consignado": {
        "pd_atual_min": 0.1105,
        "novo_estagio": 2
    }
}

# aplicar_triggers_atraso()
# - Atraso > 30 dias → Estágio 2
# - Atraso > 90 dias → Estágio 3
```

**Status:** implementação histórica sem validação regulatória independente.

---

### 4. Critérios de Migração para Estágio 3 (Art. 40 da CMN 4966)

**Requisito Legal:**
> Art. 40: A migração para o terceiro estágio ocorre quando o ativo financeiro apresenta problema de recuperação de crédito.

**Implementação Atual:**
```python
# modulo_triggers_estagios.py
def aplicar_triggers_atraso():
    # Trigger para Estágio 3 (mais de 90 dias de atraso)
    condicao_estagio3_atraso = (df_triggers[col_dias_atraso] > 90)
    
# aplicar_triggers_qualitativos()
    # Reestruturações → Estágio 3
    palavras_chave_reneg = r'(?:CONFISS[AÃ]O|RENEGOCIA[CÇ][AÃ]O)'
```

**Status:** implementação histórica sem validação regulatória independente.

---

### 5. Regra de Arrasto de Contraparte (§4º Art. 51 da CMN 4966)

**Requisito Legal:**
> Quando um instrumento financeiro for caracterizado como ativo com problema de recuperação de crédito, todos os instrumentos financeiros da mesma contraparte devem ser caracterizados como tal.

**Implementação Atual:**
```python
# modulo_triggers_estagios.py
def aplicar_arrasto_contraparte():
    # Identificar contrapartes com ao menos um contrato em Estágio 3
    contrapartes_com_estagio3 = df_triggers[
        df_triggers[col_estagio_atual] == 3
    ][col_id_contraparte].unique()
    
    # Marcar todos os contratos dessas contrapartes
    condicao_arrasto = (
        df_triggers[col_id_contraparte].isin(contrapartes_com_estagio3) &
        (df_triggers[col_estagio_atual] < 3)
    )
    df_triggers.loc[condicao_arrasto, col_estagio_atual] = 3
```

**Status:** implementação histórica sem validação regulatória independente.

---

### 6. Grupos Homogêneos de Risco (Art. 42 da CMN 4966)

**Requisito Legal:**
> §2º: Grupo homogêneo de risco é o conjunto de instrumentos financeiros com características semelhantes, considerando:
> - I: Características de risco de crédito da contraparte
> - II: Características do instrumento
> - III: Estágio de alocação
> - IV: Atraso no pagamento

**Implementação Atual:**
```python
# modulo_grupos_homogeneos.py
class GruposHomogeneosConsolidado:
    def calcular_grupos_homogeneos():
        # Método: K-means, Percentis ou Densidade
        # Variáveis: PD, Produto, Atraso
        # 4-5 grupos por segmento (Parcelado, Rotativo, Consignado)
```

**Status:** implementação histórica sem validação regulatória independente.

---

### 7. Fórmula ECL (PD × LGD × EAD)

**Requisito Legal (Art. 44-47):**
> ECL = Probabilidade de Default × Loss Given Default × Exposure at Default

**Implementação Atual:**
```python
# pipeline_ecl.py
def calcular_ecl_completo():
    # PD ajustado com Forward Looking
    pd_ajustado = pd_base * k_pd_fl
    
    # LGD segmentado
    lgd_final = self._calcular_lgd(produto, dias_atraso, ...)
    
    # EAD com CCF
    ead = saldo_utilizado + (limite_disponivel * ccf)
    
    # ECL antes do piso
    ecl_antes_piso = pd_ajustado * lgd_final * ead
    
    # Aplicar pisos mínimos (Stage 3)
    ecl_final = aplicar_piso_minimo(ecl_antes_piso, stage, carteira)
```

**Status:** implementação histórica sem validação regulatória independente.

---

### 8. LGD Segmentado (Documentação Técnica BIP)

**Requisito (Tabela 33 da Doc. Técnica):**
| Segmento | Faixa Atraso | Variáveis | LGD |
|----------|--------------|-----------|-----|
| Consignado | 0-120 | - | 42.51% |
| Consignado | 120-210 | Ocupação | 71.85%-80.02% |
| Parcelados | 0-120 | Prazo | 47.8%-63.32% |
| Rotativos | 0-120 | Valor | 19.51%-29.42% |

**Implementação Atual:**
```python
# modulo_lgd_segmentado.py
class LGDSegmentado:
    def calcular_lgd():
        # Árvore de decisão por:
        # - Tipo de produto
        # - Faixa de atraso
        # - Valor do contrato
        # - Prazo remanescente
        # - Ocupação
```

**Status:** implementação histórica sem validação regulatória independente.

---

### 9. Tratamento de Reestruturações (Art. 41 e §2º Art. 49 da CMN 4966)

**Requisito Legal:**
> §2º Art. 49: Instrumentos renegociados devem ser alocados no terceiro estágio, com provisão de 100%.

**Implementação Atual:**
```python
# modulo_reestruturacao.py
class SistemaReestruturacao:
    criterios_qualitativos = {
        'confissao_divida': ['confissão', 'acordo'],
        'renegociacao_pj': ['renegociação', 'reestrutur'],
        'parcelamento_fatura': ['parcelamento']
    }
    
    def aplicar_tratamento_reestruturacoes():
        # Alocar automaticamente em Estágio 3
        df_result.loc[mask_reestr, 'ESTAGIO_REESTRUTURACAO'] = 3
        # Provisão 100%
        df_result.loc[mask_reestr, 'PROVISAO_REESTRUTURACAO'] = 1.0
```

**Status:** implementação histórica sem validação regulatória independente.

---

### 10. Exportação BACEN Doc3040 (ContInstFinRes4966)

**Requisito (Leiaute SCR3040):**
- Tag `ContInstFinRes4966` com campos ECL obrigatórios
- Campos: ClassificacaoAtivoFinanceiro, EstagioDo, VlrPerdaAcumulada
- Componentes: PD, LGD, EAD

**Implementação Atual:**
```python
# modulo_exportacao_bacen.py
def gerar_xml_doc3040():
    # Gera XML conforme leiaute oficial
    # - Tag ContInstFinRes4966
    # - Campos: classificação, estágio, ECL
    # - Validação XSD
    # - Compactação ZIP
```

**Status:** implementação histórica sem validação regulatória independente.

---

## ⚠️ Requisitos Parcialmente Atendidos

### 1. Forward Looking (Art. 36 §4º e §5º da CMN 4966)

**Requisito Legal:**
> §4º: A estimativa de perda esperada deve considerar informações razoáveis e sustentáveis sobre eventos passados, condições atuais e previsões de condições econômicas futuras.
> §5º: Devem ser considerados cenários múltiplos ponderados por probabilidade.

**Implementação Atual:**
```python
# modulo_forward_looking.py
class ModeloForwardLooking:
    # Variáveis macroeconômicas: SELIC, PIB, IPCA, Endividamento
    # Integração com API BACEN SGS
    
    # PARCIAL: Falta múltiplos cenários ponderados
    def calcular_k_pd_fl():
        # Apenas cenário base implementado
        # Falta: cenário otimista, pessimista
```

**Lacuna Identificada:**
- Falta implementação de múltiplos cenários (otimista, base, pessimista)
- Falta ponderação de probabilidades por cenário
- Modelo atual usa apenas cenário único

**Status:** implementação parcial; cobertura regulatória não mensurada.

---

### 2. Critérios de Cura (Art. 41 da CMN 4966)

**Requisito Legal:**
> Art. 41: O instrumento pode retornar a estágio anterior quando:
> - I: As condições que originaram a migração deixarem de existir
> - II: Período de observação adequado

**Implementação Atual:**
```python
# modulo_reestruturacao.py
def definir_criterios_cura_reestruturacao():
    # Critério 1: 30% de amortização
    mask_amort_30 = (pct_amortizacao >= 0.30)
    
    # PARCIAL: Falta período mínimo de observação documentado
    # Período de cura implementado em prinad (6 meses) mas não integrado
```

**Lacuna Identificada:**
- Critérios de cura implementados, mas falta:
  - Período mínimo de observação formal (6 meses Stage 2→1, 12 meses Stage 3→2)
  - Integração com dados de pagamento contínuo
  - Flag de "em período de cura"

**Status:** implementação parcial; cobertura regulatória não mensurada.

---

### 3. Write-off e Baixa de Ativos (Art. 49 da CMN 4966)

**Requisito Legal:**
> Art. 49: O ativo financeiro deve ser baixado quando não seja provável recuperar seu valor.
> §1º: Manter controles por 5 anos mínimo após baixa.

**Implementação Atual:**
```python
# modulo_analise_writeoff.py
# Análise de write-off implementada
# PARCIAL: Falta rastreamento de 5 anos
```

**Lacuna Identificada:**
- Falta sistema de rastreamento de ativos baixados por 5 anos
- Falta integração com cobrança para acompanhamento pós-baixa

**Status:** implementação parcial; cobertura regulatória não mensurada.

---

## ❌ Requisitos Não Atendidos

### 1. Metodologia Simplificada para S4/S5 (Art. 50-51 da CMN 4966)

**Requisito:**
> Instituições S4/S5 podem usar metodologia simplificada.

**Status:** ❌ **NÃO IMPLEMENTADO** (Não aplicável - sistema é para S1-S3)

---

### 2. Contabilidade de Hedge (Capítulo V da CMN 4966)

**Requisito:**
> Arts. 52-64: Contabilidade de hedge (valor justo, fluxo de caixa, investimento no exterior).

**Status:** ❌ **NÃO IMPLEMENTADO** (Fora do escopo do sistema atual)

---

## 📋 Plano de Implementação - Gaps Identificados

### Prioridade 1: Forward Looking Multi-Cenário

**Objetivo:** Implementar cenários múltiplos ponderados conforme Art. 36 §5º

**Tarefas:**
1. [ ] Criar módulo `cenarios_fl.py` com 3 cenários (otimista, base, pessimista)
2. [ ] Definir ponderações padrão (15%, 70%, 15%)
3. [ ] Implementar cálculo de K_PD_FL ponderado
4. [ ] Atualizar pipeline ECL para usar cenários
5. [ ] Adicionar configuração para sobreposição de ponderações

**Estimativa:** 3-4 dias  
**Complexidade:** Média

---

### Prioridade 2: Sistema de Cura Formal

**Objetivo:** Implementar critérios formais de cura com período de observação

**Tarefas:**
1. [ ] Criar tabela de "período de cura" com histórico
2. [ ] Implementar contagem de meses em adimplência
3. [ ] Regra Stage 2→1: 6 meses sem atraso + melhora PD
4. [ ] Regra Stage 3→2: 12 meses + amortização significativa
5. [ ] Flag `em_periodo_cura` no resultado do pipeline
6. [ ] Integrar com módulo de triggers

**Estimativa:** 2-3 dias  
**Complexidade:** Média

---

### Prioridade 3: Rastreamento de Write-off (5 anos)

**Objetivo:** Manter controles de ativos baixados por 5 anos

**Tarefas:**
1. [ ] Criar modelo de dados para ativos baixados
2. [ ] Implementar histórico de recuperações pós-baixa
3. [ ] Dashboard de acompanhamento de write-off
4. [ ] Exportação para auditoria

**Estimativa:** 2-3 dias  
**Complexidade:** Média

---

### Prioridade 4: Validação Completa Doc3040

**Objetivo:** Validação semântica completa conforme regras BACEN

**Tarefas:**
1. [ ] Implementar todas as 15+ regras semânticas do leiaute
2. [ ] Validação de sequência de estágios
3. [ ] Validação de consistência PD × LGD × EAD = ECL
4. [ ] Relatório detalhado de validação

**Estimativa:** 2 dias  
**Complexidade:** Baixa

---

### Prioridade 5: Backtesting Automatizado

**Objetivo:** Validação periódica do modelo conforme boas práticas

**Tarefas:**
1. [ ] Implementar backtesting mensal de PD observado vs. esperado
2. [ ] Comparar LGD realizado vs. estimado
3. [ ] Alertas de degradação de modelo
4. [ ] Relatório de performance do modelo

**Estimativa:** 3-4 dias  
**Complexidade:** Alta

---

## 📊 Cronograma Sugerido

| Semana | Tarefa | Responsável | Status |
|--------|--------|-------------|--------|
| 1 | Forward Looking Multi-Cenário | Backend | 🔲 Pendente |
| 1-2 | Sistema de Cura Formal | Backend | 🔲 Pendente |
| 2 | Rastreamento Write-off | Backend | 🔲 Pendente |
| 2 | Validação Doc3040 | Backend | 🔲 Pendente |
| 3 | Backtesting Automatizado | Data Science | 🔲 Pendente |
| 3 | Testes e Documentação | QA | 🔲 Pendente |

---

## 🔍 Conclusão

O documento histórico identificou componentes implementados, mas não oferece método válido para medir conformidade. Os principais gaps registrados são:

1. **Forward Looking Multi-Cenário** - Impacto regulatório médio
2. **Sistema de Cura Formal** - Impacto regulatório médio
3. **Rastreamento de Write-off** - Impacto regulatório baixo

Recomenda-se conferir a exigência forward-looking na fonte oficial vigente e priorizar cenários completos com evidência, conforme a matriz regulatória a ser construída.

---

**Elaborado por:** avaliação automatizada histórica
**Aprovado por:** [Pendente]  
**Data de Aprovação:** [Pendente]
