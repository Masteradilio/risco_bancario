# Observabilidade da API e dos jobs

## Sinais e correlação

Cada request recebe `trace_id`, `span_id` e `request_id`. O middleware aceita
`traceparent` W3C válido, preserva o trace e cria um novo span de servidor; devolve
`traceparent` e `X-Request-ID` na resposta. Jobs de carteira acrescentam `job_id` ao
mesmo contexto local.

Os logs são JSON em UTC e incluem somente campos operacionais allowlisted. Payloads,
tokens, senhas, DSNs, nomes de cliente e resultados ECL não são enviados ao log.
Eventos principais:

- `http.request.started`, `http.request.completed`, `http.request.failed`;
- `job.started`, `job.completed`, `job.failed`.

## Métricas

`GET /metrics` expõe Prometheus text format:

- `risco_http_requests_total` por método, template de rota e classe de status;
- `risco_http_request_duration_seconds` como histograma;
- `risco_jobs_total` e `risco_job_duration_seconds` por tipo/status;
- `risco_jobs_in_progress`;
- `risco_application_info` com ambiente e versão.

IDs, paths concretos, contrato e usuário nunca são labels, evitando cardinalidade
descontrolada e exposição de dados.

## Dashboard e alertas

O profile adicional sobe Prometheus e Grafana provisionados:

```powershell
$env:RISK_ENV_FILE = ".env.local"
$env:GRAFANA_ADMIN_PASSWORD = "<secret-from-secure-store>"
docker compose --profile local --profile observability up --build
```

O dashboard `Risco Bancário - API e Jobs` mostra taxa/status HTTP, p95, resultado de
jobs e jobs em andamento. As regras alertam indisponibilidade, razão de 5xx acima de
2%, falha de carteira e job ativo por mais de 30 minutos.

Prometheus/Grafana são componentes operacionais demonstrativos. Em ambiente real,
retenção, roteamento do Alertmanager, autenticação, TLS e destino de logs devem ser
configurados pela plataforma institucional; não há integração externa presumida.
