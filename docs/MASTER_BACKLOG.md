# MASTER BACKLOG — Evolução IFRS 9 / CMN 4.966

## Projeto `risco_bancario`

**Documento de execução obrigatório para o Codex**  
**Documento de contexto obrigatório:** `docs/PROJECT_AUDIT_AND_TARGET_STATE.md`  
**Data de criação:** 13 de julho de 2026

---

## 1. Missão

Transformar o repositório `Masteradilio/risco_bancario` em uma plataforma moderna, reproduzível, auditável e tecnicamente defensável para:

- modelagem de PD, LGD, EAD e SICR;
- cálculo de perda esperada por período e cenário;
- tratamento de Stage 1, Stage 2, Stage 3 e POCI;
- aplicação dos requisitos de impairment da IFRS 9;
- atendimento demonstrável aos requisitos aplicáveis da Resolução CMN nº 4.966/2021 e normas complementares;
- aplicação separada de pisos, overlays e critérios regulatórios;
- geração e pré-validação do Documento 3040;
- governança, validação, monitoramento, segurança e auditoria;
- demonstração completa usando apenas dados sintéticos.

O objetivo é obter nota 10/10 em arquitetura, modelagem quantitativa, cálculo de ECL, validação, regulação, segurança, experiência de uso e qualidade de portfólio.

---

## 2. Instruções permanentes de execução para o Codex

### 2.1 Leitura e planejamento

Antes de modificar o código:

- [x] Ler integralmente `docs/PROJECT_AUDIT_AND_TARGET_STATE.md`.
- [x] Ler integralmente este `docs/MASTER_BACKLOG.md`.
- [x] Inspecionar o código relacionado à tarefa.
- [x] Identificar dependências, duplicações e riscos de regressão.
- [x] Registrar no próprio backlog o plano específico da tarefa, quando necessário.

### 2.2 Fluxo obrigatório por tarefa

Para cada tarefa:

1. criar ou reutilizar uma branch descritiva;
2. escrever ou atualizar testes antes ou junto da implementação;
3. implementar a menor mudança coerente;
4. executar testes unitários e de integração relacionados;
5. executar a suíte de regressão definida para a fase;
6. atualizar documentação, ADRs, model cards e matriz regulatória;
7. atualizar os checkboxes deste backlog;
8. atualizar `CHANGELOG.md`;
9. registrar limitações e decisões;
10. fazer commit descritivo;
11. fazer push da branch;
12. não marcar a tarefa como concluída enquanto os critérios de aceite não forem atendidos.

### 2.3 Regras de qualidade

- [x] Não inventar regra regulatória.
- [x] Não declarar certificação oficial.
- [x] Não usar dados reais ou PII.
- [x] Não usar variáveis latentes do gerador sintético como features.
- [x] Não preencher dados regulatórios ausentes com defaults silenciosos.
- [x] Não usar o conjunto de teste para treino, tuning, calibração ou seleção de threshold.
- [x] Não manter duas implementações canônicas da mesma regra.
- [x] Usar `Decimal` para valores monetários no domínio e definir política de arredondamento.
- [x] Versionar dados, modelos, cenários, políticas, regras e resultados.
- [x] Garantir determinismo por seed e configuração.
- [x] Tratar toda integração externa como dependência versionada e observável.

### 2.4 Definition of Done global

Uma tarefa somente pode ser concluída quando:

- [x] código implementado;
- [x] testes aprovados;
- [x] documentação atualizada;
- [x] rastreabilidade regulatória atualizada, quando aplicável;
- [x] nenhuma regressão conhecida;
- [x] logs e erros tratados;
- [x] commit e push realizados;
- [x] backlog e changelog atualizados.

---

# FASE 0 — Governança, escopo e baseline verificável

## Objetivo

Congelar o estado atual, estabelecer o escopo oficial e impedir que o projeto continue fazendo afirmações de conformidade sem evidência.

## Tarefa 0.1 — Criar baseline técnico

### Subtarefas

- [x] Criar tag ou branch de preservação do estado atual.
- [x] Registrar o commit-base da modernização.
- [x] Executar e registrar a suíte atual de testes.
- [x] Registrar testes quebrados, dependências ausentes e serviços que não iniciam.
- [x] Inventariar APIs, frontends, bancos, containers, modelos e artefatos.
- [x] Gerar relatório `docs/baseline/CURRENT_STATE_BASELINE.md`.

### Critérios de aceite

- [x] O estado anterior pode ser restaurado.
- [x] Existe uma lista verificável do que funciona e do que falha.
- [x] Nenhuma métrica do baseline é apresentada sem identificar sua origem sintética.

### Registro de execução

- Data: 14 de julho de 2026.
- Commit-base: `265cb644f4dbb7e96d1566ecd982260851ade5fb`.
- Tag de preservação publicada: `modernization-baseline-20260714`.
- Branch: `codex/phase-0-baseline`.
- Evidência: `docs/baseline/CURRENT_STATE_BASELINE.md`.
- Resultado: baseline concluído; regressões preexistentes e bloqueios de ambiente foram registrados sem alteração do código funcional.

## Tarefa 0.2 — Formalizar escopo do produto

### Subtarefas

- [x] Definir o escopo principal como IFRS 9 impairment/ECL e CMN 4.966 aplicável.
- [x] Identificar extensões de classificação e mensuração, POCI, compromissos e garantias.
- [x] Definir o que permanece fora do escopo inicial, especialmente hedge accounting, se não for implementado.
- [x] Criar `docs/SCOPE.md` com itens incluídos, excluídos e futuros.
- [x] Criar glossário oficial em `docs/GLOSSARY.md`.

### Critérios de aceite

- [x] O README não sugere cobertura integral da IFRS 9 quando o escopo for apenas impairment.
- [x] Cada módulo possui propósito e fronteira definidos.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `docs/SCOPE.md`, `docs/GLOSSARY.md` e seção de escopo do `README.md`.
- Decisão: impairment/ECL é o núcleo; classificação e mensuração são extensão limitada; hedge accounting permanece fora do escopo inicial.
- Fontes de enquadramento: páginas oficiais da IFRS Foundation, Resolução CMN nº 4.966/2021 e Resolução BCB nº 352/2023, consultadas na data acima.

## Tarefa 0.3 — Corrigir linguagem de conformidade

### Subtarefas

- [x] Remover selos e frases como “100% compliant”, “validador oficial” e equivalentes.
- [x] Substituir por linguagem de alinhamento, referência e preparação para homologação.
- [x] Marcar dashboards, métricas e datasets como sintéticos.
- [x] Remover percentuais autodeclarados de conformidade sem metodologia.
- [x] Corrigir exemplos matemáticos incorretos na documentação.

### Critérios de aceite

- [x] Nenhum arquivo promete certificação institucional.
- [x] Toda demonstração informa que usa dados sintéticos.

### Registro de execução

- Data: 14 de julho de 2026.
- Escopo da varredura: README, documentação autoral, APIs, agente, bancos, frontends ativo e legado, testes e relatórios gerados; textos oficiais arquivados foram preservados como fontes.
- Guardrail: a ferramenta `validar_conformidade` mantém a assinatura por compatibilidade, mas retorna `NAO_AVALIADO` até existirem fontes, testes e evidências versionadas.
- Matemática: exemplos escalares foram identificados como didáticos; erros de ordem de grandeza foram corrigidos e Stage 3 passou a ser descrito por cash shortfall descontado.
- Evidência: varredura automatizada sem alegações proibidas; 118 testes aprovados e 7 ignorados; sintaxe Python e contratos de guardrail aprovados.
- Limitação preexistente: o build TypeScript permanece vermelho pelas mesmas categorias registradas em `docs/baseline/CURRENT_STATE_BASELINE.md`.

---

# FASE 1 — Racionalização do repositório e arquitetura canônica

## Objetivo

Eliminar duplicações, organizar o domínio e criar uma base estável para a reconstrução quantitativa.

## Tarefa 1.1 — Mapear duplicações e fontes de verdade

### Subtarefas

- [x] Comparar `backend/prinad`, `prinad_v2` e demais cópias.
- [x] Comparar frontend atual com `frontend-nextjs-backup`.
- [x] Identificar constantes duplicadas em `shared/utils.py` e módulos locais.
- [x] Mapear regras divergentes de rating, PD e estágio.
- [x] Criar `docs/architecture/DUPLICATION_MAP.md`.

### Critérios de aceite

- [x] Cada conceito possui uma implementação canônica definida.
- [x] O plano de migração do legado está documentado.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregável: `docs/architecture/DUPLICATION_MAP.md`.
- Decisão: `backend/prinad` e `frontend` são as fontes canônicas de transição; `prinad_v2` e `frontend-nextjs-backup` ficam congelados como legado até a migração comprovada.
- Destino: o pacote `src/` será a fonte canônica definitiva; regras materiais serão tipadas e externalizadas em configuração versionada nas Tarefas 1.2 e 1.3.
- Evidência: comparação de pontos de entrada, imports, rotas, testes, hashes SHA-256, artefatos e regras divergentes de rating, PD, LGD, EAD e estágio.
- Guardrail: nenhuma divergência quantitativa foi resolvida silenciosamente nesta tarefa de inventário.

## Tarefa 1.2 — Criar arquitetura de domínio

### Subtarefas

- [x] Criar pacote `src/` com os domínios definidos no relatório de auditoria.
- [x] Criar modelos tipados para cliente, contraparte, contrato, garantia, snapshot, cenário e resultado ECL.
- [x] Usar `Decimal` para moeda.
- [x] Definir convenções de datas, timezone, percentuais e arredondamento.
- [x] Criar exceções de domínio explícitas.
- [x] Criar ADR da arquitetura.

### Critérios de aceite

- [x] O domínio não depende de FastAPI, banco, frontend ou arquivos CSV.
- [x] Tipos e invariantes são testados.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: arquitetura de pacotes em `src/`, modelos em `src/domain`, contrato de resultado em `src/ecl/calculation` e `docs/architecture/ADR-001-domain-architecture.md`.
- Convenções: BRL em `Decimal`, centavos com `ROUND_HALF_EVEN`, percentuais como frações entre zero e um, datas de negócio em `date` e timestamps aware normalizados para UTC.
- Isolamento: inspeção AST confirmou ausência de imports de FastAPI, Pydantic, pandas, NumPy, banco e CSV em `src/domain`.
- Evidência: 8 testes de domínio aprovados, cobrindo tipos, imutabilidade, arredondamento, percentuais, datas, cenários, snapshots e resultados ECL.
- Limite: thresholds e parâmetros quantitativos não foram migrados; serão configuração versionada na Tarefa 1.3.

## Tarefa 1.3 — Configuração e regras fora do código

### Subtarefas

- [x] Criar schemas versionados de configuração.
- [x] Migrar thresholds, pesos, cenários e políticas para YAML/JSON/Pydantic.
- [x] Registrar data de vigência, autor, versão e justificativa.
- [x] Impedir carregamento de configuração inválida.
- [x] Criar hash da configuração usada em cada execução.

### Critérios de aceite

- [x] Nenhuma regra material depende de número mágico disperso.
- [x] O resultado ECL identifica a versão exata da configuração.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `config/risk_policy/2026.07.1.json`, schema Pydantic estrito em `src/infrastructure/configuration` e `docs/configuration/RISK_POLICY.md`.
- Migração: rating/PD, staging, LGD, CCF e cenários passaram a possuir fonte efetiva única; `shared/utils.py` e o gerenciador legado de cenários funcionam como adaptadores de compatibilidade.
- Governança: política registra schema, versão, vigência, autor, justificativa, fontes e status demonstrativo; nenhuma premissa foi promovida a validada.
- Rastreabilidade: loader gera SHA-256 determinístico e `ECLResult` exige versão e hash da configuração.
- Evidência: 18 testes de configuração/domínio, 28 testes de cenários ECL e 94 testes PRINAD aprovados; 7 testes PRINAD ignorados conforme baseline.
- Limitação preexistente: a coleta isolada de testes de Propensão continua bloqueada pela ausência de `python-jose` no venv, já registrada no baseline e destinada à Tarefa 1.4.

## Tarefa 1.4 — Padronizar tooling

### Subtarefas

- [x] Definir versão oficial do Python.
- [x] Migrar dependências para `pyproject.toml`.
- [x] Configurar Ruff, Black, MyPy/Pyright e Pytest.
- [x] Configurar cobertura mínima progressiva.
- [x] Criar Makefile ou scripts equivalentes.
- [x] Criar comando único de setup e teste.

### Critérios de aceite

- [x] Ambiente local sobe de forma reproduzível.
- [x] Lint, type checking e testes executam em um comando.

### Registro de execução

- Data: 14 de julho de 2026.
- Runtime oficial: CPython 3.13.7, registrado em `.python-version` e limitado a `>=3.13,<3.14` no `pyproject.toml`.
- Dependências: produção e grupo `dev` migrados para `pyproject.toml`; `requirements.txt` permanece apenas como entrada de compatibilidade.
- Comandos: `scripts/setup.ps1` cria/atualiza o venv; `scripts/quality.ps1` executa Black, Ruff, MyPy, cobertura e regressão estável.
- Cobertura: piso inicial de 70%; núcleo canônico atingiu 90,37% nesta execução.
- Evidência: setup editável concluído; Black, Ruff e MyPy verdes; 18 testes canônicos e 118 testes de regressão aprovados, com 7 ignorados.
- Correção de ambiente: `python-jose` e `matplotlib`, ausentes no baseline, foram instalados pelo setup canônico.

---

# FASE 2 — Base regulatória e matriz de rastreabilidade

## Objetivo

Transformar requisitos normativos em itens testáveis, versionados e auditáveis.

## Tarefa 2.1 — Catálogo de fontes oficiais

### Subtarefas

- [x] Criar `docs/regulatory/SOURCE_REGISTER.md`.
- [x] Registrar IFRS 9 vigente, CMN 4.966 consolidada, BCB 352 vigente e documentação Doc3040.
- [x] Registrar data de consulta e vigência.
- [x] Definir processo de atualização regulatória.
- [x] Não copiar material protegido sem autorização.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregável: `docs/regulatory/SOURCE_REGISTER.md`.
- Fontes: páginas primárias da IFRS Foundation e do Banco Central do Brasil, com links, consulta, estado observado, uso e limitações.
- Processo: revisão mensal e pré-release, comparação de vigência/normas vinculadas, manifesto e SHA-256 para artefatos operacionais e atualização da rastreabilidade.
- Direito autoral: nenhum texto integral protegido da IFRS foi copiado; o catálogo mantém somente referência e síntese própria.
- Achado: a página consultada do Doc3040 lista XSD do documento 3045; nenhum XSD 3040 foi presumido.

## Tarefa 2.2 — Matriz de requisitos

### Subtarefas

- [x] Criar `docs/regulatory/TRACEABILITY_MATRIX.csv` ou formato tabular equivalente.
- [x] Mapear impairment, ECL, SICR, default, cura, write-off, forward-looking, desconto, POCI e disclosure.
- [x] Mapear requisitos CMN/BCB aplicáveis.
- [x] Mapear Documento 3040, XSD e críticas.
- [x] Vincular requisito a código, teste e evidência.

