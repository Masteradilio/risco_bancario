# TODO - Próximos Passos (Fase de Finalização)

Este documento lista as funcionalidades e melhorias pendentes para atingir 100% da implementação do sistema de Risco Bancário.

---

## ✅ Concluído

### 📊 Analytics e Relatórios

- [x] Geração de **PDFs de laudo técnico de crédito** via `@react-pdf/renderer`.
- [x] Formulário completo para preenchimento dos dados do laudo.
- [x] **Exportação regulatória BACEN Doc3040** (XML conforme Resolução CMN 4966/2021).

### 🔒 Segurança e Autenticação

- [x] Sistema de autenticação com tela de login moderna.
- [x] Controle de acesso baseado em perfis (RBAC): Analista, Gestor, Auditor, Admin.
- [x] Auditoria de logs (registro de ações do usuário no frontend).

### 🏛️ Conformidade Regulatória (BACEN 4966 / IFRS 9)

- [x] **PRINAD v2.0** - PD Calibrado (pd_12m, pd_lifetime), 11 Ratings (A1 → DEFAULT), Stage IFRS 9.
- [x] **ECL Engine v2.0** - Fórmula `ECL = PD × LGD × EAD` com 3 Estágios.
- [x] **StageClassifier** - Classificação automática em stages com triggers.
- [x] **Regra de Arrasto** - Quando um produto vai para Stage 3, todos migram.
- [x] **Critérios de Cura** - Reversão de stage após período de observação.
- [x] **Pisos Mínimos** - Pisos de provisão para Stage 3 conforme BCB 352.
- [x] **Grupos Homogêneos** - Agrupamento por PD com WOE.
- [x] **Forward Looking** - Integração com dados macroeconômicos (SGS BACEN).
- [x] **LGD Segmentado** - LGD por produto, atraso, valor, prazo.
- [x] **EAD + CCF** - Credit Conversion Factor por produto.
- [x] **Triggers de Migração** - Gatilhos para mudança de estágio.
- [x] **Historical Penalty v2.0** - Penalidades separadas (interna 25% + externa 25%), cura 6 meses.

### 📦 Infraestrutura

- [x] **Dockerização completa** - Dockerfiles para frontend e 3 backends.
- [x] **Docker Compose** - Orquestração unificada.
- [x] Reorganização da estrutura de pastas (`/backend`, `/frontend`).

### 📝 Documentação

- [x] README unificado na raiz do projeto.
- [x] CHANGELOG unificado com toda a história de desenvolvimento.
- [x] Documentação técnica ECL em `/backend/perda_esperada/docs/`.

---

## ✅ Concluído Recentemente

### 🏛️ Conformidade Regulatória BACEN 4966 (Janeiro 2026)

#### ✅ Forward Looking Multi-Cenário (Art. 36 §5º CMN 4966)
>
> **Concluído em:** 08/01/2026

- [x] **Criar módulo `cenarios_forward_looking.py`**
  - [x] Definir estrutura de dados para cenários (otimista, base, pessimista)
  - [x] Implementar ponderações padrão (15% otimista, 70% base, 15% pessimista)
  - [x] Criar função para calcular K_PD_FL ponderado por cenário
  - [x] Criar função para calcular K_LGD_FL ponderado por cenário
- [x] **Integrar com API SGS do BACEN**
  - [x] Implementar projeções macroeconômicas por cenário (SELIC, PIB, IPCA)
  - [x] Criar configuração para ajuste de spreads por cenário
- [x] **Atualizar pipeline ECL**
  - [x] Classe `GerenciadorCenarios` para consumir cenários ponderados
  - [x] Adicionar campo `cenario_aplicado` no resultado ECL
  - [x] Calcular ECL final como média ponderada dos 3 cenários
- [x] **Testes e validação**
  - [x] Criar testes unitários para cada cenário (28 testes - 100% passando)
  - [x] Validar que ECL_final = Σ(peso_i × ECL_i) para i em {otimista, base, pessimista}

