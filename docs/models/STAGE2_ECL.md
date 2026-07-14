# Cálculo de ECL Stage 2

## Definição implementada

Stage 2 calcula ECL lifetime por toda a vida comportamental remanescente. Cada mês
possui hazard, LGD lifetime, EAD programada, valor não sacado, CCF e prepagamento
esperado. O motor mantém sobrevivência de crédito separada da permanência comportamental.

O saldo do mês usa a sobrevivência a prepagamentos dos meses anteriores. Após o prazo
contratual, a exposição é multiplicada pela probabilidade explícita de extensão. Assim,
extensões não são tratadas como certas nem ignoradas.

## Individual e coletivo

O modo `individual` exige identificação do contrato e proíbe ID de grupo. O modo
`collective` exige `homogeneous_group_id`. A fórmula quantitativa é a mesma; a distinção
preserva a trilha de mensuração. A validação estatística de grupos homogêneos pertence à
Tarefa 10.5.

## Caso demonstrativo

Contrato de 18 meses, hazard 0,8% a.m., LGD 45%, saldo programado decrescente, R$ 300
não sacados, CCF 50% e EIR original 12%:

| Cenário | ECL lifetime |
|---|---:|
| otimista | R$ 62,98 |
| base | R$ 71,49 |
| pessimista | R$ 96,71 |
| stress | R$ 188,82 |

ECL ponderado: R$ 74,00. Com prepagamento esperado de 3% a.m., o ECL cai para
R$ 60,39.

Para um prazo contratual de 12 meses, o ECL é R$ 57,14. Ao adicionar seis meses de
extensão com probabilidade de 50%, o horizonte comportamental vai a 18 meses e o ECL
sobe para R$ 65,57.

## Controles e limitações

- todos os meses do prazo contratual e da extensão devem estar presentes;
- probabilidade de extensão exige meses de extensão;
- o horizonte não pode exceder a trajetória macro disponível;
- prepagamento e extensão afetam EAD, não a definição de default;
- descontos usam a EIR original por período;
- resultados permanecem por cenário, com stress separado.

Os parâmetros são sintéticos e não aprovados. A mensuração coletiva aqui identifica o
modo e o grupo; critérios estatísticos e validação de homogeneidade ainda não foram
implementados.
