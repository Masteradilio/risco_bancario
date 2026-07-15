# Exemplos da API canônica v1

Os exemplos usam apenas dados sintéticos. Antes de começar, inicie a API conforme
`ECL_API_V1.md`. Substitua usuário e senha por credenciais criadas localmente; não
grave senhas no repositório.

## Autenticar

Exemplo interativo com `curl.exe`. A senha existe somente na sessão local e a
variável é removida logo após a autenticação:

```powershell
$user = "manager"
$password = Read-Host "Senha"
$tokenResponse = curl.exe -sS http://127.0.0.1:8000/api/v1/auth/token `
  -H "Content-Type: application/json" `
  -d (ConvertTo-Json @{ username = $user; password = $password }) | ConvertFrom-Json
$token = $tokenResponse.access_token
Remove-Variable password
```

## Calcular ECL individual

O fixture publicável `docs/api/examples/ecl_individual.json` contém quatro
cenários e produz ECL ponderada de R$ 4,00.

```powershell
$result = curl.exe -sS http://127.0.0.1:8000/api/v1/ecl/individual `
  -X POST `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  --data-binary "@docs/api/examples/ecl_individual.json" | ConvertFrom-Json
$result | Select-Object execution_id, probability_weighted_ecl, lineage_hash
```

## Consultar evidência persistida

```powershell
$execution = curl.exe -sS `
  "http://127.0.0.1:8000/api/v1/ecl/executions/$($result.execution_id)" `
  -H "Authorization: Bearer $token" | ConvertFrom-Json
$execution | Select-Object execution_id, revision, status, lineage_hash
```

## Consultar limitações

```powershell
curl.exe -sS http://127.0.0.1:8000/api/v1/validation/limitations `
  -H "Authorization: Bearer $token"
```

## Processar carteira

Carteira exige papel `MANAGER` e confirmação de uso único ligada ao SHA-256 da
representação canônica do payload. A serialização deve seguir
`PortfolioRequest.model_dump(mode="json")`; consulte o exemplo executável em
`tests/interfaces/test_ecl_api.py`. Reutilizar confirmação, trocar o payload ou
omitir `X-Confirmation-Id` falha fechado.

## Respostas e falhas esperadas

- `401`: token ausente, inválido, expirado ou revogado;
- `403`: papel sem permissão;
- `409`: chave idempotente já usada com payload diferente;
- `422`: schema, horizonte ou invariantes inválidas;
- `429`: limite local excedido;
- `503`: fila de lote cheia.

Detalhes internos não são devolvidos em erros de job. Use `traceparent`, logs JSON
e a trilha de auditoria para correlação autorizada.
