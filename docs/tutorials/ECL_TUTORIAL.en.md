# Expected Credit Loss (ECL) Calculation & Benchmark Tutorial

[🇧🇷 Português](ECL_TUTORIAL.md) | [🇺🇸 English](ECL_TUTORIAL.en.md)

This practical and technical guide walks software engineers, quantitative analysts, and hiring managers through the **Expected Credit Loss (ECL)** modeling methodology under international **IFRS 9** standards and Brazilian Central Bank regulation (**CMN Resolution No. 4,966/2021 & BCB Normative Instruction No. 352**).

In addition to the analytical formulation, this tutorial provides step-by-step instructions on executing and interpreting the platform's **Master Portfolio Benchmark and Stress Testing Suite**.

---

## 1. Methodological Foundations: What the Engine Computes

For each monthly time period \(t\) under each prospective macroeconomic scenario \(s\), the engine computes the marginal discounted expected credit loss:

\[
\text{ECL}(t, s) = S(t-1, s) \times \text{PD}_{\text{marginal}}(t, s) \times \text{LGD}(t, s) \times \text{EAD}(t, s) \times D(t)
\]

Where:
* \(S(t-1, s) = \prod_{k=1}^{t-1} (1 - \text{PD}_{\text{marginal}}(k, s))\): Cumulative contract survival probability until the start of period \(t\).
* \(\text{PD}_{\text{marginal}}(t, s)\): Marginal probability of default in period \(t\), calibrated by the scenario's macroeconomic sensitivity multiplier \(K_{\text{PD\_FL}}\).
* \(\text{LGD}(t, s)\): Economic Loss Given Default, factoring in collateral haircuts, workout timelines, and recovery costs.
* \(\text{EAD}(t, s) = \text{Drawn Balance}(t) + (\text{Undrawn Line Limit}(t) \times \text{CCF})\): Exposure at Default including Credit Conversion Factor.
* \(D(t) = \frac{1}{(1 + \text{EIR})^{t/12}}\): Financial discounting factor based on the contract's Effective Interest Rate (EIR).

### Semantics of the 3 Stages (IFRS 9 / CMN 4,966):
1. **Stage 1 (Standard Risk):** Loss allowance calculated over a maximum 12-month horizon (\(t \le 12\)).
2. **Stage 2 (Significant Increase in Credit Risk - SICR):** Loss allowance calculated over the full contract remaining life (*Lifetime ECL*).
3. **Stage 3 (Credit-Impaired / Default):** Individual measurement via discounted Cash Shortfall or collateral net realizable value.
4. **POCI (Purchased or Originated Credit-Impaired):** Purchased distressed assets, discounted at the credit-adjusted effective interest rate.

---

## 2. Step-by-Step Numerical Example

Consider an operation with the following baseline inputs:
* **Drawn Principal Balance:** $10,000.00
* **Available Undrawn Credit Limit:** $2,000.00 with a 50% CCF (\(\text{EAD} = 10,000 + 2,000 \times 0.50 = \$11,000.00\))
* **1st Month Marginal PD:** 2.00% (\(0.02\))
* **Vehicle-Backed Collateral LGD:** 45.00% (\(0.45\))
* **1st Month Discount Factor:** \(D(1) = 0.9900\)

### Period-by-Period Calculation:
* **Month 1:** 
  \[
  \text{ECL}_1 = 1.0000 \times 0.02 \times 0.45 \times 11,000 \times 0.9900 = \$98.01
  \]
* **Survival Probability into Month 2:** \(S(1) = 1 - 0.02 = 0.9800\)
* **Month 2 (assuming Marginal PD 2.10% and Discount 0.9802):**
  \[
  \text{ECL}_2 = 0.9800 \times 0.0210 \times 0.45 \times 10,800 \times 0.9802 = \$98.06
  \]

### Multi-Scenario Probability Weighting (CMN 4,966 Art. 36):
Evaluating the contract under 3 forward-looking macroeconomic scenarios:
* **Optimistic (Weight 15%):** \(\text{ECL}_{\text{opt}} = \$180.00\)
* **Baseline (Weight 70%):** \(\text{ECL}_{\text{base}} = \$196.07\)
* **Pessimistic (Weight 15%):** \(\text{ECL}_{\text{pess}} = \$250.00\)

\[
\text{ECL}_{\text{Weighted}} = (0.15 \times 180.00) + (0.70 \times 196.07) + (0.15 \times 250.00) = \$201.75
\]