#### ✅ Sistema de Cura Formal (Art. 41 CMN 4966)
>
> **Concluído em:** 08/01/2026

- [x] **Criar módulo `sistema_cura.py`**
  - [x] Implementar classe `SistemaCura` com regras de reversão
  - [x] Definir períodos mínimos: Stage 2→1 (6 meses), Stage 3→2 (12 meses)
  - [x] Criar flag `em_periodo_cura` para contratos em observação
  - [x] Implementar contador de meses em adimplência
- [x] **Critérios de elegibilidade para cura**
  - [x] Stage 2→1: 6 meses consecutivos sem atraso > 30 dias + PD atual < PD na migração
  - [x] Stage 3→2: 12 meses consecutivos + amortização ≥ 30% + sem novos eventos de crédito
  - [x] Validar que reestruturações exigem critérios mais rigorosos (24 meses, 50% amortização)
- [x] **Integração com triggers de estágio**
  - [x] Implementar lógica de avaliação de cura antes de migração
  - [x] Adicionar histórico de estágios por contrato
- [x] **Testes e validação**
  - [x] Criar testes unitários para cada cenário de cura (31 testes - 100% passando)
  - [x] Testar que contratos em cura não migram prematuramente

---

## ✅ Concluído Recentemente (Sessão 2)

### 🏛️ Integração de Conformidade BACEN (08/01/2026)

#### ✅ Integrar Forward Looking com Pipeline ECL
>
> **Concluído em:** 08/01/2026

- [x] **Atualizado `pipeline_ecl.py`**
  - [x] Importar e instanciar `GerenciadorCenarios`
  - [x] Substituir cálculo de K_PD_FL/K_LGD_FL simples pelo ponderado multi-cenário
  - [x] Adicionar campos `usar_multi_cenario` e `cenarios_detalhes` no resultado ECL
  - [x] Flag `usar_multi_cenario=True` por padrão
- [x] **Testes de integração**
  - [x] Validar que pipeline usa cenários corretamente
  - [x] K_PD_FL calculado como Σ(peso × K_cenário)

#### ✅ Integrar Sistema de Cura com Triggers de Estágio
>
> **Concluído em:** 08/01/2026

- [x] **Atualizado `modulo_triggers_estagios.py`**
  - [x] Importar e instanciar `SistemaCura`
  - [x] Nova função `aplicar_avaliacao_cura()` para avaliar elegibilidade
  - [x] Nova função `aplicar_todos_triggers_com_cura()` orquestrando cura + triggers
  - [x] Flags `cura_avaliada`, `cura_aplicada`, `estagio_pre_cura` no resultado
- [x] **Testes de integração**
  - [x] Validar que contratos elegíveis para cura são revertidos
  - [x] Validar que contratos em observação mantêm estágio atual

#### ✅ Sistema de Rastreamento de Write-off (Art. 49 CMN 4966)
>
> **Concluído em:** 08/01/2026

- [x] **Criado módulo `rastreamento_writeoff.py`**
  - [x] Classe `RastreadorWriteOff` com registro de baixas
  - [x] Acompanhamento de recuperações pós-baixa por 5 anos (1825 dias)
  - [x] Cálculo de taxa de recuperação histórica (média e ponderada)
  - [x] Relatório regulatório para envio ao BACEN
- [x] **Testes e validação**
  - [x] Testes de integração completos
  - [x] Validar cálculo de recuperação

---

## 🔶 Pendente

### 🏗️ Sistema de Persistência e Frontend Perda Esperada (Concluído)
>
> **Objetivo:** Infraestrutura de banco de dados MySQL + Frontend completo para demonstração POC

#### ✅ Fase 1: Banco de Dados MySQL (Concluída 08/01/2026)

