# Changelog - Sistema de Risco Bancário

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2026-01-07] - Relatórios PDF e Sistema de Autenticação RBAC

### Adicionado
- **Sistema de Autenticação**:
  - Tela de login moderna com design glassmorphism.
  - Sistema RBAC com 4 perfis: Analista, Gestor, Auditor e Admin.
  - Permissões granulares por funcionalidade.
  - Menu do usuário com avatar e badge de role colorido.
  - Persistência de sessão via Zustand + localStorage.
  
- **Geração de Relatórios PDF**:
  - Laudo Técnico de Crédito completo usando `@react-pdf/renderer`.
  - Documento A4 profissional com logo, cabeçalho e rodapé.
  - Seções: Cliente, Classificação PRINAD, Operação, Cálculo ECL.
  - Badges coloridos para Rating e Stage IFRS 9.
  - Disclaimer de conformidade CMN 4.966/2021.

- **Logs de Auditoria (Frontend)**:
  - Página `/auditoria` com visualização de logs.
  - Filtros por ação, usuário e busca textual.
  - Exportação de logs em CSV.
  - Registro automático de navegação e ações do usuário.
  - Acesso restrito ao perfil Auditor e Admin.

- **Navegação Aprimorada**:
  - Link para "Início" na sidebar.
  - Links condicionais para Relatórios e Auditoria baseados em permissões.
  - Indicação de role do usuário no footer da sidebar.

### Modificado
- **AppLayout**: Integração completa com sistema de autenticação.
- **Versão do sistema**: Atualizada para v2.1.

### Libs Adicionadas
- `@react-pdf/renderer`: Geração de PDFs no cliente.
- `date-fns`: Formatação de datas em português.

## [2026-01-07] - Exportação Regulatória BACEN Doc3040

### Adicionado
- **Backend - Módulo Exportação BACEN**:
  - Novo módulo `modulo_exportacao_bacen.py` para geração de XML Doc3040.
  - Implementação da tag `ContInstFinRes4966` conforme Resolução CMN 4966/2021.
  - Mapeamento de campos ECL (PD, LGD, EAD, Stage) para formato BACEN.
  - ValidadorXSD para validação contra schema oficial.
  - Compactação automática em ZIP para envio via STA.
  
- **API Endpoints (ECL)**:
  - `POST /exportar_bacen`: Gera arquivo XML Doc3040 com dados ECL.
  - `POST /validar_bacen`: Valida XML contra schema e regras BACEN.
  
- **Frontend - Tab Exportação BACEN**:
  - Nova tab "Exportação BACEN" no módulo ECL.
  - Formulário de configuração (data-base, CNPJ, responsável, metodologia).
  - Validador integrado com upload de XML.
  - Download de arquivo ZIP gerado.
  - Exibição de estatísticas (clientes, operações, ECL total).
  - Indicadores visuais de status (SUCESSO/ERRO/REJEITADO).

### Documentação
- Plano de implementação em `implementation_plan.md`.
- Referência técnica baseada em:
  - SCR3040_Leiaute.xls
  - SCR_InstrucoesDePreenchimento_Doc3040.pdf
  - Instrução Normativa BCB 414

---

## [2026-01-06] - Reorganização e Frontend Web App

### Adicionado
- **Arquitetura Web**: Inicialização do frontend moderno usando Next.js 15, TypeScript e Tailwind CSS.
- **APIs Backend**: 
  - Nova API FastAPI para o módulo ECL (Perda Esperada).
  - Nova API FastAPI para o módulo Propensão (Otimização de Limites).
- **Dashboards Interativos**:
  - Implementação de gráficos usando Recharts para os módulos PRINAD, ECL e Propensão.
  - Cards de KPIs em tempo real para monitoramento de risco.
- **Funcionalidades PRINAD**:
  - Classificação individual com explicação de score.
  - Classificação em lote (batch) com upload de CSV e download de resultados.
- **Dockerização**:
  - `Dockerfile` otimizado para o frontend Next.js.
  - `Dockerfile` para cada um dos 3 serviços backend.
  - `docker-compose.yml` unificado para orquestração de todo o ecossistema.
- **Infraestrutura**:
  - Configuração do OpenRouter para futura integração com Agente de IA.
  - Sistema de temas (Claro/Escuro/Sistema) com persistência via Zustand.

### Modificado
- **Estrutura de Pastas**: Reorganização completa do projeto em `/backend` (Python) e `/frontend` (Next.js).
- **Gerenciamento de Estado**: Implementação de stores Zustand para preferências de usuário e configurações de API.
- **Segurança**: Migração de chaves e URLs para arquivos `.env`.

### Corrigido
- Erros de importação após a reorganização dos módulos backend.
- Problemas de tipagem TypeScript nos componentes de gráficos.
- Configuração de CORS para permitir comunicação entre frontend e múltiplas APIs.
