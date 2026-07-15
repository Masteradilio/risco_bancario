# Model card — EAD e CCF

## Identificação e status

| Campo | Valor |
|---|---|
| Componentes | EAD amortizada, CCF rotativo, off-balance EAD |
| Implementação | `src/models/ead/` |
| Versões de dataset | amortized `0.1.0`; CCF `0.1.0` |
| Data da avaliação | 14 de julho de 2026 |
| Status global | `not_approved` |
| Evidência | `synthetic_demonstrative_only` |
| Champion aprovado | nenhum |

## Objetivo e população

O módulo projeta exposição no default para contratos amortizados, cartões,
overdrafts, compromissos e garantias financeiras. Ele não calcula PD, LGD ou ECL e
mantém probabilidades de utilização separadas da probabilidade de default.

## Métodos

- amortizados: saldo de abertura da última competência observável antes do default,
  com cronograma revisado após prepagamento/modificação;
- rotativos: CCF realizado sobre limite disponível e Ridge por produto, utilização,
  horizonte, interação e status de limite;
- commitments: hazard parametrizado de utilização e parcela condicional de 75%;
- guarantees: hazard parametrizado de chamada e parcela condicional de 100%.

Valores brutos de CCF são preservados; target/predição são limitados a 0%–100%. CCF
com limite disponível zero é indefinido e excluído do modelo.

## Dados e separação

A EAD amortizada usa 24 defaults da carteira de aceite. Como a mesma regra gera o
target, erro zero significa reconciliação. O CCF usa carteira de desenvolvimento
separada, seed 91/400 clientes: 21 linhas até 2021 para treino e 4 linhas de 2022–2023
para validação. Compromissos/garantias não têm eventos observados e usam parâmetros.

## Performance

EAD amortizada: 24/24 reconciliados, MAE e RMSE zero. CCF holdout: CCF médio observado
0,044672, previsto 0,037665, MAE 0,039723 e RMSE 0,054894. Métricas CCF passam limites
de erro, mas falham volumes, segmentos, horizonte, eventos de limite e cobertura
temporal.

O backtest tecnicamente independente da Fase 13 também mede EAD rotativa: média prevista
de 6.280,7227 contra 4.494,1200 realizada e MAE relativo de 40,3625%. Assim, a decisão
permanece `not_approved` por erro de saldo/drawdown e volume, mesmo com CCF agregado
dentro dos limites de erro.

## Limites, sensibilidade e comportamento

O limite corrente, não o original, determina exposição. Reduções/cancelamentos são
suportados por golden cases. CCF responde a utilização e horizonte, mas a relação de
utilização é inversa e não aprovada. EAD off-balance cresce monotonicamente com limite,
horizonte e multiplicador de risco por construção.

## Uso pretendido e usos proibidos

Uso permitido: regressão técnica, reconciliação sintética, demonstração e desenho de
validação. Usos proibidos: provisionamento, decisão de crédito, capital, limite real,
reporte externo ou alegação de modelo calibrado/aprovado.

## Limitações

- somente 12 defaults rotativos e 4 linhas de holdout;
- apenas uma linha de desenvolvimento no horizonte de 12 meses;
- nenhum limite alterado nos dados de estimação/validação;
- off-balance sem utilização ou default observado;
- EAD amortizada é reconciliação tautológica do gerador;
- macroeconomia ainda não integra EAD/CCF; pertence à Fase 9;
- ausência de dados reais e aprovação humana; a independência disponível é apenas
  técnica e simulada.

## Promoção e monitoramento

Exigir volumes mínimos por produto/horizonte/status, OOT congelado, limites alterados,
eventos off-balance observados, MAE/RMSE/viés estáveis, sensibilidade plausível,
documentação jurídica do compromisso e validação independente. Monitorar erro por
produto, horizonte, utilização, limite, ano e tipo de exposição.

## Evidências

- políticas: `config/ead_policy`, `config/ccf_policy`,
  `config/off_balance_ead_policy` e `config/ead_validation`;
- código: `amortized.py`, `revolving_ccf.py`, `off_balance.py`, `validation.py`;
- testes: `tests/models/test_ead_*.py`;
- relatórios: `EAD_AMORTIZED.md`, `EAD_REVOLVING_CCF.md`, `EAD_OFF_BALANCE.md` e
  `EAD_VALIDATION_REPORT.md` e `../validation/EAD_BACKTESTING.md`.