- [x] Criar estrutura `/backend/bancos_de_dados/`
- [x] Esquema `ecl`: 4 tabelas (resultados, cenarios, parametros_fl, grupos_homogeneos)
- [x] Esquema `estagio`: 3 tabelas (historico, cura, triggers)
- [x] Esquema `writeoff`: 2 tabelas (baixas, recuperacoes)
- [x] Esquema `auditoria`: 2 tabelas (envios_bacen, validacoes)
- [x] Scripts DDL de referência para equipe TI
- [x] Script consolidado `esquema_completo.sql`

#### ✅ Fase 2: API Write-off (Concluída 08/01/2026)

- [x] Endpoint `POST /writeoff/registrar-baixa`
- [x] Endpoint `POST /writeoff/registrar-recuperacao`
- [x] Endpoint `GET /writeoff/relatorio/{contrato_id}`
- [x] Endpoint `GET /writeoff/relatorio-consolidado`
- [x] Endpoint `POST /writeoff/taxa-recuperacao`

#### ✅ Fase 3: Frontend Perda Esperada (Concluída 08/01/2026)

- [x] Renomear menu "ECL" → "Perda Esperada"
- [x] Dashboard Principal (KPIs + Gráficos)
- [x] Cálculo ECL (Individual + Portfólio)
- [x] Classificação de Estágios (Simulador triggers)
- [x] Grupos Homogêneos (Configuração + Análise)
- [x] Forward Looking (Cenários + Ponderações)
- [x] LGD Segmentado (Tabela + Radar)
- [x] Sistema de Cura (Contratos em observação)
- [x] Write-off e Recuperações (Dashboard 5 anos)
- [x] Exportação BACEN (Gerador + Download)
- [x] Pipeline Completo (Execução full + Relatório)

#### ✅ Fase 4: Testes e Validação (Concluída 18/01/2026)

- [x] Testes scripts DDL (`test_ddl_schemas.py` - 25 testes)
- [x] Testes endpoints write-off (`test_api_writeoff.py` - 23 testes passando)
- [x] Testes frontend - estrutura E2E configurada

---

### ✅ Analytics e Relatórios (Concluído 18/01/2026)

- [x] Dashboard de performance do modelo (Monitoramento de Drift e Acurácia)
  - [x] Módulo `model_monitoring.py` - Cálculo de PSI, métricas temporais, backtesting
  - [x] API `api_monitoring.py` - Endpoints FastAPI para analytics

### ✅ Segurança e Autenticação (Concluído 18/01/2026)

- [x] Estrutura para **Windows NTLM/SSO** preparada no `auth_api.py`
- [x] Integração de logs de auditoria com backend (API)
  - [x] Módulo `relatorios_auditoria.py` - Relatórios de acessos, operações críticas, conformidade

### 🔐 Perfis de Acesso de Usuário (RBAC Aprimorado)
>
> **Objetivo:** Implementar separação rigorosa de perfis seguindo princípios de Least Privilege e Separation of Duties conforme ISO 27001, SOX e GLBA.

#### Fase 1: Infraestrutura de Usuários (Backend) ✅

- [x] **Criar esquema `usuarios` no banco de dados MySQL**
  - [x] Tabela `usuarios` (id, nome, email, matricula, senha_hash, role, departamento, ativo, criado_em, atualizado_em)
  - [x] Tabela `usuarios_sessoes` (id, usuario_id, token, ip, user_agent, criado_em, expira_em)
  - [x] Tabela `usuarios_permissoes_customizadas` (usuario_id, permissao, concedido_por, data)
  - [x] Scripts DDL de referência em `/backend/bancos_de_dados/usuarios/`
- [x] **API de Gerenciamento de Usuários (FastAPI)**
  - [x] `POST /usuarios` - Criar usuário (somente Admin)
  - [x] `GET /usuarios` - Listar usuários (somente Admin)
  - [x] `GET /usuarios/{id}` - Obter usuário (Admin ou próprio)
  - [x] `PUT /usuarios/{id}` - Atualizar usuário (somente Admin)
  - [x] `DELETE /usuarios/{id}` - Desativar usuário (somente Admin, soft delete)
  - [x] `POST /usuarios/{id}/reset-senha` - Reset de senha (somente Admin)
