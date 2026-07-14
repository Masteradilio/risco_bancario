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

- [ ] Ler integralmente `docs/PROJECT_AUDIT_AND_TARGET_STATE.md`.
- [ ] Ler integralmente este `docs/MASTER_BACKLOG.md`.
- [ ] Inspecionar o código relacionado à tarefa.
- [ ] Identificar dependências, duplicações e riscos de regressão.
- [ ] Registrar no próprio backlog o plano específico da tarefa, quando necessário.

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

- [ ] Não inventar regra regulatória.
- [ ] Não declarar certificação oficial.
- [ ] Não usar dados reais ou PII.
- [ ] Não usar variáveis latentes do gerador sintético como features.
- [ ] Não preencher dados regulatórios ausentes com defaults silenciosos.
- [ ] Não usar o conjunto de teste para treino, tuning, calibração ou seleção de threshold.
- [ ] Não manter duas implementações canônicas da mesma regra.
- [ ] Usar `Decimal` para valores monetários no domínio e definir política de arredondamento.
- [ ] Versionar dados, modelos, cenários, políticas, regras e resultados.
- [ ] Garantir determinismo por seed e configuração.
- [ ] Tratar toda integração externa como dependência versionada e observável.

### 2.4 Definition of Done global

Uma tarefa somente pode ser concluída quando:

- [ ] código implementado;
- [ ] testes aprovados;
- [ ] documentação atualizada;
- [ ] rastreabilidade regulatória atualizada, quando aplicável;
- [ ] nenhuma regressão conhecida;
- [ ] logs e erros tratados;
- [ ] commit e push realizados;
- [ ] backlog e changelog atualizados.

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
- Auditoria OOT: challenger calibrado obteve ROC AUC 0,7554, AP 0,4129 e Brier 0,1493, mas PD média 0,3075 versus taxa 0,1750; não foi promovido.
- Survival boosting: ROC AUC 0,3430/AP 0,0421 com 3 eventos de validação, status `insufficient_hazard_events`.
- Transições: 34 células empíricas mensais produto/rating, estimadas somente em treino e normalizadas por origem, sem preenchimento silencioso.
- Registry: logística é champion provisório `not_approved`; boosting, survival e matrizes permanecem challengers com bloqueios explícitos.
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

- [ ] AUC, Gini, KS e PR-AUC.
- [ ] Brier Score e Log Loss.
- [ ] calibration plot e expected calibration error.
- [ ] testes binomiais por rating.
- [ ] observado versus esperado.
- [ ] estabilidade, PSI e backtesting.
- [ ] análise de viés e segmentos.

### Critérios de aceite

- [ ] O teste OOT nunca é usado no desenvolvimento.
- [ ] Lifetime PD depende do prazo real e da curva temporal.
- [ ] Métricas sintéticas são identificadas como sintéticas.
- [ ] Existe model card completo.

---

# FASE 6 — SICR, staging, default, cura e POCI

## Objetivo

Criar um único motor oficial de classificação de estágio.

## Tarefa 6.1 — Baseline de originação

### Subtarefas

- [ ] Persistir PD/rating na originação.
- [ ] Persistir data, modelo e política de originação.
- [ ] Calcular lifetime PD de originação no prazo original.

## Tarefa 6.2 — Motor SICR

### Subtarefas

- [ ] Comparar lifetime PD atual e de originação.
- [ ] Implementar variação absoluta e relativa.
- [ ] Implementar downgrade em notches.
- [ ] Implementar watchlist e eventos qualitativos.
- [ ] Implementar backstop de atraso.
- [ ] Implementar low-credit-risk exemption configurável.
- [ ] Produzir razão de decisão detalhada.

## Tarefa 6.3 — Stage 3 e default

### Subtarefas

- [ ] Unificar default contábil e operacional.
- [ ] Implementar arrasto por contraparte com exceções documentadas.
- [ ] Implementar evento de unlikeliness to pay.
- [ ] Implementar reestruturação/concessão.

