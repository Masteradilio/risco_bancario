# Relações macroeconômicas com PD, LGD, EAD e CCF

## Decisão metodológica

As relações vigentes são uma parametrização sintética transparente, não uma estimação.
Não há dados institucionais suficientes para ajustar coeficientes macroeconômicos de
forma defensável. A política `config/macro_risk_relations/2026.07.1.json` registra
`demonstrative_not_estimated_not_approved` e não pode ser apresentada como calibrada.

Para cada variável, calcula-se o desvio em relação à âncora. Para cada componente de
risco:

```text
score = escalar_segmento × (Σ beta_i × desvio_i + Σ gamma_j × desvio_j × |desvio_j|)
fator = limitar(exp(score), mínimo, máximo)
```

A transformação exponencial e os termos quadráticos permitem resposta não linear. Os
limites evitam fatores negativos ou explosivos, mas também são julgamentos sintéticos.

## Âncoras

| Variável | Âncora |
|---|---:|
| crescimento do PIB | 2,20 |
| inflação | 4,50 |
| taxa de política monetária | 9,00 |
| desemprego | 7,50 |
| endividamento das famílias | 49,00 |
| pressão de risco | 0,00 |

## Coeficientes lineares

| Componente | PIB | inflação | taxa | desemprego | dívida | pressão |
|---|---:|---:|---:|---:|---:|---:|
| PD | -0,080 | 0,015 | 0,010 | 0,055 | 0,006 | 0,015 |
| LGD | -0,035 | 0,006 | 0,004 | 0,025 | 0,004 | 0,008 |
| EAD | -0,010 | 0,002 | -0,003 | 0,012 | 0,003 | 0,003 |
| CCF | -0,025 | 0,004 | -0,006 | 0,025 | 0,005 | 0,006 |

Termos quadráticos: PD usa desemprego 0,004 e pressão 0,0015; LGD usa PIB -0,002 e
pressão 0,0008; EAD usa desemprego 0,001; CCF usa desemprego 0,002 e pressão 0,0005.

## Segmentos

Os escores são escalados separadamente para `portfolio`, `secured`, `revolving` e
`off_balance`. O segmento rotativo recebe escala 1,20 em EAD e 1,30 em CCF; garantidos
recebem menor sensibilidade, especialmente LGD 0,80. Todos os valores estão integralmente
no JSON versionado.

## Diagnóstico das trajetórias

Fatores no último mês da trajetória sintética, segmento `portfolio`, seed 91:

| Cenário | PD | LGD | EAD | CCF |
|---|---:|---:|---:|---:|
| otimista | 0,766168 | 0,887021 | 0,955830 | 0,909455 |
| base | 1,015506 | 1,006946 | 1,001998 | 1,004527 |
| pessimista | 1,713943 | 1,276602 | 1,088724 | 1,198830 |
| stress | 4,000000 | 1,976931 | 1,265016 | 1,690208 |

Todos os componentes aumentam com a severidade. A PD de stress toca o teto de 4,00,
evidência de sensibilidade forte e também uma limitação a monitorar. Esse ordenamento é
um resultado da parametrização e não valida sua plausibilidade empírica.

## Uso e limitações

Uso permitido: desenvolvimento, testes de cenário e demonstração de rastreabilidade.
Uso proibido: provisionamento real, orçamento, capital, decisão de crédito ou alegação
de calibração. A futura promoção exige dados históricos, desenho causal, estimação por
segmento, holdout temporal, estabilidade, validação independente e aprovação humana.

As curvas específicas de PD/LGD/EAD e o ECL integral serão construídos na Tarefa 9.3;
esta tarefa entrega somente fatores macroeconômicos separados e auditáveis.
