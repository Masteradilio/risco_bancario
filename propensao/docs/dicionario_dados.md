# Dicionário de Dados - Sistema PROLIMITE

## Visão Geral

Este documento descreve todos os campos de dados utilizados pelo sistema PROLIMITE,
incluindo origem, tipo, e regras de negócio associadas.

---

## Tabela: tb_clientes_base

**Descrição**: Dados cadastrais dos clientes com scores PRINAD calculados.

| Campo | Tipo | Obrigatório | Origem | Descrição |
|-------|------|-------------|--------|-----------|
| `CLIT` | VARCHAR(20) | ✅ | Banco | ID interno do cliente (uso em auditoria) |
| `CPF` | VARCHAR(11) | ✅ | Banco | CPF do cliente (mascarar em produção) |
| `IDADE_CLIENTE` | INT | ❌ | Banco | Idade em anos |
| `ESCOLARIDADE` | VARCHAR(30) | ❌ | Banco | Fundamental/Médio/Superior |
| `RENDA_BRUTA` | DECIMAL(15,2) | ✅ | Banco | Renda bruta mensal |
| `RENDA_LIQUIDA` | DECIMAL(15,2) | ❌ | Banco | Renda líquida mensal |
| `TEMPO_RELAC` | DECIMAL(10,2) | ❌ | Banco | Tempo de relacionamento em meses |
| `ESTADO_CIVIL` | VARCHAR(20) | ❌ | Banco | Solteiro/Casado/Divorciado/Viúvo |
| `TIPO_RESIDENCIA` | VARCHAR(30) | ❌ | Banco | Própria/Alugada/Cedida |
| `POSSUI_VEICULO` | VARCHAR(5) | ❌ | Banco | SIM/NAO |
| `QT_PRODUTOS` | INT | ❌ | Banco | Quantidade de produtos contratados |
| `comprometimento_renda` | DECIMAL(5,4) | ✅ | Calculado | Parcelas / Renda (0-1) |
| `margem_disponivel` | DECIMAL(15,2) | ✅ | Calculado | (Renda × 70%) - Parcelas |
| `PRINAD_SCORE` | INT | ✅ | Modelo | Score de risco 0-100 |
| `RATING` | VARCHAR(10) | ✅ | Modelo | A1/A2/A3/B1/B2/B3/C1/C2/C3/D/DEFAULT |
| `RATING_DESC` | VARCHAR(50) | ❌ | Modelo | Descrição do rating |
| `scr_score_risco` | INT | ❌ | BACEN/Sint. | Score SCR (300-900) |
| `scr_dias_atraso` | INT | ❌ | BACEN/Sint. | Dias em atraso no SFN |
| `scr_tem_prejuizo` | TINYINT | ❌ | BACEN/Sint. | 1 = Tem prejuízo no SFN |
| `scr_exposicao_total` | DECIMAL(15,2) | ❌ | BACEN/Sint. | Exposição total no SFN |
| `dt_referencia` | DATE | ✅ | Sistema | Data de referência dos dados |
| `dt_processamento` | DATETIME | ✅ | Sistema | Timestamp do processamento |

---

## Tabela: tb_clientes_produtos

**Descrição**: Dados por cliente × produto, incluindo limites, propensão e ECL.

| Campo | Tipo | Obrigatório | Origem | Descrição |
|-------|------|-------------|--------|-----------|
| `CLIT` | VARCHAR(20) | ✅ | Banco | ID do cliente |
| `produto` | VARCHAR(30) | ✅ | Banco | Nome do produto |
| `limite_total` | DECIMAL(15,2) | ✅ | Banco | Limite concedido |
| `limite_utilizado` | DECIMAL(15,2) | ✅ | Banco | Limite em uso |
| `limite_disponivel` | DECIMAL(15,2) | ✅ | Calculado | Limite livre |
| `taxa_utilizacao` | DECIMAL(5,4) | ✅ | Calculado | Utilizado / Total |
| `parcelas_mensais` | DECIMAL(15,2) | ❌ | Banco/Sint. | Valor da parcela mensal |
| `utilizacao_media_12m` | DECIMAL(5,4) | ❌ | Calculado | Média utilização 12 meses |
| `trimestres_sem_uso` | INT | ❌ | Calculado | Trimestres consecutivos sem uso (0-4) |
| `max_dias_atraso_12m` | INT | ❌ | Banco | Máximo atraso em 12 meses |
| `tipo_garantia` | VARCHAR(30) | ❌ | Derivado | Tipo de garantia |
| `valor_garantia` | DECIMAL(15,2) | ❌ | Banco/Sint. | Valor do colateral |
| `ltv` | DECIMAL(5,4) | ❌ | Calculado | Loan-to-Value |
| `propensao_score` | INT | ✅ | Modelo | Score de propensão 0-100 |
| `propensao_classificacao` | VARCHAR(10) | ✅ | Modelo | ALTA/MEDIA/BAIXA |
| `lgd` | DECIMAL(5,4) | ✅ | Modelo | Loss Given Default |
| `ecl` | DECIMAL(15,2) | ✅ | Calculado | Expected Credit Loss |
| `acao_limite` | VARCHAR(20) | ✅ | Modelo | MANTER/AUMENTAR/REDUZIR/ZERAR |
| `limite_recomendado` | DECIMAL(15,2) | ✅ | Modelo | Novo limite sugerido |
| `horizonte_dias` | INT | ✅ | Modelo | Dias até ação: 0, 30, 60 |

