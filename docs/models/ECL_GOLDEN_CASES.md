# Pacote consolidado de golden cases ECL

## Fonte de verdade

`tests/fixtures/golden/ecl_cases.csv` congela os resultados manuais. O teste
`tests/models/test_ecl_golden_cases.py` reconstrói cada caso usando as APIs canônicas e
exige igualdade exata, sem tolerância monetária.

O pacote publicável em `docs/golden_cases/` acrescenta o contrato JSON com todos
os inputs e fórmulas, uma calculadora `Decimal` independente do motor de produção
e a planilha `ecl_golden_cases.xlsx`. O teste
`tests/validation/test_golden_case_package.py` exige que as três representações
reconciliem no CI.

| Caso | Resultado | Base manual |
|---|---:|---|
| Stage 1 amortizado | R$ 9,05 | R$ 5,00 + R$ 4,05 |
| Stage 2 lifetime | R$ 12,33 | R$ 5,00 + R$ 4,05 + R$ 3,28, com sobrevivência a prepagamento |
| Stage 3 cash shortfall | R$ 25,00 | 100 − 60 − 20 + 5 |
| rotativo com CCF | R$ 7,50 | 10% × 50% × (100 + 100 × 50%) |
| contrato garantido | R$ 30,00 | 100 − 20 do devedor − 50 da garantia |
| POCI | R$ 20,00 | 15% × 10 + 70% × 20 + 15% × 30 |
| modificação sem baixa | R$ 268,15 | soma de 15 perdas mensais sobre o cronograma revisado, descontadas pela EIR original |
| multi-cenário | R$ 21,14 | 15% × 20,21 + 70% × 20,97 + 15% × 22,89 |

## Controles adicionais

O caso Stage 1 recalcula cada perda a partir da PD marginal, LGD, EAD e desconto
exibidos no próprio resultado. Assim, a LGD reportada é exatamente a usada no cálculo.
O caso multi-cenário executa duas vezes com os mesmos inputs e exige igualdade estrutural
completa.

`PD × LGD × EAD` aparece apenas nos casos didáticos de um período. O motor normal usa
soma por período e cenário, sobrevivência, desconto, CCF sobre limite não sacado,
cash-shortfall em Stage 3 e tratamento próprio de POCI. O caso multi-cenário prova que
os ECLs integrais são ponderados depois do cálculo, não por um fator médio.

## Modificação

O cronograma original Price de 12 meses é modificado após o terceiro período para 15
meses, sem derecognition. O teste confirma que a EIR aplicada permanece a original e
calcula Stage 2 sobre os saldos de abertura revisados. O valor R$ 268,15 é a soma
arredondada das perdas mensais descontadas.

## Status

Os golden cases validam a mecânica determinística e regressão quantitativa do motor.
Eles usam dados e coeficientes sintéticos; não aprovam PD, LGD, EAD, cenários ou pisos
para uso institucional.
