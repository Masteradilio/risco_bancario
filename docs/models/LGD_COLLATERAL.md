# Projeção de recuperação por garantia

`src/models/lgd/collateral.py` projeta a recuperação de garantia na data do default
sob uma política versionada e reconciliável. O resultado não altera a LGD realizada:
ele fornece um componente prospectivo separado para modelagem e sensibilidade.

## Política base

A política `config/lgd_collateral_policy/2026.07.1.json` possui status
`demonstrative_unvalidated` e hash SHA-256 em cada resultado.

| Garantia | Variação anual do valor | Haircut | Custo | Execução |
|---|---:|---:|---:|---:|
| Imóvel | +3% | 25% | 12% | 12 meses |
| Veículo | -10% | 35% | 15% | 8 meses |

O valor avaliado é atualizado da data da avaliação até o default. Depois são
aplicados parcela executável, haircut, limite pela EAD, custo de execução e desconto
pela EIR contratual até a data projetada de realização. Todo cálculo monetário usa
`Decimal` e `ROUND_HALF_EVEN` com oito casas.

As premissas são sintéticas e não representam preços de mercado, experiência de
execução, custos jurídicos ou política institucional validada.

## Controle de dupla contagem

Os cash flows com fonte `collateral_execution` são identificados e preservados como
`excluded_observed_collateral_recovery`, para comparação histórica. Eles são
excluídos da base de outras recuperações e não são somados à projeção.

A composição usada é:

`outras recuperações descontadas + min(projeção de garantia, EAD remanescente)`

O total também é limitado à EAD. Assim, a mesma garantia não aparece simultaneamente
como caixa observado e valor projetado. O cash flow observado continua disponível no
dataset workout e na LGD realizada para backtesting.

## Sensibilidades

- `upside`: +3 p.p. na variação anual, -5 p.p. no haircut, -2 p.p. no custo e dois
  meses a menos para executar;
- `base`: premissas da tabela;
- `downside`: -5 p.p. na variação anual, +10 p.p. no haircut, +3 p.p. no custo e seis
  meses adicionais para executar.

Na carteira de aceite há 20 defaults com garantia — 11 veículos e 9 imóveis — e 12
sem garantia. Entre os garantidos, as recuperações líquidas descontadas médias são
R$ 115.644,45 no upside, R$ 101.573,44 no base e R$ 73.320,10 no downside. No base,
a média equivale a 68,1058% da EAD. A recuperação de garantia observada e excluída da
composição é, em média, R$ 70.706,53. Nenhum caso sintético atingiu o cap de headroom.

Sete testes cobrem atualização de valor, haircut, custos, prazo, desconto, cenários,
cap pela EAD, ausência de garantia, consistência contratual e dupla contagem. Os
resultados servem apenas para regressão e sensibilidade demonstrativa.