### Critérios de aceite

- [x] Todo requisito implementado possui teste associado.
- [x] Todo requisito não aplicável possui justificativa.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregável: `docs/regulatory/TRACEABILITY_MATRIX.csv`, com 22 requisitos atômicos e identificadores estáveis.
- Cobertura: impairment/ECL, SICR, default, cura, write-off, forward-looking, desconto, POCI, disclosure, CMN 4.966, BCB 352 e Documento 3040.
- Estados: requisitos foram classificados como planejados, parciais ou não aplicáveis; nenhum requisito quantitativo foi declarado implementado sem teste e evidência.
- Não aplicáveis: hedge accounting e transmissão oficial do Documento 3040 possuem justificativa e evidência de escopo.
- Guardrail Doc3040: a matriz exige proveniência do schema e registra que a página consultada lista XSD 3045, não um XSD 3040.
- Evidência: 5 testes de contrato da matriz aprovados, cobrindo unicidade, tópicos, fontes, evidências parciais e justificativas de não aplicabilidade.

## Tarefa 2.3 — Testes regulatórios executáveis

### Subtarefas

- [x] Criar estrutura de testes por requisito.
- [x] Adicionar identificador regulatório nos nomes/metadados dos testes.
- [x] Gerar relatório automático de cobertura regulatória.
- [x] Bloquear release quando requisito obrigatório estiver sem evidência.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: testes em `tests/regulatory`, gerador `src/regulatory/traceability/report.py`, comando `scripts/regulatory-report.ps1` e `docs/regulatory/TESTING.md`.
- Identificação: evidências parciais usam ID no nome e marcador Pytest `regulatory(requirement_id)`.
- Relatório: cobre as 22 linhas da matriz e lista contagens, status e bloqueadores.
- Gate: `--enforce` retorna falha enquanto requisito aplicável não estiver implementado com código, teste existente e evidência.
- Estado esperado: 20 bloqueadores permanecem; o gate foi testado e bloqueou corretamente a release nesta fase.
- Evidência: 11 testes regulatórios aprovados; comando de qualidade passou a incluí-los.

---

# FASE 3 — Fábrica de dados sintéticos longitudinais

## Objetivo

Criar dados realistas, temporais e sem leakage para suportar todas as fases do projeto.

## Tarefa 3.1 — Modelo causal e temporal do gerador

### Subtarefas

- [x] Definir entidades e relacionamentos.
- [x] Definir variáveis latentes internas ao gerador.
- [x] Garantir que variáveis latentes não sejam exportadas para modelagem.
- [x] Definir ciclos macroeconômicos.
- [x] Definir dinâmica de renda, emprego, utilização, atraso e default.
- [x] Definir mecanismo de recuperação, garantia, renegociação e cura.
- [x] Criar documento `docs/data/SYNTHETIC_DATA_DESIGN.md`.

### Critérios de aceite

- [x] O target decorre de eventos futuros, não de uma classe estática usada para gerar features.
- [x] O gerador é separado do pipeline de modelagem.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregável: `docs/data/SYNTHETIC_DATA_DESIGN.md`.
- Causalidade: snapshots usam somente estado disponível até `t`; default é sorteado mensalmente para períodos futuros e o target é derivado após a simulação.
- Anti-leakage: latentes ficam em estado privado e exportações usam allowlists; o builder de modelagem só consome tabelas públicas.
- Temporalidade: horizonte padrão de 120 meses, safras/snapshots mensais e regimes de expansão, estabilidade, recessão e recuperação.
- Escopo: renda, emprego, utilização, pagamento, atraso, default, garantias, renegociação, cura, redefault, cobrança, recuperação e write-off.
- Limite: distribuições e coeficientes serão configuração versionada nas tarefas de implementação; não representam instituição real.
- Evidência: 3 testes de contrato do desenho aprovados e incluídos no comando geral de qualidade.

## Tarefa 3.2 — Gerar população e contratos

### Subtarefas

- [x] Gerar clientes PF e PJ sintéticos.
- [x] Gerar grupos econômicos e contrapartes.
- [x] Gerar produtos amortizados e rotativos.
- [x] Gerar originação, prazo, taxa efetiva, cronograma e garantias.
- [x] Gerar compromissos de crédito e garantias financeiras.
- [x] Gerar POCI e contratos adquiridos com problema de crédito.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/data/synthetic/population.py`, API em `src/data/synthetic/__init__.py` e `docs/data/SYNTHETIC_POPULATION.md`.
- Cobertura: PF/PJ, grupos, oito produtos, facilidades amortizadas/rotativas, compromissos, garantias financeiras, colaterais e POCI.
- Reprodutibilidade: seed mestre com substreams separadas para população e contratos; registros imutáveis e moeda em `Decimal`.
- Reconciliação: cronogramas amortizados liquidam principal exatamente e terminam com saldo zero na data de vencimento.
- Evidência: 7 testes aprovados; carteira de teste com 16 clientes, 32 contratos, 1.536 parcelas e 8 garantias.
- Limite: persistência, snapshots e eventos posteriores permanecem nas Tarefas 3.3–3.6.

## Tarefa 3.3 — Gerar snapshots mensais

### Subtarefas

- [x] Gerar 8 a 10 anos de snapshots.
- [x] Gerar saldo, limite, utilização, parcelas, atraso e rating.
- [x] Gerar mudanças de risco antes do default.
- [x] Gerar safras e coortes.
- [x] Gerar eventos de modificação e renegociação.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/data/synthetic/longitudinal.py`, API pública atualizada e `docs/data/SYNTHETIC_LONGITUDINAL.md`.
- Janela: snapshots mensais entre janeiro de 2016 e dezembro de 2025, limitados à vida ativa de cada contrato.
- Estado: saldo, limite, utilização, prestação, pagamento, atraso, score observável, rating canônico, safra e meses desde originação.
- Modificações: extensão de prazo registra termos anterior/novo, data, tipo e concessão sem apagar histórico.
- Anti-leakage: saídas não contêm target, default futuro nem campos latentes; defaults serão eventos posteriores na Tarefa 3.4.
- Evidência: 7 testes aprovados; carteira de teste com 2.431 snapshots, 62 safras, 10 ratings, 6 modificações e atraso máximo de 120 dias.

## Tarefa 3.4 — Gerar defaults, cobranças e recuperações

### Subtarefas

- [x] Gerar datas de default.
- [x] Gerar fluxos de recuperação mensais.
- [x] Gerar execução de garantias.
- [x] Gerar custos judiciais e operacionais.
- [x] Gerar curas e redefaults.
- [x] Gerar write-offs e recuperações pós-baixa.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/data/synthetic/events.py`, API pública atualizada e `docs/data/SYNTHETIC_CREDIT_EVENTS.md`.
- Default: evento posterior ao snapshot observável, com exposição na data e gatilho rastreável; redefaults permanecem identificados separadamente.
- Recuperação: seis fluxos mensais por default inicial, execução de garantia limitada à exposição e custos operacionais/judiciais explícitos.
- Ciclo de vida: cura com período de observação, redefault posterior, write-off reconciliado e recuperação pós-baixa preservada.
- Anti-leakage: os eventos são derivados depois do histórico e as tabelas públicas não exportam campos latentes.
- Evidência: 7 testes aprovados; carteira fixa com 25 defaults iniciais, 7 redefaults, 186 recuperações, 12 curas e 20 write-offs após backstop em 91 DPD e cobertura longitudinal.

## Tarefa 3.5 — Gerar macroeconomia e cenários

### Subtarefas

- [x] Gerar cenário observado histórico.
- [x] Gerar cenários base, otimista, pessimista e stress.
- [x] Gerar trajetórias mensais de PIB, inflação, juros, desemprego e endividamento.
- [x] Introduzir relações não lineares com risco.
- [x] Versionar pesos e trajetórias.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/data/synthetic/macroeconomics.py`, configuração `1.0.0`, API pública e `docs/data/SYNTHETIC_MACROECONOMICS.md`.
- Histórico: 120 pontos mensais sintéticos de janeiro de 2016 a dezembro de 2025, com regimes autocorrelacionados e cinco variáveis macroeconômicas.
- Forecast: trajetórias mensais de 60 meses para `upside`, `base`, `downside` e `stress`; stress permanece sensibilidade não ponderada.
- Versionamento: pesos 15%/70%/15% preservam a política canônica; versão e SHA-256 da configuração acompanham a saída.
- Não linearidade: pressão de risco usa termos quadráticos além de patamares adversos e cresce mais que proporcionalmente no stress.
- Limitação: dados e trajetórias são hipóteses sintéticas demonstrativas, não séries oficiais, forecasts ou calibração institucional.
- Evidência: 7 testes aprovados, cobrindo reprodução, periodicidade, trajetórias, pesos, severidade, não linearidade e anti-leakage.

## Tarefa 3.6 — Datasets de modelagem

### Subtarefas

- [x] Construir observation dates.
- [x] Construir target de default em 12 meses.
- [x] Construir targets de hazard mensal.
- [x] Construir datasets de LGD e EAD.
- [x] Construir datasets de SICR.
- [x] Separar treino, validação, calibração, OOT e backtesting por tempo.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/data/synthetic/modeling.py`, API pública, testes e `docs/data/SYNTHETIC_MODELING_DATASETS.md`.
- PD/hazard: observações mensais point-in-time até dezembro de 2025; targets maduros vão até 2024 e 2025 permanece nulo para backtesting futuro.
- LGD/EAD: resultados reconciliados por default, LGD realizada não descontada explicitamente nomeada e CCF para exposições com limite não utilizado.
- SICR: target futuro combina default, atraso de 31 dias e deterioração mínima de dois graus contra a originação.
- Splits: revisados na Tarefa 5.4 para treino até 2018, validação 2020, calibração 2022, OOT 2024 e backtesting futuro 2025, com embargos anuais.
- Anti-leakage: tabelas de PD/SICR não expõem datas de default, recuperação, EAD realizada ou campos latentes como features.
- Evidência atual após Tarefa 5.4: 1.026 linhas PD/SICR sem POCI, 844 targets maduros, 117 defaults 12m, 10 hazards mensais e 148 SICR positivos na carteira fixa.

## Tarefa 3.7 — Qualidade e anti-leakage

### Subtarefas

- [x] Criar testes de integridade referencial.
- [x] Criar testes de consistência temporal.
- [x] Criar detector de feature futura.
- [x] Criar análise de distribuição e correlação.
- [x] Criar data cards e dicionário de dados.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/data/synthetic/quality.py`, testes, `docs/data/DATA_CARD_SYNTHETIC_FACTORY.md` e `docs/data/DATA_DICTIONARY.md`.
- Integridade: referências entre clientes, contratos, snapshots, defaults e eventos são verificadas; órfãos bloqueiam o relatório.
- Temporalidade: duplicidade mensal, recuperação/cura anterior ao default, reconciliação, target maduro ausente e target futuro prematuro são detectados.
- Anti-leakage: detector bloqueia latentes, targets, defaults, recuperações, write-offs e EAD realizada na lista de features.
- Diagnóstico: distribuição e correlação de dez features numéricas de PD são calculadas sem usar correlação como critério de seleção.
- Cobertura: data card registra composição, proveniência, usos, proibições, qualidade e limitações; dicionário define entidades, eventos, macro e targets.
- Evidência: 8 testes aprovados, incluindo falhas injetadas de referência e temporalidade, OOT real, documentação e cobertura PD/LGD/EAD/SICR/Stage 3/POCI.

## Tarefa 3.8 — Materializar artefatos e manifesto da fábrica

### Justificativa de inclusão

O estado-alvo em `PROJECT_AUDIT_AND_TARGET_STATE.md` exige datasets Parquet obrigatórios, tabela de insumo regulatório e manifesto reproduzível, mas esses entregáveis não estavam explicitados nas tarefas originais da Fase 3. Esta tarefa fecha a lacuna antes de aceitar a fase.

### Subtarefas

- [x] Materializar os datasets Parquet obrigatórios em diretório de saída versionado.
- [x] Derivar pagamentos, atrasos e limites/drawdowns sem duplicar a fonte canônica.
- [x] Criar insumo regulatório sintético de origem sem inventar campos de leiaute Doc3040.
- [x] Gerar manifesto com seed, versões, schemas, contagens e SHA-256.
- [x] Garantir reprodução byte a byte e documentar o comando de geração.
- [x] Testar integridade dos arquivos materializados.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/data/synthetic/export.py`, `scripts/generate-synthetic-data.ps1`, `docs/data/SYNTHETIC_EXPORT.md` e `data/synthetic/acceptance-v0.1.0`.
- Materialização: 24 tabelas Parquet cobrem as 16 saídas obrigatórias e entidades/eventos auxiliares; o pacote de aceitação usa seed 91, 40 clientes e 80 contratos.
- Derivação: pagamentos, atrasos e limites/drawdowns são projeções reconciliadas dos 2.431 snapshots canônicos.
- Regulatório: `regulatory_reporting_input.parquet` contém 80 linhas de dados-fonte neutros e nenhum campo de leiaute Doc3040 presumido.
- Manifesto: registra parâmetros, versões, hash da política macro, schema, contagem e SHA-256 por arquivo, sem timestamp volátil.
- Reprodutibilidade: duas materializações em diretórios distintos resultam em igualdade byte a byte.
- Evidência: 6 testes aprovados, incluindo presença, hashes, schemas, contagens, reprodução e validação do pacote versionado no repositório.

### Critérios de aceite da fase

- [x] O dataset é reproduzível por seed.
- [x] O modelo não recebe variáveis latentes.
- [x] Existe OOT real.
- [x] Há dados para PD, LGD, EAD, SICR, Stage 3, POCI e Doc3040.

### Aceite da fase

- A fábrica foi aceita com regressão automatizada, anti-leakage, OOT temporal e artefato Parquet reproduzível.
- A cobertura Doc3040 nesta fase significa somente dados-fonte sintéticos materializados; não significa XML, aderência a XSD, crítica semântica ou autorização de envio, que permanecem na Fase 12.

---

# FASE 4 — Motor de contratos, cronogramas e fluxos de caixa

## Objetivo

Representar corretamente a vida financeira dos instrumentos.

## Tarefa 4.1 — Contratos amortizados

### Subtarefas

- [x] Implementar Price, SAC e bullet.
- [x] Projetar principal, juros, tarifas e saldo.
- [x] Suportar taxa fixa e variável.
- [x] Calcular taxa efetiva de juros.
- [x] Suportar feriados e convenção de dias configurável.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: motor canônico `src/domain/contracts/amortization.py`, API de domínio, testes e `docs/contracts/AMORTIZED_CONTRACTS.md`.
- Métodos: Price, SAC e bullet reconciliam principal e zeram saldo, com resíduo de arredondamento absorvido no último período.
- Fluxos: cada período separa principal, juros, tarifa e pagamento total, preservando saldos e datas de competência/vencimento.
- Taxas: contratos fixos bloqueiam resets; contratos variáveis exigem curva e recalculam a prestação Price a cada taxa vigente.
- EIR: taxa efetiva resolve o valor contábil inicial líquido de tarifa upfront contra fluxos futuros, incluindo tarifas periódicas.
- Calendário: ACT/365, ACT/360, 30/360 e convenções unadjusted/following/modified following/preceding com feriados explícitos.
- Evidência: 8 testes aprovados; limitações de carência, prepagamento, modificação, taxas negativas e calendários externos estão documentadas.

## Tarefa 4.2 — Produtos rotativos

### Subtarefas

- [x] Implementar limites, utilização e pagamento mínimo.
- [x] Projetar drawdown e cancelamento.
- [x] Tratar limite não utilizado.
- [x] Suportar cartões e cheque especial.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/domain/contracts/revolving.py`, API de domínio, testes e `docs/contracts/REVOLVING_FACILITIES.md`.
- Estado: limite, saldo, juros, disponibilidade, drawdown, pagamento mínimo/real, shortfall e cancelamento são reconciliados mensalmente.
- Guardrails: drawdown não excede limite disponível; pagamento não excede dívida; cancelamento não reduz limite abaixo do saldo.
- Produtos: cartão e cheque especial compartilham invariantes, mantendo tipo explícito e política de pagamento mínimo parametrizável.
- Temporalidade: exige uma atividade única, ordenada e mensal para cada período contratual.
- Evidência: 6 testes aprovados; tarifas, IOF, parcelamento de fatura, aumento de limite e políticas de cobrança permanecem fora do escopo desta tarefa.

