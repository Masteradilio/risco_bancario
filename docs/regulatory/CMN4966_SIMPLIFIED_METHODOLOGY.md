# Metodologia simplificada de provisão

## Aplicabilidade explícita

O roteador `resolve_methodology` exige que o chamador informe o regime (`CMN4966` ou `BCB352`), o segmento prudencial e, quando aplicável, os fatos de autorização ou sistema cooperativo. Conforme o art. 50 da Resolução CMN nº 4.966/2021:

- S1, S2 e S3 seguem a metodologia completa;
- S4 e S5 seguem, como regra, a metodologia simplificada;
- S4 somente usa a completa com autorização prévia do BCB;
- cooperativas dos sistemas descritos no art. 50, § 5º, seguem a exceção à metodologia simplificada.

O software não deduz segmento, autorização nem composição de sistema cooperativo. Combinações incoerentes falham de forma fechada.

## Estratégia separada

`calculate_simplified_provision` rejeita uma decisão de aplicabilidade que indique metodologia completa. A saída preserva componentes distintos:

- estimativa de perda esperada produzida pela avaliação simplificada;
- piso de perda incorrida do Anexo I;
- provisão adicional do Anexo II ou percentuais aplicáveis a ativos problemáticos;
- mínimo regulatório, excesso da perda estimada e provisão final.

Para ativos não problemáticos são usadas as quatro faixas de atraso do Anexo II. Ativos problemáticos não inadimplidos e ativos inadimplidos usam percentuais adicionais próprios. Piso de perda incorrida e adicional são somados, limitados a 100% do valor contábil bruto; quando a perda esperada estimada for maior, o excesso permanece provisionado.

A entrada `estimated_expected_loss` não é produzida pelo motor PD/LGD/EAD da metodologia completa. Ela representa a avaliação simplificada baseada nos fatores do art. 51 e, quando houver mensuração por fluxos recuperáveis, deve respeitar a taxa efetiva conforme a Instrução Normativa BCB nº 560/2024.

## Fontes e evidência

- [Resolução CMN nº 4.966/2021 consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4966&tipo=Resolu%C3%A7%C3%A3o+CMN), arts. 50 e 51;
- [Resolução BCB nº 352/2023 consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=352&tipo=Resolu%C3%A7%C3%A3o+BCB), Anexos I e II;
- [Cosif, capítulo 4](https://www3.bcb.gov.br/aplica/cosif/manual/0902177186c5797a.htm), itens 5 a 12;
- [Instrução Normativa BCB nº 560/2024](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=560&tipo=Instru%C3%A7%C3%A3o+Normativa+BCB).

Os casos sintéticos em `tests/regulatory/test_cmn4966_simplified.py` cobrem aplicabilidade, exceções, todas as taxas, composição, teto e bloqueio de mistura entre metodologias. A implementação não conclui aplicabilidade para instituição real sem evidência de enquadramento.
