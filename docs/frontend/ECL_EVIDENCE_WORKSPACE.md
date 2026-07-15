# Workspace de evidências ECL

## Escopo

O frontend ativo é um leitor autenticado de evidências ECL persistidas. Ele não calcula valores no navegador e não usa valores alternativos quando a API ou uma execução estão indisponíveis. As antigas rotas de dashboards estáticos foram removidas do grafo ativo da aplicação.

A rota `/agent` usa exclusivamente `POST /api/v1/agent/query` e apresenta resposta, classificação do guardrail e citações estruturadas. Seu contrato e limites estão em `docs/agent/GROUNDED_EVIDENCE_AGENT.md`.

Toda tela mantém o aviso de que o ambiente usa dados sintéticos e não é homologado para contabilização, decisão de crédito ou reporte oficial.

## Autenticação e autorização

- `POST /api/v1/auth/token` emite o JWT curto e revogável usado pelo navegador.
- O token é mantido em `sessionStorage`, nunca em credenciais hard-coded ou armazenamento persistente entre sessões.
- `POST /api/v1/auth/logout` revoga a sessão no servidor.
- A matriz exibida pelo cliente espelha os perfis canônicos `ANALYST`, `MANAGER`, `AUDITOR` e `ADMIN`, mas toda decisão de autorização permanece na API.
- Usuários são criados pelo bootstrap interativo descrito em `docs/api/ECL_API_V1.md` e `docs/security/THREAT_MODEL.md`; não existem botões de acesso rápido ou senhas demonstrativas embutidas.

## Contrato de evidência

O operador informa um `execution_id`. O frontend consulta `GET /api/v1/ecl/executions/{execution_id}` e renderiza somente o documento persistido:

- estágio atual, estágio de originação, ratings, PDs lifetime e códigos de motivo;
- curvas por período de PD marginal, LGD e EAD;
- ECL por período e cenário, acompanhada pelo hash SHA-256 de cada payload;
- soma por cenário, peso e reconciliação da ECL ponderada;
- estado explícito de overlay, piso regulatório e ECL reportado. Ausência é `null` e `NOT_APPLIED`, nunca zero presumido;
- hash de linhagem, revisão, status e versões de contrato, cenário, modelos, configuração e código.

O request canônico exige `stage_assessment`; `current_stage` deve coincidir com `stage`, e ao menos um `reason_code` é obrigatório. Esse contexto é persistido no contrato e em cada resultado periódico.

## Validação e limitações

`GET /api/v1/validation/limitations` fornece o conteúdo de `docs/validation/LIMITATION_REGISTER.md`, seu caminho e SHA-256. A consulta é autorizada como leitura de resultado e registrada na trilha imutável. O frontend mostra `LIMITED` e o documento integral; não converte limitações em uma conclusão positiva.

## Execução local

1. Inicie a API canônica com o ambiente virtual do projeto.
2. Em `frontend/`, execute `npm run dev`.
3. O Vite encaminha `/api` para `http://127.0.0.1:8000`. Em implantação de mesma origem nenhuma configuração é necessária; para origem separada, defina `VITE_API_URL` e configure a política de origem no gateway.
4. Autentique-se com um usuário persistido e consulte um UUID produzido por `/api/v1/ecl/individual` ou `/api/v1/ecl/portfolio`.

## Verificação

- `tests/interfaces/test_ecl_api.py` cobre o contexto de estágio, payload completo, limitações versionadas e autorização.
- `tests/interfaces/test_frontend_ecl_contract.py` impede a reativação de dashboards legados, credenciais demonstrativas e fallbacks silenciosos.
- `npm run build` executa TypeScript estrito e o build Vite; passou a integrar `scripts/quality.ps1`.