## Tarefa 4.3 — Modificações e prepagamento

### Subtarefas

- [x] Implementar prepagamento parcial e total.
- [x] Implementar modificação com e sem baixa.
- [x] Calcular ganho/perda de modificação.
- [x] Preservar EIR original quando exigido.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/domain/contracts/modifications.py`, API de domínio, testes e `docs/contracts/PREPAYMENT_AND_MODIFICATIONS.md`.
- Prepagamento: valores são limitados ao saldo; total encerra e parcial reprojeta saldo/prazo remanescentes sem reaplicar tarifa upfront.
- Sem baixa: novos fluxos são descontados pela EIR original, que permanece como taxa aplicada; ganho/perda reconcilia valor anterior e presente modificado.
- Com baixa: exige valor justo explícito, reconhece novo valor contábil, calcula ganho/perda e resolve nova EIR.
- Guardrail: o motor não inventa teste de substancialidade; `derecognize` deve vir de política aprovada e o principal revisado deve reconciliar com o saldo anterior.
- Evidência: 5 testes aprovados; contraprestação, custos de renegociação, capitalização de atraso, teste de baixa e POCI permanecem documentados como limitações.

## Tarefa 4.4 — Golden cases financeiros

### Subtarefas

- [x] Criar contratos pequenos com planilha manual de referência.
- [x] Testar saldos, juros e amortização período a período.
- [x] Testar arredondamento e reconciliação.

### Critérios de aceite

- [x] Fluxos fecham com o saldo contábil.
- [x] Resultados batem com casos manuais dentro da tolerância definida.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `tests/fixtures/golden/amortization_cases.csv`, testes e `docs/contracts/GOLDEN_AMORTIZATION_CASES.md`.
- Casos: contratos Price, SAC e bullet de R$ 1.200, três meses e 12% a.a., calculados manualmente em planilha CSV estática.
- Tolerância: R$ 0,01 por campo/período para abertura, principal, juros, pagamento e fechamento.
- Reconciliação: cada linha verifica abertura menos principal igual a fechamento e principal mais juros/tarifa igual ao pagamento.
- Aceite: os três métodos amortizam exatamente R$ 1.200 e encerram com saldo zero.
- Evidência: 3 testes golden aprovados; a referência não é regenerada pelo motor durante os testes.

### Aceite da fase

- A Fase 4 foi aceita com motores separados para amortizados e rotativos, eventos de prepagamento/modificação, EIR e casos golden independentes.
- Limitações e decisões de política permanecem explícitas e não foram convertidas em regras contábeis arbitrárias.

---

# FASE 5 — Modelo de PD e estruturas temporais

## Objetivo

Substituir a PD heurística por modelos temporais calibrados e validáveis.

## Tarefa 5.1 — Definição formal de default

### Subtarefas

- [x] Definir evento de default por população e produto.
- [x] Definir cure e redefault.
- [x] Definir materialidade e backstops.
- [x] Documentar target e exclusões.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: política `config/default_policy/2026.07.1.json`, avaliador `src/models/pd/default_definition.py`, testes e `docs/models/DEFAULT_DEFINITION.md`.
- Default: backstop em 91 DPD para operacionalizar atraso superior a 90 dias e sete indicadores qualitativos que podem antecipar o evento.
- Populações: varejo por instrumento, compromissos/garantias por contraparte e POCI separado; arrasto final permanece para a Fase 8.
- Materialidade: limiar zero conservador e explicitamente não calibrado, sem apresentação como requisito regulatório.
- Cura/redefault: quatro evidências cumulativas, hipótese operacional de três meses, exceção de 90 dias para pagamentos de baixa frequência e monitoramento de redefault por 12 meses.
- Target: primeiro default em `(t, t+12m]`, excluindo POCI, já defaultados e horizonte incompleto.
- Integração: gerador passou de `>=90` para `>=91` DPD e datasets PD/SICR deixaram de incluir POCI; pacote Parquet foi regenerado.
- Evidência: 8 testes aprovados; requisitos IFRS9-DEFAULT-001, CMN4966-DEFAULT-001 e CMN4966-CURE-001 avançaram para `partial` até staging/arrasto.

## Tarefa 5.2 — Baseline explicável

### Subtarefas

- [x] Implementar regressão logística 12m.
- [x] Implementar discrete-time hazard.
- [x] Comparar desempenho e calibração.
- [x] Criar scorecard/rating derivado de PD, sem faixas arbitrárias não calibradas.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/pd/baselines.py`, API, testes e `docs/models/PD_BASELINES.md`.
- Modelos: regressão logística 12m e hazard logístico mensal usam pipeline numérico/categórico explícito, `class_weight` balanceado e seed fixa.
- Separação: treino ajusta; validação mede; calibração deriva rating; OOT/backtesting não são consultados nesta tarefa.
- Métricas: logística 12m obteve ROC AUC 0,7548, AP 0,4271 e Brier 0,1768 na validação sintética; não constituem aprovação.
- Hazard: ROC AUC 0,6105 e AP 0,0258 com somente 3 eventos de validação; subestimação foi registrada como limitação material.
- Explicabilidade: coeficientes expandidos são retornados e bloqueiam targets/futuro; não recebem interpretação causal automática.
- Rating: R1–R5 são quintis da PD no conjunto de calibração com taxa observada, não faixas legadas arbitrárias; promoção depende das Tarefas 5.4–5.6.
- Dados: choques de cobertura longitudinais não-POCI garantem eventos em todos os splits sem serem exportados como feature; pacote Parquet foi regenerado.
- Evidência: 5 testes aprovados para targets, métricas, coeficientes, rating e determinismo.

## Tarefa 5.3 — Modelos candidatos

### Subtarefas

- [x] Avaliar gradient boosting calibrado.
- [x] Avaliar survival gradient boosting, quando adequado.
- [x] Avaliar matrizes de transição para segmentos pequenos.
- [x] Manter modelo champion e challengers.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/pd/candidates.py`, API, testes e `docs/models/PD_CANDIDATES.md`.
- Boosting 12m: estimador ajustado em treino e calibrador isotonic ajustado somente em calibração; validação pré-calibração ficou abaixo da logística.
- Auditoria OOT após split 0.2.0: challenger calibrado obteve ROC AUC 0,7246, AP 0,2610 e Brier 0,0980, com Log Loss 1,4292; não foi promovido.
- Survival boosting: ROC AUC 0,5614/AP 0,0287 com 3 eventos de validação, status `insufficient_hazard_events`.
- Transições: 25 células empíricas mensais produto/rating, estimadas somente em treino e normalizadas por origem, sem preenchimento silencioso.
- Registry: logística é referência provisória `oot_failed_not_approved`; boosting, survival e matrizes permanecem challengers e não há champion aprovado.
- Governança: OOT não selecionou hiperparâmetros/champion e foi consumido uma única vez; alterações posteriores exigem especificação congelada e backtesting futuro.
- Evidência: 5 testes aprovados para calibração reservada, survival, matrizes, registry e métricas.

## Tarefa 5.4 — Separação temporal e calibração

### Subtarefas

- [x] Usar split por data/coorte.
- [x] Separar calibração do teste OOT.
- [x] Aplicar Platt, isotonic ou beta calibration conforme validação.
- [x] Avaliar calibração por rating, produto e safra.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: split purgado `0.2.0`, `src/models/pd/calibration.py`, testes e `docs/models/PD_TEMPORAL_CALIBRATION.md`.
- Cortes: treino 2016–2018, validação 2020, calibração 2022, OOT 2024 e backtesting futuro 2025, com anos intermediários de embargo.
- Backtesting: targets de 2025 são nulos até maturarem; falsos zeros são bloqueados pelo quality gate.
- Seleção: isotonic venceu Platt por Brier em holdout temporal interno da validação; o calibrador final foi ajustado somente em calibração.
- OOT: baseline calibrado colapsou para PD constante 0,2941, ROC AUC 0,5000 e erro global 0,1782; resultado bloqueia aprovação e não foi usado para retuning.
- Segmentação: 14 cortes por rating, produto e safra registram contagem, eventos, taxa, PD média, erro e Brier.
- Evidência: 5 testes novos e pacote Parquet regenerado; resultados permanecem sintéticos e `not_approved`.

## Tarefa 5.5 — Curvas de PD

### Subtarefas

- [x] Gerar hazard mensal.
- [x] Gerar sobrevivência.
- [x] Gerar PD marginal.
- [x] Gerar PD acumulada 12m e lifetime.
- [x] Garantir monotonicidade e limites.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/pd/term_structure.py`, API, 8 casos de teste e `docs/models/PD_TERM_STRUCTURE.md`.
- Matemática: hazard condicional deriva de intensidade acumulada; sobrevivência, PD marginal e PD acumulada reconciliam período a período.
- Horizonte: PD 12m usa `min(12, prazo remanescente)` e lifetime termina na maturidade contratual real, sem prazo fixo de cinco anos.
- Forma temporal: multiplicadores mensais positivos suportam curva não plana e preservam a PD acumulada do horizonte.
- Guardrails: probabilidades são limitadas, sobrevivência não cresce, PD acumulada não diminui e entradas inválidas falham fechadas.
- Governança: curvas carregam status `synthetic_unapproved_input`; coerência matemática não supera o blocker OOT da Tarefa 5.4.

## Tarefa 5.6 — Validação de PD

### Subtarefas

- [x] AUC, Gini, KS e PR-AUC.
- [x] Brier Score e Log Loss.
- [x] calibration plot e expected calibration error.
- [x] testes binomiais por rating.
- [x] observado versus esperado.
- [x] estabilidade, PSI e controle de backtesting pendente de maturação.
- [x] análise de viés e segmentos.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/pd/validation.py`, 6 testes, `docs/models/PD_VALIDATION_REPORT.md` e `docs/models/PD_MODEL_CARD.md`.
- OOT congelado: 233 linhas/27 eventos; AUC 0,5000, Gini/KS 0,0000, PR-AUC 0,1159, Brier 0,1342, Log Loss 0,4498 e ECE 0,1782.
- Calibração: um único bin de PD 0,2941 contra taxa 0,1159; testes binomiais rejeitam A2, B1 e B2 a 5%, sem correção de multiplicidade.
- Segmentos: 14 cortes por rating, produto e safra; ausência de atributos protegidos impede conclusão de fairness demográfica.
- Estabilidade: PSI 6,7903 (`high_shift`) no score não calibrado entre calibração e backtesting futuro.
- Backtesting: framework e guardrail implementados; performance 2025 permanece `pending_target_maturation`, sem métrica inventada.
- Decisão: `not_approved`; não existe champion aprovado nem evidência além da simulação demonstrativa.

### Critérios de aceite

- [x] O teste OOT nunca é usado no desenvolvimento.
- [x] Lifetime PD depende do prazo real e da curva temporal.
- [x] Métricas sintéticas são identificadas como sintéticas.
- [x] Existe model card completo.

---

# FASE 6 — SICR, staging, default, cura e POCI

## Objetivo

Criar um único motor oficial de classificação de estágio.

## Tarefa 6.1 — Baseline de originação

### Subtarefas

- [x] Persistir PD/rating na originação.
- [x] Persistir data, modelo e política de originação.
- [x] Calcular lifetime PD de originação no prazo original.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/sicr/origination.py`, ledger JSON versionado, 8 casos de teste e `docs/models/SICR_ORIGINATION_BASELINE.md`.
- Baseline: persiste PD 12m, rating, reconhecimento, maturidade original, modelo/versão, política/hash, lifetime PD e status de aprovação.
- Prazo: lifetime PD usa a curva canônica até a maturidade contratual original; contratos curtos terminam no próprio horizonte.
- Integridade: schema `1.0.0`, unicidade por contrato, hash por registro e rejeição de adulteração.
- Governança: status padrão `not_approved`; persistência da referência não promove o modelo sintético reprovado.

## Tarefa 6.2 — Motor SICR

### Subtarefas

- [x] Comparar lifetime PD atual e de originação.
- [x] Implementar variação absoluta e relativa.
- [x] Implementar downgrade em notches.
- [x] Implementar watchlist e eventos qualitativos.
- [x] Implementar backstop de atraso.
- [x] Implementar low-credit-risk exemption configurável.
- [x] Produzir razão de decisão detalhada.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `config/sicr_policy/2026.07.1.json`, `src/models/sicr/engine.py`, 10 testes e `docs/models/SICR_ENGINE.md`.
- Comparação: lifetime PD atual versus baseline persistido, com diferença absoluta, razão relativa e downgrade em notches.
- Gatilhos diretos: 31 DPD, downgrade, watchlist, concessão/forbearance e eventos qualitativos.
- Isenção: low-credit-risk é configurável e só suprime gatilhos quantitativos; nunca sobrepõe gatilho direto.
- Explicabilidade: decisão inclui gatilhos ativos/suprimidos, razões, versão/hash da política e status da evidência.
- Governança: thresholds são hipóteses `demonstrative_unvalidated`, não limites normativos ou calibrados.

## Tarefa 6.3 — Stage 3 e default

### Subtarefas

- [x] Unificar default contábil e operacional.
- [x] Implementar arrasto por contraparte com exceções documentadas.
- [x] Implementar evento de unlikeliness to pay.
- [x] Implementar reestruturação/concessão.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: política de contágio versionada, `src/models/sicr/stage3.py`, 9 testes e `docs/models/STAGE3_DEFAULT.md`.
- Unificação: default operacional, crédito deteriorado contábil e Stage 3 compartilham decisão e motivos canônicos.
- UTP: indicadores qualitativos podem antecipar o backstop material de 91 DPD.
- Reestruturação: concessão com dificuldade financeira mapeia `distressed_restructuring`; concessão isolada não vira Stage 3 automaticamente.
- Arrasto: produtos de avaliação `counterparty` propagam default, salvo exceção permitida e documentada; facility permanece individual.
- Rastreabilidade: contratos de contágio, exceções, razões, nível, versão/hash e status da política integram a saída.

