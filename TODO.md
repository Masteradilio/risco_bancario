# TODO - Próximos Passos (Fase de Finalização)

Este documento lista as funcionalidades e melhorias pendentes para atingir 100% da implementação do sistema de Risco Bancário.

## ✅ Concluído (2026-01-07)

### 📊 Analytics e Relatórios
- [x] Geração de **PDFs de laudo técnico de crédito** via `@react-pdf/renderer`.
- [x] Formulário completo para preenchimento dos dados do laudo.
- [x] **Exportação regulatória BACEN Doc3040** (XML conforme Resolução CMN 4966/2021) - ✅ Concluído.
- [ ] Dashboard de performance do modelo (Monitoramento de Drift e Acurácia) - *Pendente*.

### 🔒 Segurança e Autenticação
- [x] Sistema de autenticação com tela de login moderna.
- [x] Controle de acesso baseado em perfis (RBAC): Analista, Gestor, Auditor, Admin.
- [x] Auditoria de logs (registro de ações do usuário no frontend).
- [ ] Implementação de **Windows NTLM/SSO** para ambiente corporativo - *Pendente backend*.
- [ ] Integração de logs de auditoria com backend (API) - *Pendente*.

---

## 🤖 Agente de IA (Prioridade)
- [ ] Integração com **LangGraph.js** no frontend.
- [ ] Implementação de ferramentas (tools) para o Agente consultar scores PRINAD, ECL e Propensão.
- [ ] Sistema de **RAG (Retrieval-Augmented Generation)** consumindo PDF/Markdown de regulamentações BACEN.
- [ ] Interface de chat persistente e proativa.

## 🧪 Qualidade e Testes
- [ ] Implementação de testes de ponta a ponta (E2E) com **Playwright**.
- [ ] Testes de carga nas APIs para suportar grandes volumes de classificação em lote.
- [ ] Cobertura de testes unitários no frontend.

## 🚀 Deploy e Infraestrutura
- [ ] Pipeline CI/CD automatizado no GitHub Actions/GitLab.
- [ ] Configuração de monitoramento e alertas (Prometheus/Grafana).
- [ ] Documentação completa da arquitetura técnica em Português.