## Tarefa 6.4 — Cura e retorno de estágio

### Subtarefas

- [ ] Implementar período de observação.
- [ ] Implementar critérios quantitativos e qualitativos.
- [ ] Registrar histórico de estágio.
- [ ] Impedir cura prematura.
- [ ] Tratar redefault.

## Tarefa 6.5 — POCI

### Subtarefas

- [ ] Identificar ativos adquiridos ou originados com problema de crédito.
- [ ] Implementar credit-adjusted EIR.
- [ ] Calcular variação de lifetime ECL.
- [ ] Criar golden cases POCI.

## Tarefa 6.6 — Validação de staging

### Subtarefas

- [ ] Stability index por período.
- [ ] taxa de migração entre estágios.
- [ ] sensibilidade a thresholds.
- [ ] comparação de definições SICR.
- [ ] falsos positivos/negativos em eventos futuros.

### Critérios de aceite

- [ ] Existe somente um motor de estágio.
- [ ] Toda decisão possui justificativa, versão e evidência.
- [ ] Stage 2 é relativo à originação, não apenas ao nível atual.

---

# FASE 7 — Modelo de LGD workout

## Objetivo

Calcular LGD a partir de recuperações líquidas e descontadas.

## Tarefa 7.1 — Dataset de LGD

### Subtarefas

- [ ] Criar default cohorts.
- [ ] Vincular recuperações, custos, garantias, cura e write-off.
- [ ] Definir janela de workout.
- [ ] Tratar observações censuradas.

## Tarefa 7.2 — LGD realizada

### Subtarefas

- [ ] Calcular EAD no default.
- [ ] Descontar recuperações pela taxa apropriada.
- [ ] Subtrair custos.
- [ ] Calcular LGD de cura e de perda.
- [ ] Tratar LGD negativa ou superior a 100% conforme política documentada.

## Tarefa 7.3 — Modelagem

### Subtarefas

- [ ] Implementar baseline segmentado.
- [ ] Avaliar one-stage regression.
- [ ] Avaliar two-stage: probabilidade de write-off/cura + severidade.
- [ ] Considerar zero/one-inflated ou beta regression quando adequado.
- [ ] Incluir garantias, LTV, produto, atraso, prazo e macroeconomia.

## Tarefa 7.4 — Garantias

### Subtarefas

- [ ] Projetar valor de garantia.
- [ ] Aplicar haircut e custos.
- [ ] Modelar tempo de execução.
- [ ] Evitar dupla contagem entre recuperação e garantia.

## Tarefa 7.5 — Validação de LGD

### Subtarefas

- [ ] previsto versus realizado.
- [ ] MAE, RMSE e calibração por faixa.
- [ ] backtesting por coorte.
- [ ] estabilidade por produto.
- [ ] análise downturn separada do ECL PIT.

### Critérios de aceite

- [ ] LGD é derivada de fluxos de recuperação.
- [ ] Toda premissa possui versão e sensibilidade.
- [ ] Existe model card e relatório de validação.

---

# FASE 8 — Modelo de EAD e CCF

## Objetivo

Projetar exposição no momento do default para produtos amortizados e rotativos.

## Tarefa 8.1 — EAD de produtos amortizados

### Subtarefas

- [ ] Usar cronograma de saldo por período.
- [ ] Incorporar prepagamento e modificação.
- [ ] Calcular EAD no período de default.

## Tarefa 8.2 — CCF de produtos rotativos

### Subtarefas

- [ ] Construir dataset de limite e drawdown antes do default.
- [ ] Calcular CCF realizado.
- [ ] Modelar CCF por produto, utilização e horizonte.
- [ ] Tratar limites reduzidos/cancelados.

## Tarefa 8.3 — EAD de compromissos e garantias

### Subtarefas

- [ ] Implementar loan commitments.
- [ ] Implementar financial guarantees.
- [ ] Modelar probabilidade de utilização.

## Tarefa 8.4 — Validação de EAD

### Subtarefas

