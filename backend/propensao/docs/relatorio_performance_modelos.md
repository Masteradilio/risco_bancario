# 📊 Relatório de Performance de Modelos
*Gerado em: 31/12/2025 20:08*

> Relatório histórico sobre dados sintéticos/demonstrativos. Métricas não representam performance institucional, teste OOT independente ou aprovação vigente.

---

## Sumário Executivo

Este relatório apresenta a validação de performance dos três modelos de risco 
do sistema PROLIMITE, seguindo os mais rigorosos padrões bancários internacionais:

- **Basel III** - Framework de capital regulatório
- **SR 11-7** - Gestão de risco de modelos (Fed/OCC)
- **IFRS 9** - Perda de crédito esperada

### Thresholds para Produção

| Métrica | Mínimo | Desejável | Excelente |
|---------|--------|-----------|-----------|
| **AUC-ROC** | ≥ 0.90 | ≥ 0.95 | ≥ 0.98 |
| **Gini** | ≥ 0.80 | ≥ 0.90 | ≥ 0.96 |
| **KS** | ≥ 50% | ≥ 60% | ≥ 70% |
| **PSI** | < 0.25 | < 0.10 | < 0.05 |

---

## 1. PRINAD - Modelo de Risco de Inadimplência

### Status Geral: AMARELO 🟡

**Objetivo**: Estimar a Probabilidade de Default (PD) para cálculo de ECL IFRS 9.

| Métrica | Valor | Status |
|---------|-------|--------|
| AUC_ROC | 0.9396 | 🟡 |
| GINI | 0.8792 | 🟡 |
| KS | 0.7297 | 🟢 |
| PSI | 0.0000 | 🟢 |
| BRIER | 0.1069 | 🟡 |

**Recomendação**: ⚠️ APROVADO COM RESSALVAS. Implementar com monitoramento intensivo e plano de contingência. Revisar métricas em 30 dias.

#### O que significa para o negócio?

BOM: O modelo atende aos requisitos mínimos para produção com bom poder de discriminação.

Impacto Financeiro: Cada ponto percentual de melhoria no AUC pode representar redução de 5-10% nas perdas de crédito. Com uma carteira de R$15 bilhões e inadimplência de 2.5%, um AUC alto pode economizar milhões em provisões.

---

## 2. PROPENSÃO - Modelo de Propensão a Crédito

### Status Geral: VERMELHO 🔴

**Objetivo**: Identificar clientes com maior propensão a contratar produtos de crédito.

| Métrica | Valor | Status |
|---------|-------|--------|
| AUC_ROC | 0.8590 | 🔴 |
| GINI | 0.7180 | 🔴 |
| KS | 0.5472 | 🟡 |
| PSI | 0.0000 | 🟢 |
| BRIER | 0.1348 | 🟡 |

**Recomendação**: ⛔ NÃO RECOMENDADO PARA PRODUÇÃO. Uma ou mais métricas críticas não atingiram o threshold mínimo. Revisar modelo antes de implementação.

---

## 3. PROLIMITE - Modelo de Alocação de Limites

### Status Geral: VERMELHO 🔴

**Objetivo**: Prever necessidade de ajuste de limites de crédito com 60 dias de antecedência.

| Métrica | Valor | Status |
|---------|-------|--------|
| AUC_ROC | 0.8050 | 🔴 |
| GINI | 0.6100 | 🔴 |
| KS | 0.4506 | 🔴 |
| PSI | 0.0000 | 🟢 |
| BRIER | 0.1633 | 🔴 |

**Recomendação**: ⛔ NÃO RECOMENDADO PARA PRODUÇÃO. Uma ou mais métricas críticas não atingiram o threshold mínimo. Revisar modelo antes de implementação.

---

## 4. Backtesting - Validação Histórica (12 meses)

### PRINAD

| Métrica | Valor |
|---------|-------|
| AUC Médio | 100.00% |
| AUC Desvio Padrão | 0.00% |
| Gini Médio | 100.00% |
| KS Médio | 100.00% |
| PSI Médio | 0.061 |
| Accuracy Ratio | 0.95 |
| **Passou Validação** | ✅ SIM |

### PROPENSÃO

| Métrica | Valor |
|---------|-------|
| AUC Médio | 100.00% |
| AUC Desvio Padrão | 0.00% |
| **Passou Validação** | ✅ SIM |

---

## 5. Impacto Financeiro Projetado

*Baseline: 3T2025 - Carteira R$ 15.8 bilhões*

| Cenário | Economia ECL | Impacto ROE | Clientes Notificados |
|---------|--------------|-------------|----------------------|
| Conservador | R$ 99.5 mi | +7.98 p.p. | 21,000 |
| Moderado | R$ 56.9 mi | +8.48 p.p. | 21,000 |
| Otimista | R$ 75.8 mi | +8.90 p.p. | 21,000 |

**✅ RECOMENDAÇÃO: Implementar cenário MODERADO. Projeção de economia de R$ 56.9 milhões em ECL com impacto positivo de 8.48 p.p. no ROE.**

---

## 6. Conclusão e Recomendações para Diretoria

### Pontos Fortes

✅ **PRINAD** apresenta AUC de 93.96%, demonstrando alta capacidade discriminatória

### Pontos de Atenção

⚠️ Modelo de Propensão precisa de mais features para melhorar discriminação
⚠️ PROLIMITE requer validação adicional com dados históricos

### Benefícios Esperados

1. **Economia de Provisão**: Até R$ 57 milhões/ano em ECL
2. **Melhoria de ROE**: +8.5 pontos percentuais
3. **Gestão Proativa**: 60 dias de antecedência para ajustes de limite
4. **Redução de Atrito**: Notificações proativas reduzem reclamações
5. **Compliance IFRS 9**: Cálculo de ECL alinhado com padrões internacionais

### Próximos Passos

1. Validação com dados históricos reais de 12 meses
2. Implementação em ambiente de homologação
3. Monitoramento por 30 dias com população controlada
4. Roll-out gradual (10% → 50% → 100%)

---

*Relatório gerado automaticamente pelo sistema PROLIMITE*
*Versão: 1.0 | Data: 31/12/2025 20:08*
