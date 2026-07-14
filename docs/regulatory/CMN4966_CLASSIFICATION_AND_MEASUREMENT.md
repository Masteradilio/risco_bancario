# Classificação, SPPI e elegibilidade ao impairment

## Modelo de negócio

`BusinessModelRecord` registra objetivo, vigência, órgão aprovador, data de aprovação e justificativa. A vigência não pode anteceder a aprovação. Os objetivos suportados no perímetro limitado do produto são manter para receber, manter para receber e vender, e outros objetivos.

O cadastro é uma evidência de política; ele não infere o modelo a partir de vendas isoladas nem substitui a avaliação institucional exigida pelo art. 5º da Resolução CMN nº 4.966/2021.

## Avaliação SPPI e classificação

`assess_sppi` verifica principal, valor do dinheiro no tempo, risco de crédito, custos e margem básicos, alavancagem, vínculos não básicos, pré-pagamento e extensão. Cada falha gera razão explícita.

`classify_financial_asset` combina modelo e SPPI:

- manter para receber e SPPI: custo amortizado;
- manter para receber e vender e SPPI: FVOCI;
- demais casos: FVTPL;
- operações de crédito seguem a regra específica do art. 4º, § 1º;
- designação irrevogável a FVTPL exige justificativa documentada para eliminar ou reduzir inconsistência contábil.

A saída indica separadamente a elegibilidade ao impairment. Instrumentos patrimoniais, derivativos e ativos FVTPL nível 1 não excepcionados são excluídos; operações de crédito e títulos privados permanecem identificados conforme o perímetro dos arts. 1º e 4º. O roteamento não executa ECL: apenas autoriza ou bloqueia a integração com o motor.

## Reclassificação

`reclassify_financial_asset` só aceita vigência no primeiro dia do mês seguinte à alteração do modelo e marca o efeito como prospectivo. A saída discrimina resultado, outros resultados abrangentes, eliminação da reserva contra o ativo ou uso do valor justo como novo valor contábil bruto, conforme origem e destino.

Ativos designados irrevogavelmente a FVTPL não podem ser reclassificados. A implementação cobre o efeito necessário à integração com impairment; não constitui subledger nem produz lançamentos contábeis completos.

## Fonte e testes

- [Resolução CMN nº 4.966/2021 consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4966&tipo=Resolu%C3%A7%C3%A3o+CMN), arts. 1º e 4º a 8º;
- [Instrução Normativa BCB nº 560/2024](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=560&tipo=Instru%C3%A7%C3%A3o+Normativa+BCB), art. 3º, para o alcance de ativos FVTPL.

`tests/regulatory/test_cmn4966_classification.py` cobre governança, razões SPPI, três categorias, regra de crédito, designação, elegibilidade e todos os sentidos materiais de reclassificação do escopo.
