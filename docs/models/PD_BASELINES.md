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
serve exclusivamente para derivar a escala de rating. Os resultados foram
recalculados sobre o split com embargo instituído na Tarefa 5.4. Este baseline
não consulta OOT nem backtesting e não representa aprovação de modelo.

## Diagnóstico reproduzível

Na carteira de aceitação (`seed=91`):

| Modelo | n validação | Eventos | Taxa | PD média | Erro calibração global | Brier | Log loss | ROC AUC | AP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Logística 12m | 193 | 38 | 0,1969 | 0,2879 | 0,0910 | 0,1969 | 0,5251 | 0,7421 | 0,3725 |
| Hazard 1m | 193 | 3 | 0,0155 | 0,0253 | 0,0098 | 0,0225 | 0,1277 | 0,4789 | 0,0270 |

O hazard possui somente três eventos de validação e baixa discriminação;
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
