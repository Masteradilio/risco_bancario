# Dataset de workout LGD

`src/models/lgd/workout.py` constrói uma linha por default observado, inclusive
redefaults, sem consultar eventos posteriores ao cutoff de observação.

Cada registro contém coorte trimestral, produto, EAD no default, EIR, janela de
workout, indicador de censura, recuperações brutas, custos, recuperações líquidas,
garantia, cura, write-off e status do desfecho. Os cash flows permanecem em nível
de evento para desconto na Tarefa 7.2.

A janela padrão é 24 meses. O cutoff efetivo é o menor entre fim da janela e
`observation_end_date`. Uma observação é censurada quando o histórico termina
antes da janela, mesmo que cura ou write-off já tenha sido observado, pois ainda
podem existir recuperações posteriores.

Na carteira de aceitação até 1º de dezembro de 2025 há 32 defaults: 12 write-offs,
10 curas, 6 abertos com janela completa e 4 abertos censurados. Sete registros
têm janela censurada, 7 são redefaults, 25 possuem cash flow e 20 têm garantia.

Seis testes cobrem unicidade por default, coortes, reconciliação bruto-custo-líquido,
vínculos, cutoff/censura e janela inválida. O dataset é sintético e não representa
experiência observada de recuperação institucional.
