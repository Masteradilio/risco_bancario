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

- [ ] Comparar `backend/prinad`, `prinad_v2` e demais cópias.
- [ ] Comparar frontend atual com `frontend-nextjs-backup`.
- [ ] Identificar constantes duplicadas em `shared/utils.py` e módulos locais.
- [ ] Mapear regras divergentes de rating, PD e estágio.
- [ ] Criar `docs/architecture/DUPLICATION_MAP.md`.

### Critérios de aceite

- [ ] Cada conceito possui uma implementação canônica definida.
- [ ] O plano de migração do legado está documentado.

## Tarefa 1.2 — Criar arquitetura de domínio

### Subtarefas

- [ ] Criar pacote `src/` com os domínios definidos no relatório de auditoria.
- [ ] Criar modelos tipados para cliente, contraparte, contrato, garantia, snapshot, cenário e resultado ECL.
- [ ] Usar `Decimal` para moeda.
- [ ] Definir convenções de datas, timezone, percentuais e arredondamento.
- [ ] Criar exceções de domínio explícitas.
- [ ] Criar ADR da arquitetura.

### Critérios de aceite

- [ ] O domínio não depende de FastAPI, banco, frontend ou arquivos CSV.
- [ ] Tipos e invariantes são testados.

## Tarefa 1.3 — Configuração e regras fora do código

### Subtarefas

- [ ] Criar schemas versionados de configuração.
- [ ] Migrar thresholds, pesos, cenários e políticas para YAML/JSON/Pydantic.
- [ ] Registrar data de vigência, autor, versão e justificativa.
- [ ] Impedir carregamento de configuração inválida.
- [ ] Criar hash da configuração usada em cada execução.

### Critérios de aceite

- [ ] Nenhuma regra material depende de número mágico disperso.
- [ ] O resultado ECL identifica a versão exata da configuração.

## Tarefa 1.4 — Padronizar tooling

### Subtarefas

- [ ] Definir versão oficial do Python.
- [ ] Migrar dependências para `pyproject.toml`.
- [ ] Configurar Ruff, Black, MyPy/Pyright e Pytest.
- [ ] Configurar cobertura mínima progressiva.
- [ ] Criar Makefile ou scripts equivalentes.
- [ ] Criar comando único de setup e teste.

### Critérios de aceite

- [ ] Ambiente local sobe de forma reproduzível.
- [ ] Lint, type checking e testes executam em um comando.

---

# FASE 2 — Base regulatória e matriz de rastreabilidade

## Objetivo

Transformar requisitos normativos em itens testáveis, versionados e auditáveis.

## Tarefa 2.1 — Catálogo de fontes oficiais

### Subtarefas

- [ ] Criar `docs/regulatory/SOURCE_REGISTER.md`.
- [ ] Registrar IFRS 9 vigente, CMN 4.966 consolidada, BCB 352 vigente e documentação Doc3040.
- [ ] Registrar data de consulta e vigência.
- [ ] Definir processo de atualização regulatória.
- [ ] Não copiar material protegido sem autorização.

## Tarefa 2.2 — Matriz de requisitos

### Subtarefas

- [ ] Criar `docs/regulatory/TRACEABILITY_MATRIX.csv` ou formato tabular equivalente.
- [ ] Mapear impairment, ECL, SICR, default, cura, write-off, forward-looking, desconto, POCI e disclosure.
- [ ] Mapear requisitos CMN/BCB aplicáveis.
- [ ] Mapear Documento 3040, XSD e críticas.
- [ ] Vincular requisito a código, teste e evidência.

### Critérios de aceite

- [ ] Todo requisito implementado possui teste associado.
- [ ] Todo requisito não aplicável possui justificativa.

## Tarefa 2.3 — Testes regulatórios executáveis

### Subtarefas

- [ ] Criar estrutura de testes por requisito.
- [ ] Adicionar identificador regulatório nos nomes/metadados dos testes.
- [ ] Gerar relatório automático de cobertura regulatória.
- [ ] Bloquear release quando requisito obrigatório estiver sem evidência.

---

# FASE 3 — Fábrica de dados sintéticos longitudinais

## Objetivo

Criar dados realistas, temporais e sem leakage para suportar todas as fases do projeto.

## Tarefa 3.1 — Modelo causal e temporal do gerador

### Subtarefas

- [ ] Definir entidades e relacionamentos.
- [ ] Definir variáveis latentes internas ao gerador.
- [ ] Garantir que variáveis latentes não sejam exportadas para modelagem.
- [ ] Definir ciclos macroeconômicos.
- [ ] Definir dinâmica de renda, emprego, utilização, atraso e default.
- [ ] Definir mecanismo de recuperação, garantia, renegociação e cura.
- [ ] Criar documento `docs/data/SYNTHETIC_DATA_DESIGN.md`.

### Critérios de aceite

- [ ] O target decorre de eventos futuros, não de uma classe estática usada para gerar features.
- [ ] O gerador é separado do pipeline de modelagem.

## Tarefa 3.2 — Gerar população e contratos

### Subtarefas

- [ ] Gerar clientes PF e PJ sintéticos.
- [ ] Gerar grupos econômicos e contrapartes.
- [ ] Gerar produtos amortizados e rotativos.
- [ ] Gerar originação, prazo, taxa efetiva, cronograma e garantias.
- [ ] Gerar compromissos de crédito e garantias financeiras.
- [ ] Gerar POCI e contratos adquiridos com problema de crédito.