- [x] **Autenticação Segura**
  - [x] Hash de senha com bcrypt/argon2
  - [x] JWT tokens com refresh token
  - [x] Rate limiting em endpoints de login

#### Fase 2: Matriz de Permissões por Perfil ✅

- [x] **Analista (Operações Diárias)**
  - Permissões: `view:prinad`, `view:ecl`, `view:propensao`, `classify:individual`, `classify:batch`, `calculate:ecl`
  - Restrições: Sem acesso a exportações BACEN, analytics avançados ou logs de auditoria
- [x] **Gestor (Supervisão e Exportações Críticas)**
  - Permissões: Tudo do Analista + `view:dashboard`, `view:analytics`, `export:pdf`, `export:csv`, `export:bacen`, `generate:xml`
  - Operações Críticas: Geração e envio de XML para BACEN (requer confirmação de alçada)
- [x] **Auditor (Conformidade e Auditoria)**
  - Permissões: Leitura em todos os módulos + `view:audit`, `export:audit_reports`, `view:user_activity_logs`, `export:compliance_reports`
  - Restrições: **Somente leitura** - Não pode executar operações, apenas visualizar e exportar
  - Funcionalidades Específicas: Relatórios de conformidade BACEN 4966, trilha de auditoria de usuários
- [x] **Admin (TI - Acesso Completo)**
  - Permissões: `*` (acesso total)
  - Exclusivo: CRUD de usuários, gestão de permissões, logs de erros do sistema, configurações de sistema

#### Fase 3: Frontend - Implementação de Perfis (Parcial)

- [x] **Refatorar `useAuth.ts`**
  - [x] Substituir mock por integração com API de autenticação
  - [x] Implementar refresh token automático
  - [x] Carregar permissões dinamicamente do backend
- [x] **Componentes de Controle de Acesso**
  - [x] `ProtectedRoute` - HOC para rotas protegidas por permissão
  - [x] `PermissionGate` - Componente para ocultar elementos sem permissão
  - [x] `RoleIndicator` - Badge visual do perfil do usuário logado
- [x] **Páginas por Perfil**
  - [x] Dashboard Admin: CRUD usuários + Logs de erros + Configurações
  - [x] Dashboard Auditor: Logs de atividade + Relatórios de conformidade + Exportação
  - [x] Navegação condicional baseada em role

#### ✅ Fase 4: Logs e Auditoria (Concluída 18/01/2026)

- [x] **Logs de Atividade de Usuário**
  - [x] Cada ação operacional registrada (classificação, cálculo, exportação)
  - [x] Estrutura: `{usuario_id, acao, recurso, detalhes, timestamp, ip}`
  - [x] Endpoint `GET /auditoria/logs` com filtros (data, usuário, ação)
- [x] **Logs de Erros do Sistema (Somente Admin)**
  - [x] Integração com logging structured (JSON)
  - [x] Endpoint `GET /sistema/erros` com filtros e paginação
  - [x] Dashboard de erros em tempo real
- [x] **Relatórios de Auditoria (Auditor/Admin)**
  - [x] Módulo `relatorios_auditoria.py` implementado
  - [x] Relatório de acessos por período
  - [x] Relatório de operações críticas (exportações BACEN)
  - [x] Exportação em CSV/PDF para evidências regulatórias

#### ✅ Fase 5: Segurança Adicional (Concluída 18/01/2026)

- [x] **Separation of Duties**
  - [x] Estrutura preparada no `auth_api.py`
  - [x] Quem calcula ECL NÃO pode aprovar exportação BACEN (Analista vs Gestor)
  - [x] Quem configura usuários NÃO é o mesmo que audita (Admin vs Auditor)
- [x] **Controles de Sessão**
  - [x] Módulo `session_manager.py` implementado
  - [x] Timeout de sessão configurável (padrão 30min para ambiente bancário)
  - [x] Logout automático por inatividade
  - [x] Token revocation em troca de senha
