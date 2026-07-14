# Baseline técnico do estado atual

## Identificação

- Data de execução: 14 de julho de 2026.
- Commit-base: `265cb644f4dbb7e96d1566ecd982260851ade5fb`.
- Referência restaurável: tag anotada `modernization-baseline-20260714`, publicada em `origin`.
- Branch de trabalho: `codex/phase-0-baseline`.
- Ambiente Python utilizado: `venv`, Python 3.13.7, pip 25.2.
- Repositório remoto: `https://github.com/Masteradilio/risco_bancario.git`.

Este documento congela o estado observado antes da modernização. Ele não certifica conformidade regulatória e não converte resultados sintéticos em evidência de desempenho institucional.

## Método

Foram executadas inspeções de Git, manifests, rotas, arquivos, dependências, testes Python, frontend e Docker. Todos os comandos Python usaram `venv\Scripts\python.exe`.

Comandos principais:

```powershell
git rev-parse HEAD
git ls-files
venv\Scripts\python.exe -m pip check
venv\Scripts\python.exe -m pytest --collect-only -q
venv\Scripts\python.exe -m pytest -q backend/bancos_de_dados/tests
venv\Scripts\python.exe -m pytest -q backend/perda_esperada/tests
venv\Scripts\python.exe -m pytest -q backend/prinad/tests
venv\Scripts\python.exe -m pytest -q backend/propensao/tests
venv\Scripts\python.exe -m pytest -q prinad_v2/tests/test_api_integration.py
npm run lint
npm run build
docker compose -f docker/docker-compose.yml config --quiet
docker compose -f docker/docker-compose.yml build
```

## Inventário verificável

### Dimensão do repositório

| Item | Quantidade observada |
|---|---:|
| Arquivos rastreados | 558 |
| Arquivos Python | 149 |
| Arquivos de teste Python | 28 |
| Arquivos TypeScript/TSX | 91 |
| Scripts SQL | 27 |
| Documentos e artefatos textuais/binários | 181 |

### APIs e serviços

| Componente | Implementação observada | Estado do baseline |
|---|---|---|
| Aplicação agregadora | `backend/main.py` | Importa com sucesso e expõe `/health` e rotas do agente. |
| PRINAD | `backend/prinad/src/api.py` | Suíte principal executável; 94 testes passaram e 7 foram ignorados. |
| PRINAD v2 duplicado | `prinad_v2/api/api.py` | Testes de integração não executam por fixtures ausentes. |
| Perda esperada | `backend/perda_esperada/src/api.py` | Módulos unitários executam, mas há 10 falhas de integração. |
| Propensão | `backend/propensao/src/api.py` | Suíte não coleta por dependência Python ausente. |
| Agente de IA | `backend/agente/agent_api.py` | Rotas agregadas importam; fluxo isolado não coleta sem `matplotlib`. |
| File search | `backend/file_search/file_search_api_routes.py` | Router identificado; serviço externo/persistência não foram homologados neste baseline. |

A aplicação agregadora expôs 16 rotas no teste de importação, incluindo documentação OpenAPI, saúde e endpoints de sessões, chat, ferramentas, upload e artefatos do agente.

### Frontends

| Componente | Estado do baseline |
|---|---|
| `frontend/` | Implementação Vite/React ativa segundo o manifesto; build TypeScript falha e lint não encontra o executável ESLint. |
| `frontend-nextjs-backup/` | Cópia Next.js concorrente, com Dockerfile próprio; não é referenciada coerentemente pelo Compose atual. |

### Persistência e dados

- Há 27 scripts SQL sob `backend/bancos_de_dados`, cobrindo ECL, estágios, write-off, auditoria, usuários e agente.
- O Compose não declara serviço de banco de dados, embora módulos dependam de PostgreSQL/PGVector ou MySQL conforme código e documentação.
- `dados/` contém CSVs de cadastro, clientes, modelo, SCR mock e Documento 3040. Esses dados são tratados exclusivamente como sintéticos ou demonstrativos; não houve validação de proveniência institucional.
- Não foi identificada uma camada única de migrations controladas.

### Containers

O Compose declara quatro serviços: `prinad-api`, `ecl-api`, `propensao-api` e `frontend`.

Problemas observados:

1. `docker compose config --quiet` aceita o arquivo, mas informa que a chave `version` está obsoleta.
2. O build não inicia porque o engine Linux do Docker Desktop não está disponível.
3. O serviço `frontend` referencia `frontend/Dockerfile`, arquivo inexistente no estado-base.
4. Os volumes do Compose usam caminhos relativos ao diretório `docker/` que precisam ser reconciliados com os contextos reais.

### Modelos e artefatos

