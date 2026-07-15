# Model card — PD 12 meses e estrutura temporal

## Identificação e status

| Campo | Valor |
|---|---|
| Modelo | `logistic_12m_isotonic_frozen` |
| Implementação | `src/models/pd/` |
| Dataset | fábrica sintética, modelagem `0.2.0` |
| Data da avaliação | 14 de julho de 2026 |
| Status | `not_approved` |
| Escopo da evidência | `synthetic_demonstrative_only` |
| Champion aprovado | nenhum |

## Objetivo, população e target

O objetivo técnico é estimar default em `(t, t+12m]` para contratos sintéticos
não-POCI ainda não defaultados e produzir curvas condicionais até a maturidade.
A definição de default/cura é a política `2026.07.1`. POCI, ativos já defaultados
e decisões de concessão ficam fora do uso pretendido.

## Dados e separação

Treino usa 2016–2018, validação 2020, calibração 2022 e OOT 2024, com embargos
anuais entre blocos. O OOT de 2024 também foi usado como backtest retrospectivo
independente; o backtesting operacional de 2025 tem 182 linhas e ainda não possui target
12m maduro. Safra de originação é metadado de análise, não feature.

Features: saldo, limite, utilização, atraso, score comportamental, rating,
produto e cinco variáveis macroeconômicas sintéticas observáveis na data-base.
Targets, identificadores, latentes e eventos futuros são excluídos.

## Método e calibração

O baseline é regressão logística com padronização numérica, one-hot encoding e
class weighting. Platt e isotonic foram comparados em holdout temporal interno
da validação; isotonic venceu por Brier e foi ajustado somente em calibração.
O OOT não alterou feature, hiperparâmetro, threshold ou método.

As curvas mensais distribuem intensidade acumulada por pesos temporais positivos,
reconciliam hazard/sobrevivência/PD marginal/acumulada e terminam na maturidade
contratual real. Os multiplicadores de forma ainda não são calibrados.

## Performance e decisão

No OOT sintético (233 linhas, 27 eventos), ROC AUC 0,5000, Gini 0,0000, KS
0,0000, PR-AUC 0,1159, Brier 0,1342, Log Loss 0,4498 e ECE 0,1782. A PD
calibrada colapsou em 0,2941. O PSI do score não calibrado entre calibração e
backtesting é 6,7903 (`high_shift`). Esses resultados bloqueiam aprovação.

O backtest independente da Fase 13 confirma a rejeição: em 12m, a PD média de
29,4118% compara com 11,5880% observado, erro absoluto de 17,8238 p.p. e drift de
17,8238 p.p. contra a referência. O horizonte de 1m passou somente como diagnóstico
derivado por hazard constante.

## Limitações, viés e riscos

- dados, eventos e macroeconomia são inteiramente sintéticos;
- amostra e eventos são pequenos, sobretudo para hazard mensal e segmentos;
- calibrador colapsou sob mudança temporal;
- ratings R1–R5 e multiplicadores temporais não estão aprovados;
- não há atributos protegidos, logo fairness demográfica não foi mensurada;
- o backtesting operacional de 2025 aguarda maturação e não possui métrica de performance;
- há apenas validação independente técnica simulada; não há função institucional, uso
  real ou homologação.

## Monitoramento, retreinamento e governança

Monitorar PSI, distribuição de score, calibração/OE por rating, produto e safra,
discriminação e qualidade de dados. Não recalibrar ou retreinar a partir do OOT.
Após maturação de 2025, deve ser executada uma nova versão do backtesting congelado; os
limites formais já estão versionados na política de validação. Qualquer promoção exige dados reais governados,
validação independente, aprovação humana, versão de artefato e trilha de decisão.

## Reprodutibilidade e evidências

- código: `src/models/pd/baselines.py`, `calibration.py`, `term_structure.py` e
  `validation.py`;
- dados: `data/synthetic/acceptance-v0.1.0` com manifesto e hashes;
- testes: `tests/models/test_pd_*.py`;
- relatórios: `PD_BASELINES.md`, `PD_TEMPORAL_CALIBRATION.md`,
  `PD_TERM_STRUCTURE.md`, `PD_VALIDATION_REPORT.md` e
  `../validation/PD_BACKTESTING.md`.
