# Validação sintética de staging/SICR

## Escopo

`src/models/sicr/validation.py` avalia, no OOT sintético, os sinais observáveis
de atraso e downgrade usados pelo motor SICR. Como não existe PD aprovada, esta
é evidência proxy e não validação institucional do staging completo.

## Resultado OOT

O OOT contém 233 linhas e 37 eventos futuros de SICR. A definição relativa com
dois notches ou 31 DPD não marca nenhuma linha: 0 verdadeiros positivos, 0
falsos positivos, 196 verdadeiros negativos e 37 falsos negativos. Recall é
zero e FNR é 1,00. Esse é um blocker explícito, não evidência de estabilidade.

A taxa prevista fica zero em treino, validação, calibração e OOT; por isso o PSI
binário também é zero e as 208 migrações mensais observadas são Stage 1→Stage 1.
PSI zero numa regra degenerada não indica modelo adequado.

## Sensibilidade

Reduzir o downgrade para um notch eleva a taxa Stage 2 a 0,4893: recall 0,6757,
precision 0,2193, FPR 0,4541 e FNR 0,3243. Alterar somente DPD para 15 ou 60 não
muda o resultado nesta amostra, porque não há atraso contemporâneo suficiente.
O OOT não foi usado para promover esse threshold alternativo.

## Comparação de definições

A definição absoluta legada (rating atual B1 ou pior, ou 31 DPD) tem recall
0,1892, precision 0,0515, FPR 0,6582 e FNR 0,8108. A concordância com a regra
relativa é 0,4163. O resultado confirma que nível atual absoluto e mudança desde
a originação não são intercambiáveis.

Foram listados contratos falsos positivos/negativos sem expor dados reais. Seis
testes cobrem reconciliação da matriz, PSI por período, migrações, sensibilidade,
comparação e status `not_approved`.
