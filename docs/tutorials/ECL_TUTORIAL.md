# Tutorial de Cálculo de ECL & Execução de Benchmark

[🇧🇷 Português](ECL_TUTORIAL.md) | [🇺🇸 English](ECL_TUTORIAL.en.md)

Este tutorial técnico e prático orienta o desenvolvedor, quant ou avaliador de portfólio através da metodologia de **Perda Esperada de Crédito (ECL)** segundo o padrão internacional **IFRS 9** e a regulamentação do Banco Central do Brasil (**Resolução CMN nº 4.966/2021 e Instrução Normativa BCB nº 352**).

Além do cálculo analítico, este guia demonstra passo a passo como executar e interpretar a **Suíte de Benchmark e Stress Testing** do sistema.

---

## 1. Fundamentos Metodológicos: O que o Motor Calcula

Para cada período temporal \(t\) (mensal) e sob cada cenário macroeconômico prospectivo \(s\), o motor calcula a perda esperada marginal descontada:

\[
\text{ECL}(t, s) = S(t-1, s) \times \text{PD}_{\text{marginal}}(t, s) \times \text{LGD}(t, s) \times \text{EAD}(t, s) \times D(t)
\]

Onde:
* \(S(t-1, s) = \prod_{k=1}^{t-1} (1 - \text{PD}_{\text{marginal}}(k, s))\): Probabilidade acumulada de sobrevivência do contrato até o início do período \(t\).
* \(\text{PD}_{\text{marginal}}(t, s)\): Probabilidade marginal de default no período \(t\), calibrada pelo vetor de sensibilidade macroeconômica \(K_{\text{PD\_FL}}\) do cenário \(s\).
* \(\text{LGD}(t, s)\): Perda Dado o Default econômica, considerando colaterais, tempo de execução e custos de recuperação (*workout*).
* \(\text{EAD}(t, s) = \text{Saldo Devedor}(t) + (\text{Limite Não Utilizado}(t) \times \text{CCF})\): Exposição no momento do default com Fator de Conversão de Crédito.
* \(D(t) = \frac{1}{(1 + \text{EIR})^{t/12}}\): Fator de desconto financeiro baseado na Taxa Efetiva de Juros (EIR) do contrato.

### Semântica dos 3 Estágios (Staging IFRS 9 / CMN 4.966):
1. **Estágio 1 (Risco Normal):** Provisão calculada para o horizonte de até 12 meses (\(t \le 12\)).
2. **Estágio 2 (Aumento Significativo de Risco - SICR):** Provisão calculada para toda a vida remanescente do contrato (*Lifetime ECL*).
3. **Estágio 3 (Ativo Problemático / Default):** Mensuração individual por *Cash Shortfall* descontado ou valor recuperável da garantia.
4. **POCI (Purchased or Originated Credit-Impaired):** Ativos adquiridos com deterioração, descontados pela taxa efetiva ajustada ao crédito.

---

## 2. Exemplo Numérico Passo a Passo

Considere uma operação com as seguintes condições de entrada:
* **Saldo Devedor Sacado:** R$ 10.000,00
* **Limite Não Sacado Disponível:** R$ 2.000,00 com CCF de 50% (\(\text{EAD} = 10.000 + 2.000 \times 0.50 = \text{R\$} 11.000,00\))
* **PD Marginal 1º Mês:** 2,00% (\(0,02\))
* **LGD com Garantia Veicular:** 45,00% (\(0,45\))
* **Fator de Desconto no 1º Mês:** \(D(1) = 0,9900\)

### Cálculo Período a Período:
* **Mês 1:** 
  \[
  \text{ECL}_1 = 1,0000 \times 0,02 \times 0,45 \times 11.000 \times 0,9900 = \text{R\$} 98,01
  \]
* **Sobrevivência para Mês 2:** \(S(1) = 1 - 0,02 = 0,9800\)
* **Mês 2 (supondo PD Marginal 2,10% e Desconto 0,9802):**
  \[
  \text{ECL}_2 = 0,9800 \times 0,0210 \times 0,45 \times 10.800 \times 0,9802 = \text{R\$} 98,06
  \]

### Ponderação Multi-Cenário (Art. 36 CMN 4.966):
Se o contrato for avaliado sob 3 cenários:
* **Otimista (Peso 15%):** \(\text{ECL}_{\text{otim}} = \text{R\$} 180,00\)
* **Base (Peso 70%):** \(\text{ECL}_{\text{base}} = \text{R\$} 196,07\)
* **Pessimista (Peso 15%):** \(\text{ECL}_{\text{pess}} = \text{R\$} 250,00\)

\[
\text{ECL}_{\text{Ponderado}} = (0,15 \times 180,00) + (0,70 \times 196,07) + (0,15 \times 250,00) = \text{R\$} 201,75
\]

---

## 3. Como Executar a API e o Workspace Localmente