## Tarefa 6.4 — Cura e retorno de estágio

### Subtarefas

- [x] Implementar período de observação.
- [x] Implementar critérios quantitativos e qualitativos.
- [x] Registrar histórico de estágio.
- [x] Impedir cura prematura.
- [x] Tratar redefault.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/sicr/history.py`, ledger imutável, 7 testes e `docs/models/STAGE_HISTORY_AND_CURE.md`.
- Cura: reutiliza período, adimplência, obrigações e capacidade da política canônica; ausência ou insuficiência mantém Stage 3.
- Retorno: cura elegível retorna a Stage 2 com SICR residual ou Stage 1 sem SICR.
- Histórico: sequência, data, estágio anterior/novo, razões, cura, redefault e hashes das políticas são registrados.
- Integridade: continuidade de contrato, sequência, data e estado falha fechada.
- Redefault: nova entrada em Stage 3 após cura é marcada e justificada explicitamente.

## Tarefa 6.5 — POCI

### Subtarefas

- [x] Identificar ativos adquiridos ou originados com problema de crédito.
- [x] Implementar credit-adjusted EIR.
- [x] Calcular variação de lifetime ECL.
- [x] Criar golden cases POCI.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/ecl/calculation/poci.py`, 2 golden cases CSV, 6 testes e `docs/models/POCI_MEASUREMENT.md`.
- População: adquiridos e originados credit-impaired são identificados separadamente e permanecem fora de PD/SICR comuns.
- Taxa: credit-adjusted EIR reconcilia preço e fluxos esperados iniciais pelas datas efetivas.
- Mensuração: lifetime ECL inicial/atual usa a mesma EIR; variação positiva é perda e negativa é ganho de impairment.
- Golden cases: taxa de 10%, perda adicional de 10 e mudança favorável de -5 reconciliam manualmente.
- Governança: fluxos desalinhados ou acima do contratual falham; saída permanece `synthetic_unapproved`.

## Tarefa 6.6 — Validação de staging

### Subtarefas

- [x] Stability index por período.
- [x] taxa de migração entre estágios.
- [x] sensibilidade a thresholds.
- [x] comparação de definições SICR.
- [x] falsos positivos/negativos em eventos futuros.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/sicr/validation.py`, 6 testes e `docs/models/SICR_VALIDATION_REPORT.md`.
- OOT: 233 linhas/37 eventos; regra relativa 2 notches/31 DPD não marca casos, com recall 0 e FNR 1, blocker explícito.
- Estabilidade/migração: taxa Stage 2 e PSI iguais a zero em todos os períodos, com 208 migrações 1→1; resultado é degeneração, não estabilidade válida.
- Sensibilidade: um notch produz taxa 0,4893, recall 0,6757 e FPR 0,4541, sem promoção pelo OOT.
- Comparação: regra absoluta B1+ tem recall 0,1892/FPR 0,6582 e concordância 0,4163 com a relativa.
- Erros: contratos falsos positivos/negativos são listados; evidência permanece `synthetic_proxy_without_approved_pd` e `not_approved`.

### Critérios de aceite

- [x] Existe somente um motor de estágio.
- [x] Toda decisão possui justificativa, versão e evidência.
- [x] Stage 2 é relativo à originação, não apenas ao nível atual.

---

# FASE 7 — Modelo de LGD workout

## Objetivo

Calcular LGD a partir de recuperações líquidas e descontadas.

## Tarefa 7.1 — Dataset de LGD

### Subtarefas

- [x] Criar default cohorts.
- [x] Vincular recuperações, custos, garantias, cura e write-off.
- [x] Definir janela de workout.
- [x] Tratar observações censuradas.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/lgd/workout.py`, 6 testes e `docs/models/LGD_WORKOUT_DATASET.md`.
- Coortes: uma linha por default/redefault observado, agrupada por trimestre e vinculada ao contrato/produto.
- Evidência: cash flows brutos/custos/líquidos, garantia, cura e write-off permanecem rastreáveis por default.
- Workout: janela padrão de 24 meses e cutoff explícito em 1º de dezembro de 2025.
- Censura: 7 de 32 defaults têm janela incompleta; nenhum evento posterior ao cutoff entra no dataset.
- Carteira: 12 write-offs, 10 curas, 6 abertos completos, 4 abertos censurados, 25 com cash flow e 20 com garantia.

## Tarefa 7.2 — LGD realizada

### Subtarefas

- [x] Calcular EAD no default.
- [x] Descontar recuperações pela taxa apropriada.
- [x] Subtrair custos.
- [x] Calcular LGD de cura e de perda.
- [x] Tratar LGD negativa ou superior a 100% conforme política documentada.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/lgd/realized.py`, política `config/lgd_policy/2026.07.1.json`, 7 testes e `docs/models/LGD_REALIZED.md`.
- Mensuração: recuperações e custos são descontados por dias corridos à EIR contratual; a EAD é a registrada no evento de default.
- Cura: o residual nominal após recuperações brutas é reconhecido como valor restaurado na data da cura, sem dupla contagem dos fluxos já observados.
- Governança: LGD bruta permanece auditável; a variável de modelagem é limitada a 0%–100% com ação explícita e política versionada/hashada.
- Censura: 7 de 32 observações são provisórias; a estatística de aceite usa apenas os 25 workouts completos.
- Evidência sintética: LGD média completa de 52,2805414%, sendo 17,3693342% para cura e 71,9180954% para perda; nenhuma observação da carteira exigiu limite.
- Limitação: convenção e métricas são demonstrativas, não validadas com recuperações institucionais.

## Tarefa 7.3 — Modelagem

### Subtarefas

- [x] Implementar baseline segmentado.
- [x] Avaliar one-stage regression.
- [x] Avaliar two-stage: probabilidade de write-off/cura + severidade.
- [x] Considerar zero/one-inflated ou beta regression quando adequado.
- [x] Incluir garantias, LTV, produto, atraso, prazo e macroeconomia.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/lgd/modeling.py`, 7 testes e `docs/models/LGD_MODELING.md`.
- Amostra: 25 workouts fechados; treino temporal com 15 defaults de 2017–2021 e validação com 10 defaults de 2022–2023; 7 censurados excluídos.
- Features: produto, garantia, LTV, EAD, atraso, prazo remanescente e macro observado point-in-time, sem fluxos futuros como preditores.
- Candidatos: baseline segmentado, Ridge one-stage, two-stage cura/severidade e one-inflated Ridge foram comparados no mesmo holdout.
- Adequação: seis perdas integrais justificam avaliar one-inflation; não há massa em zero e beta puro não acomoda os limites sem transformação.
- Seleção provisória: `ridge_one_stage` teve o menor RMSE (0,452035), contra 0,453292 do two-stage, 0,455493 do one-inflated e 0,509690 do baseline.
- Guardrail: todos os candidatos permanecem `demonstrative_not_approved`; a amostra sintética pequena e diferenças marginais impedem aprovação.

## Tarefa 7.4 — Garantias

### Subtarefas

- [x] Projetar valor de garantia.
- [x] Aplicar haircut e custos.
- [x] Modelar tempo de execução.
- [x] Evitar dupla contagem entre recuperação e garantia.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/lgd/collateral.py`, política `config/lgd_collateral_policy/2026.07.1.json`, 7 testes e `docs/models/LGD_COLLATERAL.md`.
- Projeção: valor desde a avaliação até o default, enforceability, haircut, custo, prazo de execução e desconto pela EIR são componentes separados e auditáveis.
- Sensibilidade: cenários upside, base e downside alteram valor, haircut, custo e prazo sob a mesma versão de política.
- Dupla contagem: cash flows observados de `collateral_execution` são excluídos da base, a projeção ocupa somente o headroom após outras recuperações e o total é limitado à EAD.
- Carteira: 20 defaults garantidos (11 veículos e 9 imóveis) e 12 sem garantia; recuperação líquida descontada base média de R$ 101.573,44 ou 68,1058% da EAD garantida.
- Faixa: médias de R$ 115.644,45 no upside e R$ 73.320,10 no downside; nenhum caso atingiu o cap de headroom.
- Limitação: parâmetros e resultados são sintéticos, demonstrativos e não aprovados para uso institucional.

## Tarefa 7.5 — Validação de LGD

### Subtarefas

- [x] previsto versus realizado.
- [x] MAE, RMSE e calibração por faixa.
- [x] backtesting por coorte.
- [x] estabilidade por produto.
- [x] análise downturn separada do ECL PIT.

### Critérios de aceite

- [x] LGD é derivada de fluxos de recuperação.
- [x] Toda premissa possui versão e sensibilidade.
- [x] Existe model card e relatório de validação.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/lgd/validation.py`, política `config/lgd_validation/2026.07.1.json`, 7 testes, `docs/models/LGD_VALIDATION_REPORT.md` e `docs/models/LGD_MODEL_CARD.md`.
- Holdout: 10 defaults de 2022–2023, já usados para seleção na Tarefa 7.3; ausência de OOT independente é blocker explícito.
- Performance: LGD realizada média de 0,568917, prevista de 0,571144, MAE 0,358173 e RMSE 0,452035; uma de três faixas excede o erro de calibração máximo.
- Coortes/produtos: todas as seis coortes estão abaixo do mínimo; credit card e mortgage não aparecem na validação.
- Downturn: quartil macro adverso tem 7 casos e addon zero, mantido como sensibilidade descritiva separada do ECL PIT, sem inferência de ausência de risco downturn.
- Decisão: `not_approved`; não existe champion LGD aprovado até haver workouts institucionais maduros, amostra mínima, OOT congelado e validação independente.

### Aceite da fase

- A Fase 7 foi aceita como implementação técnica reproduzível: LGD deriva de cash flows descontados, políticas e sensibilidades são versionadas, garantias evitam dupla contagem e há model card/relatório.
- O aceite da entrega não aprova o modelo: os blockers quantitativos e de independência permanecem formais e impedem uso institucional.

---

# FASE 8 — Modelo de EAD e CCF

## Objetivo

Projetar exposição no momento do default para produtos amortizados e rotativos.

## Tarefa 8.1 — EAD de produtos amortizados

### Subtarefas

- [x] Usar cronograma de saldo por período.
- [x] Incorporar prepagamento e modificação.
- [x] Calcular EAD no período de default.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/ead/amortized.py`, política `config/ead_policy/2026.07.1.json`, 7 testes e `docs/models/EAD_AMORTIZED.md`.
- Temporalidade: EAD usa o saldo de abertura da última competência observável antes do default, coerente com default anterior ao pagamento agendado.
- Ajustes: resultados canônicos de prepagamento parcial/total e modificação substituem o cronograma somente quando efetivos até o default; eventos futuros não vazam.
- Componentes: a política sintética inclui principal sacado e exclui explicitamente juros corridos e parcela não utilizada de operações amortizadas.
- Reconciliação: 24 defaults iniciais — 8 veículos, 8 mortgages e 8 acquired distressed — reconciliam ao centavo, com EAD total de R$ 3.090.369,67.
- Modificação sintética: uma extensão pré-default é identificada, mas não reamortizada sem fluxos revisados; o caminho canônico completo é coberto por golden case.
- Limitação: regra e dados são demonstrativos e não validam componentes de EAD institucionais.

## Tarefa 8.2 — CCF de produtos rotativos

### Subtarefas

- [x] Construir dataset de limite e drawdown antes do default.
- [x] Calcular CCF realizado.
- [x] Modelar CCF por produto, utilização e horizonte.
- [x] Tratar limites reduzidos/cancelados.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/ead/revolving_ccf.py`, política `config/ccf_policy/2026.07.1.json`, 7 testes e `docs/models/EAD_REVOLVING_CCF.md`.
- Desenvolvimento: carteira separada e determinística com seed 91, 400 clientes e 2 contratos por cliente, pois a carteira principal contém apenas um default rotativo.
- Dataset: 12 defaults, 25 linhas — 15 cartões e 10 overdrafts — em horizontes exatos de 3/6/12 meses; 11 horizontes sem histórico foram omitidos.
- CCF: média 0,056834 e faixa 0–0,272929; bruto preservado, target limitado e denominador zero tratado como indefinido/excluído.
- Modelo: Ridge por produto, utilização, horizonte, interação e status de limite; 21 linhas de treino, MAE in-sample 0,025137 e RMSE 0,033649, sem alegação de validação.
- Limites: redução, cancelamento e aumento possuem tratamento explícito e golden cases, mas todos os 25 casos estimados ficaram `unchanged`; o efeito não é identificável.
- Guardrail: apenas uma linha tem horizonte de 12 meses e quatro ficam para validação; modelo `demonstrative_not_approved`.

## Tarefa 8.3 — EAD de compromissos e garantias

### Subtarefas

- [x] Implementar loan commitments.
- [x] Implementar financial guarantees.
- [x] Modelar probabilidade de utilização.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/ead/off_balance.py`, política `config/off_balance_ead_policy/2026.07.1.json`, 7 testes e `docs/models/EAD_OFF_BALANCE.md`.
- Fronteira: probabilidade de utilização/chamada é condicional e separada da PD da contraparte, evitando dupla contagem conceitual no futuro ECL.
- Compromissos: hazard mensal parametrizado de utilização, sensível a horizonte, risco e utilização atual, combinado com parcela condicional de 75% do limite disponível.
- Garantias: probabilidade parametrizada de chamada separada, com parcela condicional de 100% do valor disponível.
- Limites: usa limite corrente executável; redução e cancelamento não restauram exposição e a EAD é limitada ao valor corrente.
- Carteira base em 12 meses: 10 compromissos com probabilidade média 0,387290/EAD média R$ 31.489,89 e 10 garantias com 0,262002/R$ 46.934,74.
- Guardrail: o gerador não possui utilizações/defaults observados desses produtos; status `demonstrative_parameterized_not_estimated`, sem alegação de calibração.

## Tarefa 8.4 — Validação de EAD

### Subtarefas

- [x] previsto versus realizado.
- [x] erro por segmento.
- [x] estabilidade temporal.
- [x] sensibilidade a utilização e limite.

### Critérios de aceite

- [x] EAD é temporal e consistente com o produto.
- [x] CCF não é apenas uma constante global.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/ead/validation.py`, política `config/ead_validation/2026.07.1.json`, 7 testes, `docs/models/EAD_VALIDATION_REPORT.md` e `docs/models/EAD_MODEL_CARD.md`.
- Amortizados: 24 previstos versus realizados com MAE/RMSE zero por produto e ano; resultado é reconciliação do gerador, não validação preditiva independente.
- CCF holdout: 4 linhas de 2022–2023, média realizada 0,044672, prevista 0,037665, MAE 0,039723 e RMSE 0,054894.
- Segmentos: cada combinação produto/horizonte CCF tem uma observação; não há horizonte de 12 meses nem limite alterado no holdout.
- Sensibilidade: CCF responde a utilização/horizonte sem direção aprovada; EAD off-balance responde monotonicamente ao limite por construção.
- Decisão: `not_approved` por volume, cobertura, ausência de eventos de limite, parâmetros off-balance não estimados e evidência não institucional.