## Tarefa 3.3 — Gerar snapshots mensais

### Subtarefas

- [ ] Gerar 8 a 10 anos de snapshots.
- [ ] Gerar saldo, limite, utilização, parcelas, atraso e rating.
- [ ] Gerar mudanças de risco antes do default.
- [ ] Gerar safras e coortes.
- [ ] Gerar eventos de modificação e renegociação.

## Tarefa 3.4 — Gerar defaults, cobranças e recuperações

### Subtarefas

- [ ] Gerar datas de default.
- [ ] Gerar fluxos de recuperação mensais.
- [ ] Gerar execução de garantias.
- [ ] Gerar custos judiciais e operacionais.
- [ ] Gerar curas e redefaults.
- [ ] Gerar write-offs e recuperações pós-baixa.

## Tarefa 3.5 — Gerar macroeconomia e cenários

### Subtarefas

- [ ] Gerar cenário observado histórico.
- [ ] Gerar cenários base, otimista, pessimista e stress.
- [ ] Gerar trajetórias mensais de PIB, inflação, juros, desemprego e endividamento.
- [ ] Introduzir relações não lineares com risco.
- [ ] Versionar pesos e trajetórias.

## Tarefa 3.6 — Datasets de modelagem

### Subtarefas

- [ ] Construir observation dates.
- [ ] Construir target de default em 12 meses.
- [ ] Construir targets de hazard mensal.
- [ ] Construir datasets de LGD e EAD.
- [ ] Construir datasets de SICR.
- [ ] Separar treino, validação, calibração, OOT e backtesting por tempo.

## Tarefa 3.7 — Qualidade e anti-leakage

### Subtarefas

- [ ] Criar testes de integridade referencial.
- [ ] Criar testes de consistência temporal.
- [ ] Criar detector de feature futura.
- [ ] Criar análise de distribuição e correlação.
- [ ] Criar data cards e dicionário de dados.

### Critérios de aceite da fase

- [ ] O dataset é reproduzível por seed.
- [ ] O modelo não recebe variáveis latentes.
- [ ] Existe OOT real.
- [ ] Há dados para PD, LGD, EAD, SICR, Stage 3, POCI e Doc3040.

---

# FASE 4 — Motor de contratos, cronogramas e fluxos de caixa

## Objetivo

Representar corretamente a vida financeira dos instrumentos.

## Tarefa 4.1 — Contratos amortizados

### Subtarefas

- [ ] Implementar Price, SAC e bullet.
- [ ] Projetar principal, juros, tarifas e saldo.
- [ ] Suportar taxa fixa e variável.
- [ ] Calcular taxa efetiva de juros.
- [ ] Suportar feriados e convenção de dias configurável.

## Tarefa 4.2 — Produtos rotativos

### Subtarefas

- [ ] Implementar limites, utilização e pagamento mínimo.
- [ ] Projetar drawdown e cancelamento.
- [ ] Tratar limite não utilizado.
- [ ] Suportar cartões e cheque especial.

## Tarefa 4.3 — Modificações e prepagamento

### Subtarefas

- [ ] Implementar prepagamento parcial e total.
- [ ] Implementar modificação com e sem baixa.
- [ ] Calcular ganho/perda de modificação.
- [ ] Preservar EIR original quando exigido.

## Tarefa 4.4 — Golden cases financeiros

### Subtarefas

- [ ] Criar contratos pequenos com planilha manual de referência.
- [ ] Testar saldos, juros e amortização período a período.
- [ ] Testar arredondamento e reconciliação.

### Critérios de aceite

- [ ] Fluxos fecham com o saldo contábil.
- [ ] Resultados batem com casos manuais dentro da tolerância definida.

---

# FASE 5 — Modelo de PD e estruturas temporais

## Objetivo

Substituir a PD heurística por modelos temporais calibrados e validáveis.

## Tarefa 5.1 — Definição formal de default

### Subtarefas

- [ ] Definir evento de default por população e produto.
- [ ] Definir cure e redefault.
- [ ] Definir materialidade e backstops.
- [ ] Documentar target e exclusões.

## Tarefa 5.2 — Baseline explicável

### Subtarefas

- [ ] Implementar regressão logística 12m.
- [ ] Implementar discrete-time hazard.
- [ ] Comparar desempenho e calibração.
- [ ] Criar scorecard/rating derivado de PD, sem faixas arbitrárias não calibradas.

## Tarefa 5.3 — Modelos candidatos

### Subtarefas

- [ ] Avaliar gradient boosting calibrado.
- [ ] Avaliar survival gradient boosting, quando adequado.
- [ ] Avaliar matrizes de transição para segmentos pequenos.
- [ ] Manter modelo champion e challengers.

## Tarefa 5.4 — Separação temporal e calibração

### Subtarefas

- [ ] Usar split por data/coorte.
- [ ] Separar calibração do teste OOT.
- [ ] Aplicar Platt, isotonic ou beta calibration conforme validação.
- [ ] Avaliar calibração por rating, produto e safra.

## Tarefa 5.5 — Curvas de PD

### Subtarefas

- [ ] Gerar hazard mensal.
- [ ] Gerar sobrevivência.
- [ ] Gerar PD marginal.
- [ ] Gerar PD acumulada 12m e lifetime.
- [ ] Garantir monotonicidade e limites.

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