---

## 3. Running the API and Workspace Locally

### Step 1: Start Services with Docker
```powershell
Copy-Item .env.local.example .env.local
$env:RISK_ENV_FILE = ".env.local"
docker compose --profile local up --build
```

### Step 2: Calculate a Single Contract via FastAPI
Send a calculation payload to the canonical endpoint:
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = Get-Content docs/api/examples/ecl_individual.json -Raw
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/ecl/individual" -Method Post -Headers $headers -Body $body
```

### Step 3: Inspect Real-Time Evidence in the React Workspace
1. Open `http://127.0.0.1:8080` in your web browser.
2. Explore the **ECL Calculation Workspace**, **Staging Matrix**, **Model Backtesting Charts**, and **BACEN Document 3040 Pre-validator**.

---

## 4. How to Execute & Interpret the Master Benchmark

To evaluate full-pipeline robustness across 4 dimensions (Stress Testing, Model Risk, Throughput, and Governance), run:

```powershell
python scripts/run_portfolio_benchmark.py
```

### Benchmark Dimensions & Interpretation:

```
======================================================================
 MASTER PORTFOLIO BENCHMARK SUITE EXECUTION 
======================================================================

 [DIMENSION 1] MACROECONOMIC STRESS TESTING & STAGING DYNAMICS
   * Cohort: 1,000 synthetic retail credit contracts.
   * Applied Shock: Selic +350bps, Unemployment +4.0%, Collateral Haircut -20%, CCF Draw-down +8%.
   * Success Metric: Over 20% of contracts migrate preventatively from Stage 1 to Stage 2 (SICR) prior to actual delinquency.

 [DIMENSION 2] MODEL RISK MANAGEMENT & STATISTICAL BACKTESTING
   * PSI (Population Stability Index): Quantifies population drift between baseline and stressed regimes.
   * AUC-ROC / Gini: Discriminatory capability of the PD model (Industry Benchmark: > 0.75 | Obtained: 0.8842).
   * Brier Score: Calibration accuracy of forecasted vs. observed defaults (Benchmark: < 0.05 | Obtained: 0.0418).

 [DIMENSION 3] SOFTWARE ENGINEERING & HIGH-THROUGHPUT PERFORMANCE (50,000 Contracts)
   * Throughput: Contracts processed per second (Benchmark: > 5,000/s | Obtained: > 17,000/s).
   * Memory Peak: Bounded RAM allocation (Peak: < 10 MB).
   * API Latencies: P50 (12.4ms), P95 (18.2ms), P99 (27.5ms).

 [DIMENSION 4] GOVERNANCE, ACCOUNTING RECONCILIATION & BACEN COMPLIANCE
   * Golden Cases: 100% exact match across all 8 canonical test cases with zero Decimal tolerance.
   * Document 3040 BACEN: Syntactic and semantic XML pre-validation according to BCB 352.
   * Audit Trail: Tamper-evident ledger sealed with SHA-256 cryptographic hashes.
```

### Extreme-Scale Batch Benchmark (100k to 1M Contracts):
For memory-bounded high-scale validation:
```powershell
python scripts/performance_benchmark.py --sizes 10000 100000
```

---

## 5. Overlays and Regulatory Provision Floors

The platform strictly isolates managerial judgment from statistical calculation:
1. **Baseline Economic ECL:** Pure statistical output from PD/LGD/EAD models.
2. **Managerial Overlays:** Fully auditable adjustments registered in the ledger with formal justification, expiration date, and scope (`src/ecl/overlays/management.py`).
3. **Regulatory Floors:** Guaranteed compliance with minimum regulatory loss allowance percentages mandated by BCB Instruction No. 352 (`src/regulatory/cmn4966/provision_floor.py`).
4. **Reported Final ECL:** \(\text{ECL}_{\text{Final}} = \max(\text{ECL}_{\text{Economic}} + \text{Overlay}, \text{Regulatory Floor})\).

---

## 6. Related Documentation & References

* [Consolidated Portfolio Benchmark Scorecard](docs/PORTFOLIO_BENCHMARK.md)
* [System Architecture Document](docs/architecture/SYSTEM_ARCHITECTURE.md)
* [Quantitative Risk Technical Interview Guide](docs/portfolio/TECHNICAL_INTERVIEW_GUIDE.md)
* [API v1 Specifications & Contracts](docs/api/ECL_API_V1.md)
* [Model Limitation Register](docs/validation/LIMITATION_REGISTER.md)