- [ ] previsto versus realizado.
- [ ] erro por segmento.
- [ ] estabilidade temporal.
- [ ] sensibilidade a utilização e limite.

### Critérios de aceite

- [ ] EAD é temporal e consistente com o produto.
- [ ] CCF não é apenas uma constante global.

---

# FASE 9 — Forward-looking e cenários macroeconômicos

## Objetivo

Calcular riscos e ECL completos por cenário, com relações macroeconômicas demonstráveis.

## Tarefa 9.1 — Serviço de cenários

### Subtarefas

- [ ] Criar schema de trajetória macro por período.
- [ ] Suportar cenários base, otimista, pessimista e stress.
- [ ] Validar soma dos pesos.
- [ ] Versionar cenários e aprovação.
- [ ] Criar cache e snapshot para fontes externas.

## Tarefa 9.2 — Relações macro-risco

### Subtarefas

- [ ] Estimar ou parametrizar de forma transparente a relação macro-PD.
- [ ] Estimar relação macro-LGD.
- [ ] Estimar relação macro-EAD/CCF.
- [ ] Permitir relações não lineares.
- [ ] Documentar coeficientes sintéticos.

## Tarefa 9.3 — ECL por cenário

### Subtarefas

- [ ] Gerar curvas PD/LGD/EAD específicas por cenário.
- [ ] Calcular ECL integral de cada cenário.
- [ ] Ponderar valores de ECL.
- [ ] Não ponderar apenas fatores médios.

## Tarefa 9.4 — Sensibilidade e overlays

### Subtarefas

- [ ] Executar sensibilidade a pesos e trajetórias.
- [ ] Implementar stress testing.
- [ ] Criar framework de management overlays separado do modelo.
- [ ] Registrar motivo, valor, aprovador, vigência e reversão do overlay.

### Critérios de aceite

- [ ] Alterações macroeconômicas afetam curvas e ECL de forma rastreável.
- [ ] ECL final reconcilia com a soma ponderada dos cenários.

---

# FASE 10 — Motor completo de ECL

## Objetivo

Implementar o núcleo de cálculo período a período, descontado e reconciliável.

## Tarefa 10.1 — Cálculo Stage 1

### Subtarefas

- [ ] Usar defaults possíveis nos próximos 12 meses.
- [ ] Aplicar perdas lifetime associadas a esses defaults.
- [ ] Calcular por período, cenário e contrato.
- [ ] Descontar pela EIR original.

## Tarefa 10.2 — Cálculo Stage 2

### Subtarefas

- [ ] Calcular lifetime ECL pela vida remanescente.
- [ ] Tratar prepagamento e extensão contratual esperada.
- [ ] Suportar cálculo individual e coletivo.

## Tarefa 10.3 — Cálculo Stage 3

### Subtarefas

- [ ] Projetar recebimentos e recuperações.
- [ ] Calcular cash shortfall.
- [ ] Descontar fluxos.
- [ ] Tratar garantias, custos, cura e write-off.
- [ ] Calcular juros sobre base apropriada.

## Tarefa 10.4 — Cálculo POCI

### Subtarefas

- [ ] Calcular credit-adjusted EIR.
- [ ] Reconhecer mudanças na lifetime ECL.
- [ ] Tratar apresentação e disclosure.

## Tarefa 10.5 — Cálculo coletivo e grupos homogêneos

### Subtarefas

- [ ] Definir critérios estatísticos de agrupamento.
- [ ] Validar homogeneidade.
- [ ] Impedir agrupamentos baseados apenas em faixas arbitrárias do score.
- [ ] Permitir cálculo individual para exposições relevantes.

## Tarefa 10.6 — Reconciliação

### Subtarefas

- [ ] Reconciliar por período.
- [ ] Reconciliar por cenário.
- [ ] Reconciliar contrato, cliente, produto e carteira.
- [ ] Reconciliar ECL bruto, overlay, piso e ECL final.
- [ ] Criar ledger de execução imutável.

