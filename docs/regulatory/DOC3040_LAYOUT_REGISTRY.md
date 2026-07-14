# Registry de leiaute do Documento 3040

## Pacote suportado

O registry canônico seleciona o pacote do Documento 3040 pela data-base e falha quando
não existe uma versão observada, íntegra e não ambígua. O primeiro pacote é
`2026.07-observed-20260714`, aplicável de julho a outubro de 2026. Maio e junho não são
retroativamente suportados porque os artefatos disponíveis na consulta de 14 de julho já
haviam sido atualizados; novembro está bloqueado porque a alteração futura `NR3` ainda
não foi incorporada a um pacote testado.

O manifesto fica em
`config/regulatory/doc3040/layouts/2026.07-observed-20260714.json`. Ele registra:

- período de vigência suportado e data de observação;
- atos normativos IN BCB 733/2026 e IN BCB 735/2026;
- URLs oficiais e SHA-256 do leiaute/domínios, instruções, críticas e regras de
  reconciliação Bacen;
- abas que contêm tabelas de domínio;
- marcadores vigentes e o marcador futuro que deve ser filtrado;
- data da última atualização observada da planilha de críticas;
- estado explícito da proveniência XSD e bloqueio de geração.

## Artefatos observados em 14 de julho de 2026

| Artefato | SHA-256 |
|---|---|
| `SCR3040_Leiaute.xls` | `ab3cad54fe481a52b5c4c24c832af3b1c0ef1e0d75cbaa3639611c903ed5c70f` |
| `SCR_InstrucoesDePreenchimento_Doc3040.pdf` | `3a2f9dff406b404b26617ab0dce79b5992cc67ac410ff60047236c73b11daf8b` |
| `SCR3040_Criticas.xls` | `10718c233c5a27f07d49554b716c68c35dfbd92f1df2d0d328be56b1507cda40` |
| `SCR3040_RegrasValidacaoBacen.xls` | `8efd7bbd8ad50fdb0acf7413532235740eefdadbdda56312274154cb491e92e5` |

Os binários oficiais não são redistribuídos pelo repositório. O manifesto permite baixar
uma cópia autorizada da origem e conferir nome e hash antes de qualquer extração. Uma
cópia diferente é rejeitada, mesmo que tenha o mesmo nome.

## Seleção e bloqueios

`layout_for_reference_month()` exige o primeiro dia do mês e exatamente uma versão
aplicável. Não há fallback para a versão “mais recente”, porque isso aplicaria regras
futuras a datas passadas ou regras antigas a datas novas. Faixas sobrepostas e versões
duplicadas também invalidam o registry.

O catálogo de domínios aponta para as abas `Anexo` e
`Anexo 26 - InfosAdicionais` do workbook cujo hash está no manifesto. O catálogo de
críticas referencia tanto `SCR3040_Criticas.xls` quanto as regras de reconciliação. Nesta
tarefa eles estão **versionados, mas ainda não executados**; parsing, compilação e
execução pertencem à Tarefa 12.4.

## Proveniência XSD

Na consulta registrada, a página oficial do Documento 3040 lista um XSD para o
documento **3045**, não para o 3040. O registry não substitui nem renomeia esse arquivo.
O campo `xsd` permanece nulo, `generation_enabled` permanece falso e
`require_official_xsd()` retorna erro com a causa registrada.

O carregador de XSD está implementado para um pacote futuro: exige código de documento
3040, URL oficial, nome e SHA-256 compatíveis. Um XSD 3045 é recusado antes da leitura.
Assim, o requisito `DOC3040-XSD-001` está implementado como controle de proveniência,
mas a validação XSD de um XML 3040 continua indisponível até existir um artefato 3040
identificado e incorporado. O projeto não transforma essa ausência em falsa validação.

## Evidência

`tests/regulatory/test_doc3040_layout_registry.py` cobre seleção por data-base, bloqueio
de meses não suportados, integridade dos catálogos, hash/nome de artefatos e rejeição do
XSD de outro documento. A interface permanece descrita como pré-validador.
