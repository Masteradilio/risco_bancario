# Contratos amortizados

`src/domain/contracts/amortization.py` é o motor canônico de cronogramas para
empréstimos Price, SAC e bullet. Entradas financeiras usam `Decimal`; valores
monetários são arredondados a centavos com `ROUND_HALF_EVEN` e o último período
absorve o resíduo para zerar o saldo.

## Métodos

- `price`: prestação de principal mais juros nivelada para taxa fixa sob
  convenção mensal 30/360; o último fluxo pode variar por arredondamento. Em taxa
  variável, a prestação é recalculada no reset usando saldo e prazo restantes.
- `sac`: principal constante, com juros sobre o saldo de abertura.
- `bullet`: juros periódicos e principal integral no vencimento.

Cada período preserva início/fim de competência, vencimento ajustado, saldo de
abertura, taxa anual, fração de ano, principal, juros, tarifa, pagamento total e
saldo final.

## Taxas e EIR

Taxa fixa não admite resets. Taxa variável exige uma curva de `RateReset`; a taxa
vigente é o último reset efetivo até o início da competência. A curva é um input
versionável do chamador, não uma previsão criada pelo motor.

A taxa efetiva de juros é a raiz que iguala o valor contábil inicial aos fluxos
contratuais futuros. O valor inicial é principal menos tarifa upfront; tarifas
periódicas permanecem nos fluxos. A raiz usa as datas ajustadas e a convenção de
dias escolhida.

## Calendário

Convenções suportadas: ACT/365, ACT/360 e 30/360. Vencimentos podem permanecer
sem ajuste ou usar following, modified following e preceding. Finais de semana e
a lista explícita de feriados são considerados; o motor não presume calendário
nacional, estadual ou municipal.

## Limitações

O motor ainda não trata prepagamento, carência, taxas negativas, capitalização de
juros, modificação contratual ou convenções de calendário externas. Produtos
rotativos e compromissos pertencem à Tarefa 4.2; prepagamento/modificações, à 4.3.

Oito testes cobrem os três métodos, reconciliação, taxa variável, tarifas/EIR,
feriados, ajustes de dia útil, convenções de dias e validação de curvas.
