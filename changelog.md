# Changelog - Sistema de Risco Bancário

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

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
