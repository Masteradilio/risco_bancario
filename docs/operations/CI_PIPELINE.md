# Pipeline de integração contínua

## Contrato

O workflow `.github/workflows/ci.yml` é executado em todo `push`, pull request e
acionamento manual. A aprovação de uma mudança exige todos os jobs abaixo verdes:

- `Quality / Python and frontend`: Black, Ruff, MyPy, testes canônicos e legados,
  cobertura mínima configurada e build TypeScript/Vite;
- `Security / dependency audit`: `pip-audit` no ambiente Python resolvido e
  `npm audit` nas dependências de produção;
- `Security / secret scan`: Gitleaks sobre todo o histórico Git;
- `Container / api` e `Container / frontend`: builds reproduzíveis, sem publicação.

As actions de terceiros são fixadas por SHA e comentadas com a versão humana. O
workflow possui somente permissão de leitura do conteúdo e cancela execuções antigas
da mesma referência. A resolução Python é congelada em `requirements-ci.lock`,
gerado a partir de todos os extras do `pyproject.toml` com CPython 3.13.

## Execução local

No Windows, a porta de entrada oficial usa o ambiente virtual do projeto:

```powershell
.\scripts\quality.ps1
```

Para executar uma seção isolada:

```powershell
.\scripts\quality.ps1 --stage static
.\scripts\quality.ps1 --stage tests
.\scripts\quality.ps1 --stage frontend
```

O mesmo contrato multiplataforma usado no GitHub está em `scripts/quality.py`.

As auditorias locais são:

```powershell
.\venv\Scripts\python.exe -m pip_audit --local --skip-editable
npm audit --prefix frontend --omit=dev --audit-level=high
```

Para atualizar deliberadamente o lock após mudar o manifesto:

```powershell
.\venv\Scripts\python.exe -m piptools compile --all-extras --strip-extras --output-file=requirements-ci.lock pyproject.toml
```

## Containers

Os arquivos `docker/Dockerfile.api` e `docker/Dockerfile.frontend` executam como
usuários sem privilégio. A API não inclui segredos: `RISK_API_JWT_SECRET` e demais
configurações devem ser injetados somente em runtime. A indisponibilidade local do
daemon Docker não autoriza ignorar o gate; o Buildx do GitHub é a evidência oficial
de build da Tarefa 15.1.

## Proteção da `main`

Os cinco checks acima devem ser configurados como obrigatórios na regra de proteção
da `main`. A ativação da regra ocorre depois que o workflow está verde na branch de
modernização, evitando registrar nomes de checks inexistentes.
