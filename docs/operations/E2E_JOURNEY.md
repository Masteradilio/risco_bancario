# Jornada E2E canônica

## Objetivo

`scripts/e2e_pipeline.py` executa, sem mocks do backend legado, a jornada
demonstrativa completa do núcleo reconstruído. O comando materializa a fábrica
sintética em diretório temporário, treina e valida os modelos, executa a
classificação SICR, calcula e persiste ECL, aplica overlay e piso em camadas
separadas, reconcilia o ledger e gera o candidato do Documento 3040.

```powershell
.\venv\Scripts\python.exe scripts/e2e_pipeline.py --output evidence/e2e
```

Em um clone Git, a linhagem usa o commit curto corrente. Em um source archive
sem `.git`, o runner calcula um fingerprint SHA-256 determinístico de `src`,
`config`, `scripts` e `pyproject.toml`; `--commit` permite informar manualmente
um identificador hexadecimal de 7 a 40 caracteres.

## Semântica do resultado

O status esperado é `COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS`. A execução técnica
termina, mas PD, SICR, LGD e EAD permanecem `not_approved` porque a amostra e as
evidências são sintéticas e não atendem aos gates institucionais. “Validar e
aprovar” significa executar a decisão governada; não significa substituir uma
reprovação por aprovação artificial.

O XML recebe apenas `PREVALIDATED_DERIVED_XSD`. O XSD oficial e as críticas do
BCB não estão disponíveis no repositório e, portanto, não são declarados como
executados.

## Evidências

- `evidence/e2e/journey.json`: manifesto estruturado, bloqueios e linhagem;
- `evidence/e2e/report.md`: resumo legível da execução;
- `evidence/e2e/doc3040.xml`: candidato sintético;
- `evidence/e2e/prevalidation.json`: resultado detalhado da pré-validação local.

O frontend consulta a mesma execução persistida por
`/api/v1/ecl/executions/{execution_id}` e exibe status, resultados, versões e
hash de linhagem. A auditabilidade é demonstrada pelo registro persistido da
execução e pelo hash imutável do ledger; isso não equivale a homologação.
