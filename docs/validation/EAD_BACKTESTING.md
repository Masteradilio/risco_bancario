# Backtesting independente de EAD e CCF

## Escopo

`src/validation/backtesting/ead.py` recebe saldos e CCF congelados, sem estimar ou
recalibrar os componentes. A política `config/validation/backtesting/ead-2026.07.1.json`
separa EAD amortizada e rotativa e exige cortes rotativos por produto e faixa de
utilização.

Compromissos e garantias financeiras não possuem eventos realizados na fábrica atual.
Eles permanecem em `off_balance_without_realized_history` e não recebem target ou
performance inventados.

## Saldo/EAD previsto versus realizado

Os 24 defaults amortizados reconciliam exatamente porque projeção e observado usam a
mesma convenção temporal do gerador. Isso testa a mecânica de saldo, não capacidade
preditiva independente.

O holdout rotativo contém quatro observações. A previsão de EAD é o saldo observado mais
limite disponível vezes CCF previsto; a comparação usa EAD no default.

| Componente | N | EAD média prevista | EAD média realizada | MAE | MAE relativo |
|---|---:|---:|---:|---:|---:|
| amortizado | 24 | 128.765,4029 | 128.765,4029 | 0,00 | 0,00% |
| rotativo | 4 | 6.280,7227 | 4.494,1200 | 1.813,9392 | 40,3625% |

O limite objetivo de MAE relativo rotativo é 15%; logo o saldo/drawdown falha mesmo
quando a métrica de CCF isolada parece aceitável.

## CCF por produto e utilização

| Corte | N | CCF previsto | CCF realizado | MAE |
|---|---:|---:|---:|---:|
| agregado | 4 | 3,7665% | 4,4672% | 3,9723 p.p. |
| credit card | 2 | 3,2716% | 0,0000% | 3,2716 p.p. |
| overdraft | 2 | 4,2614% | 8,9343% | 4,6730 p.p. |
| utilização baixa | 1 | 8,5227% | 17,8687% | 9,3459 p.p. |
| utilização média | 3 | 2,1811% | 0,0000% | 2,1811 p.p. |

O MAE e o RMSE agregados do CCF ficam abaixo de 10% e 15%, mas quatro linhas não
atingem o mínimo de 100 e nenhuma célula atinge 30.

## Decisão e evidência

Decisão objetiva: `rejected`, por volume rotativo insuficiente e MAE relativo de EAD
acima do limite.

- gerador: `scripts/generate_ead_backtest_report.py`;
- relatórios: `evidence/validation/ead/2026.07.1/report.json` e `report.md`;
- escopo: `synthetic_independent_backtest`;
- limite: carteira pequena, sem realizado off-balance ou aprovação institucional.
