# Motor de ECL por cenário

## Escopo

`src/ecl/calculation/scenario_engine.py` calcula curvas e perdas por período para cada
trajetória macroeconômica. Este componente é anterior à orquestração por Stage: recebe
uma curva de risco baseline explícita e entrega o integral de cenário. Stage 1, Stage 2,
Stage 3, POCI e agrupamentos serão integrados na Fase 10.

## Entrada por período

Cada mês recebe hazard condicional, LGD, EAD sacada, limite não sacado, CCF e fator de
desconto. As datas devem coincidir com a trajetória macro e não podem exceder seu
horizonte.

Para cada cenário e período, o motor:

1. aplica o fator macro-PD ao hazard condicional;
2. deriva PD marginal a partir da sobrevivência remanescente;
3. aplica o fator macro-LGD e limita a LGD a 100%;
4. aplica macro-EAD somente ao saldo sacado;
5. aplica macro-CCF ao CCF do valor não sacado;
6. calcula `PD marginal × LGD × EAD × desconto`;
7. soma os períodos daquele cenário.

Somente depois de integrar cada cenário o motor multiplica pelos pesos. O stress tem
peso zero e é reportado separadamente.

## Golden case neutro

Dois meses, hazard 10%, LGD 50%, R$ 100 sacados, R$ 100 não sacados, CCF 50% e desconto
1. Com fatores macro unitários:

| Mês | Sobrevivência inicial | PD marginal | EAD | Perda |
|---|---:|---:|---:|---:|
| 1 | 1,00 | 0,10 | R$ 150,00 | R$ 7,50 |
| 2 | 0,90 | 0,09 | R$ 150,00 | R$ 6,75 |
| Total |  |  |  | R$ 14,25 |

Todos os cenários neutros produzem R$ 14,25 e a ponderação também reconcilia em
R$ 14,25.

## Caso demonstrativo com trajetórias

Para três meses da fonte sintética, seed 91 e a mesma baseline:

| Cenário | ECL integral | Peso | Contribuição sem arredondamento final |
|---|---:|---:|---:|
| otimista | R$ 20,21 | 0,15 | R$ 3,03150000 |
| base | R$ 20,97 | 0,70 | R$ 14,67900000 |
| pessimista | R$ 22,89 | 0,15 | R$ 3,43350000 |
| stress | R$ 27,37 | 0,00 | R$ 0,00000000 |

ECL ponderado: R$ 21,14. Stress separado: R$ 27,37. A precisão das contribuições é
preservada até a soma, e o arredondamento monetário final usa `ROUND_HALF_EVEN`.

## Guardrails

- não há média prévia de fatores PD/LGD/EAD;
- PD marginal não pode ultrapassar a sobrevivência disponível;
- LGD e CCF ajustados ficam entre 0% e 100%;
- o CCF afeta somente o montante não sacado;
- versões e hashes do conjunto de cenários e da política macro acompanham o resultado;
- pesos inválidos são rejeitados no domínio de cenários.

Os números são sintéticos, demonstrativos e não aprovados. O motor comprova a
mecânica de cenário, não adequação para provisionamento institucional.
