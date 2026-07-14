# POCI — identificação e mensuração

`src/ecl/calculation/poci.py` mantém ativos adquiridos ou originados com problema
de recuperação de crédito em fluxo separado do PD/SICR padrão.

## Identificação

`classify_poci` distingue `acquired_credit_impaired` e
`originated_credit_impaired`. Sem uma dessas evidências, o ativo não é marcado
como POCI. A fábrica sintética já exclui POCI dos datasets PD e SICR comuns.

## Credit-adjusted EIR

A taxa efetiva ajustada ao risco de crédito é a taxa que iguala o preço de
compra aos fluxos de caixa esperados na originação, já incorporando as perdas de
crédito iniciais. A implementação usa datas efetivas e busca determinística da
raiz; fluxos precisam ocorrer após o reconhecimento.

## Mudança subsequente de lifetime ECL

Fluxos contratuais, esperados iniciais e esperados atuais usam as mesmas datas.
Todos são descontados pela credit-adjusted EIR original:

```text
ECL inicial = VP(fluxos contratuais) - VP(fluxos esperados iniciais)
ECL atual   = VP(fluxos contratuais) - VP(fluxos esperados atuais)
mudança     = ECL atual - ECL inicial
```

Mudança positiva é `impairment_loss`; negativa é `impairment_gain`. Fluxo
esperado não pode exceder o contratual e entradas desalinhadas falham fechadas.

## Golden cases

`tests/fixtures/golden/poci_cases.csv` contém dois casos manuais de um ano:

- preço 80, esperado inicial 88 e atual 77: EIR 10%, mudança de perda +10;
- preço 80, esperado inicial 88 e atual 93,50: EIR 10%, ganho de impairment -5.

Seis casos de teste cobrem identificação, taxa, reconciliação manual, perda,
ganho e entradas inválidas. Resultados têm status `synthetic_unapproved` e não
constituem política contábil homologada.