## Tarefa 10.7 — Golden cases ECL

### Subtarefas

- [ ] Stage 1 amortizado.
- [ ] Stage 2 lifetime.
- [ ] Stage 3 cash shortfall.
- [ ] rotativo com CCF.
- [ ] contrato garantido.
- [ ] POCI.
- [ ] modificação.
- [ ] multi-cenário.

### Critérios de aceite

- [ ] Todos os golden cases batem com cálculo manual.
- [ ] `PD × LGD × EAD` simples permanece apenas como baseline didático.
- [ ] Nenhuma LGD exibida diverge da usada no cálculo.
- [ ] Toda execução é reproduzível.

---

# FASE 11 — CMN 4.966, provisões mínimas e perímetro completo

## Objetivo

Separar corretamente cálculo contábil, regras locais, metodologia simplificada e demais componentes do perímetro.

## Tarefa 11.1 — Regras locais de provisão mínima

### Subtarefas

- [ ] Implementar tabelas e regras apenas a partir de fonte oficial vigente.
- [ ] Versionar por data-base.
- [ ] Aplicar após o ECL econômico/contábil, em camada separada.
- [ ] Exibir ECL calculado, piso e provisão final separadamente.

## Tarefa 11.2 — Metodologia simplificada

### Subtarefas

- [ ] Verificar aplicabilidade vigente para segmentos/instituições.
- [ ] Implementar como estratégia separada.
- [ ] Criar casos sintéticos e documentação.
- [ ] Impedir mistura com metodologia completa.

## Tarefa 11.3 — Classificação e mensuração

### Subtarefas

- [ ] Implementar cadastro de business model.
- [ ] Implementar teste SPPI.
- [ ] Classificar amortized cost, FVOCI e FVTPL.
- [ ] Integrar elegibilidade ao motor de impairment.
- [ ] Tratar reclassificação quando aplicável.

## Tarefa 11.4 — Modificação, baixa e reconhecimento

### Subtarefas

- [ ] Implementar regras de modificação sem derecognition.
- [ ] Implementar derecognition.
- [ ] Implementar write-off parcial e total.
- [ ] Implementar recuperações pós-baixa.

## Tarefa 11.5 — Disclosures

### Subtarefas

- [ ] Gerar reconciliação de allowance por estágio.
- [ ] Gerar movimentações e transferências de estágio.
- [ ] Gerar exposição por rating e segmento.
- [ ] Gerar sensibilidades e overlays.
- [ ] Gerar pacote de disclosure sintético.

### Critérios de aceite

- [ ] O sistema diferencia claramente IFRS 9, CMN 4.966, piso regulatório e capital IRB.
- [ ] Não há uso direto de LGD downturn regulatória como LGD contábil sem ajuste e documentação.

---

# FASE 12 — Documento 3040 e reportes regulatórios

## Objetivo

Substituir o simulador heurístico por um gerador e pré-validador versionado, sem dados inventados.

## Tarefa 12.1 — Contrato de entrada regulatória

### Subtarefas

- [ ] Definir todos os campos obrigatórios e condicionais.
- [ ] Definir domínios e formatos.
- [ ] Mapear origem de cada campo.
- [ ] Rejeitar ausência ou inconsistência.
- [ ] Remover datas, portes, COSIFs, CEPs e códigos default silenciosos.

## Tarefa 12.2 — Versionamento de leiaute

### Subtarefas

- [ ] Implementar registry por data-base.
- [ ] Carregar XSD correspondente.
- [ ] Versionar críticas e tabelas de domínio.
- [ ] Bloquear data-base sem versão suportada.

## Tarefa 12.3 — Geração XML

### Subtarefas

- [ ] Gerar cabeçalho, clientes, operações e blocos aplicáveis.
- [ ] Gerar vencimentos completos.
- [ ] Gerar IPOC conforme regra oficial vigente.
- [ ] Gerar totalizadores.
- [ ] Remover toda lógica arbitrária, incluindo frações artificiais de ECL.

