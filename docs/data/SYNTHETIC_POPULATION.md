# População e contratos sintéticos

A implementação da Tarefa 3.2 está em `src/data/synthetic/population.py`. Ela é
determinística por seed e gera registros imutáveis antes de qualquer snapshot,
default ou target.

## Cobertura

- clientes e contrapartes PF/PJ;
- grupos econômicos para contrapartes PJ;
- empréstimo pessoal, veículo, imobiliário, cartão e cheque especial;
- compromisso de crédito não sacado e garantia financeira;
- ativo adquirido com problema de recuperação de crédito (`acquired_credit_impaired`);
- originação, vencimento, taxa efetiva, valor original, limite e saldo inicial;
- cronograma Price em centavos para produtos amortizados;
- garantias de veículo e imóvel com avaliação e parcela executável.

IDs não têm significado real. Moeda é BRL e valores usam `Decimal`. A seed
mestre deriva substreams independentes para população e contratos. O método
`as_tables()` expõe somente schemas públicos e é testado contra campos `_latent`.

Uso mínimo:

```python
from src.data.synthetic import PopulationConfig, generate_population

portfolio = generate_population(PopulationConfig(seed=42, clients=16))
tables = portfolio.as_tables()
```

Persistência em Parquet, snapshots e eventos futuros pertencem às próximas
tarefas e não são simulados por este módulo.
