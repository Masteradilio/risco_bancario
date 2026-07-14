# Model card — LGD workout

## Identificação e status

| Campo | Valor |
|---|---|
| Modelo | `ridge_one_stage` |
| Implementação | `src/models/lgd/` |
| Dataset | workout/modeling `0.1.0` |
| Data da avaliação | 14 de julho de 2026 |
| Status | `not_approved` |
| Escopo da evidência | `synthetic_demonstrative_only` |
| Champion aprovado | nenhum |

## Objetivo, população e target

O objetivo técnico é estimar LGD workout descontada para defaults sintéticos. O
target é `1 - recuperações líquidas descontadas / EAD no default`, com valor de cura
se aplicável e limites de 0%–100% para modelagem; o valor bruto é preservado.

A população contém contratos com default e janela de workout completa. Observações
censuradas são excluídas de treino/validação, mas permanecem rastreáveis no dataset.

## Dados e features

Treino contém 15 defaults de 2017–2021. O holdout de 2022–2023 contém 10. As features
são EAD, produto, garantia, valor executável, LTV, atraso, prazo remanescente e cinco
variáveis macroeconômicas conhecidas no default. Recuperações, custos, cura, write-off
e eventos futuros não são features.

Dados, macroeconomia, defaults e recuperações são inteiramente sintéticos. Não há
representatividade institucional demonstrada.

## Método e alternativas

O candidato usa Ridge com padronização numérica e one-hot encoding, alpha 10 e
predições limitadas a 0%–100%. Foram comparados no mesmo holdout: média por
produto/garantia, Ridge one-stage, two-stage cura/severidade e one-inflated Ridge.

O Ridge foi selecionado pelo menor RMSE (0,452035), marginalmente melhor que two-stage
(0,453292) e one-inflated (0,455493). O baseline teve RMSE 0,509690 e o menor MAE
entre os quatro. O holdout de seleção não é validação independente.

## Garantias e sensibilidades

A projeção de garantia é um componente separado e versionado. Ela aplica atualização
de valor, enforceability, haircut, custos, tempo e desconto. Cash flow observado de
execução é excluído antes de combinar a projeção, evitando dupla contagem.

Sensibilidades upside/base/downside alteram valor, haircut, custo e prazo. Elas não
recalibram o modelo e não constituem LGD downturn aprovada.

## Performance e decisão

No holdout, a LGD média realizada é 0,568917 e a prevista 0,571144, mas o MAE é
0,358173 e o RMSE 0,452035. A faixa superior apresenta erro de calibração 0,157964.
Coortes têm de 1 a 3 casos; somente acquired distressed e vehicle finance aparecem
na validação, com 5 casos cada.

O status é `not_approved` por erro, amostra, ausência de cobertura de produtos e
ausência de OOT independente após seleção.

## Uso pretendido e usos proibidos

Uso permitido: regressão automatizada, demonstração metodológica e desenho de futura
validação. Usos proibidos: provisionamento real, decisão de crédito, precificação,
capital regulatório, definição de downturn LGD, reporte externo ou alegação de
conformidade/aprovação.

## Limitações e riscos

- somente 25 workouts maduros e 10 no holdout;
- holdout reutilizado para seleção e avaliação;
- produtos ausentes na validação e segmentos mínimos;
- valores em 100% e curas difíceis de separar com a amostra atual;
- parâmetros de garantia e macro são demonstrativos;
- nenhum dado real, validação independente, fairness ou governança institucional;
- sensibilidade downturn sem evidência de relação monotônica na amostra.

## Monitoramento e promoção futura

Monitorar maturação/censura, MAE, RMSE, erro por faixa, coorte, produto, cura/perda,
valor/tempo de garantia e estabilidade macro. A promoção exige nova política
congelada, volumes mínimos, OOT intocado após seleção, validação independente,
comparação de challengers, aprovação humana e artefato de modelo versionado.

## Reprodutibilidade e evidências

- código: `workout.py`, `realized.py`, `modeling.py`, `collateral.py` e
  `validation.py`;
- políticas: `config/lgd_policy`, `config/lgd_collateral_policy` e
  `config/lgd_validation`;
- testes: `tests/models/test_lgd_*.py`;
- relatórios: `LGD_WORKOUT_DATASET.md`, `LGD_REALIZED.md`, `LGD_MODELING.md`,
  `LGD_COLLATERAL.md` e `LGD_VALIDATION_REPORT.md`.
