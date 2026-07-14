# Datasets sintéticos de modelagem

`src/data/synthetic/modeling.py` constrói tabelas point-in-time a partir da
população, dos snapshots, dos eventos de crédito e do histórico macroeconômico
sintéticos. O módulo apenas prepara observações e targets; não treina, seleciona
ou valida modelos.

## Data de observação e targets

As linhas de PD e SICR usam snapshots mensais até dezembro de 2024. Esse corte
preserva doze meses completos de resultado na janela simulada. Contratos deixam
o conjunto de risco de PD a partir do primeiro default.

- `target_default_12m`: default estritamente depois da data de observação e até
  doze meses depois;
- `target_hazard_1m`: default no mês imediatamente seguinte;
- `target_sicr_12m`: default, atraso de pelo menos 31 dias ou deterioração de ao
  menos dois graus em relação ao rating de originação nos doze meses seguintes.

Os campos de feature contêm somente saldo, limite, utilização, atraso, score,
rating, produto e macroeconomia disponíveis na data de observação. Datas futuras,
recuperações e exposições no default não aparecem nas tabelas de PD/SICR.

## LGD e EAD

O dataset de LGD possui uma linha por default inicial. O target
`target_realized_lgd_undiscounted` reconcilia exposição no default e todas as
recuperações líquidas observadas, inclusive pós-baixa. O nome explicita que o
desconto pela EIR ainda não foi aplicado; isso pertence às fases de LGD/ECL.

O dataset de EAD seleciona uma observação anterior ao default, preferencialmente
doze meses antes, e preserva a exposição realizada como target. Produtos com
limite ou compromisso também recebem `target_ccf`, limitado ao intervalo de zero
a um. O gerador mantém ao menos um caso determinístico desse tipo na carteira de
aceitação.

## Separação temporal

Nenhuma linha é sorteada entre amostras. Os cortes são fixos e disjuntos:

- treino: até dezembro de 2019;
- validação: janeiro a dezembro de 2020;
- calibração: janeiro a dezembro de 2021;
- OOT: janeiro de 2022 a dezembro de 2023;
- backtesting: janeiro a dezembro de 2024.

Esses nomes definem o uso permitido das linhas. Treino/tuning não pode consultar
calibração, OOT ou backtesting, e o conjunto de teste não pode orientar seleção
de variável, threshold ou hiperparâmetro.

## Evidência de aceitação

Com `seed=91`, 40 clientes e dois contratos por cliente, foram geradas 1.299
linhas de PD/hazard, 1.299 de SICR, 25 de LGD e 25 de EAD. Há 194 targets de
default em 12 meses, 16 hazards mensais, 247 targets de SICR e ao menos um target
de CCF. Sete testes verificam janelas, targets, reconciliação, ordem temporal,
splits e anti-leakage.
