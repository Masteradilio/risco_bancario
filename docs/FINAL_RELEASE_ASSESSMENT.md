# Avaliação final da modernização

## Resultado

Esta avaliação acompanha a release de modernização `v2.0.1`. A candidata
`v2.0.0` foi preservada como tag imutável, mas sua entrega falhou antes da
publicação por uma invocação de script sem o root do repositório no `sys.path`.

O backlog atingiu **10/10 de completude técnica** nas dez dimensões revisadas
para o escopo de demonstração sintética. A nota mede se os critérios do estado-alvo
possuem implementação, teste, documentação e evidência rastreável. Ela **não é
aprovação de modelo, certificação regulatória, homologação institucional nem
autorização de uso em produção**.

O status institucional continua bloqueado. PD, SICR, LGD e EAD permanecem
`not_approved`; o backtesting de ECL foi rejeitado por ausência de snapshots
maduros; o Documento 3040 permanece `PREVALIDATED_DERIVED_XSD`, pois passou
somente pelo XSD derivado e pelo subconjunto semântico local. O scorecard estruturado está em
`evidence/release/final_scorecard.json`.

## Notas e decisões

| Dimensão | Nota técnica | Decisão quantitativa/operacional | Evidência-chave |
|---|---:|---|---|
| Arquitetura | 10/10 | demonstrada | domínio tipado, ADRs, API/migrations versionadas, CI |
| PD | 10/10 | `not_approved` | split temporal, calibração, curvas, OOT/backtesting, model card |
| LGD | 10/10 | `not_approved` | workout descontado, custos/garantias, segmentação e backtesting |
| EAD | 10/10 | `not_approved` | projeção temporal, CCF por produto/horizonte e backtesting |
| ECL | 10/10 | reconciliação aprovada; backtest rejeitado | período/cenário, EIR, Stage 1/2/3/POCI, ledger e golden cases |
| Staging | 10/10 | `not_approved` | baseline de originação, SICR, cura, histórico e OOT |
| Regulação | 10/10 | `PREVALIDATED_DERIVED_XSD` | fontes, matriz, regras versionadas, Doc3040 e manifesto |
| Validação | 10/10 | framework operacional; modelos bloqueados | validação independente simulada, backtests, monitoring e limitações |
| Segurança | 10/10 | controles demonstrados; sem pentest independente | JWT/RBAC, confirmação, auditoria, SAST e testes adversariais |
| Experiência e portfólio | 10/10 | demo sintética reproduzível | quickstart, frontend, tutorial, API e guia técnico |

## Por que uma implementação rejeitada pode ter nota técnica 10/10

O critério de engenharia não exige fabricar um resultado favorável. Um pipeline
de validação completo deve ser capaz de reprovar o modelo quando os dados ou as
métricas não sustentam promoção. Neste projeto, substituir `not_approved` por
“aprovado” para alcançar a nota seria uma falha de governança. A completude está
em medir, documentar, bloquear e tornar o resultado reproduzível.

## Evidências objetivas

- suíte canônica: 580 testes aprovados, 91,25% de cobertura no gate final,
  incluindo a verificação dos quatro model cards; suíte legada: 118 aprovados e
  7 ignorados;
- instalação limpa: source archive isolado, `venv` novo, dependências instaladas,
  wheel editável construído e smoke import aprovado; a demo subsequente concluiu
  com os quatro bloqueios de modelo esperados;
- benchmark: 1.000.000 de contratos sintéticos em 69,049503 s e pico Python de
  10.107.428 bytes, dentro do alvo demonstrativo versionado;
- golden cases: oito casos reconciliados entre JSON, CSV, planilha independente
  e motor canônico;
- E2E: fábrica com 24 arquivos/16.628 linhas, cálculo/persistência/ledger/Doc3040
  concluídos como `COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS`;
- regulação: 27 requisitos no pacote, seis bloqueadores preservados, XSD oficial
  e críticas oficiais explicitamente não executados;
- frontend: login real contra API local e consulta da mesma execução persistida,
  sem dados substitutos ou credenciais embutidas.

## Bloqueios para uso institucional

1. substituir a base sintética por dados reais governados, com qualidade,
   representatividade e lineage institucional;
2. reservar OOT/holdouts independentes e maduros, sem consumo em seleção;
3. recalibrar e validar PD, SICR, LGD e EAD com volumes mínimos por segmento;
4. formar histórico de snapshots ECL e desfechos para backtesting completo;
5. executar validação independente, aprovação humana e governança de mudança;
6. obter leiaute/XSD/críticas oficiais aplicáveis e homologar o processo de envio;
7. executar pentest, revisão de infraestrutura, continuidade e controles de
   produção no ambiente da instituição.

Esses itens são condições futuras de adaptação, não tarefas omitidas do escopo
sintético definido para esta modernização.
