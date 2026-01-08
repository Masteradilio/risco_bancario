# Changelog - Sistema de Gestão de Risco Bancário

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).


---

## [2.5.0] - 2026-01-08

### Sistema de Perfis de Acesso (RBAC Aprimorado)

#### Backend - Infraestrutura de Usuários
- **Nova estrutura `/backend/bancos_de_dados/usuarios/`**: Scripts DDL para gerenciamento de usuários
  - Tabela `usuarios`: Dados do usuário integrados com Windows AD
  - Tabela `usuarios_sessoes`: Controle de sessões com timeout de 30 minutos
  - Tabela `auditoria_atividades`: Log de todas as ações de usuários
  - Tabela `sistema_erros`: Log de erros visível apenas para Admin
  - Tabela `permissoes_perfil`: Mapeamento configurável de permissões
- **Novo módulo `/backend/shared/auth_api.py`**: Autenticação e RBAC
  - Integração preparada para Windows NTLM/SSO
  - JWT tokens com refresh token (30min / 7 dias)
  - Funções: `authenticate_windows_user`, `get_current_user`, `require_permission`, `require_roles`
  - Gerenciamento de usuários: `create_user`, `list_users`, `update_user`, `delete_user`
  - Auditoria: `log_activity`, `log_error`, `get_audit_logs`, `get_system_errors`
- **Novo router `/backend/shared/auth_router.py`**: Endpoints FastAPI
  - `POST /auth/login`, `POST /auth/logout`, `POST /auth/refresh`, `GET /auth/me`
  - CRUD `/usuarios` (Admin only)
  - `GET /auditoria/logs` (Auditor, Admin)
  - `GET /sistema/erros` (Admin only)

#### Frontend - Componentes RBAC
- **Novo componente `PermissionGate.tsx`**: Controle de exibição por permissão
  - `PermissionGate`: Renderiza conteúdo se usuário tem permissão
  - `RoleGate`: Renderiza conteúdo se usuário tem perfil específico
  - `ReadOnlyGate`: Desabilita interações para perfil Auditor (somente leitura)
- **Atualizado `useAuth.ts`**: Enhanced User interface
  - Novos campos: `loginWindows`, `cargo`, `isExterno`, `expiresAt`
  - Permissões refinadas por perfil:
    - ANALISTA: Operações diárias (classify, calculate)
    - GESTOR: Analista + Exportações BACEN + Analytics
    - AUDITOR: Leitura completa + Logs + Relatórios (READ-ONLY)
    - ADMIN: Acesso total + CRUD usuários + Erros sistema

#### Matriz de Perfis
| Perfil | Operações | Exportações | Logs | Usuários |
|--------|-----------|-------------|------|----------|
| ANALISTA | ✅ | ❌ | ❌ | ❌ |
| GESTOR | ✅ | ✅ BACEN | ❌ | ❌ |
| AUDITOR | 👁️ Leitura | ✅ Auditoria | ✅ | ❌ |
| ADMIN | ✅ | ✅ | ✅ | ✅ |

#### Auditores Externos BACEN
- Flag `isExterno` para distinguir auditores internos e externos
- Contas temporárias com `expiresAt` (padrão 30 dias)
- Admin pode criar usuários temporários para auditoria externa

#### Dashboard de Administração (`/admin`) - NOVO
- **Gerenciamento de Usuários**: CRUD completo com modal interativo
  - Criar, editar e desativar usuários do sistema
  - Campos: Nome, Email, Matrícula, Login Windows, Perfil, Departamento, Cargo
  - Toggle para marcar como Auditor Externo (expiração automática em 30 dias)
  - Filtros por perfil e busca por nome/email/matrícula
- **Logs de Erros do Sistema**: Visualização de erros com níveis
  - Cards coloridos por severidade (CRITICAL, ERROR, WARNING, INFO)
  - Exibição de módulo, timestamp e mensagem de erro
- **Configurações do Sistema**:
  - Timeout de sessão (15/30/60 minutos)
  - Validade de usuários externos (7/15/30/60 dias)
  - Retenção de logs de auditoria (30/60/90/365 dias)

#### Dashboard de Auditoria Aprimorado (`/auditoria`) - MELHORADO
- **Trilha de Auditoria Completa**:
  - Filtros avançados por período (1/7/30/90 dias), ação e usuário
  - Exportação para CSV com todos os campos
  - Estatísticas: Total de logs, atividades hoje, usuários ativos, exportações
- **Relatórios de Conformidade** (nova aba):
  - Relatório de Provisionamento ECL (CMN 4966 - Art. 36)
  - Relatório de Migração de Estágios (IFRS 9)
  - Relatório de Write-off e Recuperações (CMN 4966 - Art. 49)
  - Relatório Forward Looking (CMN 4966 - Art. 36 §5º)
  - Status de cada relatório (completo/pendente) com opção de exportação
