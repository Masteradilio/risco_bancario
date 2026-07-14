# Mapa de duplicações e fontes de verdade

## Objetivo e método

Este documento registra o estado encontrado na Tarefa 1.1 do backlog. Ele não
homologa regras quantitativas existentes: define fontes canônicas de transição,
o destino arquitetural e a ordem segura de migração. A comparação foi feita por
pontos de entrada, imports, rotas, testes, hashes SHA-256 e diferenças de código.

Data do inventário: 14 de julho de 2026. Commit-base da modernização:
`265cb644f4dbb7e96d1566ecd982260851ade5fb`.

## Decisão geral

Há dois níveis de fonte de verdade:

1. **Canônica de transição:** implementação que permanece executável enquanto
   a reconstrução avança. Ela preserva compatibilidade, mas não transforma
   regras hard-coded ou resultados sintéticos em evidência regulatória.
2. **Canônica de destino:** pacote `src/` descrito no relatório de auditoria.
   Regras materiais só serão canônicas depois de tipadas, versionadas,
   configuráveis, testadas e rastreáveis.

Nenhuma árvore concorrente deve receber novas funcionalidades. Código antigo só
pode ser removido após teste de caracterização, migração de consumidores e uma
regressão equivalente ou superior.

## Inventário PRINAD

### Cópias encontradas

| Conceito | `backend/prinad` | `prinad_v2` | Diagnóstico |
|---|---|---|---|
| API | `src/api.py` e `src/api_monitoring.py` | `api/api.py` e `api/api_monitoring.py` | Mesmas responsabilidades, com imports e detalhes divergentes. |
| Modelo e preparação | 10 módulos em `src/` | os mesmos 10 nomes em `modelos/` | Estrutura quase espelhada; todos os pares diferem no hash, embora nove pares tenham a mesma contagem de linhas. |
| Classificador | `src/classifier.py` | `modelos/classifier.py` | Divergiu em carregamento de artefatos, readiness, tratamento de fallback e correções posteriores. |
| Artefatos | `modelo/` | `artefatos/` | Cinco binários são byte a byte idênticos; três relatórios JSON divergem. |
| Testes | seis arquivos em `backend/prinad/tests/` | um teste de integração em `prinad_v2/tests/` | A suíte mantida e aprovada está em `backend/prinad/tests/`; a cópia v2 depende de fixtures ausentes. |
| Documentação | `backend/prinad/docs/` | `prinad_v2/docs/`, DOCX e PDF | Materiais sobrepostos e históricos, sem contrato único de versão. |

Artefatos idênticos por SHA-256 nas duas árvores:
`ensemble_model.joblib`, `feature_names.joblib`, `preprocessor.joblib`,
`shap_explainer.joblib` e `training_metrics.joblib`. Os arquivos
`balancing_comparison_report.json`, `data_quality_report.json` e
`optimization_report.json` possuem conteúdo diferente.

### Fonte canônica

- **Transição:** `backend/prinad`, pois é a árvore usada pelo Compose, contém a
  suíte de regressão mantida e já integra `shared.utils`.
- **Destino:** `src/models/pd/` para modelo/calibração, `src/application/` para
  casos de uso e API e um repositório versionado de artefatos definido nas fases
  de MLOps. O nome PRINAD poderá permanecer como produto ou adaptador, não como
  segundo núcleo quantitativo.
- **Legado:** `prinad_v2` fica congelado até ser movido para `legacy/` ou
  removido depois da migração. Seus três relatórios divergentes devem ser
  preservados apenas como evidência histórica, nunca escolhidos implicitamente.

## Inventário de frontends

