# Backtesting independente de LGD

## Escopo e separação

`src/validation/backtesting/lgd.py` recebe previsões congeladas e evidência workout; não
ajusta nem seleciona o candidato. A política
`config/validation/backtesting/lgd-2026.07.1.json` exige 100 workouts fechados, 30 por
segmento, MAE máximo de 15% e RMSE máximo de 20%.

O candidato `ridge_one_stage` foi selecionado anteriormente no mesmo holdout. Portanto,
a evidência de 2022–2023 é um backtest retrospectivo tecnicamente independente, mas não
um OOT intocado após seleção. Os dados são sintéticos e a separação não representa uma
função institucional de validação.

## Workouts fechados

Dez defaults possuem janela completa, previsão congelada e LGD realizada descontada. O
pacote calcula LGD prevista versus realizada, MAE, RMSE e recuperação monetária, no
agregado e por coorte trimestral, resultado de cura/write-off e presença de garantia.

| Métrica | Resultado | Limite |
|---|---:|---:|
| N fechado | 10 | mínimo 100 |
| LGD média prevista | 57,1144% | diagnóstico |
| LGD média realizada | 56,8917% | diagnóstico |
| MAE | 35,8173% | máximo 15% |
| RMSE | 45,2035% | máximo 20% |
| recuperação prevista | 164.759,9973 | diagnóstico |
| recuperação realizada descontada | 236.223,9888 | diagnóstico |

A proximidade das médias não compensa erros individuais e monetários grandes. Todas as
células de coorte falham volume, e os cortes de cura, write-off e garantia permanecem
visíveis no evidence pack.

## Workouts abertos

Sete defaults censurados estão separados em quatro coortes de 2024–2025. O relatório
reconcilia EAD, recuperação descontada até a data de observação, cura, write-off e
garantia. Mesmo quando já existe cura ou write-off parcial, a janela de 24 meses ainda
não está completa; por isso o status é `not_scored_until_workout_closure` e nenhuma LGD
final é imputada. As previsões históricas desses casos não foram preservadas e aparecem
explicitamente como ausentes.

## Decisão e evidência

Decisão objetiva: `rejected`, por volume fechado abaixo do mínimo e MAE/RMSE acima dos
limites.

- gerador: `scripts/generate_lgd_backtest_report.py`;
- relatório legível: `evidence/validation/lgd/2026.07.1/report.md`;
- relatório estruturado: `evidence/validation/lgd/2026.07.1/report.json`;
- escopo: `synthetic_independent_backtest`;
- limite: sem OOT novo, dados reais ou aprovação institucional.
