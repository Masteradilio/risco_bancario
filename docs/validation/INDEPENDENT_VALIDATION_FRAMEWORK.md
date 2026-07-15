# Framework de validação independente

## Escopo e independência

O pacote `src/validation/model_risk` implementa uma função de segunda linha simulada e
separada do desenvolvimento. A separação é verificável no contrato:

- toda submissão de desenvolvimento entra como `not_approved`;
- o validador deve usar a função `independent_model_validation`, atestar independência,
  ter identificador diferente do responsável pelo desenvolvimento e pertencer a outra
  unidade;
- a submissão fixa commit Git, hash SHA-256 do dataset e hashes SHA-256 dos artefatos;
- somente o pacote de validação produz a decisão final.

Esses controles demonstram segregação técnica no projeto. Eles não representam comitê,
alçada ou aprovação institucional real.

## Política objetiva

A política versionada está em `config/validation/model_risk/2026.07.1.json`. Uma decisão
exige ao menos três critérios e cobertura das categorias `conceptual_soundness`, `data` e
`performance`.

| Resultado | Condição objetiva |
|---|---|
| `approved` | todos os critérios aprovados e nenhuma constatação aberta |
| `approved_with_reservations` | apenas avisos, falhas não obrigatórias ou constatações baixas/médias |
| `rejected` | falha obrigatória ou constatação alta/crítica |

Cada critério registra valor observado, limiar e referências de evidência. Cada
constatação registra severidade, detalhe, remediação e prazo quando aplicável. Critérios
obrigatórios não podem ser neutralizados por ressalva.

## Reprodutibilidade e uso

`validate_model_submission` ordena critérios e constatações por identificador, aplica a
política e calcula um hash SHA-256 canônico do relatório. `render_validation_report`
produz Markdown determinístico com identidade, política, evidências, decisão, razões e
hash. Assim, a mesma submissão, política e evidência produzem o mesmo relatório,
independentemente da ordem de entrada.

Os backtests das tarefas seguintes devem transformar suas métricas em critérios e
evidências desse contrato. Até que dados reais e uma função institucional independente
existam, os relatórios devem manter o estado `synthetic_independent_validation` e o aviso
de que não constituem aprovação institucional.