## Tarefa 12.4 — Validação

### Subtarefas

- [ ] Validar XML contra XSD.
- [ ] Validar domínios.
- [ ] Validar críticas semânticas.
- [ ] Validar totalizadores.
- [ ] Validar consistência com carteira e ECL.
- [ ] Gerar relatório de erros por linha/campo/regra.

## Tarefa 12.5 — Golden files

### Subtarefas

- [ ] Criar XML sintético válido.
- [ ] Criar arquivos inválidos por categoria de erro.
- [ ] Testar regressão por versão de leiaute.

### Critérios de aceite

- [ ] O fluxo padrão usa XSD e críticas, não apenas parse XML.
- [ ] Nenhum campo regulatório é inventado.
- [ ] A interface usa “pré-validador” até homologação oficial.

---

# FASE 13 — Validação independente, MRM e monitoramento

## Objetivo

Criar evidências de que modelos e cálculos funcionam, permanecem estáveis e podem ser contestados.

## Tarefa 13.1 — Framework de validação independente

### Subtarefas

- [ ] Criar pacote separado de validação.
- [ ] Impedir que o pipeline de desenvolvimento aprove automaticamente o modelo.
- [ ] Definir critérios de aprovação, ressalva e rejeição.
- [ ] Criar relatório de validação reproduzível.

## Tarefa 13.2 — Backtesting de PD

### Subtarefas

- [ ] previsto versus observado.
- [ ] por rating, produto, safra e horizonte.
- [ ] calibration drift.
- [ ] testes de cobertura e intervalos.

## Tarefa 13.3 — Backtesting de LGD

### Subtarefas

- [ ] recuperações previstas versus realizadas.
- [ ] coortes fechadas e abertas.
- [ ] cura, write-off e garantias.

## Tarefa 13.4 — Backtesting de EAD

### Subtarefas

- [ ] saldo/drawdown previsto versus realizado.
- [ ] CCF por produto e faixa de utilização.

## Tarefa 13.5 — Backtesting de ECL

### Subtarefas

- [ ] ECL inicial versus perdas realizadas.
- [ ] attribution analysis: volume, estágio, PD, LGD, EAD, cenário e overlay.
- [ ] análise por safra e ciclo econômico.

## Tarefa 13.6 — Monitoramento

### Subtarefas

- [ ] data quality e schema drift.
- [ ] PSI e distribuição.
- [ ] performance e calibração.
- [ ] estabilidade de staging.
- [ ] monitoramento de cenários.
- [ ] alertas e critérios de recalibração.

## Tarefa 13.7 — Model cards e evidence pack

### Subtarefas

- [ ] PD model card.
- [ ] SICR model/policy card.
- [ ] LGD model card.
- [ ] EAD model card.
- [ ] ECL methodology document.
- [ ] validation reports.
- [ ] limitation register.

### Critérios de aceite

- [ ] Todo modelo pode ser aprovado ou rejeitado por critérios objetivos.
- [ ] Há evidência independente de cálculo e performance.

---

# FASE 14 — Persistência, APIs, segurança, auditoria e frontend

## Objetivo

Integrar o núcleo reconstruído à plataforma sem comprometer rastreabilidade.

## Tarefa 14.1 — Persistência versionada

### Subtarefas

- [ ] Criar migrations.
- [ ] Persistir contratos, snapshots, modelos, cenários e resultados.
- [ ] Persistir lineage e hashes.
- [ ] Implementar idempotência e reprocessamento.
- [ ] Separar dados operacionais, modelos e auditoria.

## Tarefa 14.2 — APIs

### Subtarefas

- [ ] Versionar endpoints.
- [ ] Criar endpoints para cálculo individual e carteira.
- [ ] Criar jobs assíncronos para lote.
- [ ] Validar schemas de entrada.
- [ ] Expor decomposição por período/cenário.
- [ ] Expor relatórios e evidências.

## Tarefa 14.3 — Segurança e segregação

### Subtarefas