- **Histórico de Envios BACEN** (nova aba):
  - Tabela com todas as remessas Doc3040 enviadas
  - Colunas: Código, Documento, Data Base, Data Envio, Status, Protocolo

#### Navegação Condicional
- Link "Admin" visível apenas para perfil ADMIN (permissão `manage:users`)
- Atualização de versão no rodapé do sidebar: `v2.5 - RBAC Admin`

#### Novos Componentes UI
- **Dialog** (`/components/ui/dialog.tsx`): Modal Radix UI para formulários
- **Switch** (`/components/ui/switch.tsx`): Toggle para opções booleanas

#### Dependências Adicionadas
- `@radix-ui/react-dialog` - Componente de modal acessível
- `@radix-ui/react-switch` - Componente de toggle acessível

---

## [2.4.0] - 2026-01-08

### Otimização e Usabilidade - Frontend Perda Esperada
- **Fluxo de Trabalho Intuitivo**: Reorganização dos menus para refletir o ciclo de vida do cálculo (Pipeline -> Exportação).
- **Integração Pipeline-Exportação**:
  - Geração de XML condicionada à execução bem-sucedida do pipeline na sessão.
  - Alertas visuais guiando o usuário entre as etapas de processamento e reporte regulatório.
- **Transparência Regulatória**:
  - Adição de Cards Informativos "Compliance CMN 4966" em todas as telas do módulo.
  - Explicação didática sobre cada componente (Estágios, LGD, Forward Looking, Cura, Write-off) e seu embasamento legal (Artigos específicos da resolução).
- **Correções Técnicas**:
  - Ajustes de tipagem e imports nos gráficos do módulo de LGD.

---

## [2.3.0] - 2026-01-08

### Adicionado - Infraestrutura de Banco de Dados

#### Banco de Dados MySQL para Persistência Regulatória
- **Nova estrutura `/backend/bancos_de_dados/`**: Scripts DDL de referência para integração
- **4 esquemas organizados por domínio**:
  - `ecl`: ecl_resultados, ecl_cenarios, ecl_parametros_fl, ecl_grupos_homogeneos
  - `estagio`: estagio_historico, estagio_cura, estagio_triggers
  - `writeoff`: writeoff_baixas, writeoff_recuperacoes
  - `auditoria`: auditoria_envios_bacen, auditoria_validacoes
- **11 tabelas** com campos para conformidade CMN 4966 / IFRS 9
- **Script consolidado `esquema_completo.sql`** para deploy unificado
- **Scripts DDL + INSERT** por tabela para referência da equipe de TI

#### API Write-off (Art. 49 CMN 4966)
- **5 novos endpoints** em `/writeoff/`:
  - `POST /writeoff/registrar-baixa` - Registra baixa contábil
  - `POST /writeoff/registrar-recuperacao` - Registra recuperação pós-baixa
  - `GET /writeoff/relatorio/{contrato_id}` - Relatório por contrato
  - `GET /writeoff/relatorio-consolidado` - Relatório consolidado
  - `POST /writeoff/taxa-recuperacao` - Taxa de recuperação histórica com filtros
- **8 Pydantic models** para requests e responses
- Integração com módulo `rastreamento_writeoff.py`

#### Frontend Perda Esperada
- **Renomeação**: Menu "ECL" → "Perda Esperada" 
- **Layout com submenu** de 10 itens de navegação
- **10 páginas completas** com Recharts:
  - Dashboard Principal (KPIs, PieChart, AreaChart, Tabela)
  - Cálculo ECL (Formulário + RadarChart)
  - Classificação de Estágios (Simulador + Histórico)
  - Grupos Homogêneos (Cards + PieChart)
  - Forward Looking (Cenários + Slider de Pesos)
  - LGD Segmentado (BarChart + RadarChart)
  - Sistema de Cura (Progress + Regras Art. 41)
  - Write-off (Dashboard + Formulários)
  - Exportação BACEN (Doc3040 + Download)
  - Pipeline Completo (Etapas Animadas)
- **Componentes shadcn/ui** adicionados: Badge, Progress, Slider
- **API Frontend** com 7 novos endpoints write-off



### Adicionado - Conformidade BACEN 4966


#### Forward Looking Multi-Cenário (Art. 36 §5º CMN 4966)
- **Novo módulo `cenarios_forward_looking.py`**: Implementação completa de cenários macroeconômicos ponderados
  - 3 cenários: Otimista (15%), Base (70%), Pessimista (15%)
  - Integração com API SGS do BACEN para dados macroeconômicos (SELIC, PIB, IPCA)
  - Cálculo de K_PD_FL e K_LGD_FL ponderados por cenário
  - ECL final calculado como média ponderada: `ECL_final = Σ(peso_i × ECL_i)`
