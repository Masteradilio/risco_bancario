# Model card — SICR e classificação de estágio

## Identificação e status

| Campo | Valor |
|---|---|
| Componente | `relative_sicr_validation_proxy` |
| Implementação | `src/models/sicr/` |
| Política | `config/sicr_policy/2026.07.1.json` |
| Dataset | fábrica sintética, OOT com 233 contratos |
| Data da avaliação | 14 de julho de 2026 |
| Status | `not_approved` |
| Escopo da evidência | `synthetic_demonstrative_only` |
| Regra aprovada | nenhuma |

## Objetivo e uso pretendido

O componente demonstra uma decisão auditável de aumento significativo do risco de
crédito. Ele compara a lifetime PD atual com o baseline persistido na originação e
combina sinais quantitativos com downgrade, atraso, watchlist, concessão e eventos
qualitativos. Seu uso é restrito à demonstração sintética do fluxo de Stage 1 para
Stage 2; não deve decidir estágio em carteira institucional.

## Dados e separação temporal

A validação usa o bloco OOT sintético congelado, com 233 contratos e 37 eventos
futuros de SICR. As variáveis avaliadas são observáveis na data-base. O OOT não foi
usado para promover thresholds, calibrar a política ou escolher a alternativa de um
notch. Não há dados reais, decisão humana histórica nem amostra institucional.

## Método e política demonstrativa

A política `2026.07.1` combina aumento absoluto de lifetime PD de 0,05, razão
relativa de 2,00, downgrade de dois notches e backstop de 31 DPD. A isenção de baixo
risco é limitada a A1–A3 e lifetime PD atual de até 0,02, sem suprimir gatilhos
qualitativos ou diretos. Esses valores são hipóteses versionadas e explicitamente
`demonstrative_unvalidated`, não limites prescritos pela IFRS 9, CMN ou BCB.

## Performance e decisão

Na avaliação OOT, a regra relativa proxy não marcou contratos: 0 verdadeiros
positivos, 0 falsos positivos, 196 verdadeiros negativos e 37 falsos negativos.
Recall é zero e FNR é 1,00. A taxa prevista também é zero nos quatro blocos temporais;
portanto, PSI zero representa uma regra degenerada, não estabilidade.

A sensibilidade de um notch produz recall 0,6757, precision 0,2193, FPR 0,4541 e FNR
0,3243, mas não foi promovida. A regra absoluta legada tem recall 0,1892 e FPR
0,6582. A decisão permanece `not_approved`.

## Limitações e riscos

- a PD usada no fluxo também não está aprovada;
- o target é um proxy sintético, sem adjudicação institucional de SICR;
- amostra, eventos, atraso contemporâneo e diversidade de transições são limitados;
- o comportamento por produto, rating, safra e cenário não tem poder estatístico;
- a isenção de baixo risco e os gatilhos qualitativos não foram validados em produção;
- não existe validação independente institucional nem aprovação humana.

## Monitoramento e governança

Monitorar matriz de confusão, recall/FNR, FPR, taxa de Stage 2, migrações, PSI e
distribuições dos gatilhos por produto, rating e safra. O OOT permanece congelado e
não pode ser usado para tuning. Qualquer promoção exige dados reais governados,
target adjudicado, calibração fora do OOT, validação independente, aprovação humana,
versão de política e trilha imutável de decisão.

## Reprodutibilidade e evidências

- código: `src/models/sicr/engine.py`, `baseline.py`, `stage_history.py` e
  `validation.py`;
- política: `config/sicr_policy/2026.07.1.json`;
- testes: `tests/models/test_sicr_*.py`;
- documentação: `SICR_ENGINE.md`, `SICR_ORIGINATION_BASELINE.md`,
  `STAGE_HISTORY_AND_CURE.md` e `SICR_VALIDATION_REPORT.md`;
- evidência E2E: `../../evidence/e2e/journey.json`.
