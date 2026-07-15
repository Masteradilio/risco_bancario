# Agente fundamentado em evidências

## Decisão de arquitetura

O agente ativo não é um chatbot geral. Ele é um leitor determinístico, somente leitura, de uma execução ECL explicitamente informada e autorizada. Não chama LLM, web, RAG, shell, SQL arbitrário ou ferramentas legadas; assim, uma instrução do usuário não pode ampliar suas fontes ou permissões.

O router de `backend/agente` foi retirado do servidor legado. Esse pacote permanece apenas como código histórico congelado e não integra a fronteira de produção/demo. Ele contém geradores aleatórios e não deve ser importado, montado ou usado como evidência.

## Fluxo autorizado

`POST /api/v1/agent/query` recebe `execution_id` e `question`. A dependência RBAC exige `ecl:result:read`, portanto ANALYST, MANAGER e AUDITOR podem consultar, enquanto ADMIN não recebe acesso quantitativo implícito. A execução é buscada por parâmetro SQL interno fixo; nenhuma parte da pergunta participa da consulta.

O serviço em `src/agent/evidence.py` lê somente:

- `calculation_executions`, para revisão, status, data-base e linhagem;
- `calculation_results`, para contexto de estágio e valores periódicos/cenários;
- `docs/validation/LIMITATION_REGISTER.md`, para limites de validade.

Toda consulta é auditada com usuário, perfil, execução, hash da pergunta, status do guardrail e quantidade de citações. O texto da pergunta não é copiado para a trilha.

## Contrato de resposta

A resposta sempre declara `data_classification=SYNTHETIC` e `official_conformity=NOT_ASSESSED`. Respostas factuais possuem:

- citação de linhagem com o `lineage_hash` persistido;
- citação da coleção ordenada de resultados, cujo hash é derivado dos hashes imutáveis individuais;
- citação documental com o SHA-256 do Limitation Register.

Os identificadores aparecem no próprio texto e na lista estruturada `citations`, com tipo, localizador e hash. Respostas fundamentadas ficam `LIMITED`, porque as limitações de validação permanecem vigentes. O agente nunca transforma essa classificação em homologação ou certificação.

## Guardrails

Solicitações para ignorar instruções, revelar prompt/segredo/token/senha, burlar autorização/RBAC, ativar modo desenvolvedor ou executar SQL/shell/comandos são recusadas antes de qualquer leitura de execução. A resposta `REFUSED` não inclui citações porque nenhuma fonte é acessada.

O desenho reduz a superfície de prompt injection por não delegar decisão de ferramenta a um modelo generativo. O filtro textual é defesa adicional, não a fronteira primária: mesmo uma formulação não reconhecida continua limitada às três fontes fixas e às consultas parametrizadas.

## Limites

- Não há autorização row-level por dono/carteira; nesta fase `ecl:result:read` permite leitura do conjunto de resultados. Uma política de escopo institucional deve ser adicionada antes de dados reais.
- Não há geração livre, memória conversacional ou interpretação de documentos externos.
- O resumo atual cobre uma execução; análises entre execuções exigem novo contrato explícito e testes de escopo.
- O código histórico de `backend/agente` ainda existe para rastreabilidade, mas não é suportado nem montado.

## Verificação

`tests/interfaces/test_ecl_api.py` cobre grounding, hashes/citações, pergunta sobre conformidade, quatro padrões de prompt injection, execução inexistente, ausência de autenticação e negação ao perfil sem leitura de resultado. `tests/interfaces/test_frontend_ecl_contract.py` bloqueia a remontagem do router aleatório e exige que a rota ativa use o cliente fundamentado sem fallback.
