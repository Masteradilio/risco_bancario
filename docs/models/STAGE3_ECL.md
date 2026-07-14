# Cálculo de ECL Stage 3

## Abordagem de cash shortfall

Stage 3 não usa `PD × LGD × EAD`. Para cada cenário e período:

```text
cash shortfall = fluxo contratual
               - recebimento esperado do devedor
               - recuperação sem garantia
               - recuperação de colateral
               - recuperação de garantia financeira
               - recuperação pós-write-off
               + custos de cobrança e execução
```

O shortfall é descontado pela EIR original. Valores negativos por excesso de recuperação
podem compensar outros períodos; o ECL total do cenário possui piso zero.

## Golden case

Fluxo contratual de R$ 100, recebimento esperado de R$ 60, recuperação de colateral de
R$ 20 e custos de R$ 5, com taxa zero:

```text
100 - 60 - 20 + 5 = R$ 25
```

O teste automatizado reconcilia ECL de R$ 25 em todos os cenários. Em projeções
distintas, ECL otimista/base/pessimista/stress de R$ 20/R$ 40/R$ 60/R$ 80 produzem
ponderação de R$ 40 e stress separado de R$ 80.

## Garantias, custos, cura e write-off

Colateral e garantia financeira possuem campos próprios e entram uma única vez como
recuperações. Custos aumentam o shortfall. Cada cenário admite um evento de cura e o
resultado preserva esse indicador.

Write-off é evento contábil rastreado, não uma segunda perda adicionada ao shortfall. No
golden case, write-off de R$ 100 com recuperação pós-baixa de R$ 20 resulta em ECL de
R$ 80, não R$ 180. Recuperação pós-baixa sem write-off anterior é rejeitada.

## Receita de juros

Para ativo credit-impaired, a receita é calculada sobre o valor contábil líquido:

```text
base líquida = valor contábil bruto - allowance de abertura
juros mensais = base líquida × EIR original / 12
```

No golden case, R$ 1.000 brutos menos R$ 200 de allowance, a 12% a.a., geram R$ 8 de
juros mensais. A base fica identificada como
`net_carrying_amount_for_credit_impaired_asset`.

## Controles

- projeções devem cobrir exatamente os quatro cenários;
- cenários compartilham datas futuras, únicas e ordenadas;
- allowance não pode exceder o valor contábil bruto;
- reversão/cura e recuperação pós-baixa são validadas temporalmente;
- contribuições são ponderadas somente após integrar os fluxos de cada cenário;
- versões e hash do conjunto de cenários acompanham o resultado.

Os fluxos são sintéticos e demonstrativos. A mecânica está testada, mas não existe
aprovação institucional das projeções de recuperação.
