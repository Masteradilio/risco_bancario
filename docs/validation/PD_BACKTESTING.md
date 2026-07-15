# Backtesting independente de PD

## Escopo executado

O pacote `src/validation/backtesting/pd.py` recebe probabilidades congeladas e targets
maduros; ele não ajusta, calibra ou seleciona o modelo. A política objetiva
`config/validation/backtesting/pd-2026.07.1.json` exige cobertura nos horizontes de 1 e
12 meses e cortes por rating, produto e safra.

A execução versionada usa a carteira sintética determinística de seed 91. O bloco de
calibração de 2022 é somente a referência de drift e o OOT de 2024 é a avaliação
retrospectiva. A referência é otimista porque foi usada para ajustar o calibrador; essa
limitação torna a deterioração OOT mais evidente, mas não constitui benchmark externo.

A PD de 1 mês é derivada da PD de 12 meses pela hipótese diagnóstica de hazard constante,
`1 - (1 - PD12m)^(1/12)`. Ela não é um modelo mensal calibrado separadamente.

## Critérios e resultado

São calculados contagem, eventos, PD média, taxa observada, O/E, erro absoluto, intervalo
exato de Clopper-Pearson e teste binomial exato. A célula agregada exige 30 observações;
segmentos exigem 10. O erro absoluto máximo é 5 p.p. e o aumento máximo contra a
referência é 3 p.p., ambos definidos na política versionada.

| Horizonte | N | Eventos | PD média | Observado | Erro absoluto | Drift do erro | Resultado |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 mês | 233 | 3 | 2,8608% | 1,2876% | 1,5733 p.p. | 0,8885 p.p. | passou |
| 12 meses | 233 | 27 | 29,4118% | 11,5880% | 17,8238 p.p. | 17,8238 p.p. | falhou |

Decisão objetiva: `rejected`. A cobertura agregada de 12 meses falhou e o drift de
calibração excedeu o limite. As 30 células agregadas/segmentadas estão no relatório
versionado; nenhum corte adverso foi ocultado para alterar a decisão.

## Maturação e evidência

As 182 observações de 2025 permanecem `pending_target_maturation`. Elas entram apenas na
contagem de pendência e não recebem performance, zero ou target imputado. Quando os
desfechos forem observáveis, devem formar uma nova versão de evidência sem recalibrar o
modelo com o mesmo bloco.

- gerador: `scripts/generate_pd_backtest_report.py`;
- relatório legível: `evidence/validation/pd/2026.07.1/report.md`;
- relatório estruturado: `evidence/validation/pd/2026.07.1/report.json`;
- escopo: `synthetic_independent_backtest`;
- limite: segregação técnica simulada, sem aprovação institucional.
