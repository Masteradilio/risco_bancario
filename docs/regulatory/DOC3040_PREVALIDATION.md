# Pré-validação local do Documento 3040

## Resultado possível

O serviço `prevalidate_xml()` retorna `PREVALIDATED_DERIVED_XSD` somente quando não há
erro ou bloqueio nas camadas locais. Esse status significa **pré-validação local do
perímetro sintético suportado**. Ele não significa aceitação pelo BCB, execução do
aplicativo validador, conformidade institucional ou autorização de transmissão.

Dois campos do relatório permanecem falsos por desenho:

- `official_xsd_executed`, porque a página oficial consultada lista XSD 3045, não 3040;
- `official_critics_executed`, porque a planilha completa de críticas está versionada,
  mas esta entrega executa um subconjunto semântico local.

Essas limitações também aparecem como warnings rastreáveis no relatório aprovado.

## Camadas executadas

### XSD estrutural derivado

`config/regulatory/doc3040/schemas/doc3040-2026.07-derived.xsd` foi construído a partir
do leiaute oficial cujo hash está no manifesto. O schema verifica estrutura, ordem dos
blocos do perímetro, atributos obrigatórios, datas, inteiros e escalas numéricas. Seu
hash também é conferido antes do uso.

O arquivo contém comentário explícito de que não é XSD oficial. O controle de
proveniência oficial continua separado e continua rejeitando o XSD 3045.

### Domínios

`config/regulatory/doc3040/domains/2026.07-supported-subset.json` é uma allowlist
versionada do perímetro sintético. Ela está vinculada ao SHA-256 do workbook oficial e
inclui os domínios necessários aos casos suportados. Modalidades, origens, garantias e
informações adicionais fora do subconjunto são rejeitadas, mesmo que possam existir no
leiaute amplo. Isso é uma restrição conservadora, não uma declaração de inexistência.

### Críticas semânticas locais

O subconjunto executado verifica, entre outros pontos:

- unicidade e composição corrente do IPOC;
- unicidade de contrato por cliente/modalidade;
- `TotalCli` no perímetro individualizado;
- limites de ECL em relação ao valor contábil bruto;
- reconciliação de vencimentos com valor bruto no produto sintético suportado;
- ausência de controles de carteira/ECL e controles órfãos.

As regras usam IDs `LOCAL-*` justamente para não se passarem por códigos executados do
validador BCB. A planilha `SCR3040_Criticas.xls` e as regras de reconciliação continuam
identificadas por hash no registry para a etapa de ampliação de cobertura.

### Carteira e ECL

Cada operação XML exige `PortfolioEclControl` com IPOC, valor contábil bruto, ECL e
identificador da evidência. `VlrContBr` e `VlrPerdaAcum` devem reconciliar exatamente. A
ausência do controle é blocker; controles sem operação XML também são erro.

## Relatório de erros

Cada `ValidationIssue` contém:

- `rule_id`;
- severidade `warning`, `error` ou `blocker`;
- mensagem;
- linha do XML quando disponível;
- campo/atributo;
- XPath do elemento.

XML malformado, data-base sem registry, conjunto de domínios incompatível e hash de XSD
divergente falham antes das críticas de negócio. O parser desabilita rede e resolução de
entidades externas.

## Evidência

`tests/regulatory/test_doc3040_validation.py` cobre aprovação local com limitações
explícitas, erro XSD por linha, domínio, total de clientes, carteira/ECL, vencimentos,
limite da perda, controle ausente/órfão e XML malformado.
