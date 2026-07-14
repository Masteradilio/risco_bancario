# Cálculo de ECL Stage 1

## Definição implementada

Stage 1 considera eventos de default possíveis nos próximos 12 meses, ou até o fim do
prazo remanescente quando inferior. Para cada mês, a LGD de entrada representa toda a
perda lifetime associada ao default naquele período; ela não é uma perda limitada aos
12 meses.

`src/ecl/calculation/stage1.py` constrói a curva baseline por contrato e delega ao motor
integral por cenário. Cada período contém hazard condicional, LGD lifetime, saldo
sacado, valor não sacado e CCF.

## Desconto

`src/ecl/discounting/effective_interest.py` calcula:

```text
fator_m = 1 / (1 + EIR_original)^(m/12)
```

A taxa é a EIR original do contrato. Para 12% a.a., o fator no mês 12 é 0,89285714 e
R$ 112,00 têm valor presente de R$ 100,00. A taxa zero produz fator unitário.

## Caso demonstrativo

Contrato com 12 hazards mensais de 1%, LGD lifetime de 40%, saldo inicial R$ 1.000
reduzido em R$ 50 por mês, R$ 200 não sacados, CCF 50% e EIR original 12%:

| Cenário | ECL | Peso | Contribuição |
|---|---:|---:|---:|
| otimista | R$ 33,60 | 0,15 | R$ 5,04000000 |
| base | R$ 36,95 | 0,70 | R$ 25,86500000 |
| pessimista | R$ 46,45 | 0,15 | R$ 6,96750000 |
| stress | R$ 76,60 | 0,00 | R$ 0,00000000 |

ECL Stage 1 ponderado: R$ 37,87. Stress separado: R$ 76,60. Os fatores de desconto
vão de 0,99060040 no mês 1 a 0,89285714 no mês 12.

## Controles

- aceita entre 1 e 12 períodos futuros;
- contratos com prazo menor usam somente os meses disponíveis;
- datas devem seguir a data-base e alinhar com o cenário;
- a sobrevivência limita a PD marginal em cada cenário;
- LGD lifetime, EAD e CCF permanecem visíveis por período;
- versões/hashes de cenários e relações macro acompanham o resultado.

Os parâmetros e cenários continuam sintéticos e não aprovados. Esta tarefa comprova a
mecânica de Stage 1; a integração com ledger, agrupamentos e execução completa ocorre
nas demais tarefas da Fase 10.
