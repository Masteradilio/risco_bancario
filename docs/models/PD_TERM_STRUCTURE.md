# Curvas mensais de PD

`src/models/pd/term_structure.py` transforma uma PD acumulada no horizonte de
até 12 meses em uma curva mensal limitada à maturidade real do contrato. A API
não usa a aproximação legada de cinco anos fixos.

## Relações matemáticas

Para pesos temporais positivos `w_t`, a intensidade acumulada é
`H = -ln(1 - PD_horizonte)`. A intensidade de cada mês é proporcional a `w_t`
e normalizada sobre `min(12, prazo_remanescente)`. O hazard condicional mensal é:

```text
h_t = 1 - exp(-H * w_t / soma_pesos_horizonte)
```

A curva aplica, em ordem:

```text
PD_marginal_t = sobrevivencia_(t-1) * h_t
sobrevivencia_t = sobrevivencia_(t-1) * (1 - h_t)
PD_acumulada_t = 1 - sobrevivencia_t
```

Isso reconcilia a PD de entrada no horizonte de calibração, mantém a soma das
PDs marginais igual à PD acumulada e garante hazards, sobrevivência e PDs entre
zero e um. Sobrevivência é não crescente e PD acumulada é não decrescente.

## Prazo e forma temporal

O número de pontos é calculado entre `observation_date` e `maturity_date`, com
arredondamento para cima quando existe fração de mês. Contratos com menos de 12
meses calibram a PD até a própria maturidade; contratos longos produzem lifetime
PD além do primeiro ano.

Sem multiplicadores, a intensidade mensal é plana. Multiplicadores explícitos
permitem uma curva crescente, decrescente ou não monotônica de hazard, sem
quebrar a reconciliação da PD acumulada. Eles são interface técnica para os
cenários forward-looking da Fase 9, não parâmetros calibrados nesta tarefa.

## Limites de uso

A entrada continua dependente de um modelo de PD aprovado. Como a calibração
sintética da Tarefa 5.4 falhou no OOT, a estrutura retorna status
`synthetic_unapproved_input`. A coerência matemática da curva não valida o nível
de risco, a forma temporal nem qualquer uso institucional.

Oito casos de teste cobrem reconciliação, prazo curto/longo, curva não plana,
monotonicidade, limites, calendário e falha fechada para entradas inválidas.