- [ ] Revisar RBAC.
- [ ] Separar cálculo, aprovação, exportação e auditoria.
- [ ] Implementar confirmação de operações críticas.
- [ ] Revisar JWT, sessões, senha e rate limit.
- [ ] Redigir threat model.

## Tarefa 14.4 — Auditoria

### Subtarefas

- [ ] Logar usuário, ação, entrada, versão e resultado.
- [ ] Criar trilha imutável para execução ECL.
- [ ] Registrar overrides e overlays.
- [ ] Registrar exportações e validações.

## Tarefa 14.5 — Frontend

### Subtarefas

- [ ] Remover dashboards que exibem dados mockados sem aviso.
- [ ] Exibir estágio, justificativas e comparação com originação.
- [ ] Exibir curvas PD/LGD/EAD.
- [ ] Exibir ECL por período e cenário.
- [ ] Exibir reconciliação, overlays e pisos.
- [ ] Exibir status de validação e limitações.
- [ ] Manter visualização de dados sintéticos claramente identificada.

## Tarefa 14.6 — Agente de IA

### Subtarefas

- [ ] Restringir o agente a dados persistidos e autorizados.
- [ ] Remover respostas baseadas em métricas inventadas.
- [ ] Exigir citações internas de execução e documentação.
- [ ] Implementar guardrails para não afirmar conformidade oficial.
- [ ] Testar prompt injection e acesso indevido.

### Critérios de aceite

- [ ] Toda informação exibida é rastreável a dados e versão.
- [ ] Nenhum mock silencioso permanece em produção/demo.

---

# FASE 15 — CI/CD, observabilidade, desempenho e segurança técnica

## Objetivo

Transformar a plataforma em um sistema reproduzível e confiável.

## Tarefa 15.1 — CI

### Subtarefas

- [ ] Lint e formatação.
- [ ] type checking.
- [ ] testes unitários e integração.
- [ ] testes quantitativos.
- [ ] cobertura.
- [ ] dependency audit.
- [ ] secret scan.
- [ ] build de containers.

## Tarefa 15.2 — CD e ambientes

### Subtarefas

- [ ] ambientes local, test e demo.
- [ ] configurações separadas.
- [ ] migrations automáticas controladas.
- [ ] rollback.
- [ ] release notes.

## Tarefa 15.3 — Observabilidade

### Subtarefas

- [ ] logs estruturados.
- [ ] métricas de API e jobs.
- [ ] tracing.
- [ ] dashboards Prometheus/Grafana ou equivalente.
- [ ] alertas.

## Tarefa 15.4 — Performance

### Subtarefas

- [ ] benchmark de 10 mil, 100 mil e 1 milhão de contratos sintéticos.
- [ ] processamento vetorizado e particionado.
- [ ] filas para lote.
- [ ] cache apenas quando seguro e versionado.
- [ ] testes de concorrência.

## Tarefa 15.5 — Segurança

### Subtarefas

- [ ] SAST e dependency scan.
- [ ] revisão de autenticação/autorização.
- [ ] proteção de arquivos exportados.
- [ ] validação de uploads.
- [ ] política de retenção e exclusão.
- [ ] pentest automatizado básico.

### Critérios de aceite

- [ ] CI verde é obrigatório para merge.
- [ ] O sistema processa o volume-alvo definido.
- [ ] Falhas são observáveis e recuperáveis.

---

# FASE 16 — Testes E2E, pacote de evidências e release 10/10

## Objetivo

Demonstrar de ponta a ponta que o sistema atende ao escopo declarado.

## Tarefa 16.1 — Jornada E2E completa

### Subtarefas

- [ ] Gerar carteira sintética.
- [ ] Treinar modelos.
- [ ] Validar e aprovar modelos.
- [ ] Classificar estágios.
- [ ] Calcular ECL.
- [ ] Aplicar overlays e pisos separadamente.
- [ ] Persistir e reconciliar resultados.
- [ ] Gerar reportes.
- [ ] Pré-validar Doc3040.
- [ ] Visualizar e auditar no frontend.

