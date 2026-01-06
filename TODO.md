# TODO - Próximos Passos (Fase de Finalização)

Este documento lista as funcionalidades e melhorias pendentes para atingir 100% da implementação do sistema de Risco Bancário.

## 🤖 Agente de IA (Prioridade)
- [ ] Integração com **LangGraph.js** no frontend.
- [ ] Implementação de ferramentas (tools) para o Agente consultar scores PRINAD, ECL e Propensão.
- [ ] Sistema de **RAG (Retrieval-Augmented Generation)** consumindo PDF/Markdown de regulamentações BACEN.
- [ ] Interface de chat persistente e proativa.

## 🔒 Segurança e Autenticação
- [ ] Implementação de **Windows NTLM/SSO** para ambiente corporativo.
- [ ] Controle de acesso baseado em perfis (RBAC): Analista, Gestor, Auditor.
- [ ] Auditoria de logs (quem consultou qual CPF).

## 📊 Analytics e Relatórios
- [ ] Geração de PDFs de laudo técnico de crédito.
- [ ] Exportação de relatórios regulatórios para o BACEN (formato XML/JSON).
- [ ] Dashboard de performance do modelo (Monitoramento de Drift e Acurácia).

## 🧪 Qualidade e Testes
- [ ] Implementação de testes de ponta a ponta (E2E) com **Playwright**.
- [ ] Testes de carga nas APIs para suportar grandes volumes de classificação em lote.
- [ ] Cobertura de testes unitários no frontend.

## 🚀 Deploy e Infraestrutura
- [ ] Pipeline CI/CD automatizado no GitHub Actions/GitLab.
- [ ] Configuração de monitoramento e alertas (Prometheus/Grafana).
- [ ] Documentação completa da arquitetura técnica em Português.
