# POCI por cenário e apresentação

## Abordagem

Ativos POCI permanecem fora da transição comum de Stage. A credit-adjusted EIR é
calculada no reconhecimento inicial a partir do preço e dos fluxos esperados que já
incorporam perdas de crédito. Depois, reconhece-se a mudança acumulada na lifetime ECL,
favorável ou desfavorável.

`measure_poci_scenarios` recebe fluxos atuais específicos por cenário, desconta todos
pela mesma credit-adjusted EIR inicial, calcula a lifetime ECL de cada cenário e só então
pondera ECL e mudança.

## Golden case

- preço de compra: R$ 80;
- fluxo contratual em um ano: R$ 110;
- fluxo inicial esperado: R$ 88;
- credit-adjusted EIR: 10%;
- valor presente contratual: R$ 100;
- valor presente inicial esperado: R$ 80;
- lifetime ECL inicial: R$ 20.

| Cenário | Fluxo atual | Lifetime ECL | Mudança | Apresentação |
|---|---:|---:|---:|---|
| otimista | R$ 99 | R$ 10 | -R$ 10 | ganho de impairment |
| base | R$ 88 | R$ 20 | R$ 0 | sem mudança |
| pessimista | R$ 77 | R$ 30 | R$ 10 | perda de impairment |
| stress | R$ 66 | R$ 40 | R$ 20 | perda de impairment |

ECL ponderado: R$ 20. Mudança ponderada: R$ 0. Stress separado: R$ 40. Um conjunto
integralmente adverso de R$ 77 produz mudança ponderada de R$ 10 e apresentação como
perda; um conjunto de R$ 99 produz -R$ 10 e apresentação como ganho.

## Controles e disclosure

- os quatro cenários devem estar presentes uma única vez;
- datas esperadas devem coincidir com as contratuais;
- fluxo esperado não pode exceder o contratual;
- a credit-adjusted EIR é única e preservada em todos os cenários;
- ECL atual, mudança acumulada, classificação, peso e contribuição ficam por cenário;
- stress, versão e hash do cenário ficam separados no resultado;
- juros POCI são apresentados pela base `credit_adjusted_eir_on_amortized_cost`.

O status permanece `synthetic_unapproved`. A mecânica não implica validação da
identificação POCI ou dos fluxos esperados em uma instituição real.
