# Testes e gate de cobertura regulatória

Testes regulatórios ficam em `tests/regulatory`. Cada teste de evidência usa o
marcador Pytest `regulatory` e inclui o identificador estável da matriz no nome e
no metadado, por exemplo `IFRS9-ECL-002`.

Gerar relatório sem bloquear:

```powershell
.\scripts\regulatory-report.ps1 --output build/regulatory-coverage.md
```

Executar o gate de release:

```powershell
.\scripts\regulatory-report.ps1 --output build/regulatory-coverage.md --enforce
```

O gate retorna código diferente de zero enquanto qualquer requisito aplicável
ou condicionalmente aplicável não estiver `implemented` com código, teste
existente e evidência. Requisitos `partial` continuam bloqueando release. Itens
`not_applicable` não bloqueiam desde que possuam justificativa e evidência.

O comando geral `scripts/quality.ps1` executa os testes regulatórios e valida o
gerador do relatório, mas não usa `--enforce`: durante a modernização, o gate de
release deve continuar vermelho até as fases responsáveis concluírem os 20
requisitos atualmente abertos.
