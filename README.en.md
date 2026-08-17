# Banking Credit Risk — Expected Credit Loss (ECL) Engine

[🇧🇷 Português](README.md) | [🇺🇸 English](README.en.md)

Production-grade quantitative engineering platform designed to model Expected Credit Loss (ECL) under **IFRS 9** and the Brazilian Central Bank regulation (**CMN Resolution No. 4,966 / BCB Normative Instruction No. 352**), using 100% synthetic longitudinal data.

The platform provides a strictly typed domain, longitudinal cohort simulation, machine learning and econometric models for PD, LGD, EAD, multi-scenario forward-looking macroeconomic staging (SICR), lifetime cash-flow discounting, versioned persistence, FastAPI service with RBAC and immutable audit ledgers, a React evidence workspace, and an automated regulatory reporting package.

> **Disclaimer & Usage Limits:** This project is a quantitative software engineering demonstration built with synthetic data. It has not been institutionally certified by the Central Bank of Brazil (BACEN). Quantitative models remain flagged as `not_approved` to reflect institutional governance boundaries. Regulatory outputs are pre-validated candidates against derived XSD schemas, not official submissions.

---

## ⚡ One-Command Quickstart

Requires Windows PowerShell and Python 3.13. The script creates a dedicated `venv`, installs pinned dependencies, and verifies canonical imports:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Next, execute the complete end-to-end synthetic pipeline:

```powershell
.\venv\Scripts\python.exe scripts\e2e_pipeline.py
```

Expected result: `COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS` — the pipeline executes with zero runtime errors while preserving governance blockers (PD, SICR, LGD, EAD). Generated evidence artifacts are stored in `evidence/e2e/`.

---

## 🏆 Master Portfolio Benchmark & Robustness Scorecard

Run the master 4-dimensional benchmark suite in a single command:

```powershell
python scripts/run_portfolio_benchmark.py
```

### Benchmark Summary (Synthetic Retail Portfolio):

| Evaluated Dimension | Key Metric | Result Obtained | Market Benchmark | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Batch Processing Engine** | Multi-threaded throughput | **17,480 contracts/sec** | $> 5,000$ contracts/sec | **Superior** ⚡ |
| **API Response Latency** | Single-calculation ($P_{95}$) | **18.2 ms** | $< 50$ ms | **Low Latency** 🚀 |
| **Engine Memory Footprint** | Peak RAM consumption | **6.25 MB** | Zero memory leak | **Optimized** 🧠 |
| **Model Discrimination (PD)** | AUC-ROC / Gini Coefficient | **0.8842 / 0.7684** | $> 0.75$ | **Strong Discrimination** 🎯 |
| **Probability Calibration** | Brier Score | **0.0418** | $< 0.05$ | **Excellent** 🔬 |
| **SICR Staging Sensitivity** | Preventative Stage 1 $\to$ 2 Migration | **224 contracts migrated** | Early Detection | **IFRS 9 Compliant** 📈 |
| **Financial Arithmetic** | Golden Cases Reconciliation | **8 cases (Zero Tolerance)** | 100% `Decimal` accuracy | **Exact** 💎 |
| **Regulatory Validation** | BACEN Doc3040 XML Layout | **PREVALIDATED_CANONICAL** | BCB 352 Validated | **Auditable** 🏛️ |

*Detailed benchmark methodology and stress-testing reports: [docs/PORTFOLIO_BENCHMARK.md](docs/PORTFOLIO_BENCHMARK.md).*

---

## 🏛️ System Architecture

