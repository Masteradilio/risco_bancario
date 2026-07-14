# Baselines explicáveis de PD

`src/models/pd/baselines.py` implementa dois baselines determinísticos sobre o
dataset point-in-time sintético:

- regressão logística para default em 12 meses;
- regressão logística em tempo discreto para hazard no mês seguinte.

Ambos usam somente saldo, limite, utilização, atraso, score comportamental,
cinco variáveis macroeconômicas, produto e rating observados. Variáveis numéricas
são padronizadas e categorias recebem one-hot encoding. Targets, identificadores,
datas futuras e eventos de recuperação não entram na matriz de features.

## Protocolo desta tarefa

O ajuste usa somente `train`; as métricas abaixo usam `validation`; `calibration`
serve exclusivamente para derivar a escala de rating. OOT e backtesting não são
consultados. Calibração probabilística formal, embargo de horizonte e avaliação
OOT pertencem à Tarefa 5.4; portanto estes resultados não aprovam modelo.

## Diagnóstico reproduzível

Na carteira de aceitação (`seed=91`):

| Modelo | n validação | Eventos | Taxa | PD média | Erro calibração global | Brier | Log loss | ROC AUC | AP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Logística 12m | 193 | 38 | 0,1969 | 0,2620 | 0,0651 | 0,1768 | 0,4723 | 0,7548 | 0,4271 |
| Hazard 1m | 193 | 3 | 0,0155 | 0,0006 | 0,0149 | 0,0156 | 0,2350 | 0,6105 | 0,0258 |

O hazard possui somente três eventos de validação e subestima fortemente a taxa;
isso é limitação material. Class weighting permite estimar o baseline, mas não
substitui mais dados, calibração nem intervalos de incerteza.

## Explicabilidade e rating

A tabela completa de coeficientes é retornada com o nome expandido de cada
feature. Não se converte coeficiente em interpretação causal.

R1–R5 são quintis da PD logística no conjunto reservado de calibração. Os limites
não são faixas manuais nem os ratings demonstrativos legados. Cada faixa registra
PD mínima/máxima/média, contagem e taxa de default observada. Essa escala é
provisória: só poderá ser promovida após calibração, monotonicidade, estabilidade
e validação nas tarefas seguintes.

## Cobertura sintética

Para evitar splits sem eventos, a fábrica introduz choques determinísticos de
cobertura em financiamentos de veículo e imobiliários não-POCI, distribuídos por
safra. O choque não é exportado como feature, mas altera a prevalência; métricas
são exclusivamente evidência de funcionamento do pipeline sintético.

Cinco testes verificam os dois targets, métricas, coeficientes sem leakage,
ratings derivados da calibração e reprodução do treinamento.
