# Definição formal de default, cura e target

A política executável está em `config/default_policy/2026.07.1.json` e o código
em `src/models/pd/default_definition.py`. Ela é demonstrativa e requer validação
institucional antes de uso real.

## Fontes e hierarquia

- [IFRS 9 B5.5.37](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/): a definição deve ser consistente com a gestão interna, considerar indicadores qualitativos e ser aplicada consistentemente; existe presunção refutável de que default não ocorre depois de 90 dias de atraso.
- [Resolução CMN 4.966/2021 consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4966&tipo=Resolu%C3%A7%C3%A3o+CMN): caracteriza ativo com problema de recuperação, disciplina arrasto de contraparte e critérios de descaracterização.
- [Resolução BCB 352/2023 consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=352&tipo=Resolu%C3%A7%C3%A3o+BCB) e [alteração BCB 504/2025](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=504&tipo=Resolu%C3%A7%C3%A3o+BCB): detalham atraso superior a 90 dias, indicadores qualitativos, cura verificável e exceção para pagamentos com intervalo mínimo de três meses.

O texto integral da IFRS não é reproduzido. A implementação usa síntese própria e
os localizadores registrados na matriz regulatória.

## Evento de default

O backstop CMN/BCB “superior a 90 dias” é operacionalizado em 91 DPD. Default
também pode ocorrer antes por incapacidade financeira, reestruturação por
dificuldade, falência/recuperação, medida judicial restritiva, perda relevante de
liquidez, quebra material de covenant ou venda de dívida com desconto de crédito.

A materialidade demonstrativa é zero: qualquer valor vencido positivo permite o
backstop. Isso é escolha conservadora, não calibração regulatória; uma instituição
deve aprovar e versionar seus próprios critérios sem atrasar o backstop aplicável.

## Populações

- empréstimos PF, imobiliário, veículo, cartão e cheque especial: avaliação no
  instrumento, mantendo possibilidade de arrasto posterior;
- compromissos e garantias financeiras: avaliação de contraparte;
- POCI: população separada, fora do modelo PD 12 meses padrão.

O arrasto de instrumentos da mesma contraparte e sua exceção documentada serão
aplicados no motor de staging da Fase 8; por isso os requisitos regulatórios
permanecem `partial` na matriz.

## Cura e redefault

Cura exige cumulativamente inexistência de vencidos, pagamentos tempestivos,
cumprimento das demais obrigações e evidência de capacidade de pagamento integral
sem recorrer a garantias. Três meses tempestivos são hipótese operacional
versionada, não prazo normativo declarado. Para instrumentos com pagamentos a
cada três meses ou mais, a exceção exige pelo menos 90 dias de evidência de
capacidade. Após cura, novos defaults são identificados como redefault e
monitorados por 12 meses, também como hipótese operacional.

## Target e exclusões

`target_default_12m` vale um quando o primeiro default ocorre em `(t, t+12m]`.
São excluídos POCI, instrumentos já defaultados na observação e linhas sem doze
meses completos de resultado. Modificações permanecem na população com flag
observável; redefaults pertencem à análise pós-cura, não ao primeiro-default PD.

Oito testes cobrem versão/hash, backstop, materialidade, gatilhos qualitativos,
populações, entradas desconhecidas, cura, exceção de baixa frequência e target.
