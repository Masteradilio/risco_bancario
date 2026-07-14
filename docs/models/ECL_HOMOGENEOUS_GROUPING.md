# Agrupamento homogêneo para ECL coletivo

## Política

`config/ecl_grouping/2026.07.1.json` define critérios explícitos e versionados. O
agrupamento coletivo não é uma faixa arbitrária de score: exige pelo menos duas
dimensões não-score entre produto, colateral, safra e comportamento.

Dimensões permitidas:

- produto;
- tipo de colateral;
- safra de originação em intervalos de dois anos;
- bucket comportamental de risco;
- faixa de score, somente como dimensão adicional.

## Roteamento individual

Exposições com EAD igual ou superior a R$ 500.000 são materiais e devem ser mensuradas
individualmente. Elas não podem permanecer em grupos coletivos mesmo que os demais
indicadores pareçam homogêneos.

## Validação estatística

Um grupo exige ao menos 20 contratos únicos. São calculados coeficientes de variação de
PD 12m, LGD e EAD, com máximos de 0,50, 0,40 e 0,75. A maior exposição não pode exceder
25% da EAD do grupo.

No caso demonstrativo de 20 hipotecas residenciais da safra 2024–2025 e mesmo bucket
comportamental:

| Variável | Média | CV | Limite |
|---|---:|---:|---:|
| PD 12m | 0,020095 | 0,004004 | 0,50 |
| LGD | 0,300500 | 0,001664 | 0,40 |
| EAD | R$ 10.095,00 | 0,005712 | 0,75 |

A concentração máxima é 0,050471. O grupo passa todos os gates. Testes adicionais
rejeitam alta dispersão, tamanho insuficiente, dimensões divergentes, duplicatas,
concentração e exposição material.

## Integração

O resultado retorna ID determinístico do grupo, métricas, blockers, versão e hash da
política. Somente grupos válidos podem usar o modo `collective` de Stage 2; exposições
materiais seguem o modo `individual`.

Os limites são sintéticos e `not_approved`. Uma implantação real precisa recalibrá-los
por portfólio e validar estabilidade, representatividade e granularidade ao longo do
tempo.
