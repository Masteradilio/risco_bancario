# Datasets sintéticos de modelagem

`src/data/synthetic/modeling.py` constrói tabelas point-in-time a partir da
população, dos snapshots, dos eventos de crédito e do histórico macroeconômico
sintéticos. O módulo apenas prepara observações e targets; não treina, seleciona
ou valida modelos.

## Data de observação e targets

As linhas de PD e SICR usam snapshots mensais até dezembro de 2025. Targets
maduros existem somente até dezembro de 2024; as linhas de 2025 representam o
backtesting futuro e mantêm targets nulos, em vez de registrar falsos zeros.
Contratos deixam o conjunto de risco de PD a partir do primeiro default.

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

Nenhuma linha é sorteada entre amostras. Os cortes são fixos, disjuntos e
separados por doze meses de embargo entre os blocos de desenvolvimento:

- treino: até dezembro de 2018;
- embargo: janeiro a dezembro de 2019;
- validação: janeiro a dezembro de 2020;
- embargo: janeiro a dezembro de 2021;
- calibração: janeiro a dezembro de 2022;
- embargo: janeiro a dezembro de 2023;
- OOT: janeiro a dezembro de 2024;
- backtesting futuro: janeiro a dezembro de 2025, ainda sem target maduro.

Esses nomes definem o uso permitido das linhas. Treino/tuning não pode consultar
calibração, OOT ou backtesting, e o conjunto de teste não pode orientar seleção
de variável, threshold ou hiperparâmetro.

## Evidência de aceitação

Com `seed=91`, 40 clientes e dois contratos por cliente, foram geradas 1.026
linhas de PD/hazard e SICR, das quais 844 possuem target maduro e 182 pertencem
ao backtesting futuro. Há 117 defaults em 12 meses, 10 hazards mensais, 148
targets de SICR positivos e ao menos um target de CCF. Os testes verificam
janelas, nulidade futura, embargo, reconciliação, ordem temporal e anti-leakage.