---

## Produtos do Sistema

| Código | Nome | Limite Comprometimento | Conta no 70%? |
|--------|------|------------------------|---------------|
| `consignado` | Consignado | 35% | Sim |
| `banparacard` | Banparacard | 20% | Sim |
| `cartao_credito_rotativo` | Cartão Rotativo | N/A | **Não** |
| `cartao_credito_parcelado` | Cartão Parcelado | N/A | **Não** |
| `imobiliario` | Imobiliário | 30% | Sim |
| `credito_sazonal` | Crédito Sazonal | 80%* | **Não** |
| `cred_veiculo` | Crédito Veículo | 25% | Sim |
| `energia_solar` | Energia Solar | 25% | Sim |
| `cheque_especial` | Cheque Especial | 10% | Sim |

*80% do valor do 13º salário ou restituição de IR

---

## Ratings PRINAD

| Rating | PRINAD | Descrição | Ação Sugerida |
|--------|--------|-----------|---------------|
| A1 | 0-4.99% | Risco Mínimo | Aumento de limite |
| A2 | 5-14.99% | Risco Muito Baixo | Aumento moderado |
| A3 | 15-24.99% | Risco Baixo | Manter |
| B1 | 25-34.99% | Risco Baixo-Moderado | Manter |
| B2 | 35-44.99% | Risco Moderado | Manter com monitoramento |
| B3 | 45-54.99% | Risco Moderado-Alto | Monitoramento intensivo |
| C1 | 55-64.99% | Risco Alto | Reduzir limite |
| C2 | 65-74.99% | Risco Muito Alto | Reduzir significativamente |
| C3 | 75-84.99% | Risco Crítico | Reduzir 50% |
| D | 85-94.99% | Pré-Default | Reduzir 75% |
| DEFAULT | 95-100% | Default | Zerar limite, cobrança |

---

## Classificação de Propensão

| Classificação | Score | Significado |
|---------------|-------|-------------|
| ALTA | 70-100 | Cliente propenso a utilizar crédito |
| MEDIA | 40-69 | Propensão moderada |
| BAIXA | 0-39 | Pouco propenso |

---

## Ações de Limite

| Ação | Condição | Novo Limite | Horizonte |
|------|----------|-------------|-----------|
| **ZERAR** | Rating DEFAULT (PRINAD ≥ 95%) | 0 | Imediato |
| **REDUZIR 25%** | Rating D (PRINAD 85-94%) | 25% do atual | Imediato |
| **REDUZIR 50%** | Rating C3 (PRINAD 75-84%) | 50% do atual | 30 dias |
| **REDUZIR 50%** | Propensão < 45 E Utilização < 30% | 50% do atual | 60 dias |
| **AUMENTAR** | PRINAD < 75% + Propensão > 55 + Margem + Comprometimento < 65% | +25% | Imediato |
| **MANTER** | Todos os demais | Sem alteração | - |

---

## Garantias

| Tipo | LGD Base | Produtos Associados |
|------|----------|---------------------|
| `imovel_residencial` | 25% | imobiliario |
| `consignacao` | 25% | consignado, credito_sazonal |
| `veiculo` | 40% | cred_veiculo |
| `equipamento` | 40% | energia_solar |
| `nenhuma` | 60% | banparacard, cartões, cheque |

---

## Fórmulas Principais

### ECL (Expected Credit Loss)
```
ECL = PD × LGD × EAD

Onde:
- PD = PRINAD_SCORE / 100
- LGD = Baseado no tipo de garantia
- EAD = limite_utilizado + (limite_disponivel × 0.5)
```

### Comprometimento de Renda
```
comprometimento_renda = Σ parcelas (que contam) / renda_bruta

Produtos que NÃO contam:
- cartao_credito_rotativo
- cartao_credito_parcelado
- credito_sazonal
```

### Margem Disponível
```
margem_disponivel = (renda_bruta × 0.70) - Σ parcelas
```

---

## Frequência de Atualização

| Dado | Frequência | Responsável |
|------|------------|-------------|
| Cadastro | Diária | Core Banking |
| Limites | Diária | Sistema de Crédito |
| SCR | Mensal | API BACEN |
| PRINAD | Diária (após carga) | PROLIMITE |
| Propensão | Diária (após PRINAD) | PROLIMITE |
| Notificações | Diária (após modelos) | PROLIMITE |

---

## Contato

Para dúvidas sobre este dicionário de dados, contatar a equipe de Analytics.
