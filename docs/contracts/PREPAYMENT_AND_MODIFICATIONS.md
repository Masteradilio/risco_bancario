# Prepagamento e modificações

`src/domain/contracts/modifications.py` aplica eventos a cronogramas amortizados
sem apagar o contrato original.

## Prepagamento

O evento ocorre depois de um período identificado. O valor aplicado é limitado
ao saldo de fechamento. Prepagamento total encerra o cronograma; prepagamento
parcial cria um novo cronograma para o saldo e prazo restantes, sem reaplicar a
tarifa upfront. Taxas variáveis preservam a curva futura e a taxa vigente.

## Modificação sem baixa

O principal revisado deve reconciliar com o valor contábil imediatamente antes
da modificação. Os novos fluxos são descontados pela EIR original. O valor
contábil passa ao valor presente revisado, a EIR original é preservada e o
ganho/perda é `valor anterior - valor presente modificado`.

## Modificação com baixa

A baixa exige valor justo explícito do instrumento substituto. O valor contábil
novo é esse valor justo, o ganho/perda é `valor justo - valor anterior` e uma
nova EIR é resolvida contra os fluxos do instrumento reconhecido. O motor não
decide se os termos são substancialmente diferentes; essa classificação é input
de uma política aprovada e auditável.

## Limitações

Não há teste quantitativo automático de baixa, contraprestação em caixa,
capitalização de atraso, custos de renegociação ou tratamento POCI. Esses itens
exigem políticas e golden cases posteriores. Cinco testes cobrem prepagamento
parcial/total, reconciliação, continuidade de EIR, baixa, valor justo e regras de
entrada.