### Aceite da fase

- A Fase 8 foi aceita como implementação técnica reproduzível: EAD é temporal e específica ao produto; o CCF varia por produto, utilização e horizonte; limites e exposições off-balance têm regras explícitas.
- O aceite técnico não aprova CCF ou off-balance: os blockers do relatório/model card impedem uso institucional.

---

# FASE 9 — Forward-looking e cenários macroeconômicos

## Objetivo

Calcular riscos e ECL completos por cenário, com relações macroeconômicas demonstráveis.

## Tarefa 9.1 — Serviço de cenários

### Subtarefas

- [x] Criar schema de trajetória macro por período.
- [x] Suportar cenários base, otimista, pessimista e stress.
- [x] Validar soma dos pesos.
- [x] Versionar cenários e aprovação.
- [x] Criar cache e snapshot para fontes externas.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: domínio de trajetórias em `src/domain/scenarios`, serviço em `src/application/services/scenarios.py`, política `config/scenario_service/2026.07.1.json`, 7 testes e `docs/models/SCENARIO_SERVICE.md`.
- Fonte preservada: trajetórias sintéticas `1.0.0`, com 60 meses por cenário entre janeiro de 2026 e dezembro de 2030.
- Pesos probabilísticos: otimista 0,15, base 0,70 e pessimista 0,15; stress 0,00 e separado da ponderação.
- Governança: versão/hash obrigatórios; estado `approved` exige aprovador e data. A versão vigente permanece `not_approved` e `synthetic_demonstrative_only`.
- Fontes externas: cache JSON content-addressed, timestamp UTC e verificação de integridade; nenhuma chamada externa ocorre dentro do cálculo determinístico.

## Tarefa 9.2 — Relações macro-risco

### Subtarefas

- [x] Estimar ou parametrizar de forma transparente a relação macro-PD.
- [x] Estimar relação macro-LGD.
- [x] Estimar relação macro-EAD/CCF.
- [x] Permitir relações não lineares.
- [x] Documentar coeficientes sintéticos.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/models/forward_looking/relations.py`, política `config/macro_risk_relations/2026.07.1.json`, 7 testes e `docs/models/MACRO_RISK_RELATIONS.md`.
- Método: fatores separados de PD, LGD, EAD e CCF por mês/segmento, com transformação exponencial, termos quadráticos e limites explícitos.
- Segmentação: `portfolio`, `secured`, `revolving` e `off_balance`, com sensibilidades específicas por componente.
- Diagnóstico terminal: todos os fatores ordenam otimista < base < pessimista < stress; PD de stress atinge o teto parametrizado de 4,00.
- Guardrail: coeficientes são sintéticos, documentados e `demonstrative_not_estimated_not_approved`; não existe alegação de estimação ou calibração institucional.

## Tarefa 9.3 — ECL por cenário

### Subtarefas

- [x] Gerar curvas PD/LGD/EAD específicas por cenário.
- [x] Calcular ECL integral de cada cenário.
- [x] Ponderar valores de ECL.
- [x] Não ponderar apenas fatores médios.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/ecl/calculation/scenario_engine.py`, 7 testes e `docs/models/SCENARIO_ECL.md`.
- Mecânica: hazard/sobrevivência/PD marginal, LGD, EAD sacada, CCF sobre não sacado e desconto são calculados por mês e cenário.
- Golden case neutro de 2 meses: perdas de R$ 7,50 e R$ 6,75, total R$ 14,25, reconciliado manualmente.
- Caso sintético de 3 meses: ECL otimista R$ 20,21, base R$ 20,97, pessimista R$ 22,89, ponderado R$ 21,14 e stress separado R$ 27,37.
- Guardrail: a ponderação ocorre sobre os ECLs integrais; não existe média prévia de fatores. A integração específica de Stage pertence à Fase 10.

## Tarefa 9.4 — Sensibilidade e overlays

### Subtarefas

- [x] Executar sensibilidade a pesos e trajetórias.
- [x] Implementar stress testing.
- [x] Criar framework de management overlays separado do modelo.
- [x] Registrar motivo, valor, aprovador, vigência e reversão do overlay.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/ecl/calculation/sensitivity.py`, `src/ecl/overlays/management.py`, política `config/scenario_sensitivity/2026.07.1.json`, 7 testes e `docs/models/SCENARIO_SENSITIVITY_AND_OVERLAYS.md`.
- Caso de 6 meses: base R$ 121,51; sensibilidades de peso R$ 125,61/R$ 130,65; choques de trajetória R$ 133,51/R$ 137,22; stress separado R$ 187,54.
- Overlay: ECL econômico, valor gerencial e ECL final permanecem separados; registro exige motivo, aprovador, vigência e trilha de reversão.
- Guardrail: sensibilidades são derivadas e versionadas; overlays não alteram curvas, fatores, pesos ou integrais de cenário.

### Critérios de aceite

- [x] Alterações macroeconômicas afetam curvas e ECL de forma rastreável.
- [x] ECL final reconcilia com a soma ponderada dos cenários.

### Aceite da fase

- A Fase 9 foi aceita tecnicamente: trajetórias, pesos, relações macro-risco, ECL integral por cenário, sensibilidades, stress e overlays possuem contratos versionados, testes e reconciliação.
- O aceite não aprova cenários ou coeficientes para uso institucional. As fontes e relações permanecem sintéticas, demonstrativas e `not_approved`; a orquestração completa por Stage pertence à Fase 10.

---

# FASE 10 — Motor completo de ECL

## Objetivo

Implementar o núcleo de cálculo período a período, descontado e reconciliável.

## Tarefa 10.1 — Cálculo Stage 1

### Subtarefas

- [x] Usar defaults possíveis nos próximos 12 meses.
- [x] Aplicar perdas lifetime associadas a esses defaults.
- [x] Calcular por período, cenário e contrato.
- [x] Descontar pela EIR original.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/ecl/calculation/stage1.py`, desconto em `src/ecl/discounting/effective_interest.py`, 7 testes e `docs/models/STAGE1_ECL.md`.
- Horizonte: 1 a 12 defaults mensais possíveis, limitado ao prazo remanescente; LGD de cada período é lifetime condicional ao default.
- Caso de 12 meses: ECL otimista R$ 33,60, base R$ 36,95, pessimista R$ 46,45, ponderado R$ 37,87 e stress separado R$ 76,60.
- Desconto: EIR original de 12% produz fator 0,99060040 no mês 1 e 0,89285714 no mês 12; golden PV de R$ 112 em 12 meses = R$ 100.

## Tarefa 10.2 — Cálculo Stage 2

### Subtarefas

- [x] Calcular lifetime ECL pela vida remanescente.
- [x] Tratar prepagamento e extensão contratual esperada.
- [x] Suportar cálculo individual e coletivo.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/ecl/calculation/stage2.py`, 7 testes e `docs/models/STAGE2_ECL.md`.
- Lifetime: caso de 18 meses produz ECL otimista R$ 62,98, base R$ 71,49, pessimista R$ 96,71, ponderado R$ 74,00 e stress R$ 188,82.
- Comportamento: prepagamento esperado de 3% a.m. reduz o ECL para R$ 60,39; extensão de 6 meses com probabilidade de 50% eleva o caso de 12 meses de R$ 57,14 para R$ 65,57.
- Modos: mensuração individual proíbe grupo; coletiva exige `homogeneous_group_id`. Validação estatística dos grupos permanece na Tarefa 10.5.

## Tarefa 10.3 — Cálculo Stage 3

### Subtarefas

- [x] Projetar recebimentos e recuperações.
- [x] Calcular cash shortfall.
- [x] Descontar fluxos.
- [x] Tratar garantias, custos, cura e write-off.
- [x] Calcular juros sobre base apropriada.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/ecl/stage3/cash_shortfall.py`, 8 testes e `docs/models/STAGE3_ECL.md`.
- Golden shortfall: R$ 100 contratual − R$ 60 devedor − R$ 20 colateral + R$ 5 custos = ECL R$ 25.
- Multi-cenário: otimista/base/pessimista/stress R$ 20/R$ 40/R$ 60/R$ 80, ponderado R$ 40.
- Write-off: baixa de R$ 100 e recuperação pós-baixa de R$ 20 resultam em ECL R$ 80, sem dupla contagem.
- Juros: valor bruto R$ 1.000 menos allowance R$ 200, EIR 12%, produz R$ 8 mensais sobre base líquida Stage 3.

## Tarefa 10.4 — Cálculo POCI

### Subtarefas

- [x] Calcular credit-adjusted EIR.
- [x] Reconhecer mudanças na lifetime ECL.
- [x] Tratar apresentação e disclosure.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: extensão de `src/ecl/calculation/poci.py`, 7 novos testes (13 POCI combinados) e `docs/models/POCI_SCENARIO_ECL.md`.
- Golden case: preço R$ 80, fluxo esperado inicial R$ 88 e contratual R$ 110 produzem credit-adjusted EIR 10% e ECL inicial R$ 20.
- Cenários atuais: lifetime ECL R$ 10/R$ 20/R$ 30/R$ 40, ponderado R$ 20, mudança ponderada zero e stress R$ 40.
- Apresentação: mudanças positivas são perda, negativas são ganho; juros usam `credit_adjusted_eir_on_amortized_cost`. Status `synthetic_unapproved`.

## Tarefa 10.5 — Cálculo coletivo e grupos homogêneos

### Subtarefas

- [x] Definir critérios estatísticos de agrupamento.
- [x] Validar homogeneidade.
- [x] Impedir agrupamentos baseados apenas em faixas arbitrárias do score.
- [x] Permitir cálculo individual para exposições relevantes.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/ecl/calculation/grouping.py`, política `config/ecl_grouping/2026.07.1.json`, 7 testes e `docs/models/ECL_HOMOGENEOUS_GROUPING.md`.
- Dimensões: produto, colateral, safra, comportamento e score apenas como complemento; mínimo de duas dimensões não-score.
- Gates: mínimo 20 contratos, CV máximo PD/LGD/EAD 0,50/0,40/0,75 e concentração individual máxima 25%.
- Caso válido: CV PD 0,004004, LGD 0,001664, EAD 0,005712 e concentração 0,050471.
- Roteamento: EAD ≥ R$ 500.000 exige mensuração individual. Limites permanecem sintéticos e `not_approved`.

## Tarefa 10.6 — Reconciliação

### Subtarefas

- [x] Reconciliar por período.
- [x] Reconciliar por cenário.
- [x] Reconciliar contrato, cliente, produto e carteira.
- [x] Reconciliar ECL bruto, overlay, piso e ECL final.
- [x] Criar ledger de execução imutável.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/validation/reconciliation/ecl_ledger.py`, 8 testes e `docs/models/ECL_RECONCILIATION_LEDGER.md`.
- Golden case: cenários ponderados R$ 28 + R$ 21 = contratos R$ 13 + R$ 36 = ECL econômico do portfólio R$ 49.
- Camadas: overlays R$ 1, pisos somados R$ 20 e ECLs finais contratuais somados R$ 55, sem reaplicar piso no agregado.
- Ledger: objetos congelados, SHA-256 determinístico independente da ordem e encadeamento opcional pelo hash anterior.
- Fail-closed: duplicidade, pesos, cobertura de cenário, metadata, timestamp, ajuste e qualquer diferença de reconciliação bloqueiam a execução.

## Tarefa 10.7 — Golden cases ECL

### Subtarefas

- [x] Stage 1 amortizado.
- [x] Stage 2 lifetime.
- [x] Stage 3 cash shortfall.
- [x] rotativo com CCF.
- [x] contrato garantido.
- [x] POCI.
- [x] modificação.
- [x] multi-cenário.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `tests/fixtures/golden/ecl_cases.csv`, 8 testes consolidados e `docs/models/ECL_GOLDEN_CASES.md`.
- Resultados exatos: Stage 1 R$ 9,05; Stage 2 R$ 12,33; Stage 3 R$ 25,00; rotativo R$ 7,50; garantido R$ 30,00; POCI R$ 20,00; modificação R$ 268,15; multi-cenário R$ 21,14.
- Controles: igualdade entre LGD exibida/usada por período; repetição determinística do caso multi-cenário; modificação sem baixa preserva EIR original.

### Critérios de aceite

- [x] Todos os golden cases batem com cálculo manual.
- [x] `PD × LGD × EAD` simples permanece apenas como baseline didático.
- [x] Nenhuma LGD exibida diverge da usada no cálculo.
- [x] Toda execução é reproduzível.

### Aceite da fase

- A Fase 10 foi aceita tecnicamente: Stage 1, Stage 2, Stage 3, POCI, agrupamento, reconciliação, ledger e oito golden cases estão implementados e reproduzíveis.
- O aceite comprova a mecânica com dados sintéticos; componentes quantitativos anteriormente `not_approved` permanecem não aprovados para uso institucional.

---

# FASE 11 — CMN 4.966, provisões mínimas e perímetro completo

## Objetivo

Separar corretamente cálculo contábil, regras locais, metodologia simplificada e demais componentes do perímetro.

## Tarefa 11.1 — Regras locais de provisão mínima

### Subtarefas

- [x] Implementar tabelas e regras apenas a partir de fonte oficial vigente.
- [x] Versionar por data-base.
- [x] Aplicar após o ECL econômico/contábil, em camada separada.
- [x] Exibir ECL calculado, piso e provisão final separadamente.

## Tarefa 11.2 — Metodologia simplificada

### Subtarefas

- [x] Verificar aplicabilidade vigente para segmentos/instituições.
- [x] Implementar como estratégia separada.
- [x] Criar casos sintéticos e documentação.
- [x] Impedir mistura com metodologia completa.

## Tarefa 11.3 — Classificação e mensuração

### Subtarefas

- [x] Implementar cadastro de business model.
- [x] Implementar teste SPPI.
- [x] Classificar amortized cost, FVOCI e FVTPL.
- [x] Integrar elegibilidade ao motor de impairment.
- [x] Tratar reclassificação quando aplicável.

## Tarefa 11.4 — Modificação, baixa e reconhecimento

### Subtarefas

- [x] Implementar regras de modificação sem derecognition.
- [x] Implementar derecognition.
- [x] Implementar write-off parcial e total.
- [x] Implementar recuperações pós-baixa.

## Tarefa 11.5 — Disclosures

### Subtarefas

- [x] Gerar reconciliação de allowance por estágio.
- [x] Gerar movimentações e transferências de estágio.
- [x] Gerar exposição por rating e segmento.
- [x] Gerar sensibilidades e overlays.
- [x] Gerar pacote de disclosure sintético.

## Tarefa 11.6 — Fechamento de evidências regulatórias da fase

### Subtarefas

- [x] Gerar manifesto de revisão mensal de estágio e provisão.
- [x] Fechar a rastreabilidade CMN 4.966 para staging, default, cura, ECL e revisão.
- [x] Vincular a aplicabilidade BCB 352 aos motores de staging e ECL sem duplicar fórmulas.

### Critérios de aceite

- [x] O sistema diferencia claramente IFRS 9, CMN 4.966, piso regulatório e capital IRB.
- [x] Não há uso direto de LGD downturn regulatória como LGD contábil sem ajuste e documentação.

---

