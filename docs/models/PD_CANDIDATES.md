# Candidatos de PD e registry

`src/models/pd/candidates.py` mantém challengers separados do baseline logístico.
Nenhum modelo está aprovado para uso institucional.

## Gradient boosting 12 meses

O `HistGradientBoostingClassifier` usa profundidade 3, learning rate 0,05, 150
iterações, pesos balanceados e seed fixa. O estimador-base é ajustado somente em
treino. Um calibrador isotonic congelando o estimador é ajustado apenas em
`calibration`.

Na validação, antes da calibração, o challenger teve ROC AUC 0,7481, AP 0,3928 e
Brier 0,1953, abaixo do baseline logístico. Após calibração, foi auditado uma
única vez no OOT: 240 linhas, 42 eventos, ROC AUC 0,7554, AP 0,4129, Brier
0,1493, taxa observada 0,1750 e PD média 0,3075. A sobrestimação global de 0,1325
impede promoção.

O OOT não foi usado para hiperparâmetros nem para escolher o champion. Como já
foi consumido para auditoria, qualquer ajuste posterior exige congelamento de
especificação e avaliação final em backtesting futuro.

## Survival gradient boosting

O segundo challenger usa a mesma família para hazard mensal em tempo discreto.
Na validação obteve ROC AUC 0,3430, AP 0,0421 e somente três eventos. Ele fica no
registry com status `insufficient_hazard_events`, sem calibração ou promoção.

## Matrizes de transição

Para segmentos pequenos, são estimadas probabilidades empíricas mensais entre
ratings usando apenas treino. As 34 células existentes somam um por combinação
produto/rating de origem. Ausência de uma transição não é preenchida
silenciosamente; smoothing e pooling exigem validação posterior.

## Registry

- `logistic_12m`: champion provisório por explicabilidade e melhor evidência de
  validação, status `not_approved`;
- `hist_gradient_boosting_12m`: challenger calibrado, OOT avaliado e não aprovado;
- `hist_gradient_boosting_discrete_hazard`: challenger bloqueado por eventos;
- `rating_transition_matrix`: challenger para segmentos pequenos, pendente.

Cinco testes verificam calibrador reservado, hazard, somas das matrizes, registry
sem aprovação e métricas finitas.
