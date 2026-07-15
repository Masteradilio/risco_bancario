# Backtesting independente de ECL

## Escopo

`src/validation/backtesting/ecl.py` recebe a série de ECL inicial prevista e perdas realizadas por contrato, além das trajetórias de atribuição (waterfall), sem interferir no cálculo. A política `config/validation/backtesting/ecl-2026.07.1.json` exige o mapeamento ordenado dos componentes de variação (volume, estágio, PD, LGD, EAD, cenário e overlay).

## ECL inicial versus perdas realizadas

A fábrica de dados sintéticos atual não preserva o snapshot do ECL calculado e a série histórica de perdas/defaults observadas por contrato de maneira contínua e madura.

Por conta dessa limitação de infraestrutura e dados, as observações maduras são zero, impossibilitando a medição quantitativa de viés agregado ou por vintage/ciclo econômico.

## Análise de atribuição (Waterfall)

Não há snapshots intermediários de transição para reconciliar a waterfall de atribuição por contrato no portfólio. Os efeitos agregados de volume, estágio, PD, LGD, EAD, cenário e overlay permanecem não computados devido a essa ausência de série histórica.

## Decisão e evidência

Decisão objetiva: `rejected`, por ausência de observações maduras e dados históricos de snapshots para atribuição completa.

- gerador: `scripts/generate_ecl_backtest_report.py`;
- relatórios: `evidence/validation/ecl/2026.07.1/report.json` e `report.md`;
- escopo: `synthetic_independent_backtest`;
- limite: histórico sintético incompleto para validação de ECL, sem aprovação do modelo.
