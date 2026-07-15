# Relatório de validação de PD

## Escopo

Este relatório reproduz a avaliação OOT congelada do baseline logístico 12m com
calibração isotonic selecionada sem acesso ao OOT. Todos os dados são sintéticos;
o relatório não é validação independente nem aprovação institucional.

## Resultado agregado OOT

O OOT de 2024 contém 233 linhas e 27 defaults em 12 meses.

| Métrica | Resultado |
|---|---:|
| ROC AUC | 0,5000 |
| Gini | 0,0000 |
| KS | 0,0000 |
| PR-AUC | 0,1159 |
| Brier Score | 0,1342 |
| Log Loss | 0,4498 |
| ECE | 0,1782 |

O calibration plot possui um único bin populado: as 233 previsões são 0,2941,
contra taxa observada 0,1159. A perda completa de ranking e a sobrestimação
material confirmam falha OOT.

## Rating, observado/esperado e segmentos

Testes binomiais exatos bilaterais rejeitam igualdade observado/esperado a 5%
em A2, B1 e B2; A3 não rejeita. Os testes são diagnósticos sem correção por
múltiplas comparações e não sustentam aprovação. As 14 visões por rating,
produto e ano de safra incluem contagem, eventos, taxa observada, PD média,
O/E, erro absoluto e Brier.

Não há atributos protegidos no dataset. Portanto, a análise cobre desempenho
por segmentos de risco e negócio, não fairness demográfica. Ausência desses
atributos impede concluir ausência de viés.

## Estabilidade e backtesting

O PSI do score logístico não calibrado entre calibração (2022) e backtesting
futuro (2025) é 6,7903, classificado como `high_shift`. O score não calibrado é
usado porque a transformação isotonic colapsada seria incapaz de revelar drift.

As linhas de 2025 não têm target 12m maduro. O status de backtesting é
`pending_target_maturation`; AUC, calibração ou O/E de backtesting não são
calculados nem substituídos por zeros. A Fase 13 executou separadamente o backtest
retrospectivo sobre o OOT maduro de 2024 e preservou as 182 linhas operacionais de 2025
como pendentes; consulte `docs/validation/PD_BACKTESTING.md`.

## Decisão

Status: `not_approved`. O modelo não atende discriminação, calibração ou
estabilidade. Não há champion aprovado; a logística permanece somente referência
explicável congelada, e challengers também continuam não aprovados.