```
                                  ┌────────────────────────────────────────┐
                                  │      React Evidence Workspace (Vite)   │
                                  └───────────────────┬────────────────────┘
                                                      │ HTTP / REST
                                  ┌───────────────────▼────────────────────┐
                                  │        FastAPI Canonical API v1        │
                                  │    (RBAC, JWT, Rate-Limiting, Audit)   │
                                  └───────────────────┬────────────────────┘
                                                      │
         ┌────────────────────────────────────────────┼────────────────────────────────────────────┐
         │                                            │                                            │
┌────────▼────────┐                          ┌────────▼────────┐                          ┌────────▼────────┐
│  src/models     │                          │  src/ecl        │                          │  src/regulatory │
│  - PD (PIT/TTC) │                          │  - 12m & Life   │                          │  - CMN 4966     │
│  - SICR Engine  │ ───────────────────────► │  - Forward-Look │ ───────────────────────► │  - Doc3040 XML  │
│  - LGD Workout  │                          │  - Overlays     │                          │  - BCB 352      │
│  - EAD & CCF    │                          │  - Provision Fl │                          │  - Traceability │
└─────────────────┘                          └─────────────────┘                          └─────────────────┘
         │                                            │                                            │
         └────────────────────────────────────────────┼────────────────────────────────────────────┘
                                                      │
                                  ┌───────────────────▼────────────────────┐
                                  │           src/infrastructure           │
                                  │    PostgreSQL / SQLite + Migrations    │
                                  │   SHA-256 Tamper-Evident Audit Ledger  │
                                  └────────────────────────────────────────┘
```

### Canonical Structure:
- `src/domain`: Immutable value objects, monetary quantities (`Decimal`), risk percentages, dates.
- `src/models`: PD calibration (PIT/TTC), qualitative & quantitative SICR triggers, LGD collateral/workout, EAD with Credit Conversion Factors (CCF).
- `src/ecl`: Period-by-period discounting, multi-scenario probability weighting, managerial overlays, and regulatory provision floors.
- `src/infrastructure`: Explicit persistence (SQLite/PostgreSQL with no silent fallback), structured JSON logging, Prometheus metrics.
- `src/interfaces/api`: FastAPI v1 endpoints with OAuth2 JWT, RBAC authorization, and transactional audit trails.
- `src/regulatory`: Versioned layout engine for BACEN Document 3040, schema validation, and regulatory traceability matrix.
- `frontend`: Modern React workspace consuming persisted calculation and validation evidence.

---

## 🐳 Containerized Local Demo

To launch both the API and the React workspace with Docker:

```powershell
Copy-Item .env.local.example .env.local
$env:RISK_ENV_FILE = ".env.local"
docker compose --profile local up --build
```

- **Frontend Workspace:** `http://127.0.0.1:8080`
- **Interactive OpenAPI Documentation:** `http://127.0.0.1:8000/docs`

*(No hardcoded credentials are baked in: create an initial admin user following the [API Contract](docs/api/ECL_API_V1.md)).*

---

## 🧪 Verification & Quality Gate

The quality suite enforces Black, Ruff, MyPy, 754 canonical unit/integration tests, legacy regression tests, code coverage, and frontend TypeScript build:

```powershell
.\venv\Scripts\python.exe scripts\quality.py
```

- **Canonical Test Suite:** 754 tests passed (99.04% code coverage).
- **Legacy Suite:** 118 regression tests passed.
- **Golden Cases:** 100% verified against published baseline spreadsheets with zero tolerance (`Decimal(ROUND_HALF_EVEN)`).

---

## 📚 Technical Documentation & Guides

- [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Master Portfolio Benchmark & Robustness Scorecard](docs/PORTFOLIO_BENCHMARK.md)
- [Expected Credit Loss & Benchmark Tutorial](docs/tutorials/ECL_TUTORIAL.en.md)
- [API Examples & Contracts](docs/api/EXAMPLES.md)
- [Technical Interview Guide](docs/portfolio/TECHNICAL_INTERVIEW_GUIDE.md)
- [End-to-End Journey & Blocker Semantics](docs/operations/E2E_JOURNEY.md)
- [Model Limitations Register](docs/validation/LIMITATION_REGISTER.md)
- [Regulatory Package & Traceability](docs/regulatory/REGULATORY_PACKAGE.md)

---

## 📄 License & Attribution

This repository is published under the [MIT License](LICENSE) for research, portfolio demonstration, and educational purposes.
