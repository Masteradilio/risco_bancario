# Golden cases de amortização

A referência manual está em
`tests/fixtures/golden/amortization_cases.csv`. Os três contratos usam principal
de R$ 1.200,00, prazo de três meses, taxa nominal de 12% a.a., competência
mensal 30/360, sem tarifa e originação em 15/01/2026. A tolerância de comparação
é de R$ 0,01 por campo e período.

## Cálculo independente

- Juros mensais: `saldo de abertura × 12% ÷ 12`.
- SAC: principal mensal `1.200 ÷ 3 = 400`.
- Bullet: principal zero nos meses 1–2 e R$ 1.200 no mês 3.
- Price: prestação teórica
  `1.200 × 1% ÷ (1 - (1 + 1%)^-3)`, com principal igual à prestação menos
  juros. Cada componente é arredondado a centavos por `ROUND_HALF_EVEN`; o
  último principal absorve o resíduo para fechar o saldo.

O CSV foi mantido deliberadamente simples e legível como uma pequena planilha.
Ele não é gerado pelo motor durante os testes. A suíte carrega os valores
estáticos, compara abertura, principal, juros, pagamento e fechamento linha a
linha, e verifica as identidades contábeis de cada período.
