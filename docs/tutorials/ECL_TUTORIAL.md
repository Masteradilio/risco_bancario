# Tutorial de ECL com evidência rastreável

## 1. O que o motor calcula

Para cada período `t` e cenário `s`, o motor calcula a perda incremental:

```text
ECL(t,s) = sobrevivência(t-1,s) × PD_marginal(t,s)
           × LGD(t,s) × EAD(t,s) × desconto(t)
```

A soma dos períodos forma a ECL do cenário. A ECL econômica é a soma ponderada
pelos pesos dos cenários. O motor conserva a decomposição, permitindo reconciliar
cada centavo com PD, LGD, EAD, sobrevivência e desconto.

Stage 1 usa no máximo 12 meses. Stage 2 usa a curva lifetime fornecida. Stage 3
é mensurado por cash shortfall descontado em serviço próprio. POCI mantém a
comparação com a taxa efetiva ajustada ao crédito. Essas quatro semânticas não
são reduzidas a uma fórmula única.

## 2. Exemplo mínimo

Considere uma exposição sacada de R$ 100, PD marginal de 10%, LGD de 40% e fator
de desconto 1 no primeiro período. Sem saldo não sacado:

```text
EAD = 100 + (0 × CCF) = 100
ECL = 1 × 0,10 × 0,40 × 100 × 1 = R$ 4,00
```

Se base, upside e downside tiverem a mesma curva, com pesos 50%, 20% e 30%, a
ECL ponderada também será R$ 4,00. Um stress com peso zero continua calculado e
publicado, mas não altera o valor ponderado.

## 3. Execute o caso pela API

1. Inicie a API e obtenha um JWT conforme `docs/api/ECL_API_V1.md`.
2. Envie o payload completo de `docs/api/examples/ecl_individual.json` para
   `POST /api/v1/ecl/individual`.
3. Guarde `execution_id` e consulte
   `GET /api/v1/ecl/executions/{execution_id}`.
4. Confirme que `probability_weighted_ecl` é `4.00`, que existem quatro cenários
   e que todos os resultados possuem `payload_hash`.
5. Abra o workspace React e informe o `execution_id`; o painel consulta a mesma
   evidência persistida, sem criar números substitutos.

Exemplo PowerShell completo em `docs/api/EXAMPLES.md`.

## 4. Estágio e cenários

`stage_assessment` registra estado de originação e atual, rating, PD lifetime e
códigos de motivo. O campo `current_stage` deve coincidir com `stage`. O motor
não infere uma justificativa ausente.

Cada cenário contém série macroeconômica, tipo, peso e versão. Os pesos são parte
do pedido auditável; não existem pesos regulatórios universais embutidos. Alterar
curva, peso, modelo, configuração ou commit altera a linhagem.

## 5. Ajustes e reporte

O resultado econômico é preservado antes dos ajustes. Overlay gerencial e piso
regulatório têm políticas, justificativas e aprovações próprias. O ledger separa:

- ECL econômica;
- overlay gerencial;
- piso regulatório;
- ECL final reportada.

Não aplicado é diferente de zero. Essa distinção evita que ausência de decisão
seja apresentada como decisão por valor nulo.

## 6. Como interpretar a demonstração

Os dados são sintéticos e úteis para testar contratos, cálculos, governança e
rastreabilidade. Eles não demonstram desempenho em uma carteira institucional.
Consulte `docs/validation/LIMITATION_REGISTER.md` antes de interpretar métricas.
Os golden cases independentes em `docs/golden_cases/` validam aritmética; OOT e
backtesting avaliam evidências distintas e não transformam modelos reprovados em
aprovados.
