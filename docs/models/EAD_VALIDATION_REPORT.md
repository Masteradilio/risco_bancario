# Relatório de validação de EAD e CCF

## Escopo

Este relatório consolida a reconciliação da EAD amortizada, o holdout temporal do
CCF rotativo e sensibilidades de utilização/horizonte/limite. A política
`config/ead_validation/2026.07.1.json` foi congelada antes da execução e exige
evidência institucional para aprovação.

Os dados são sintéticos. A reconciliação amortizada usa a mesma convenção temporal do
gerador; ela comprova implementação, não capacidade preditiva independente.

## EAD amortizada: previsto versus realizado

| Segmento | N | EAD média observada | EAD média projetada | MAE |
|---|---:|---:|---:|---:|
| acquired distressed | 8 | R$ 41.169,69 | R$ 41.169,69 | R$ 0,00 |
| mortgage | 8 | R$ 302.893,43 | R$ 302.893,43 | R$ 0,00 |
| vehicle finance | 8 | R$ 42.233,09 | R$ 42.233,09 | R$ 0,00 |
| Total | 24 | R$ 128.765,40 | R$ 128.765,40 | R$ 0,00 |

MAE e RMSE são zero em todos os anos de default de 2017 a 2025. Isso confirma a regra
de saldo temporal e a ausência de vazamento de amortização posterior ao default. Não
substitui validação dos componentes de EAD com dados reais.

## CCF rotativo: holdout temporal

O holdout contém dois defaults e quatro linhas de 2022–2023:

| Produto/horizonte | N | CCF realizado | CCF previsto | Erro absoluto |
|---|---:|---:|---:|---:|
| credit card / 3m | 1 | 0,000000 | 0,056984 | 0,056984 |
| credit card / 6m | 1 | 0,000000 | 0,008448 | 0,008448 |
| overdraft / 3m | 1 | 0,178687 | 0,085227 | 0,093459 |
| overdraft / 6m | 1 | 0,000000 | 0,000000 | 0,000000 |

| Métrica | Resultado | Limite |
|---|---:|---:|
| N | 4 | mínimo 100 |
| CCF médio realizado | 0,044672 | diagnóstico |
| CCF médio previsto | 0,037665 | diagnóstico |
| MAE | 0,039723 | máximo 0,100000 |
| RMSE | 0,054894 | máximo 0,150000 |

MAE/RMSE ficam abaixo dos limites, mas o volume é 4% do mínimo. Não há horizonte de
12 meses, limite reduzido/cancelado ou mais de uma observação por segmento.

Em 2022, N=2, CCF observado médio 0,089343, previsto 0,042614 e MAE 0,046730. Em
2023, N=2, observado zero, previsto 0,032716 e MAE 0,032716. Dois anos não atingem os
três mínimos e não sustentam conclusão de estabilidade.

## Sensibilidades

| Teste | Input baixo | Base | Input alto | Resultado |
|---|---:|---:|---:|---|
| CCF × utilização (0,2/0,5/0,8) | 0,170687 | 0,003207 | 0,000000 | responsivo; direção diagnóstica |
| CCF × horizonte (3/6/12m) | 0,000000 | 0,003207 | 0,021660 | responsivo; direção diagnóstica |
| EAD commitment × limite (50/75/100) | 14,523384 | 21,785076 | 29,046768 | monotônico por parametrização |

A relação inversa entre utilização e CCF previsto pode refletir menos limite
disponível, mas não pode ser interpretada com 21 linhas de treino. A monotonicidade
off-balance é propriedade da fórmula parametrizada, não descoberta empírica.

## Decisão

Status: `not_approved`. Blockers:

- somente 4 linhas e 2 anos no holdout CCF;
- todos os segmentos abaixo de 30 observações;
- nenhum limite reduzido/cancelado na validação;
- baseline CCF marcado `demonstrative_not_approved`;
- compromissos/garantias parametrizados, não estimados;
- evidência de validação sintética, não institucional.

Não existe modelo EAD/CCF aprovado. A EAD amortizada fica aceita como mecânica
reconciliada; CCF e off-balance permanecem componentes demonstrativos bloqueados.