- [x] **Segurança de Senhas**
  - [x] Módulo `password_policy.py` implementado
  - [x] Política de complexidade (mín. 12 chars, upper, lower, number, special)
  - [x] Expiração de senha a cada 90 dias
  - [x] Histórico para impedir reutilização (últimas 5)

### 🤖 Agente IA Especialista em Crédito (Concluído 19/01/2026) ✅

#### Backend & Ferramentas

- [x] **Core do Agente (`agent_api.py`)**
  - [x] Integração com LLM (OpenRouter/Mistral)
  - [x] Detecção inteligente de intenções (Regex + Contexto)
  - [x] Orquestrador de Ferramentas (`tools_orquestrador.py`)
  - [x] Sistema de Memória de Contexto (Sessões)
  - [x] Controle de acesso RBAC por ferramenta

- [x] **Ferramentas de Negócio (Function Calling)**
  - [x] `consultar_score_prinad`: Busca dados de risco de clientes
  - [x] `calcular_ecl_contrato`: Cálculo financeiro detalhado com fluxos
  - [x] `calcular_ecl_portfolio`: Simulação de carteira com 10k+ contratos
  - [x] `analisar_cenarios`: Simulações Forward-Looking
  - [x] `buscar_regulamentacao`: Pesquisa em XMLs/PDFs técnicos

- [x] **Gerador de Artefatos Autônomo (`tools_documentos.py`)**
  - [x] **Gráficos**: Seaborn/Matplotlib com temas Dark/Light (Linha, Barra, Pizza, Histograma, Heatmap)
  - [x] **Relatórios PDF**: Documentos executivos formatados com ReportLab
  - [x] **Excel**: Planilhas com dados brutos formatados e ajustados
  - [x] **Apresentações PowerPoint**: Geração de slides com insights
  - [x] **Word/Markdown**: Documentação técnica e resumos

- [x] **Sistema de Upload & RAG Light**
  - [x] Suporte a CSV, Excel, TXT, PDF, Imagens
  - [x] Extração de texto para contexto do agente
  - [x] Processamento de planilhas para análise de dados

#### Frontend (Chat & Interface)

- [x] Interface estilo ChatGPT (`/agente`)
- [x] **Gestão de Artefatos**
  - [x] Sidebar automática de artefatos gerados
  - [x] Preview de gráficos e documentos em Modal
  - [x] Botões de Download Inteligentes (Digital/Impressão)
- [x] Upload de arquivos drag-and-drop
- [x] Histórico de Sessões Persistente

### 🧪 Qualidade e Testes

- [ ] Implementação de testes de ponta a ponta (E2E) com **Playwright**.
- [ ] Testes de carga nas APIs para suportar grandes volumes de classificação em lote.
- [ ] Cobertura de testes unitários no frontend.

### 🚀 Deploy e Infraestrutura

- [ ] Pipeline CI/CD automatizado no GitHub Actions/GitLab.
- [ ] Configuração de monitoramento e alertas (Prometheus/Grafana).

---

## 📋 Backlog Técnico

### Melhorias de Performance

- [ ] Cache de resultados de classificação (Redis).
- [ ] Implementação de filas para processamento em lote (Celery/RabbitMQ).
- [ ] Otimização de consultas ao SCR (batch queries).

### Melhorias de UX

- [ ] Modo offline para classificação individual.
- [ ] Exportação de dashboards em PDF.
- [ ] Comparativo temporal de métricas.

### Integrações

- [ ] Integração real com API SCR BACEN (substituir mock).
- [ ] Webhook para notificações externas.
- [ ] API GraphQL (alternativa ao REST).

---

## 📌 Notas

- **Data da última atualização**: 2026-01-18
- **Versão atual**: v3.0
- Para detalhes das mudanças, consulte o [CHANGELOG.md](CHANGELOG.md)
