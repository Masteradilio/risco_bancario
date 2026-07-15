# Relatório de validação de LGD

## Escopo e independência

Este relatório avalia o `ridge_one_stage` contra LGD workout descontada no holdout
temporal de 2022–2023. O holdout já foi usado para selecionar o candidato de menor
RMSE na Tarefa 7.3; portanto, esta avaliação não é validação independente nem OOT
intocado. Defaults posteriores ainda têm janelas censuradas e não são usados como
se fossem maduros.

Todos os dados são sintéticos. A política de validação
`config/lgd_validation/2026.07.1.json` foi definida antes da execução e exige ao
menos 100 observações de validação, 30 por coorte/produto, 50 downturn, MAE de no
máximo 0,15, RMSE de no máximo 0,20 e erro por faixa de no máximo 0,10.

## Previsto versus realizado

| Default | Data | Produto | Realizada | Prevista | Erro |
|---|---|---|---:|---:|---:|
| DEF-0000017 | 2022-02-01 | acquired_distressed | 0,095717 | 0,807502 | 0,711785 |
| DEF-0000019 | 2022-05-01 | vehicle_finance | 0,201385 | 0,305097 | 0,103712 |
| DEF-0000015 | 2022-06-01 | vehicle_finance | 1,000000 | 0,306529 | -0,693471 |
| DEF-0000001 | 2022-11-01 | vehicle_finance | 0,195744 | 0,305189 | 0,109445 |
| DEF-0000018 | 2022-11-01 | acquired_distressed | 1,000000 | 0,809015 | -0,190985 |
| DEF-0000007 | 2022-12-01 | acquired_distressed | 0,909877 | 0,810628 | -0,099249 |
| DEF-0000031 | 2023-02-01 | acquired_distressed | 0,096105 | 0,821099 | 0,724994 |
| DEF-0000002 | 2023-08-01 | vehicle_finance | 1,000000 | 0,355829 | -0,644171 |
| DEF-0000032 | 2023-11-01 | acquired_distressed | 1,000000 | 0,848148 | -0,151852 |
| DEF-0000024 | 2023-12-01 | vehicle_finance | 0,190338 | 0,342406 | 0,152068 |

| Métrica | Resultado | Limite |
|---|---:|---:|
| Observações | 10 | mínimo 100 |
| LGD média realizada | 0,568917 | diagnóstico |
| LGD média prevista | 0,571144 | diagnóstico |
| Erro de nível | 0,002228 | diagnóstico |
| MAE | 0,358173 | máximo 0,150000 |
| RMSE | 0,452035 | máximo 0,200000 |

O erro de nível agregado pequeno esconde erros individuais grandes e de sinais
opostos. Ele não compensa a reprovação de MAE e RMSE.

## Calibração por faixa

| Faixa | N | Predição mínima | Predição máxima | Média prevista | Média realizada | Erro |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 0,305097 | 0,342406 | 0,314805 | 0,396867 | 0,082062 |
| 2 | 3 | 0,355829 | 0,809015 | 0,657449 | 0,698572 | 0,041124 |
| 3 | 3 | 0,810628 | 0,848148 | 0,826625 | 0,668661 | 0,157964 |

A terceira faixa excede o limite de erro de 0,10. Com apenas três ou quatro casos
por faixa, as estimativas são descritivas e instáveis.

## Backtesting por coorte

| Coorte | N | Média prevista | Média realizada | MAE |
|---|---:|---:|---:|---:|
| 2022-Q1 | 1 | 0,807502 | 0,095717 | 0,711785 |
| 2022-Q2 | 2 | 0,305813 | 0,600693 | 0,398591 |
| 2022-Q4 | 3 | 0,641611 | 0,701874 | 0,133226 |
| 2023-Q1 | 1 | 0,821099 | 0,096105 | 0,724994 |
| 2023-Q3 | 1 | 0,355829 | 1,000000 | 0,644171 |
| 2023-Q4 | 2 | 0,595277 | 0,595169 | 0,151960 |

Nenhuma coorte alcança as 30 observações mínimas.

## Estabilidade por produto

| Produto | Treino N | Validação N | LGD treino | LGD validação | Mudança |
|---|---:|---:|---:|---:|---:|
| acquired_distressed | 3 | 5 | 0,921382 | 0,620340 | -0,301042 |
| credit_card | 2 | 0 | 0,621622 | N/A | N/A |
| mortgage | 6 | 0 | 0,416475 | N/A | N/A |
| vehicle_finance | 4 | 5 | 0,218682 | 0,517494 | 0,298811 |

Dois produtos não aparecem no holdout e os demais têm apenas cinco casos. A direção
das mudanças é material, mas não é estimável com precisão.

## Downturn separado do ECL PIT

A sensibilidade downturn usa, apenas como diagnóstico, o quartil superior de
`desemprego - crescimento do PIB` nos 25 workouts fechados. O limiar é 7,9446 e há
7 observações; a LGD realizada média é 0,448198, abaixo da predição PIT média de
0,571144, produzindo addon igual a zero.

Isso não prova ausência de efeito downturn: indica que a amostra sintética não o
identifica. A análise recebe status `descriptive_sensitivity_not_approved` e seu
resultado não é aplicado à LGD PIT nem ao ECL. LGD downturn regulatória e LGD
contábil permanecem conceitos separados.

## Decisão

Status: `not_approved`. Blockers:

- ausência de OOT independente após seleção;
- amostra total, por coorte, por produto e downturn abaixo dos mínimos;
- MAE e RMSE acima dos limites;
- erro da faixa superior acima do limite;
- dados e premissas exclusivamente sintéticos, sem validação independente.

Não existe champion LGD aprovado. O Ridge permanece somente candidato provisório
para regressão técnica até haver dados governados, workouts maduros, novo OOT
congelado e aprovação humana independente.

O backtest separado da Fase 13 confirma essa decisão e adiciona recuperação monetária,
coortes abertas, cura, write-off e garantia. Consulte
`docs/validation/LGD_BACKTESTING.md`; esse novo cálculo é tecnicamente independente,
mas não transforma o holdout reutilizado em OOT intocado nem aprovação institucional.
