# EAD de compromissos e garantias financeiras

`src/models/ead/off_balance.py` projeta utilização de loan commitments e chamadas de
financial guarantees. A política `config/off_balance_ead_policy/2026.07.1.json` tem
status `demonstrative_parameterized_not_estimated` e hash propagado aos resultados.

## Fronteira entre utilização e PD

A probabilidade deste módulo é condicional de utilização/chamada e não é a
probabilidade de default da contraparte. A integração ECL deve preservar essa
separação para não multiplicar ou duplicar eventos de crédito. Não há default ou
utilização observada desses produtos no gerador atual: saldos começam e permanecem
zero, e o detector de default exclui saldo zero.

Portanto, os parâmetros são hipóteses transparentes, não coeficientes estimados.

## Loan commitments

A probabilidade mensal base de utilização é 4%, ajustada por multiplicador de risco e
pela utilização corrente. A utilização condicional é 75% do limite ainda disponível.

`EAD = saldo sacado + limite disponível × P(utilização no horizonte) × 75%`

## Financial guarantees

A probabilidade mensal base de chamada é 2,5%, ajustada pelo mesmo multiplicador. A
parcela condicional chamada é 100%.

`EAD = valor disponível × P(chamada no horizonte)`

Em ambos os casos, a probabilidade acumulada é
`1 - (1 - probabilidade mensal)^meses`. O multiplicador permitido vai de 0 a 3.

## Limites e sensibilidades

O cálculo usa o limite corrente executável, nunca restaura o limite original. Limites
reduzidos recebem status `reduced`; limite corrente zero recebe `cancelled` e zera a
utilização incremental. Saldo sacado não pode exceder o limite corrente e a EAD nunca
excede esse limite.

Na carteira de aceite há 10 commitments e 10 guarantees. Em 12 meses:

| Multiplicador | P utilização commitment | EAD média commitment | P chamada guarantee | EAD média guarantee |
|---:|---:|---:|---:|---:|
| 0,75 | 0,306158 | R$ 24.893,14 | 0,203188 | R$ 36.398,86 |
| 1,00 | 0,387290 | R$ 31.489,89 | 0,262002 | R$ 46.934,74 |
| 1,50 | 0,524080 | R$ 42.612,00 | 0,367866 | R$ 65.899,26 |

Essas sensibilidades demonstram monotonicidade, não intervalo estatístico. Sete testes
cobrem as duas categorias, horizonte/risco, cancelamento/redução, carteira, linhagem e
falhas de contrato. Uso institucional exige eventos reais, definição jurídica do
limite executável, calibração, validação independente e controle de dupla contagem com
PD/ECL.