# FASE 12 — Documento 3040 e reportes regulatórios

## Objetivo

Substituir o simulador heurístico por um gerador e pré-validador versionado, sem dados inventados.

## Tarefa 12.1 — Contrato de entrada regulatória

### Subtarefas

- [x] Definir todos os campos obrigatórios e condicionais.
- [x] Definir domínios e formatos.
- [x] Mapear origem de cada campo.
- [x] Rejeitar ausência ou inconsistência.
- [x] Remover datas, portes, COSIFs, CEPs e códigos default silenciosos.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: contrato fail-closed em `src/regulatory/doc3040/contract.py`, catálogo de
  campos, API pública, testes e `docs/regulatory/DOC3040_INPUT_CONTRACT.md`.
- Cobertura: cabeçalho, clientes, operações, vencimentos, garantias, informações
  adicionais/Sicor, CMN 4.966, estágios, perdas, IPOCs conectados e agregações.
- Linhagem: todo escalar presente exige sistema, campo de origem e evidência; opcionais e
  condicionais devem ser explicitamente fornecidos ou marcados ausentes.
- Guardrails: sem defaults para datas, porte, COSIF, CEP ou códigos; condições PJ,
  exterior, atraso, parcelas, Sicor, totalizadores, datas e unicidade falham de forma
  explícita.
- Versionamento: formatos e referências de domínio estão catalogados, mas o conteúdo dos
  domínios permanece bloqueado até o registry por data-base da Tarefa 12.2.
- Evidência: 11 testes direcionados aprovados; geração XML, XSD e críticas permanecem
  fora do aceite desta tarefa.

## Tarefa 12.2 — Versionamento de leiaute

### Subtarefas

- [x] Implementar registry por data-base.
- [x] Carregar XSD correspondente.
- [x] Versionar críticas e tabelas de domínio.
- [x] Bloquear data-base sem versão suportada.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: registry em `src/regulatory/doc3040/layout_registry.py`, manifesto
  `2026.07-observed-20260714`, testes e
  `docs/regulatory/DOC3040_LAYOUT_REGISTRY.md`.
- Perímetro: datas-base de julho a outubro de 2026; meses anteriores e novembro/2026 em
  diante são bloqueados até existir pacote observado e testado próprio.
- Integridade: URLs BCB e hashes SHA-256 versionam leiaute/domínios, instruções, críticas
  e regras de reconciliação consultados em 14/07/2026.
- XSD: o loader exige documento 3040, origem oficial, nome e hash; como a página oficial
  lista XSD 3045, o manifesto atual não habilita geração nem validação XSD e falha com
  causa explícita.
- Evidência: 6 testes do registry e 11 do contrato aprovados; execução de domínios e
  críticas permanece na Tarefa 12.4.

## Tarefa 12.3 — Geração XML

### Subtarefas

- [x] Gerar cabeçalho, clientes, operações e blocos aplicáveis.
- [x] Gerar vencimentos completos.
- [x] Gerar IPOC conforme regra oficial vigente.
- [x] Gerar totalizadores.
- [x] Remover toda lógica arbitrária, incluindo frações artificiais de ECL.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: gerador determinístico em `src/regulatory/doc3040/generator.py`, API,
  testes e `docs/regulatory/DOC3040_XML_GENERATION.md`.
- Conteúdo: cabeçalho, clientes/operações, vencimentos, garantias, informações
  adicionais, Sicor, CMN 4.966, estágios, perdas, agregações e IPOCs conectados.
- IPOC: composição oficial é recalculada e comparada ao valor-fonte; divergência bloqueia
  a saída.
- Guardrails: nenhum vértice, data, COSIF, totalizador ou valor contábil é inferido; perda
  reconhecida preserva o valor fornecido e não usa fração artificial de ECL.
- Interface: o artefato é `pre-validator`, recebe estado `XSD_AND_CRITICS_PENDING` e não
  é apresentado como XML válido ou pronto para envio.
- Evidência: 6 testes de geração e 17 testes de contrato/registry aprovados.

## Tarefa 12.4 — Validação

### Subtarefas

