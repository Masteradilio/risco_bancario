# Eventos de crédito sintéticos

`src/data/synthetic/events.py` deriva eventos posteriores aos snapshots
observáveis. A geração é determinística por `seed` e contrato, sem usar dados
reais ou expor variáveis latentes.

## Linha do tempo

- O default ocorre depois do snapshot que contém a exposição observada. Os
  gatilhos possíveis são atraso de 90 dias, hazard estocástico e choque
  idiossincrático controlado para garantir cobertura de garantias.
- Cada default inicial recebe ações de cobrança e seis fluxos mensais de
  recuperação em caixa.
- Contratos garantidos podem ter execução de colateral. O valor recuperável é
  limitado pela exposição ainda aberta e pela parcela executável da avaliação.
- Recuperações registram valor bruto, custo, tipo de custo e valor líquido.
  Cobrança em caixa usa custo operacional; execução de garantia usa custo
  judicial e operacional.
- Curas exigem seis meses de observação. Um contrato curado pode voltar a
  default; a nova data é posterior à cura.
- Exposições não curadas são baixadas após doze meses. O write-off reconcilia a
  exposição no default menos as recuperações líquidas pré-baixa, preservando
  separadamente recuperações posteriores.

## Contratos públicos

`generate_credit_events(population, history)` retorna `CreditEventHistory` com
as tabelas `defaults`, `collections`, `recoveries`, `cures` e `writeoffs`. Os
identificadores conectam todo fluxo ao contrato e ao default de origem. A saída
de `as_tables()` não contém campos latentes.

Os eventos são evidência sintética para desenvolvimento e teste; não representam
taxas observadas, calibração institucional ou política contábil aprovada.

## Evidência de aceitação

Com `seed=91`, 40 clientes e dois contratos por cliente, a suíte fixa produziu:

- 25 defaults iniciais e 7 redefaults;
- 75 ações de cobrança;
- 150 recuperações mensais em caixa e 16 execuções de garantia;
- 12 curas;
- 20 write-offs e 20 recuperações pós-baixa.

Choques determinísticos de cobertura em contratos longos não-POCI distribuem
eventos entre os cortes temporais. Eles servem à testabilidade do pipeline, não
representam frequência ou calibração observada e nunca são exportados como feature.

Sete testes verificam reprodutibilidade, ordem temporal, fluxo mensal, custos,
execução de garantia, cura/redefault, reconciliação de baixa e anti-leakage.