## Tarefa 16.2 — Pacote de golden cases

### Subtarefas

- [ ] Publicar inputs, fórmulas e outputs esperados.
- [ ] Incluir planilhas ou notebooks de verificação independente.
- [ ] Automatizar comparação no CI.

## Tarefa 16.3 — Pacote regulatório

### Subtarefas

- [ ] Exportar matriz de rastreabilidade.
- [ ] Exportar cobertura de testes por requisito.
- [ ] Exportar limitações e itens não aplicáveis.
- [ ] Exportar versões de leiaute e normas consultadas.

## Tarefa 16.4 — Documentação de portfólio

### Subtarefas

- [ ] Reescrever README principal.
- [ ] Criar arquitetura e diagramas.
- [ ] Criar quickstart de um comando.
- [ ] Criar tutorial de ECL.
- [ ] Criar guia para entrevista técnica.
- [ ] Criar exemplos de API.
- [ ] Criar screenshots e demo, sem dados reais.

## Tarefa 16.5 — Revisão final de notas

### Subtarefas

- [ ] Avaliar arquitetura.
- [ ] Avaliar PD.
- [ ] Avaliar LGD.
- [ ] Avaliar EAD.
- [ ] Avaliar ECL.
- [ ] Avaliar staging.
- [ ] Avaliar regulação.
- [ ] Avaliar validação.
- [ ] Avaliar segurança.
- [ ] Avaliar experiência e portfólio.
- [ ] Registrar evidências para cada nota 10/10.

### Critérios de aceite da release

- [ ] Setup e demo executam do zero.
- [ ] Todos os testes passam.
- [ ] Golden cases reconciliam.
- [ ] OOT e backtesting estão publicados.
- [ ] Nenhuma afirmação de certificação indevida permanece.
- [ ] Toda saída regulatória é versionada e pré-validada.
- [ ] Todo resultado é rastreável a dados, modelo, política, cenário e código.
- [ ] O projeto está pronto para adaptação a dados reais de uma instituição, sem alegar homologação prévia.

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

- [ ] lint;
- [ ] type checking;
- [ ] testes de domínio;
- [ ] testes do gerador;
- [ ] anti-leakage;
- [ ] reprodutibilidade.

## Marco B — Modelos

Após Fases 4 a 9:

- [ ] testes de cashflow;
- [ ] PD OOT;
- [ ] LGD workout;
- [ ] EAD/CCF;
- [ ] staging;
- [ ] cenários;
- [ ] model cards.

## Marco C — ECL e regulação

Após Fases 10 a 13:

- [ ] golden cases;
- [ ] reconciliação;
- [ ] Stage 3;
- [ ] POCI;
- [ ] pisos e overlays;
- [ ] Doc3040 XSD/semântica;
- [ ] backtesting.

## Marco D — Produto

Após Fases 14 a 16:

- [ ] API;
- [ ] persistência;
- [ ] RBAC;
- [ ] auditoria;
- [ ] E2E;
- [ ] carga;
- [ ] segurança;
- [ ] demo do zero.

---

# 19. Entregáveis finais obrigatórios

- [ ] `docs/PROJECT_AUDIT_AND_TARGET_STATE.md` atualizado.
- [ ] `docs/MASTER_BACKLOG.md` concluído.
- [ ] `docs/SCOPE.md`.
- [ ] `docs/GLOSSARY.md`.
- [ ] matriz de rastreabilidade regulatória.
- [ ] arquitetura e ADRs.
- [ ] fábrica de dados sintéticos.
- [ ] data cards.
- [ ] model cards de PD, SICR, LGD e EAD.
- [ ] metodologia ECL.
- [ ] relatórios de validação.
- [ ] golden cases.
- [ ] pacote Doc3040 sintético.
- [ ] CI/CD.
- [ ] observabilidade.
- [ ] README e quickstart.
- [ ] relatório final de limitações.
- [ ] release versionada.

---
