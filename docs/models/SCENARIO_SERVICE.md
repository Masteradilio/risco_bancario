# Serviço de cenários macroeconômicos

## Escopo

O serviço canônico transforma a fonte sintética versionada já existente em trajetórias
macroeconômicas mensais tipadas. Ele preserva uma única fonte de verdade em
`config/synthetic/macroeconomic_scenarios/1.0.0.json` e adiciona governança por meio de
`config/scenario_service/2026.07.1.json`.

Os dados são sintéticos e demonstrativos. O conjunto vigente tem status
`not_approved`; não representa projeção oficial, consenso de mercado ou aprovação de
uma instituição financeira.

## Contrato das trajetórias

Cada cenário contém 60 períodos mensais, de janeiro de 2026 a dezembro de 2030. Todo
período possui o mesmo schema:

- crescimento do PIB;
- inflação;
- taxa de política monetária;
- desemprego;
- endividamento das famílias;
- pressão de risco sintética não linear.

O domínio rejeita datas que não sejam início de mês, lacunas na sequência mensal,
mudança do schema entre períodos, IDs repetidos ou horizontes divergentes.

## Cenários e pesos

| ID | Nome | Uso | Peso |
|---|---|---|---:|
| `upside` | Otimista | cenário probabilístico | 0,15 |
| `base` | Base | cenário probabilístico | 0,70 |
| `downside` | Pessimista | cenário probabilístico | 0,15 |
| `stress` | Stress | sensibilidade separada | 0,00 |

Os três cenários probabilísticos devem somar exatamente 1. O stress deve ter peso zero
e não entra silenciosamente no ECL ponderado.

## Versão e aprovação

O resultado carrega versão do serviço, hash SHA-256 da fonte, estado de aprovação,
aprovador e data de aprovação. Um conjunto com estado `approved` é inválido sem
aprovador e data; estados não aprovados não podem carregar esses campos.

Versão vigente: `2026.07.1`. Evidência: `synthetic_demonstrative_only`. Status:
`not_approved`.

## Cache e snapshots externos

`ScenarioSnapshotCache` materializa primeiro a resposta de qualquer provedor externo
em JSON canônico. O nome contém provedor, versão da fonte e hash do payload. A leitura
recalcula o hash e rejeita adulteração. O timestamp de captura deve possuir fuso e é
normalizado para UTC.

Assim, nenhuma chamada externa integra o cálculo determinístico. A captura externa e o
consumo quantitativo ficam separados, reproduzíveis e auditáveis. A implementação não
inclui credenciais ou integração com um provedor real nesta fase.

## Evidências

- domínio: `src/domain/scenarios/models.py`;
- serviço: `src/application/services/scenarios.py`;
- política: `config/scenario_service/2026.07.1.json`;
- fonte sintética: `config/synthetic/macroeconomic_scenarios/1.0.0.json`;
- testes: `tests/application/test_scenario_service.py`.

As relações entre as variáveis macro e PD/LGD/EAD pertencem à Tarefa 9.2; o cálculo de
ECL integral por cenário pertence à Tarefa 9.3.
