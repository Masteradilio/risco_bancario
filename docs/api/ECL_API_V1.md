# API canônica de ECL v1

## Finalidade e limites

A API em `src/interfaces/api` expõe o motor canônico de ECL por cenário e sua persistência versionada. Ela é demonstrativa, opera somente com dados sintéticos e não representa homologação ou certificação pelo Banco Central do Brasil.

O contrato v1 recebe curvas de risco já produzidas e validadas pelos componentes de PD, LGD e EAD. Não recebe variáveis cadastrais brutas nem chama o pipeline heurístico legado. Stage 1 aceita no máximo 12 períodos; Stage 2 aceita a curva lifetime informada. Stage 3 e POCI permanecem em seus serviços canônicos próprios e ainda não são rotas HTTP desta versão.

## Execução local

```powershell
$env:DATABASE_BACKEND = "sqlite"
$env:DATABASE_SQLITE_PATH = "var/api-demo.sqlite3"
$env:JWT_SECRET = "substitua-por-segredo-aleatorio-com-32-bytes-ou-mais"
.\venv\Scripts\python.exe scripts\bootstrap_api_user.py manager MANAGER
.\venv\Scripts\python.exe -m uvicorn --factory src.interfaces.api.app:create_app --host 127.0.0.1 --port 8000
```

O OpenAPI fica em `http://127.0.0.1:8000/docs`. Para PostgreSQL, selecione `DATABASE_BACKEND=postgresql` e forneça `DATABASE_URL`; falhas nunca produzem fallback silencioso.

## Endpoints

| Método | Rota | Contrato |
|---|---|---|
| `POST` | `/api/v1/auth/token` | valida credenciais e emite JWT curto com sessão persistida |
| `POST` | `/api/v1/auth/logout` | revoga a sessão do token atual |
| `POST` | `/api/v1/security/confirmations` | cria confirmação de uso único vinculada a ação e hash do payload |
| `GET` | `/api/v1/audit/events` | AUDITOR/ADMIN consultam eventos encadeados; a leitura também é auditada |
| `POST` | `/api/v1/ecl/individual` | valida e calcula uma curva, persiste execução/resultados e retorna decomposição por cenário e período |
| `POST` | `/api/v1/ecl/portfolio` | aceita até 10.000 cálculos e retorna `202` com um job persistido |
| `GET` | `/api/v1/ecl/jobs/{job_id}` | retorna estado, hash do pedido, resultado ou código de erro não sensível |
| `GET` | `/api/v1/ecl/executions/{execution_id}` | retorna evidência da execução, linhagem versionada e hashes dos resultados |
| `GET` | `/api/v1/validation/limitations` | retorna o registro de limitações, caminho e SHA-256; a leitura é auditada |

Campos desconhecidos são rejeitados. Taxas ficam entre zero e um, dinheiro usa `Decimal`, hashes exigem SHA-256 em minúsculas e o commit exige hexadecimal de 7 a 40 caracteres. O payload deve identificar versões de modelos, cenário, configuração e código. `stage_assessment` é obrigatório, compara estágio, rating e PD lifetime com a originação e exige ao menos um código de motivo; `current_stage` deve coincidir com `stage`.

Cada resultado periódico persiste o contexto de estágio, tipo e peso do cenário, sobrevivência, PD marginal, LGD, EAD, CCF, desconto, ECL e estado de ajustes. Overlay, piso e ECL reportado não aplicados são representados como `null` com status `NOT_APPLIED`, sem conversão silenciosa em zero. O workspace de leitura está documentado em `docs/frontend/ECL_EVIDENCE_WORKSPACE.md`.

## Jobs

O job muda de `PENDING` para `RUNNING` e termina em `SUCCEEDED` ou `FAILED`. Nesta entrega o executor usa `BackgroundTasks` no mesmo processo, adequado à demonstração local. Reinício, retry distribuído, fila externa, concorrência multiworker e cancelamento serão tratados na infraestrutura de ambientes; o estado e o resultado já ficam persistidos.

Erros de lote são registrados como código estável `CALCULATION_FAILED`; detalhes técnicos permanecem nos logs e não são devolvidos ao cliente.

## Segurança e confirmação crítica

ANALYST calcula individualmente; MANAGER também calcula carteira; AUDITOR lê resultados; ADMIN não recebe acesso quantitativo implícito. Aprovação, exportação, auditoria e gestão de usuários são permissões independentes. O contrato completo está em `docs/security/THREAT_MODEL.md`.

Para carteira, serialize `PortfolioRequest.model_dump(mode="json")` como JSON canônico, calcule SHA-256 e solicite uma confirmação com ação `ecl:calculate:portfolio`. Envie o identificador retornado em `X-Confirmation-Id`. A confirmação expira, pertence ao usuário e não pode ser reutilizada.

O rate limit local é por login e por usuário/permissão. Ele não substitui controle distribuído no gateway quando houver múltiplos workers.

Entradas e resultados de operações relevantes são registrados por hash na trilha append-only descrita em `docs/architecture/AUDIT_TRAIL.md`.
