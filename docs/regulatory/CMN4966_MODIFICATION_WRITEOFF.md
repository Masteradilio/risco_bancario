# Modificação, desreconhecimento e baixa

## Decisão de modificação

`assess_modification` registra fatos verificáveis que alteram direitos contratuais ou tornam os termos substancialmente diferentes: expiração, novação, troca de contraparte, moeda, tipo de instrumento ou resultado SPPI. A decisão expõe todas as razões; não usa um percentual arbitrário como substituto do julgamento para ativos financeiros.

`account_for_modification` integra essa decisão ao motor contratual existente:

- sem desreconhecimento, os fluxos revisados são descontados pela EIR original e o ganho ou perda de modificação é reconhecido;
- com desreconhecimento, o ativo anterior é baixado, o substituto parte do valor justo e recebe nova EIR;
- valor justo de substituição é proibido na rota sem baixa e obrigatório na rota com baixa.

## Ledger de write-off

O `WriteOffLedger` mantém valor contábil bruto, allowance, baixas, recuperações e eventos em ordem cronológica. Toda baixa exige evidência identificável de que a recuperação não é provável.

Baixas parciais e totais reduzem separadamente o valor bruto e a allowance. Se a allowance for insuficiente, a diferença é explicitada como perda direta no resultado, sem saldo implícito. Recuperações pós-baixa são reconhecidas como receita e não reinstalam silenciosamente o ativo; o total recuperado não pode superar a baixa ainda não recuperada.

As projeções de write-off e recuperação usadas para mensurar Stage 3 continuam em `src/ecl/stage3/cash_shortfall.py`. O ledger desta entrega registra eventos contábeis realizados e, portanto, não substitui nem duplica a projeção de ECL.

## Fontes e limites

- [Resolução CMN nº 4.966/2021 consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4966&tipo=Resolu%C3%A7%C3%A3o+CMN), arts. 22 a 35 e art. 49;
- [Instrução Normativa BCB nº 560/2024](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=560&tipo=Instru%C3%A7%C3%A3o+Normativa+BCB), esclarecimentos vigentes relacionados.

O módulo não é um subledger completo e não toma decisão jurídica de transferência de riscos e benefícios. Os testes sintéticos em `tests/regulatory/test_cmn4966_writeoff.py` demonstram as duas rotas de modificação, baixa parcial/total, insuficiência de allowance, recuperação e falhas fechadas.
