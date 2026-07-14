# Produtos rotativos

`src/domain/contracts/revolving.py` é o motor mensal canônico para cartões de
crédito e cheque especial. Limite, saldo sacado e parcela não utilizada são
estados distintos e reconciliados em cada período.

O chamador fornece uma atividade por mês com drawdown solicitado, pagamento e
cancelamento de limite. O motor:

- calcula juros sobre o saldo de abertura;
- limita novas utilizações à disponibilidade depois dos juros;
- calcula pagamento mínimo como o maior entre valor fixo e percentual, limitado
  ao total devido;
- registra insuficiência quando o pagamento realizado fica abaixo do mínimo;
- aloca pagamento primeiro aos juros e depois ao principal;
- cancela somente limite não utilizado, sem reduzir o limite abaixo do saldo;
- preserva saldo, limite e disponibilidade de fechamento.

Cartão e cheque especial compartilham as mesmas invariantes financeiras, mas
mantêm tipos de produto distintos para políticas posteriores. O pagamento mínimo
é parametrizado: por exemplo, um cheque especial pode exigir 100% ao vencimento.

As atividades devem formar sequência mensal completa, única e ordenada desde a
data inicial. Valores solicitados além do limite ou além da dívida são truncados
e o valor efetivamente aplicado permanece auditável.

## Limitações

O motor não presume compras, saques, parcelamento de fatura, tarifas, IOF,
mudança positiva de limite ou política de cobrança. Tais eventos devem chegar
como inputs versionados. CCF e EAD são estimados em fases próprias e não são
embutidos no cronograma contratual.

Seis testes cobrem pagamento mínimo, limite não utilizado, cap de drawdown,
cancelamento, alocação, shortfall, cartão, cheque especial e calendário estrito.
