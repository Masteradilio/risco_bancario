# CCF de produtos rotativos

`src/models/ead/revolving_ccf.py` constrói observações anteriores ao default, calcula
CCF realizado e ajusta um baseline por produto, utilização e horizonte. A política
`config/ccf_policy/2026.07.1.json` é versionada, hashada e tem status
`demonstrative_unvalidated`.

## Dataset e cálculo

A carteira principal tem somente um default rotativo. Para permitir uma comparação
minimamente variável sem alterar o artefato de aceite, a política congela uma carteira
de desenvolvimento separada: seed 91, 400 clientes e 2 contratos por cliente.

Para cada default inicial de cartão ou overdraft, são procuradas observações exatas a
3, 6 e 12 meses. O cálculo é:

`CCF bruto = max(0, EAD no default - saldo observado) / limite disponível observado`

O limite disponível é `limite - saldo`. Se ele for zero, CCF é indefinido e a linha
é excluída da modelagem; zero não é fabricado. O CCF bruto permanece auditável e o
target de modelagem é limitado a 0%–100%, com ação explícita.

O dataset registra limite observado, limite imediatamente anterior ao default e
status `unchanged`, `reduced`, `cancelled` ou `increased`. Saldo/EAD acima do limite
aplicável e datas não point-in-time falham de forma fechada.

## Modelo

O baseline é Ridge com alpha 5. As features são:

- produto (`credit_card` ou `overdraft`);
- utilização na observação;
- horizonte em meses;
- interação utilização × horizonte;
- status de limite.

O treino usa defaults até 2021; defaults posteriores ficam separados para a validação
da Tarefa 8.4. Predições são limitadas a 0%–100%. O modelo não é uma constante global:
os coeficientes e predições variam com produto, utilização e horizonte.

## Evidência e limitações

A amostra tem 12 defaults e 25 linhas: 15 de cartão e 10 de overdraft. Há 12 linhas
de 3 meses, 12 de 6 meses e somente 1 de 12 meses; 11 combinações foram omitidas por
falta de histórico, sem aproximação temporal. O CCF realizado varia de 0 a 0,272929,
com média 0,056834; nenhum valor exigiu limite.

O treino contém 21 linhas. As métricas in-sample — não validação — são média prevista
0,062388, MAE 0,025137 e RMSE 0,033649, com predições de 0 a 0,182127. Quatro linhas
posteriores permanecem para avaliação temporal.

Todos os limites da amostra ficaram `unchanged`. Redução e cancelamento são tratados
e testados contra o contrato canônico, mas não há observações para estimar seu efeito;
o coeficiente de status não é informativo. O horizonte de 12 meses, os dois produtos
e o número de defaults também são insuficientes para aprovação.

Sete testes cobrem fórmula, limites reduzidos/cancelados/aumentados, CCF acima de 100%,
limite disponível zero, dataset, modelo e falhas temporais. O status permanece
`demonstrative_not_approved`.
