# API canônica de ECL v1

## Finalidade e limites

A API em `src/interfaces/api` expõe o motor canônico de ECL por cenário e sua persistência versionada. Ela é demonstrativa, opera somente com dados sintéticos e não representa homologação ou certificação pelo Banco Central do Brasil.

O contrato v1 recebe curvas de risco já produzidas e validadas pelos componentes de PD, LGD e EAD. Não recebe variáveis cadastrais brutas nem chama o pipeline heurístico legado. Stage 1 aceita no máximo 12 períodos; Stage 2 aceita a curva lifetime informada. Stage 3 e POCI permanecem em seus serviços canônicos próprios e ainda não são rotas HTTP desta versão.

## Execução local

```powershell
$env:DATABASE_BACKEND = "sqlite"
$env:DATABASE_SQLITE_PATH = "var/api-demo.sqlite3"
.\venv\Scripts\python.exe -m uvicorn src.interfaces.api.app:app --host 127.0.0.1 --port 8000
```

O OpenAPI fica em `http://127.0.0.1:8000/docs`. Para PostgreSQL, selecione `DATABASE_BACKEND=postgresql` e forneça `DATABASE_URL`; falhas nunca produzem fallback silencioso.

## Endpoints

| Método | Rota | Contrato |
|---|---|---|
| `POST` | `/api/v1/ecl/individual` | valida e calcula uma curva, persiste execução/resultados e retorna decomposição por cenário e período |
| `POST` | `/api/v1/ecl/portfolio` | aceita até 10.000 cálculos e retorna `202` com um job persistido |
| `GET` | `/api/v1/ecl/jobs/{job_id}` | retorna estado, hash do pedido, resultado ou código de erro não sensível |
| `GET` | `/api/v1/ecl/executions/{execution_id}` | retorna evidência da execução, linhagem versionada e hashes dos resultados |

Campos desconhecidos são rejeitados. Taxas ficam entre zero e um, dinheiro usa `Decimal`, hashes exigem SHA-256 em minúsculas e o commit exige hexadecimal de 7 a 40 caracteres. O payload deve identificar versões de modelos, cenário, configuração e código.

## Jobs

O job muda de `PENDING` para `RUNNING` e termina em `SUCCEEDED` ou `FAILED`. Nesta entrega o executor usa `BackgroundTasks` no mesmo processo, adequado à demonstração local. Reinício, retry distribuído, fila externa, concorrência multiworker e cancelamento serão tratados na infraestrutura de ambientes; o estado e o resultado já ficam persistidos.

Erros de lote são registrados como código estável `CALCULATION_FAILED`; detalhes técnicos permanecem nos logs e não são devolvidos ao cliente. A Tarefa 14.3 adicionará autenticação/RBAC e rate limit antes de qualquer exposição além do ambiente local controlado.
