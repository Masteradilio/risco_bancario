# LGD realizada descontada

`src/models/lgd/realized.py` calcula a LGD workout por default a partir do dataset
point-in-time da Tarefa 7.1. O cálculo preserva a EAD registrada no evento de default,
os fluxos individuais, a política aplicada e seu hash SHA-256.

## Metodologia

Para cada recuperação ou custo na data `t`, o valor presente é calculado por dias
corridos, base 365, usando a taxa efetiva contratual do instrumento:

`VP_t = fluxo_t / (1 + EIR) ^ (dias desde o default / 365)`

A recuperação líquida descontada é a soma das recuperações brutas descontadas,
menos os custos descontados, mais o valor de cura quando aplicável. A LGD bruta é:

`LGD bruta = 1 - recuperações líquidas descontadas / EAD no default`

O cálculo usa `Decimal`, precisão interna de 28 dígitos e arredondamento
`ROUND_HALF_EVEN` para oito casas decimais. EAD não positiva, taxa menor ou igual a
-100% e fluxo anterior ao default falham de forma fechada.

## Cura e perda

Em um workout curado, a parcela nominal ainda exposta após as recuperações brutas é
tratada como valor restaurado na data da cura e então descontada. Isso evita contar
duas vezes as recuperações já observadas. O resultado recebe o tipo `cure_lgd`; os
demais recebem `loss_lgd`.

Essa é uma convenção demonstrativa para o gerador sintético. Não afirma que o saldo
curado equivale a caixa recebido nem substitui a validação institucional do tratamento
de curas, redefaults e fluxos posteriores.

## Limites e censura

A política `config/lgd_policy/2026.07.1.json` é versionada como
`demonstrative_unvalidated`. Ela preserva a LGD bruta para auditoria e fornece uma
LGD limitada ao intervalo de 0% a 100% para modelagem. Valores negativos são
limitados a zero; valores acima de 100% são limitados a um; `bound_action` registra a
ação. Nenhum valor bruto é descartado ou sobrescrito.

Workouts cuja janela de 24 meses ainda não terminou recebem
`censored_provisional`. Eles podem ser calculados para rastreabilidade, mas não devem
ser tratados como desfechos fechados na calibração ou validação.

## Evidência de aceite

Com seed 91 e cutoff em 1º de dezembro de 2025, foram calculados 32 defaults: 25
completos e 7 censurados. Há 10 resultados de cura e 22 de perda no total. Entre os
workouts completos, a LGD média limitada foi 52,2805414%; a média de cura foi
17,3693342% e a média de perda foi 71,9180954%. A faixa bruta foi de 9,571705% a
100%, sem aplicação de limites nessa carteira específica.

Esses números são exclusivamente sintéticos e servem para regressão da metodologia.
Sete testes manuais cobrem EAD, desconto, custos, cura, limites, censura e linhagem da
política; o dataset-base possui seis testes adicionais.
