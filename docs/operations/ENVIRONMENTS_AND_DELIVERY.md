# Ambientes, entrega e rollback

## Ambientes

Os perfis versionados e sem segredos ficam em `config/environments/`:

| Ambiente | Banco | Startup da API | Política de tag |
|---|---|---|---|
| `local` | SQLite isolado | aplica migrations pendentes | livre |
| `test` | SQLite isolado | aplica migrations pendentes | livre |
| `demo` | PostgreSQL externo | apenas valida schema corrente | SemVer |

Copie o exemplo correspondente para um arquivo ignorado pelo Git e preencha os
segredos fora do repositório:

```powershell
Copy-Item .env.local.example .env.local
$env:RISK_ENV_FILE = ".env.local"
docker compose --profile local up --build
```

`local`, `test` e `demo` têm caminhos/credenciais e portas separados. Nenhum perfil
faz fallback silencioso de PostgreSQL para SQLite.

## Migrations controladas

`DATABASE_MIGRATION_MODE` aceita:

- `apply`: desenvolvimento/teste aplica automaticamente migrations imutáveis;
- `validate`: startup somente verifica versões e checksums, falhando se algo faltar;
- `disabled`: uso excepcional em processos que não acessam schema.

Em `demo`, somente `validate` é aceito. A etapa de mudança de schema deve ocorrer
antes da promoção, de forma explícita:

```powershell
.\venv\Scripts\python.exe scripts/deploy.py migrate --environment demo --env-file .env.demo
```

Falhas SQL são transacionais. Migrations aplicadas são forward-only e protegidas por
checksum; alterar ou apagar uma migration histórica é erro de integridade.

## Continuous delivery

O workflow `Controlled delivery` produz um plano JSON auditável e publica as imagens
API/frontend no GHCR com tag imutável. `demo` exige versão semântica e pode usar
aprovação no GitHub Environment. Tags `vX.Y.Z` também geram release notes a partir
de `.github/release.yml`; o conteúdo final deve seguir
`docs/operations/RELEASE_NOTES_TEMPLATE.md`.

Publicar uma imagem não substitui a promoção no alvo nem prova conformidade. O plano,
o run de CI e a aprovação humana devem permanecer associados à release.

## Rollback

O rollback troca somente a aplicação pela versão anterior registrada:

```powershell
.\venv\Scripts\python.exe scripts/deploy.py promote --environment test --image-tag candidate-2 --commit <sha>
.\venv\Scripts\python.exe scripts/deploy.py rollback --environment test
```

O banco não recebe down migration automática. Antes de uma promoção, a mudança de
schema deve preservar compatibilidade com a versão anterior; se isso não for possível,
é obrigatória uma migration forward corretiva e uma janela de mudança específica.
