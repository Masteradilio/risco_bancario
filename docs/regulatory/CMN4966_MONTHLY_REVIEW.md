# Evidência de revisão mensal

`create_monthly_review_manifest` registra, por contrato e data-base, estágio e allowance anteriores e atuais, motivo da revisão, variação, horário de conclusão e hash SHA-256.

O controle exige meses-calendário consecutivos, contratos únicos, uma única data-base e conclusão não anterior à referência. Assim, uma execução isolada não pode ser apresentada como cumprimento recorrente: cada mês precisa de seu próprio manifesto encadeável pelo processo operacional futuro.

Fonte: [Resolução CMN nº 4.966/2021 consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4966&tipo=Resolu%C3%A7%C3%A3o+CMN), art. 48, e requisitos correspondentes da [Resolução BCB nº 352/2023](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=352&tipo=Resolu%C3%A7%C3%A3o+BCB).

`tests/regulatory/test_monthly_review.py` cobre totais, mudança de estágio, hash, mês omitido, duplicidade e conclusão temporal inválida.
