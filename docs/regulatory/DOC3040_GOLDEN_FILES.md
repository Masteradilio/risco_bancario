# Golden files do Documento 3040

## Pacote

O diretório `tests/fixtures/doc3040/2026.07` contém fixtures imutáveis para a versão
`2026.07-observed-20260714`. `manifest.json` registra SHA-256, resultado esperado e a
qualificação `synthetic_local_prevalidation_not_bcb_homologation`.

| Arquivo | Categoria esperada |
|---|---|
| `valid_minimal.xml` | `PREVALIDATED_DERIVED_XSD` |
| `invalid_xsd_missing_cep.xml` | `DERIVED-XSD` |
| `invalid_domain_modality.xml` | `LOCAL-DOMAIN` |
| `invalid_semantic_total.xml` | `LOCAL-TOTAL-CLIENTS` |

O caso positivo reconcilia uma operação PF de modalidade 0203, valor contábil bruto de
R$ 980,00, perda acumulada de R$ 20,00 e vencimentos de R$ 580,00 + R$ 400,00. O teste
compara o arquivo ao gerador byte a byte, desconsiderando apenas a quebra final de linha
do arquivo textual.

## Regressão de versão

O teste fixa julho-outubro de 2026 na versão observada. Junho de 2026 é bloqueado porque
o snapshot de julho não prova o estado histórico exato; novembro é bloqueado até a
incorporação da mudança `NR3`. Não há fallback para outra versão.

## Limites

“Válido” no nome da fixture significa válido para as camadas locais documentadas: XSD
estrutural derivado, allowlist do subconjunto, críticas semânticas locais e controle de
carteira/ECL. O relatório conserva `official_xsd_executed=false` e
`official_critics_executed=false`. O pacote não é exemplo oficial do BCB, não foi
submetido ao aplicativo validador e não está pronto para transmissão.

## Evidência

`tests/regulatory/test_doc3040_golden_files.py` verifica bytes, hashes, categorias de
erro, versão e ausência de alegação oficial. As fixtures inválidas permanecem legíveis e
alteram uma categoria principal por arquivo.