| Aspecto | `frontend` | `frontend-nextjs-backup` |
|---|---|---|
| Stack | React 18, Vite 6, React Router | React 19, Next.js 16 App Router |
| Páginas | 15 páginas de produto, além de componentes auxiliares | 16 rotas `page.tsx` |
| Cobertura comum | dashboard, PRINAD, ECL, estágios, cálculo, LGD, forward-looking, cura, write-off, exportação, grupos, pipeline, propensão, auditoria, relatórios, configurações e administração | As mesmas jornadas, com rota adicional/alternativa de IA |
| Execução documentada | README orienta `cd frontend` e `npm run dev` | Não é o fluxo de desenvolvimento documentado |
| Estado operacional | Tem testes E2E e integrações mais recentes, mas build/lint já estavam vermelhos no baseline | Possui Dockerfile próprio, mas está nomeado como backup e não é referenciado de forma coerente pelo Compose |

O Compose tenta construir `frontend/Dockerfile`, que não existe, e ao mesmo
tempo usa variáveis `NEXT_PUBLIC_*`, incompatíveis com o frontend Vite atual.
Isso é uma inconsistência de implantação, não evidência de que o backup Next.js
seja a aplicação principal.

### Fonte canônica

- **Transição e destino:** `frontend` (React/Vite). Todas as novas correções e
  integrações devem ocorrer nessa árvore.
- **Legado:** `frontend-nextjs-backup` fica congelado e será movido para
  `legacy/` após conferir se há comportamento exclusivo útil. Componentes como
  o laudo PDF devem ser portados por requisito e teste, não copiados em massa.
- O Compose será corrigido contra a árvore canônica em tarefa própria, sem
  manter configuração híbrida Vite/Next.js.

## Constantes e regras duplicadas

### Catálogo, limites, LGD e EAD

`shared/utils.py` hoje concentra `PRODUTOS_PF`, `LGD_POR_PRODUTO`,
`IMPACTO_GARANTIA`, `LGD_POR_GARANTIA`, `CCF_POR_PRODUTO`, limites de renda,
rating, PD, estágio e cura. Ele é importado por PRINAD, ECL e Propensão, mas
mistura utilidades técnicas, premissas de produto, regras de decisão e alegadas
premissas regulatórias.

Há divergência dentro do próprio arquivo: por exemplo, consignação possui LGD
de produto 0,35, `lgd_base` de garantia 0,12 e outra LGD de garantia 0,25.
`pipeline_ecl.py` ainda possui fallback local 0,45. Parâmetros de propensão,
monitoramento, grupos homogêneos, reestruturação e triggers também aparecem
como constantes de classe ou dicionários locais.

**Canônica de transição:** `shared/utils.py` somente para consumidores que já o
importam; fallbacks locais não podem ser promovidos a regra. **Canônica de
destino:** schemas versionados de configuração da Tarefa 1.3, separados por
domínio (`pd`, `lgd`, `ead`, `sicr`, cenários e políticas). O pacote de domínio
da Tarefa 1.2 fornecerá tipos e invariantes, não números mágicos.

### Rating e PD

Foram encontradas três representações concorrentes:

- `shared/utils.py`: `PRINAD_TO_RATING` e `PD_POR_RATING`;
- `RatingMapper.RATING_CONFIG` nos dois classificadores copiados;
- outro `RatingMapper` em cada cópia de `train_model.py`.

Além disso, `backend/propensao/src/limit_optimizer.py` considera rating D a
partir de PRINAD 90, enquanto os mapeamentos compartilhado e do classificador
iniciam D em 85. A PD por rating usa faixas hard-coded e maturidade média fixa
de cinco anos, sem artefato de calibração versionado.

**Canônica de transição:** limites de faixa em `shared/utils.py`, por serem o
único ponto já compartilhado entre módulos; resultados continuam
demonstrativos. **Canônica de destino:** `src/models/pd/` mais configuração
versionada. A aplicação não poderá derivar estágio diretamente de um rating ou
score sem passar pelo serviço canônico de SICR/staging.

### Estágio e SICR

As regras atuais são materialmente divergentes:

| Implementação | Stage 2 | Stage 3 |
|---|---|---|
| `shared.utils.get_ifrs9_stage` | PRINAD de 20 até abaixo de 70 | PRINAD a partir de 70 |
| `shared.utils.get_stage_from_criteria` | atraso a partir de 31 dias ou downgrade de 2 notches | atraso a partir de 91 dias ou eventos qualitativos |
| classificadores PRINAD | atraso a partir de 30 dias ou PRINAD a partir de 50 | atraso a partir de 90 dias ou PRINAD a partir de 85 |
| `backend/perda_esperada/src/modulo_triggers_estagios.py` | faixas absolutas distintas de PD por modalidade | reestruturação textual pode levar ao Stage 3 |
| módulos de pipeline/Propensão | combinações próprias de score, atraso, rating e flags | combinações próprias, nem sempre com a mesma fronteira inclusiva |

Nenhuma dessas funções é declarada fonte quantitativa definitiva. **Canônica de
transição:** `get_stage_from_criteria` apenas como contrato de compatibilidade,
porque é a versão mais centralizada e aceita eventos qualitativos; seus
limiares ainda precisam de justificativa e testes. **Canônica de destino:**
`src/domain/staging/` e `src/models/sicr/`, com política versionada, data de
vigência, inputs da concessão e da data-base, overrides separados e trilha de
decisão.

## Matriz final de fontes de verdade

| Conceito | Canônica de transição | Canônica de destino | Legado congelado |
|---|---|---|---|
| PRINAD/API | `backend/prinad` | `src/models/pd` + `src/application` | `prinad_v2` |
| Artefatos PRINAD | `backend/prinad/modelo` | registro versionado das fases de MLOps | `prinad_v2/artefatos` |
| Frontend | `frontend` | `frontend` saneado | `frontend-nextjs-backup` |
| Rating e PD | `shared/utils.py` | `src/models/pd` + config versionada | mappers locais |
| Staging/SICR | `shared.utils.get_stage_from_criteria` como compatibilidade | `src/domain/staging` + `src/models/sicr` | funções por score e triggers locais |
| ECL | `backend/perda_esperada` | `src/ecl` | fórmulas escalares e fallbacks espalhados |
| LGD/EAD | imports existentes de `shared/utils.py` | `src/models/lgd`, `src/models/ead` + config | defaults locais |
| Propensão | `backend/propensao` | adaptador/aplicação fora do núcleo ECL | regras que duplicam rating/staging |
| API agregadora | `backend/main.py` para agente; APIs modulares atuais para produtos | `src/application/api` | servidores concorrentes após migração |

## Plano de migração do legado

1. **Caracterizar antes de mover:** capturar testes e contratos dos pontos de
   entrada canônicos de transição, inclusive casos limítrofes de rating e
   estágio.
2. **Criar o domínio alvo:** executar a Tarefa 1.2 sem dependência de FastAPI,
   DataFrame, CSV, banco ou frontend.
3. **Externalizar regras:** executar a Tarefa 1.3, com schema, vigência, versão,
   justificativa e hash. Nenhum valor divergente será escolhido silenciosamente.
4. **Adaptar consumidores:** fazer PRINAD, ECL, Propensão, agente, APIs e frontend
   chamarem os serviços canônicos; manter adaptadores com avisos de depreciação
   quando necessário.
5. **Consolidar artefatos:** manter uma única cópia referenciada por manifesto e
   hash. Relatórios divergentes tornam-se evidência histórica identificada.
6. **Congelar e isolar:** mover `prinad_v2` e `frontend-nextjs-backup` para
   `legacy/` somente após equivalência funcional e busca por imports/referências.
7. **Remover com evidência:** apagar o legado apenas quando regressão, cobertura,
   documentação e Compose estiverem verdes e não houver consumidor ativo.

## Guardrails para as próximas tarefas

- Não adicionar regra material a `shared/utils.py`, às cópias PRINAD ou ao
  frontend legado.
- Não usar o número da versão, o nome da pasta ou um comentário regulatório como
  critério de autoridade.
- Não resolver divergências pela média ou pelo valor mais conservador sem
  requisito, fonte, data de vigência e teste.
- Preservar resultados históricos com hash e origem; não tratá-los como
  validação de modelo.
- Atualizar este mapa se uma investigação posterior encontrar novo consumidor
  ou implementação concorrente.