- [x] Validar XML contra XSD.
- [x] Validar domínios.
- [x] Validar críticas semânticas.
- [x] Validar totalizadores.
- [x] Validar consistência com carteira e ECL.
- [x] Gerar relatório de erros por linha/campo/regra.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/regulatory/doc3040/validation.py`, XSD estrutural derivado, allowlist
  de domínios, API, testes e `docs/regulatory/DOC3040_PREVALIDATION.md`.
- Camadas: XSD derivado com hash, domínios do subconjunto sintético, críticas semânticas
  locais, totalizadores e reconciliação por IPOC com controle de carteira/ECL.
- Relatório: regra, severidade, mensagem, linha, campo e XPath; XML/data-base/artefato
  inválidos falham de forma fechada.
- Limites: `official_xsd_executed=false` e `official_critics_executed=false`; warnings
  impedem confundir pré-validação local com o validador ou homologação BCB.
- Evidência: 7 testes de validação e 23 testes anteriores do Doc3040 aprovados.

## Tarefa 12.5 — Golden files

### Subtarefas

- [x] Criar XML sintético válido.
- [x] Criar arquivos inválidos por categoria de erro.
- [x] Testar regressão por versão de leiaute.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: quatro fixtures, manifesto com hashes,
  `tests/regulatory/test_doc3040_golden_files.py` e
  `docs/regulatory/DOC3040_GOLDEN_FILES.md`.
- Caso positivo: XML sintético reproduzível e localmente pré-validado com carteira/ECL
  reconciliados.
- Casos negativos: ausência de campo XSD, modalidade fora do domínio suportado e
  totalizador semântico divergente.
- Versão: julho-outubro/2026 fixados no pacote observado em 14/07; meses anteriores e
  novembro/2026 em diante permanecem bloqueados.
- Evidência: 7 testes golden/versionamento e 30 testes anteriores do Doc3040 aprovados.

### Critérios de aceite

- [x] O fluxo padrão usa XSD e críticas, não apenas parse XML.
- [x] Nenhum campo regulatório é inventado.
- [x] A interface usa “pré-validador” até homologação oficial.

### Aceite da fase

- O fluxo padrão usa XSD estrutural derivado, domínios versionados, críticas semânticas
  locais e reconciliação carteira/ECL; parse XML isolado não produz aceite.
- A cobertura é deliberadamente limitada ao subconjunto sintético julho-outubro/2026.
  XSD oficial 3040 e execução integral da planilha de críticas BCB permanecem ausentes e
  são expostos no relatório, sem falsa alegação de homologação.
- Contrato, registry, geração, pré-validação e golden files eliminam os defaults e
  cálculos arbitrários do simulador legado.

---

# FASE 13 — Validação independente, MRM e monitoramento

## Objetivo

Criar evidências de que modelos e cálculos funcionam, permanecem estáveis e podem ser contestados.

## Tarefa 13.1 — Framework de validação independente

### Subtarefas

- [x] Criar pacote separado de validação.
- [x] Impedir que o pipeline de desenvolvimento aprove automaticamente o modelo.
- [x] Definir critérios de aprovação, ressalva e rejeição.
- [x] Criar relatório de validação reproduzível.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: `src/validation/model_risk`, política `2026.07.1`, testes de contrato e
  `docs/validation/INDEPENDENT_VALIDATION_FRAMEWORK.md`.
- Independência: submissões de desenvolvimento são obrigatoriamente `not_approved`; a
  identidade, unidade, função e atestado do validador são verificados antes da decisão.
- Decisão: critérios obrigatórios e severidades definem aprovação, ressalva ou rejeição
  sem override silencioso do desenvolvimento.
- Reprodutibilidade: commit, dataset, artefatos, política, evidências e relatório possuem
  hashes/identificadores determinísticos; a ordem de entrada não altera o resultado.
- Limite: a independência é simulada e técnica, sem alegação de aprovação institucional.
- Evidência: 15 testes direcionados integrados ao gate geral, além de Black, Ruff e MyPy.

## Tarefa 13.2 — Backtesting de PD

### Subtarefas

- [x] previsto versus observado.
- [x] por rating, produto, safra e horizonte.
- [x] calibration drift.
- [x] testes de cobertura e intervalos.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: política versionada, `src/validation/backtesting/pd.py`, gerador,
  `docs/validation/PD_BACKTESTING.md` e evidence pack JSON/Markdown com hashes.
- Evidência madura: 233 observações OOT de 2024 em 1m/12m e 30 células agregadas ou
  segmentadas por rating, produto e safra.
- Métodos: previsto versus observado, O/E, erro absoluto, Clopper-Pearson, teste binomial
  exato e drift do erro contra a referência de calibração.
- Decisão: `rejected`; em 12m, PD média 29,4118%, observado 11,5880%, erro/drift de
  17,8238 p.p., acima dos limites objetivos.
- Maturação: 182 linhas de 2025 permanecem sem target e não recebem performance imputada.
- Limite: o 1m usa hazard constante derivado e toda evidência é sintética, sem aprovação
  institucional.
- Evidência de teste: 12 testes direcionados aprovados e artefato golden versionado.

## Tarefa 13.3 — Backtesting de LGD

### Subtarefas

- [x] recuperações previstas versus realizadas.
- [x] coortes fechadas e abertas.
- [x] cura, write-off e garantias.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: política e cálculo independente em `src/validation/backtesting/lgd.py`,
  gerador, `docs/validation/LGD_BACKTESTING.md` e evidence pack JSON/Markdown.
- Fechados: 10 workouts de 2022–2023, com LGD prevista/realizada, recuperação monetária,
  MAE/RMSE e cortes por coorte, cura/write-off e garantia.
- Abertos: 7 workouts censurados em quatro coortes de 2024–2025; EAD, recuperações até a
  data, cura, write-off e garantia são inventariados sem LGD final imputada.
- Decisão: `rejected`; amostra 10 versus mínimo 100, MAE 35,8173% e RMSE 45,2035%,
  contra limites de 15% e 20%.
- Limite: o holdout já participou da seleção, as previsões dos abertos não foram
  preservadas e toda a evidência é sintética.
- Evidência de teste: 14 testes direcionados aprovados e artefato golden versionado.

## Tarefa 13.4 — Backtesting de EAD

### Subtarefas

- [x] saldo/drawdown previsto versus realizado.
- [x] CCF por produto e faixa de utilização.

### Registro de execução

- Data: 14 de julho de 2026.
- Entregáveis: política e cálculo independente em `src/validation/backtesting/ead.py`,
  gerador, `docs/validation/EAD_BACKTESTING.md` e evidence pack JSON/Markdown.
- Amortizados: 24/24 saldos reconciliados, evidência mecânica e não preditiva.
- Rotativos: 4 linhas, EAD média prevista 6.280,7227 versus 4.494,1200 realizada e MAE
  relativo de 40,3625%, acima do limite de 15%.
- CCF: MAE 3,9723 p.p. e RMSE 5,4894 p.p., com cortes por credit card/overdraft e
  utilização baixa/média; volume 4 versus mínimo 100.
- Decisão: `rejected` por volume e erro de EAD; off-balance permanece excluído por não
  possuir eventos realizados.
- Evidência de teste: 14 testes direcionados aprovados e artefato golden versionado.

## Tarefa 13.5 — Backtesting de ECL

### Subtarefas

- [x] ECL inicial versus perdas realizadas.
- [x] attribution analysis: volume, estágio, PD, LGD, EAD, cenário e overlay.
- [x] análise por safra e ciclo econômico.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: política e cálculo em `src/validation/backtesting/ecl.py`, gerador `scripts/generate_ecl_backtest_report.py`, `docs/validation/ECL_BACKTESTING.md` e evidence pack JSON/Markdown.
- Resultados: 80 observações do conjunto de dados sintéticos analisadas; as observações maduras são zero devido à ausência de histórico longitudinal ligando ECL inicial a perdas reais por contrato.
- Decisão: `rejected` devido à amostra nula de outcomes maduros e ausência de snapshots comparáveis para a waterfall de atribuição.
- Evidência de teste: 12 testes direcionados em `tests/validation/test_ecl_backtesting.py` aprovados.

## Tarefa 13.6 — Monitoramento

### Subtarefas

- [x] data quality e schema drift.
- [x] PSI e distribuição.
- [x] performance e calibração.
- [x] estabilidade de staging.
- [x] monitoramento de cenários.
- [x] alertas e critérios de recalibração.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: estrutura em `src/validation/monitoring/models.py`, métricas em `src/validation/monitoring/metrics.py`, `docs/validation/MONITORING.md`.
- Monitoramento estatístico: implementado cálculo de PSI (Population Stability Index) para drift, teste de calibração em desvio de métricas, e testes de estabilidade de estágio.
- Monitoramento operacional: implementado detector de schema drift (colunas ausentes/adicionadas, tipo de dados e nulos) e monitoramento de desvio macroeconômico em trajetórias de cenário.
- Evidência de teste: 11 testes em `tests/validation/test_monitoring.py` aprovados.

## Tarefa 13.7 — Model cards e evidence pack

### Subtarefas

- [x] PD model card.
- [x] SICR model/policy card.
- [x] LGD model card.
- [x] EAD model card.
- [x] ECL methodology document.
- [x] validation reports.
- [x] limitation register.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: `docs/models/PD_MODEL_CARD.md`, `docs/models/LGD_MODEL_CARD.md`, `docs/models/EAD_MODEL_CARD.md`, `docs/validation/LIMITATION_REGISTER.md` e relatórios de validação integrados.
- Model Cards: documentam premissas, escopo, performance, calibração e restrições de cada modelo.
- Limitações: o Limitation Register consolida deficiências amostrais da base de holdout (233 PD, 10 LGD, 4 CCF) e o colapso de calibração do Ridge/Isotonic no OOT.

### Critérios de aceite

- [x] Todo modelo pode ser aprovado ou rejeitado por critérios objetivos.
- [x] Há evidência independente de cálculo e performance.

### Aceite da fase

- A Fase 13 foi aceita com a implementação do framework de validação e model risk, geradores de backtesting para todos os componentes (PD, LGD, EAD, ECL), e rotinas de monitoramento operacional/estatístico.
- Conforme as políticas de validação, os modelos de PD, LGD e EAD rotativo foram objetivamente REJEITADOS devido a limitações amostrais e calibragem inadequada na base de holdout, garantindo governança rígida e sem falsos pareceres de conformidade.

---

# FASE 14 — Persistência, APIs, segurança, auditoria e frontend

## Objetivo

Integrar o núcleo reconstruído à plataforma sem comprometer rastreabilidade.

## Tarefa 14.1 — Persistência versionada

### Subtarefas

- [x] Criar migrations.
- [x] Persistir contratos, snapshots, modelos, cenários e resultados.
- [x] Persistir lineage e hashes.
- [x] Implementar idempotência e reprocessamento.
- [x] Separar dados operacionais, modelos e auditoria.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: manager explícito e fail-closed, migrations SQLite/PostgreSQL versionadas por checksum e repositório em `src/infrastructure/database`.
- Persistência: contratos, snapshots, observações macro, modelos, cenários, execuções revisionadas, resultados por período/cenário e eventos de linhagem possuem fronteiras lógicas próprias.
- Exatidão: `Decimal` é serializado sem ponto flutuante; SQLite usa texto decimal exato e PostgreSQL usa `NUMERIC`.
- Idempotência: identidades repetidas com o mesmo hash são reutilizadas; colisões divergentes falham; reprocessamento explícito cria revisão ligada à execução anterior.
- Segurança operacional: PostgreSQL nunca cai silenciosamente para SQLite e migrations aplicadas não podem mudar de checksum.
- Documentação: `docs/architecture/PERSISTENCE_VERSIONING.md` registra configuração, decisões e limitações.
- Evidência: testes automatizados cobrem migrations, separação, ausência de usuários fictícios, hashes, conflitos, reprocessamento, precisão monetária e imutabilidade da linhagem.

## Tarefa 14.2 — APIs

### Subtarefas

- [x] Versionar endpoints.
- [x] Criar endpoints para cálculo individual e carteira.
- [x] Criar jobs assíncronos para lote.
- [x] Validar schemas de entrada.
- [x] Expor decomposição por período/cenário.
- [x] Expor relatórios e evidências.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: application factory e contratos estritos em `src/interfaces/api`, endpoints `/api/v1/ecl/*` e migration `0002_api_jobs.sql`.
- Integração: a API usa o motor canônico de cenário e a persistência versionada; o rascunho Antigravity baseado no pipeline legado, `float` e hashes fictícios não foi promovido.
- Lote: pedidos de até 10.000 contratos retornam `202`; estado, hash, resultado e código de falha ficam persistidos. O executor em processo é uma limitação explícita da versão demonstrativa.
- Rastreabilidade: respostas expõem cenário/período e a rota de evidência retorna linhagem, revisão e hashes persistidos.
- Schemas: campos extras, taxas, dinheiro, horizontes, SHA-256, commit e cobertura dos cenários são validados sem defaults silenciosos.
- Limite: v1 expõe curvas Stage 1/Stage 2 já validadas; Stage 3/POCI HTTP, autenticação, rate limit e fila distribuída permanecem tarefas posteriores.
- Documentação: `docs/api/ECL_API_V1.md` contém quickstart, endpoints, contratos e limites.
- Evidência: testes de API e persistência cobrem OpenAPI, cálculo, decomposição, idempotência, evidência, lote, jobs, validação e respostas 404.

## Tarefa 14.3 — Segurança e segregação

### Subtarefas

- [x] Revisar RBAC.
- [x] Separar cálculo, aprovação, exportação e auditoria.
- [x] Implementar confirmação de operações críticas.
- [x] Revisar JWT, sessões, senha e rate limit.
- [x] Redigir threat model.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: pacote `src/security`, migration `0003_security.sql`, autenticação e autorização integradas à API v1 e bootstrap interativo sem senha em argumentos.
- RBAC: ANALYST, MANAGER, AUDITOR e ADMIN possuem permissões explícitas sem curinga; cálculo, aprovação, exportação, leitura de auditoria e gestão de usuários permanecem segregados.
- Autenticação: bcrypt direto, JWT HS256 curto com segredo externo de no mínimo 32 bytes, issuer/audience, claims obrigatórias, `jti`, sessão persistida e logout revogável.
- Operações críticas: cálculo de carteira exige confirmação curta, de uso único, ligada a usuário, ação e SHA-256 canônico do payload.
- Abuso: rate limit cobre login e usuário/permissão; a limitação multiworker está documentada e não é ocultada.
- Threat model: `docs/security/THREAT_MODEL.md` distingue controles implementados, dependências do ambiente e riscos residuais; alegações falsas de NTLM e fallback foram removidas.
- Evidência: Black, Ruff e MyPy aprovados; 513 testes canônicos aprovados com 91,22% de cobertura; regressão legada com 109 aprovados e 16 ignorados. Os testes de segurança cobrem configuração fail-closed, senha, sessão/revogação, matriz RBAC, confirmação, rate limit e respostas HTTP 401/403/404/429.

## Tarefa 14.4 — Auditoria

### Subtarefas

- [x] Logar usuário, ação, entrada, versão e resultado.
- [x] Criar trilha imutável para execução ECL.
- [x] Registrar overrides e overlays.
- [x] Registrar exportações e validações.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: `src/audit`, migration `0004_audit_events.sql`, integração com a API v1 e rota protegida `/api/v1/audit/events`.
- Minimização: entradas e resultados são preservados por SHA-256; ator, papel, ação, recurso, execução, estado, versões, IP e timestamp compõem o documento canônico sem copiar payload sensível.
- Imutabilidade: triggers bloqueiam atualização/exclusão e cada evento encadeia o hash anterior; o verificador detecta adulteração mesmo após bypass privilegiado do trigger.
- Cobertura operacional: login/logout, rate limit, confirmação crítica, cálculo individual, carteira, leitura de evidência e leitura de auditoria são integrados; falhas relevantes também geram evento.
- Contratos adicionais: overrides, overlays, exportações e validações possuem métodos tipados, justificativa obrigatória quando aplicável e testes dedicados.
- Segregação: somente AUDITOR e ADMIN possuem `audit:read`; consultar a trilha também é auditado.
- Documentação: `docs/architecture/AUDIT_TRAIL.md` registra contrato, minimização, cadeia, eventos e limites multiwriter/WORM.
- Evidência: 30 testes focados aprovados com 93,18% de cobertura nos pacotes auditados; Black, Ruff e MyPy aprovados; regressão canônica com 518 testes aprovados e 91,16% de cobertura; regressão legada com 109 aprovados e 16 ignorados.

## Tarefa 14.5 — Frontend

### Subtarefas

- [x] Remover dashboards que exibem dados mockados sem aviso.
- [x] Exibir estágio, justificativas e comparação com originação.
- [x] Exibir curvas PD/LGD/EAD.
- [x] Exibir ECL por período e cenário.
- [x] Exibir reconciliação, overlays e pisos.
- [x] Exibir status de validação e limitações.
- [x] Manter visualização de dados sintéticos claramente identificada.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: workspace React ativo em `frontend/src/pages/ecl/ECLDashboardPage.tsx`, cliente tipado em `frontend/src/lib/api/ecl_api.ts`, sessão JWT real, contrato `stage_assessment`, evidência periódica expandida, endpoint versionado de limitações e `docs/frontend/ECL_EVIDENCE_WORKSPACE.md`.
- Fonte: o workspace consulta exclusivamente execuções persistidas e autorizadas; falhas exibem indisponibilidade sem fallback, valores ou status inventados. Dashboards estáticos, calculadora didática, agente e demais rotas mockadas foram removidos do grafo ativo.
- Rastreabilidade: estágio/rating/PD de originação e atuais, motivos, curvas PD/LGD/EAD, ECL por período/cenário e hashes individuais são exibidos com revisão e hash de linhagem.
- Reconciliação: ECL por cenário e ponderada são derivadas dos resultados persistidos; overlays, piso e ECL reportado ausentes ficam explicitamente `NOT_APPLIED`/`null`, nunca zero presumido.
- Validação: o Limitation Register é servido com caminho e SHA-256, sob RBAC e auditoria, e permanece `LIMITED`.
- Segurança: removidos usuários, senhas e logs fictícios do navegador; JWT revogável fica em `sessionStorage`, com autorização efetiva sempre no servidor.
- Evidência: 11 testes focados aprovados; gate único com Black, Ruff, MyPy, 522 testes canônicos e 91,17% de cobertura, 109 testes legados aprovados/16 ignorados e build TypeScript/Vite de produção aprovado. O build frontend passou a integrar `scripts/quality.ps1`.

## Tarefa 14.6 — Agente de IA

### Subtarefas

- [x] Restringir o agente a dados persistidos e autorizados.
- [x] Remover respostas baseadas em métricas inventadas.
- [x] Exigir citações internas de execução e documentação.
- [x] Implementar guardrails para não afirmar conformidade oficial.
- [x] Testar prompt injection e acesso indevido.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: `src/agent`, rota `POST /api/v1/agent/query`, página `frontend/src/pages/agent/EvidenceAgentPage.tsx`, documentação `docs/agent/GROUNDED_EVIDENCE_AGENT.md` e extensão do threat model.
- Grounding: o agente é determinístico e somente leitura; recebe uma execução explícita, exige `ecl:result:read` e consulta apenas `calculation_executions`, `calculation_results` e o Limitation Register por caminhos fixos/SQL parametrizado.
- Citações: toda resposta factual inclui identificadores e hashes de linhagem, coleção de resultados e documento; classificação permanece `SYNTHETIC`, `LIMITED` e conformidade oficial `NOT_ASSESSED`.
- Guardrails: não há LLM, web, RAG, shell ou seleção dinâmica de ferramenta; tentativas de ignorar regras, revelar segredos, burlar RBAC, ativar modo desenvolvedor ou executar comandos são recusadas antes de ler a execução.
- Legado: o router aleatório de `backend/agente` foi desmontado do servidor legado e removido do grafo ativo; o código histórico permanece congelado e explicitamente fora da fronteira confiável.
- Estado da execução: o repositório agora muda uma execução de `STARTED` para `COMPLETED` somente após resultados e evento de linhagem persistirem, impedindo que o agente apresente cálculo incompleto como concluído.
- Evidência: 26 testes focados aprovados; gate único com Black, Ruff, MyPy, 527 testes canônicos e 91,18% de cobertura, 109 testes legados aprovados/16 ignorados e build TypeScript/Vite de produção aprovado. Os testes cobrem grounding, auditoria minimizada, citações, conformidade, quatro padrões de prompt injection, autenticação e RBAC.

### Critérios de aceite

- [x] Toda informação exibida é rastreável a dados e versão.
- [x] Nenhum mock silencioso permanece em produção/demo.

---

# FASE 15 — CI/CD, observabilidade, desempenho e segurança técnica

## Objetivo

Transformar a plataforma em um sistema reproduzível e confiável.

## Tarefa 15.1 — CI

### Subtarefas

- [x] Lint e formatação.
- [x] type checking.
- [x] testes unitários e integração.
- [x] testes quantitativos.
- [x] cobertura.
- [x] dependency audit.
- [x] secret scan.
- [x] build de containers.

### Registro de execução

- Data: 15 de julho de 2026.
- Pipeline: `.github/workflows/ci.yml`, com actions fixadas por SHA, permissões mínimas,
  cancelamento concorrente e execução em todo push, pull request ou disparo manual.
- Reprodutibilidade: CPython 3.13.7 e resolução congelada em `requirements-ci.lock`;
  frontend instalado por `npm ci` a partir do lockfile auditado.
- Qualidade local: `scripts/quality.ps1` delega ao runner multiplataforma
  `scripts/quality.py`; Black, Ruff e MyPy verdes, 532 testes canônicos aprovados,
  cobertura de 91,19%, 118 testes legados aprovados e 7 skips esperados.
- Segurança: migração de `python-jose` para PyJWT, atualização das dependências
  vulneráveis e auditorias `pip-audit`/`npm audit` sem vulnerabilidades conhecidas.
- Containers: imagens canônicas separadas para API e frontend, execução sem
  privilégio, healthchecks e ausência de segredos embutidos.
- Evidência GitHub: run `29441776705` verde no commit `37c2732`, incluindo os jobs
  de qualidade, dependency audit, Gitleaks, `Container / api` e
  `Container / frontend`.
- Documentação operacional: `docs/operations/CI_PIPELINE.md`.

## Tarefa 15.2 — CD e ambientes

### Subtarefas

- [x] ambientes local, test e demo.
- [x] configurações separadas.
- [x] migrations automáticas controladas.
- [x] rollback.
- [x] release notes.

### Registro de execução

- Data: 15 de julho de 2026.
- Ambientes: perfis estritos e sem segredos em `config/environments/`, exemplos
  `.env.local.example`, `.env.test.example` e `.env.demo.example`, bancos/caminhos
  separados e compose canônico em `compose.yaml`.
- Migrations: startup controlado por `apply`, `validate` ou `disabled`; `demo`
  exige `validate` e falha quando o schema não está corrente. Aplicação explícita
  pré-promoção usa `scripts/deploy.py migrate`; versões e checksums permanecem
  imutáveis e transacionais.
- Entrega: `.github/workflows/cd.yml` gera plano auditável, usa GitHub Environment
  e publica imagens API/frontend no GHCR por tag; `demo` aceita somente SemVer.
- Rollback: histórico atômico impede reutilizar uma tag para outro commit e restaura
  a aplicação anterior; schema é deliberadamente forward-only, sem down migration
  automática ou alegação enganosa de reversibilidade.
- Release notes: categorias em `.github/release.yml`, geração automática para tags
  `vX.Y.Z` e checklist em `docs/operations/RELEASE_NOTES_TEMPLATE.md`.
- Evidência: 30 testes focados aprovados, compose validado para o perfil local e
  pipeline integral verde com 537 testes canônicos, cobertura de 91,13%, 118 testes
  legados, 7 skips esperados e build frontend.
- Documentação: `docs/operations/ENVIRONMENTS_AND_DELIVERY.md`.

## Tarefa 15.3 — Observabilidade

### Subtarefas

- [x] logs estruturados.
- [x] métricas de API e jobs.
- [x] tracing.
- [x] dashboards Prometheus/Grafana ou equivalente.
- [x] alertas.

### Registro de execução

- Data: 15 de julho de 2026.
- Logs: formatter JSON UTC reaproveitado e endurecido em
  `src/infrastructure/logging/`, com serviço/versão/ambiente e correlação
  allowlisted; payloads, credenciais, clientes e resultados não são logados.
- Tracing: middleware propaga `traceparent` W3C válido, cria span de servidor e
  devolve `traceparent`/`X-Request-ID`; jobs acrescentam `job_id` ao contexto.
- Métricas: `/metrics` expõe contadores e histogramas Prometheus para requests,
  latência, jobs por status/duração/em andamento e identidade do build; labels usam
  templates de rota e classes de status para limitar cardinalidade.
- Jobs: o fluxo real de carteira registra início, sucesso/falha, duração e gauge;
  falhas antes ou durante o processamento também encerram o sinal de execução.
- Operação: Prometheus, Grafana provisionado e dashboard entram pelo profile
  `observability` do compose; regras cobrem indisponibilidade, 5xx, falha de lote e
  job travado, sem presumir Alertmanager institucional.
- Evidência: configurações YAML/JSON e compose válidos; 17 testes focados aprovados;
  pipeline integral verde com 542 testes canônicos, 91,22% de cobertura, 118 testes
  legados, 7 skips esperados e build frontend.
- Documentação: `docs/operations/OBSERVABILITY.md`.

## Tarefa 15.4 — Performance

### Subtarefas

- [x] benchmark de 10 mil, 100 mil e 1 milhão de contratos sintéticos.
- [x] processamento vetorizado e particionado.
- [x] filas para lote.
- [x] cache apenas quando seguro e versionado.
- [x] testes de concorrência.

### Registro de execução

- Data: 15 de julho de 2026.
- Processamento: `PartitionedStage1Processor` consome iteráveis em partições de até
  10 mil contratos, agrega centavos com NumPy sob verificação de overflow e não
  retém a carteira nem todos os resultados em memória.
- Cache: LRU limitado e thread-safe; a chave inclui o perfil quantitativo completo,
  além das versões e hashes do conjunto de cenários e da política macroeconômica.
- Filas: executor local limitado por workers e capacidade aplica backpressure com
  HTTP 503 auditável; jobs interrompidos por reinício são marcados
  `FAILED/PROCESS_RESTARTED` para reenvio explícito.
- Benchmark sintético: 10 mil em 1,148983 s, 100 mil em 8,430652 s e 1 milhão em
  69,049503 s; no maior volume, vazão de 14.482,36 contratos/s e pico Python de
  10.107.428 bytes, aprovando o alvo demonstrativo de 120 s e 512 MiB.
- Limitação: a amostra usa 64 perfis determinísticos com IDs únicos e a fila é
  local ao processo; a evidência não constitui SLA ou dimensionamento institucional.
- Evidência: `evidence/performance/batch-benchmark.json`, 20 testes focados e gate
  integral verde com 550 testes canônicos, 91,22% de cobertura, 118 testes legados,
  7 skips esperados e build frontend.
- Documentação: `docs/operations/PERFORMANCE.md`.

## Tarefa 15.5 — Segurança

### Subtarefas

- [x] SAST e dependency scan.
- [x] revisão de autenticação/autorização.
- [x] proteção de arquivos exportados.
- [x] validação de uploads.
- [x] política de retenção e exclusão.
- [x] pentest automatizado básico.

### Registro de execução

- Data: 15 de julho de 2026.
- SAST/SCA: o gate executa Ruff Security sobre todo `src`; SQL dinâmico foi
  restringido por allowlist. `pip-audit` e `npm audit` locais não encontraram
  vulnerabilidades conhecidas, e Gitleaks permanece obrigatório na CI.
- Autenticação/autorização: revisão confirmou segredo externo, JWT com algoritmo,
  issuer/audience e sessão fixos, bcrypt, revogação, rate limit, RBAC sem curingas e
  confirmação crítica ligada ao usuário/ação/hash; headers defensivos foram
  adicionados a todas as respostas.
- Arquivos: exports usam raiz privada, nome gerado pelo servidor, criação exclusiva,
  hash e permissões restritas. Uploads futuros têm allowlist CSV/JSON/XML, limite de
  tamanho, validação de MIME/estrutura/UTF-8 e bloqueio de traversal, DTD e entidades.
- Retenção: política `2026.07.1` e comando operacional removem somente sessões,
  confirmações, jobs e exports vencidos; resultados, linhagem e auditoria ficam fora
  da exclusão automática, e cada expurgo gera evento `RETENTION_PURGE`.
- Teste ofensivo: regressões automatizadas cobrem SQL injection no login, JWT
  `alg=none`, acesso anônimo/indevido, método não exposto e controles de arquivos.
  A evidência não é apresentada como pentest independente ou homologação.
- Evidência: 23 testes focados aprovados; gate integral com SAST verde, 562 testes
  canônicos, 91,14% de cobertura, 118 testes legados, 7 skips esperados e build
  frontend; documentação em `docs/security/SECURITY_OPERATIONS.md`.

### Critérios de aceite

- [x] CI verde é obrigatório para merge.
- [x] O sistema processa o volume-alvo definido.
- [x] Falhas são observáveis e recuperáveis.

---

# FASE 16 — Testes E2E, pacote de evidências e release 10/10

## Objetivo

Demonstrar de ponta a ponta que o sistema atende ao escopo declarado.

## Tarefa 16.1 — Jornada E2E completa

### Subtarefas

- [x] Gerar carteira sintética.
- [x] Treinar modelos.
- [x] Validar e submeter os modelos ao gate de aprovação, preservando a decisão `not_approved`.
- [x] Classificar estágios.
- [x] Calcular ECL.
- [x] Aplicar overlays e pisos separadamente.
- [x] Persistir e reconciliar resultados.
- [x] Gerar reportes.
- [x] Pré-validar Doc3040.
- [x] Visualizar e auditar no frontend.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: `src/application/e2e.py`, `scripts/e2e_pipeline.py`, regressão
  `tests/application/test_e2e_journey.py`, guia `docs/operations/E2E_JOURNEY.md`
  e pacote reproduzível em `evidence/e2e/`.
- Fábrica: 24 datasets, 16.628 linhas e manifesto SHA-256; os Parquets são
  temporários e somente o manifesto resumido é versionado como evidência.
- Modelos: PD, SICR, LGD e EAD foram treinados/avaliados pelos fluxos canônicos;
  o gate devolveu `not_approved` para todos e os bloqueios foram preservados.
- ECL: econômico R$ 4,00, overlay R$ 1,00, piso R$ 0,00 e final R$ 5,00;
  quatro resultados persistidos e ledger reconciliado com hash imutável.
- Documento 3040: candidato sintético aprovado na pré-validação derivada local;
  XSD oficial e críticas BCB não foram executados e permanecem avisos explícitos.
- Resultado: `COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS`, adequado a demonstração
  sintética e sem alegação de homologação institucional.

## Tarefa 16.2 — Pacote de golden cases

### Subtarefas

- [x] Publicar inputs, fórmulas e outputs esperados.
- [x] Incluir planilha de verificação independente.
- [x] Automatizar comparação no CI.

### Registro de execução

- Data: 15 de julho de 2026.
- Publicados oito casos em `docs/golden_cases/golden_cases.json`, preservando a
  fixture canônica `tests/fixtures/golden/ecl_cases.csv` como baseline do motor.
- Criada `docs/golden_cases/ecl_golden_cases.xlsx` com inputs editáveis, fórmulas
  visíveis, schedule independente de modificação e checks reconciliados.
- Adicionado comparador `Decimal` independente em
  `src/validation/golden_cases.py`, sem importar o motor ECL, e regressão CI em
  `tests/validation/test_golden_case_package.py`.
- Resultado focado: 10 testes aprovados (oito do motor e dois do pacote),
  tolerância monetária zero e todos os checks da planilha em `OK`.

## Tarefa 16.3 — Pacote regulatório

### Subtarefas

- [x] Exportar matriz de rastreabilidade.
- [x] Exportar cobertura de testes por requisito.
- [x] Exportar limitações e itens não aplicáveis.
- [x] Exportar versões de leiaute e normas consultadas.

### Registro de execução

- Data: 15 de julho de 2026.
- Entregáveis: exportador `src/regulatory/traceability/package.py`, CLI
  `scripts/export_regulatory_package.py`, regressões determinísticas e pacote em
  `evidence/regulatory/`.
- Snapshot: 27 requisitos, cobertura por caminhos e funções de teste, dois itens
  não aplicáveis, catálogo de fontes e registry de leiaute com hashes.
- Gate: seis requisitos permanecem `partial`/`planned`; o manifesto os preserva
  como bloqueadores e qualifica o escopo como pré-validação sintética, não
  certificação.

## Tarefa 16.4 — Documentação de portfólio

### Subtarefas

- [x] Reescrever README principal.
- [x] Criar arquitetura e diagramas.
- [x] Criar quickstart de um comando.
- [x] Criar tutorial de ECL.
- [x] Criar guia para entrevista técnica.
- [x] Criar exemplos de API.
- [x] Criar screenshots e demo, sem dados reais.

### Registro de execução

- Data: 15 de julho de 2026.
- README: substituído o texto externo incorreto por um mapa conciso do núcleo
  canônico, quickstart de um comando, limites de uso e links para as evidências.
- Arquitetura: `docs/architecture/SYSTEM_ARCHITECTURE.md` documenta camadas,
  fluxo da execução e decisões fail-closed com diagramas Mermaid.
- Aprendizado: `docs/tutorials/ECL_TUTORIAL.md` e
  `docs/portfolio/TECHNICAL_INTERVIEW_GUIDE.md` explicam cálculo, reconciliação,
  staging, governança e respostas conservadoras para apresentação técnica.
- API: exemplo JSON validado pelo schema canônico e comandos de autenticação,
  cálculo, consulta e limitações publicados em `docs/api/`.
- Demo: captura real do frontend React contra API e SQLite efêmeros, usando
  somente fixture sintético; nenhum dado ou segredo institucional foi incluído.
- Guardrails: documentação rejeita o pipeline legado como fonte canônica,
  fallback silencioso, pesos macroeconômicos inventados e alegações de
  certificação/homologação.
- Testes: contrato documental verifica caminhos, alertas, fixture e presença da
  captura publicável.

## Tarefa 16.5 — Revisão final de notas

### Subtarefas

- [x] Avaliar arquitetura.
- [x] Avaliar PD.
- [x] Avaliar LGD.
- [x] Avaliar EAD.
- [x] Avaliar ECL.
- [x] Avaliar staging.
- [x] Avaliar regulação.
- [x] Avaliar validação.
- [x] Avaliar segurança.
- [x] Avaliar experiência e portfólio.
- [x] Registrar evidências para cada nota 10/10.

### Critérios de aceite da release

- [x] Setup e demo executam do zero.
- [x] Todos os testes passam.
- [x] Golden cases reconciliam.
- [x] OOT e backtesting estão publicados.
- [x] Nenhuma afirmação de certificação indevida permanece.
- [x] Toda saída regulatória é versionada e pré-validada.
- [x] Todo resultado é rastreável a dados, modelo, política, cenário e código.
- [x] O projeto está pronto para adaptação a dados reais de uma instituição, sem alegar homologação prévia.

### Registro de execução

- Data: 15 de julho de 2026.
- Semântica: 10/10 mede completude técnica dos critérios de estado-alvo no
  escopo sintético; não significa aprovação quantitativa ou regulatória.
- Scorecard: dez dimensões, evidências e limites residuais publicados em
  `evidence/release/final_scorecard.json` e `docs/FINAL_RELEASE_ASSESSMENT.md`.
- Decisões preservadas: PD, SICR, LGD e EAD `not_approved`; backtesting ECL
  rejeitado; Doc3040 `PREVALIDATED_DERIVED_XSD`, sem XSD/críticas oficiais.
- Setup limpo: source archive do commit `22b1e39` em caminho curto isolado,
  CPython 3.13, `venv` novo, instalação editável e smoke import aprovados.
- Demo limpa: jornada E2E reconciliada, persistida e concluída como
  `COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS`; evidência resumida em
  `evidence/release/setup_smoke.json`.
- Robustez: quickstart passou a contornar Execution Policy explicitamente; o
  runner E2E usa fingerprint determinístico quando `.git` não está disponível.
- Gate: Black, Ruff/SAST e MyPy verdes; 578 testes canônicos com 91,25% de
  cobertura, 118 legados aprovados/7 ignorados e build React aprovado.
- Claims: TODO obsoleto substituído, DDL/telas/módulos legados qualificados e
  varredura final limitada a menções negativas ou de guardrail.

---

# 17. Ordem de execução e dependências

| Ordem | Fase | Dependência principal |
|---:|---|---|
| 1 | Fase 0 | nenhuma |
| 2 | Fase 1 | Fase 0 |
| 3 | Fase 2 | Fases 0 e 1 |
| 4 | Fase 3 | Fases 1 e 2 |
| 5 | Fase 4 | Fases 1 e 3 |
| 6 | Fase 5 | Fases 3 e 4 |
| 7 | Fase 6 | Fase 5 |
| 8 | Fase 7 | Fases 3, 4 e 6 |
| 9 | Fase 8 | Fases 3, 4 e 6 |
| 10 | Fase 9 | Fases 3, 5, 7 e 8 |
| 11 | Fase 10 | Fases 4 a 9 |
| 12 | Fase 11 | Fases 2 e 10 |
| 13 | Fase 12 | Fases 2, 10 e 11 |
| 14 | Fase 13 | Fases 5 a 12 |
| 15 | Fase 14 | Fases 1, 10, 12 e 13 |
| 16 | Fase 15 | Todas as fases técnicas em andamento |
| 17 | Fase 16 | Fases 0 a 15 |

---

# 18. Suítes mínimas de regressão por marco

## Marco A — Fundação

Após Fases 0 a 3:

- [x] lint;
- [x] type checking;
- [x] testes de domínio;
- [x] testes do gerador;
- [x] anti-leakage;
- [x] reprodutibilidade.

## Marco B — Modelos

Após Fases 4 a 9:

- [x] testes de cashflow;
- [x] PD OOT;
- [x] LGD workout;
- [x] EAD/CCF;
- [x] staging;
- [x] cenários;
- [x] model cards.

## Marco C — ECL e regulação

Após Fases 10 a 13:

- [x] golden cases;
- [x] reconciliação;
- [x] Stage 3;
- [x] POCI;
- [x] pisos e overlays;
- [x] Doc3040 XSD/semântica;
- [x] backtesting.

## Marco D — Produto

Após Fases 14 a 16:

- [x] API;
- [x] persistência;
- [x] RBAC;
- [x] auditoria;
- [x] E2E;
- [x] carga;
- [x] segurança;
- [x] demo do zero.

---

# 19. Entregáveis finais obrigatórios

- [x] `docs/PROJECT_AUDIT_AND_TARGET_STATE.md` atualizado.
- [x] `docs/MASTER_BACKLOG.md` concluído.
- [x] `docs/SCOPE.md`.
- [x] `docs/GLOSSARY.md`.
- [x] matriz de rastreabilidade regulatória.
- [x] arquitetura e ADRs.
- [x] fábrica de dados sintéticos.
- [x] data cards.
- [x] model cards de PD, SICR, LGD e EAD.
- [x] metodologia ECL.
- [x] relatórios de validação.
- [x] golden cases.
- [x] pacote Doc3040 sintético.
- [x] CI/CD.
- [x] observabilidade.
- [x] README e quickstart.
- [x] relatório final de limitações.
- [x] release versionada (`v2.0.2`).

### Fechamento da modernização

- Data: 15 de julho de 2026.
- Release: `v2.0.2`, sucessora da release histórica `v1.0.0` e correspondente à
  reconstrução canônica descrita neste backlog.
- A candidata `v2.0.0` foi mantida imutável após a entrega revelar uma invocação
  sem o root do repositório no `sys.path`; `v2.0.1` também foi mantida imutável
  ao revelar import prematuro do driver de banco. `v2.0.2` cobre ambos os casos,
  inclusive com subprocesso Python `-S` sem dependências de runtime.
- O scan agregado da primeira integração na `main` identificou quatro strings
  históricas exclusivamente sintéticas em testes/documentação; os fingerprints
  exatos foram classificados em `.gitleaksignore`, sem regra ampla de exclusão.
- Gates locais finais: Black, Ruff, Ruff SAST e MyPy aprovados; 581 testes
  canônicos aprovados com 91,25% de cobertura; 118 testes legados aprovados, 7
  ignorados por dependência opcional; build React aprovado.
- Jornada E2E regenerada contra `20411a3e8e79`, concluída como
  `COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS`, com ECL reconciliada e Doc3040 somente
  `PREVALIDATED_DERIVED_XSD`.
- A completude do backlog não promove modelos nem remove blockers: PD, SICR, LGD
  e EAD permanecem `not_approved`; validação institucional, XSD/críticas oficiais,
  dados reais governados e pentest independente continuam fora do escopo sintético.

---
