# Modelagem LGD workout

`src/models/lgd/modeling.py` constrói uma amostra point-in-time a partir dos workouts
fechados e compara quatro abordagens demonstrativas. Observações censuradas não entram
no treino nem na validação.

## Amostra e separação temporal

A carteira de aceite contém 25 workouts completos: 15 defaults de 2017–2021 para
treino e 10 defaults de 2022–2023 para validação temporal. Outros 7 workouts são
excluídos por censura. A seleção não consulta os casos censurados nem usa fluxos de
recuperação como features.

Cada linha inclui somente evidência conhecida no default:

- produto e tipo de garantia;
- EAD, valor de garantia, parcela executável e LTV, limitado a 10 para estabilidade;
- atraso do último snapshot anterior ao default;
- prazo remanescente contratual;
- PIB, inflação, taxa de política, desemprego e endividamento observados na data.

Os targets são a LGD realizada limitada, o indicador de cura e o indicador de perda
integral. A LGD bruta permanece no artefato anterior para auditoria, mas não é feature.

## Candidatos

1. `segmented_mean`: média de treino por produto e garantia, com média global como
   fallback.
2. `ridge_one_stage`: regressão Ridge única com variáveis numéricas padronizadas e
   categorias one-hot; somente a predição é limitada a 0%–100%.
3. `cure_probability_and_severity`: regressão logística para cura e duas regressões
   condicionais de severidade, combinadas pela probabilidade prevista de cura.
4. `one_inflated_ridge`: probabilidade logística de LGD igual a 100% mais regressão
   da severidade fracionária.

Há seis perdas exatamente iguais a 100% e nenhuma LGD zero. Por isso o candidato
one-inflated é pertinente; zero inflation não é observado. Uma regressão beta pura
não acomoda o limite em 100% sem transformação e não é defensável com a amostra
reduzida, portanto não foi promovida como candidato separado.

## Comparação de validação temporal

| Modelo | LGD média prevista | Erro de nível | MAE | RMSE |
|---|---:|---:|---:|---:|
| Segmented mean | 0,570032 | 0,001115 | 0,345090 | 0,509690 |
| Ridge one-stage | 0,571144 | 0,002228 | 0,358173 | 0,452035 |
| Two-stage cure/severity | 0,550867 | 0,018050 | 0,357667 | 0,453292 |
| One-inflated Ridge | 0,553988 | 0,014929 | 0,364276 | 0,455493 |

A LGD média realizada no holdout é 0,568917. O `ridge_one_stage` segue para a Tarefa
7.5 exclusivamente por apresentar o menor RMSE pré-definido. A diferença entre os
três modelos de regressão é pequena, o MAE do baseline segmentado é menor e os
segmentos de treino têm somente 2 a 6 observações. Nenhum candidato está aprovado.

Sete testes cobrem censura, corte temporal, features requeridas, reconciliação de
targets, comparação uniforme, escolha one-inflated e falhas de contrato. Toda a
evidência é sintética e `demonstrative_not_approved`.