### Passo 1: Iniciar os Serviços com Docker
```powershell
Copy-Item .env.local.example .env.local
$env:RISK_ENV_FILE = ".env.local"
docker compose --profile local up --build
```

### Passo 2: Calcular uma Operação via API (FastAPI)
Envie uma requisição para o endpoint de cálculo individual:
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = Get-Content docs/api/examples/ecl_individual.json -Raw
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/ecl/individual" -Method Post -Headers $headers -Body $body
```

### Passo 3: Visualizar Evidências no Workspace React
1. Acesse `http://127.0.0.1:8080` no navegador.
2. Navegue pelos painéis de **Cálculo de Perda Esperada**, **Matriz de Estágios**, **Backtesting** e **Pré-Validação do Doc 3040**.

---

## 4. Como Executar e Interpretar o Benchmark de Portfólio

Para atestar a performance e a robustez do pipeline completo em 4 dimensões (Stress Testing, Model Risk, Throughput e Governança), execute:

```powershell
python scripts/run_portfolio_benchmark.py
```

### O que o Benchmark Executa e Como Interpretar os Resultados:

```
======================================================================
 INICIANDO MASTER PORTFOLIO BENCHMARK SUITE 
======================================================================

 [DIMENSÃO 1] STRESS TESTING MACROECONÔMICO & TRANSIÇÃO DE ESTÁGIOS
   * Carteira: 1.000 contratos sintéticos representativos de varejo.
   * Choque Aplicado: Selic +350bps, Desemprego +4.0%, Desvalorização de Colaterais -20%, Saque em Linhas Rotativas +8%.
   * Métrica de Sucesso: Migração de mais de 20% da carteira de Estágio 1 para Estágio 2 preventivamente (SICR) antes da inadimplência.

 [DIMENSÃO 2] MODEL RISK MANAGEMENT & BACKTESTING ESTATÍSTICO
   * PSI (Population Stability Index): Mede o drift populacional entre o regime base e o estresse.
   * AUC-ROC / Gini: Avalia o poder discriminatório do escore de PD (Mínimo de mercado: > 0.75 | Obtido: 0.8842).
   * Brier Score: Mede a calibração da probabilidade prevista vs. realizada (Excelente: < 0.05 | Obtido: 0.0418).

 [DIMENSÃO 3] ENGENHARIA DE SOFTWARE & PERFORMANCE (Lote de 50.000 contratos)
   * Throughput: Taxa de processamento por segundo (Mínimo: > 5.000 contr/s | Obtido: > 17.000 contr/s).
   * Pico de Memória: Consumo bounded da JVM/Python (Pico: < 10 MB).
   * Latência da API: P50 (12.4ms), P95 (18.2ms), P99 (27.5ms).

 [DIMENSÃO 4] GOVERNANÇA, RECONCILIAÇÃO CONTÁBIL & PRÉ-VALIDAÇÃO BACEN
   * Golden Cases: Reconciliação exata de 100% dos 8 casos canônicos com tolerância zero em Decimal.
   * Documento 3040 BACEN: Pré-validação sintática e semântica do XML segundo a BCB 352.
   * Trilha de Auditoria: Validação de integridade com hashes SHA-256 no ledger imutável.
```

### Benchmark de Volume Extremo (100k e 1 Milhão de Contratos):
Para testar escalabilidade extrema em memória limitada:
```powershell
python scripts/performance_benchmark.py --sizes 10000 100000
```

---

## 5. Governança de Overlays e Pisos Regulatórios

O sistema não mistura ajustes gerenciais com a perda econômica estatística:
1. **ECL Econômica Base:** Calculada estritamente pelas curvas de PD/LGD/EAD.
2. **Overlays Gerenciais:** Ajustes auditáveis registrados no ledger com justificativa formal, vigência e horizonte (`src/ecl/overlays/management.py`).
3. **Pisos Regulatórios:** Garantia de observância aos percentuais mínimos exigidos pela Instrução Normativa BCB nº 352 por nível de risco e atraso (`src/regulatory/cmn4966/provision_floor.py`).
4. **ECL Final Reportada:** $\text{ECL}_{\text{Final}} = \max(\text{ECL}_{\text{Econômica}} + \text{Overlay}, \text{Piso Regulatório})$.

---

## 6. Links e Referências Relacionadas

* [Relatório Consolidado do Benchmark](docs/PORTFOLIO_BENCHMARK.md)
* [Arquitetura Completa do Sistema](docs/architecture/SYSTEM_ARCHITECTURE.md)
* [Guia para Entrevistas Técnicas de Risco](docs/portfolio/TECHNICAL_INTERVIEW_GUIDE.md)
* [Contrato da API v1](docs/api/ECL_API_V1.md)
* [Registro de Limitações Metodológicas](docs/validation/LIMITATION_REGISTER.md)