- **Testes unitários**: 28 testes cobrindo todos os cenários e conformidade CMN 4966

#### Sistema de Cura Formal (Art. 41 CMN 4966)
- **Novo módulo `sistema_cura.py`**: Implementação de critérios formais de reversão de estágio
  - Stage 2 → 1: 6 meses de observação + melhora de PD
  - Stage 3 → 2: 12 meses de observação + 30% amortização
  - Reestruturações: 24 meses + 50% amortização (critérios mais rigorosos)
  - Flag `em_periodo_cura` para contratos em observação
  - Histórico de estágios por contrato
  - Reset automático do período de cura em caso de novos atrasos
- **Testes unitários**: 31 testes cobrindo todos os cenários de cura

#### Rastreamento de Write-off (Art. 49 CMN 4966) 
- **Novo módulo `rastreamento_writeoff.py`**: Sistema de acompanhamento de baixas por 5 anos
  - Classe `RastreadorWriteOff` com registro de baixas e recuperações
  - Acompanhamento de recuperações pós-baixa por 1825 dias (5 anos)
  - Cálculo de taxa de recuperação histórica (média e ponderada)
  - Geração de relatório regulatório para envio ao BACEN
  - Processamento em lote de DataFrames de baixas

### Integrado

#### Forward Looking Multi-Cenário integrado ao Pipeline ECL
- **Atualizado `pipeline_ecl.py`**:
  - Nova flag `usar_multi_cenario=True` no construtor
  - Instanciação automática de `GerenciadorCenarios`
  - K_PD_FL e K_LGD_FL calculados como média ponderada dos 3 cenários
  - Resultado ECL inclui `cenarios_detalhes` com breakdown por cenário

#### Sistema de Cura integrado aos Triggers de Estágio
- **Atualizado `modulo_triggers_estagios.py`**:
  - Nova função `aplicar_avaliacao_cura()` para avaliar elegibilidade
  - Nova função `aplicar_todos_triggers_com_cura()` com fluxo completo
  - Avaliação de cura ANTES dos triggers de deterioração
  - Flags: `cura_avaliada`, `cura_aplicada`, `estagio_pre_cura`

### Arquivos Criados
- `backend/perda_esperada/src/cenarios_forward_looking.py`
- `backend/perda_esperada/src/sistema_cura.py`
- `backend/perda_esperada/src/rastreamento_writeoff.py`
- `backend/perda_esperada/tests/test_cenarios_forward_looking.py`
- `backend/perda_esperada/tests/test_sistema_cura.py`
- `backend/perda_esperada/tests/test_integracao_conformidade.py`
- `backend/perda_esperada/test_integracao_bacen.py`

### Arquivos Modificados
- `backend/perda_esperada/src/pipeline_ecl.py` - Integração multi-cenário
- `backend/perda_esperada/src/modulo_triggers_estagios.py` - Integração cura


---

## [2.2.0] - 2026-01-07

### Adicionado
- **Unificação de documentação**: README.md e TODO.md consolidados na raiz
- **Análise de conformidade BACEN**: Documento `docs/ANALISE_CONFORMIDADE_BACEN.md`
- **Dashboard de investigação**: Seção "Investigate Transaction" funcional

### Alterado
- Melhoria no sistema de atualização do dashboard (separação entre auto-update e componentes estáticos)
- Refatoração do menu de seleção de transações

---

## [2.1.0] - 2026-01-06

### Adicionado
- **ECL IFRS 9**: Pipeline completo de cálculo de Perda Esperada
- **Grupos Homogêneos**: Segmentação automática por perfil de risco
- **LGD Segmentado**: Cálculo diferenciado por tipo de operação
- **Forward Looking básico**: Ajuste de PD por variáveis macroeconômicas
- **Exportação BACEN Doc3040**: Geração de XML para envio regulatório

### Alterado
- Migração para arquitetura IFRS 9 (3 estágios)
- Refatoração do módulo PRINAD para v2.0

---

## [2.0.0] - 2026-01-02

### Adicionado
- **PRINAD v2.0**: Modelo de Probabilidade de Inadimplência calibrado
  - Integração com dados SCR do BACEN
  - Score base + penalidades + boost de PD
  - Mapeamento para Rating BACEN (A-H)
- **Arrastar de Contraparte**: Regra §4º Art. 51 CMN 4966
- **Reestruturação**: Tratamento conforme Art. 41 e §2º Art. 49

---

## [1.0.0] - 2025-12-15

### Adicionado
- Estrutura inicial do projeto
- Backend FastAPI para APIs de risco
- Frontend Next.js para dashboard
- Módulo PROLIMITE para propensão a crédito
- Documentação base

---

*Para mais detalhes sobre cada funcionalidade, consulte o [README.md](README.md).*