- Há artefatos PRINAD duplicados em `backend/prinad/modelo/` e `prinad_v2/artefatos/`.
- Foram encontrados modelos `ensemble_model.joblib`, preprocessadores, explainer SHAP, nomes de features e relatórios de treinamento.
- Não existe, no estado-base, um registry canônico que prove versão de dados, seed, commit, configuração, aprovação e validade de cada artefato.
- Qualquer AUC, Gini, PD, ECL ou métrica contida nesses artefatos, dashboards ou documentos deve ser interpretada como resultado de dados sintéticos/demonstrativos até que as fases de dados e validação produzam evidência rastreável.

## Resultado dos testes

### Coleta global

`pytest --collect-only -q` encontrou 232 testes e terminou com 8 erros de coleta:

- `backend/prinad/test_diagnosis.py`: import absoluto `classifier` inválido no contexto da raiz;
- seis módulos de Propensão: `ModuleNotFoundError: jose`;
- `backend/scripts/test_agente_flow.py`: `ModuleNotFoundError: matplotlib`.

O `venv` não possui `python-jose` nem `matplotlib`, embora ambos constem em `requirements.txt`. `pip check` não detecta isso porque valida apenas dependências dos pacotes instalados, não a completude do manifesto do projeto.

### Suítes por módulo

| Suíte | Resultado | Observação |
|---|---|---|
| Banco de dados/DDL | 24 aprovados | Execução completa. |
| PRINAD principal | 94 aprovados, 7 ignorados | Execução completa da configuração local do módulo. |
| Perda esperada | 92 aprovados, 10 falharam | Falhas concentradas em imports relativos do pipeline e integração do sistema de cura. |
| Propensão | 6 erros de coleta | Bloqueada pela ausência de `python-jose`. |
| PRINAD v2 | 5 erros de setup | Fixtures `client` e `cpf` não existem no escopo da suíte. |
| Fluxo do agente | erro de coleta global | Bloqueado pela ausência de `matplotlib`. |

Principais falhas de Perda Esperada:

- `pipeline_ecl.py` é importado como módulo solto pelos testes, mas usa imports relativos de pacote;
- `SISTEMA_CURA_DISPONIVEL` fica falso no caminho exercitado;
- as colunas esperadas de cura não são geradas nos testes integrados.

### Frontend

- `npm run lint`: falha porque `eslint` não está instalado/declarado nas dependências de desenvolvimento do frontend ativo.
- `npm run build`: falha com erros TypeScript, incluindo tipo ausente para `window.electronAPI`, imports/variáveis não usados, `ImportMeta.env` sem tipagem e formatters Recharts incompatíveis com valores opcionais.
- Não há script de teste no `package.json` do frontend ativo; os arquivos Playwright existentes não fazem parte de um comando reproduzível do manifesto.

### Serviços

- `import backend.main` foi bem-sucedido.
- O build e a inicialização completa da topologia Docker estão bloqueados pelo engine indisponível e pelos problemas de configuração listados.
- Bancos, autenticação externa, fontes macroeconômicas e integrações LLM não foram iniciados; faltam serviços e configuração reproduzível no baseline.

## Riscos de regressão e duplicação

1. `backend/prinad` e `prinad_v2` mantêm código e artefatos concorrentes.
2. `frontend` e `frontend-nextjs-backup` mantêm implementações concorrentes.
3. Os imports variam entre pacote e manipulação de `sys.path`, tornando o resultado dependente do diretório de execução.
4. `requirements.txt` usa limites mínimos sem lockfile Python, e o ambiente observado está incompleto.
5. Testes regulatórios existentes usam linguagem de conformidade e constantes que ainda carecem de rastreabilidade oficial.
6. Grandes CSVs e artefatos binários estão no repositório sem lineage canônico.
7. O cálculo e os dashboards contêm métricas sintéticas ou mockadas que ainda precisam ser rotuladas de forma uniforme na Tarefa 0.3.

## Decisões e limitações do baseline

- O baseline registra falhas preexistentes; não altera fórmulas, dependências ou código funcional.
- A restauração do estado rastreado é feita pela tag `modernization-baseline-20260714`.
- Resultados aprovados demonstram apenas comportamento da suíte atual com dados sintéticos/demonstrativos; não demonstram correção quantitativa, conformidade regulatória ou desempenho em produção.
- As falhas serão tratadas nas tarefas correspondentes do backlog, sem transformar a Tarefa 0.1 em uma refatoração ampla.

## Conclusão

O estado anterior está preservado e restaurável. Há uma lista reproduzível do que funciona, do que falha e do que não pôde ser iniciado. A base é ampla, mas a regressão global não está verde, o ambiente não é reproduzível e existem duplicações arquiteturais relevantes. Este é o ponto de comparação oficial para as próximas tarefas.
