# Sensibilidade, stress e management overlays

## Sensibilidades versionadas

A política `config/scenario_sensitivity/2026.07.1.json` congela dois deslocamentos de
pesos e dois choques de trajetória. Cada execução deriva um novo hash do snapshot sem
alterar ou promover o conjunto de cenários original.

Caso sintético de seis meses, seed 91, segmento `portfolio`:

| Execução | ECL | Delta |
|---|---:|---:|
| pesos originais | R$ 121,51 | — |
| peso maior no pessimista | R$ 125,61 | R$ 4,10 |
| peso severo no pessimista | R$ 130,65 | R$ 9,14 |
| desemprego +1 p.p. | R$ 133,51 | R$ 12,00 |
| PIB -1 p.p. | R$ 137,22 | R$ 15,71 |
| stress original, não ponderado | R$ 187,54 | R$ 66,03 |

Os resultados confirmam resposta rastreável a pesos e trajetórias. São sensibilidades
da parametrização sintética, não previsão ou validação empírica.

## Stress testing

O stress permanece uma trajetória integral com peso zero. O relatório registra seu ECL
e delta contra o ECL ponderado sem incluí-lo silenciosamente na probabilidade. Mudanças
no stress exigem nova versão de cenário ou choque derivado identificável.

## Management overlays

`src/ecl/overlays/management.py` implementa uma camada posterior e separada do modelo.
Cada overlay exige:

- ID e versão;
- valor positivo ou negativo;
- motivo;
- aprovador e timestamp UTC;
- início e fim de vigência;
- quando revertido, timestamp, responsável e motivo da reversão.

Somente overlays ativos na data-base são somados. IDs duplicados, janelas inválidas,
reversões parciais, timestamps sem fuso e reversões anteriores à aprovação/vigência são
rejeitados. Um overlay revertido não pode ser revertido novamente.

O resultado preserva separadamente `economic_ecl`, `overlay_amount` e `final_ecl`, além
dos IDs aplicados. O overlay nunca modifica hazard, PD, LGD, EAD, CCF, pesos ou o ECL de
cada cenário. O ECL final possui piso operacional zero; pisos regulatórios pertencem à
Fase 11.

## Status e limitações

O framework está tecnicamente testado, mas não há overlays reais ou aprovação humana.
As sensibilidades e o stress usam coeficientes sintéticos `not_approved`. O uso permitido
continua restrito a testes, demonstração e preparação para validação independente.
