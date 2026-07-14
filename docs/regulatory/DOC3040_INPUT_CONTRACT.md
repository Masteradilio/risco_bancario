# Contrato de entrada do Documento 3040

## Estado e limite da entrega

Este documento descreve o contrato canônico de entrada do **pré-validador** sintético do
Documento 3040. A implementação não transmite arquivos, não substitui o aplicativo
validador do Banco Central do Brasil (BCB), não representa homologação institucional e
não aceita um valor apenas porque ele possui o tamanho correto.

A fonte operacional consultada em 14 de julho de 2026 foi a página oficial
[Documento 3040 e Documento 3026](https://www.bcb.gov.br/estabilidadefinanceira/scrdoc3040),
incluindo o leiaute e as instruções marcados como NR. A
[Instrução Normativa BCB 733/2026](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=733&tipo=Instru%C3%A7%C3%A3o+Normativa+BCB)
estabelece alterações com vigência nas datas-base de maio, julho e novembro de 2026.
Por isso, a validade de domínios e blocos depende da data-base e será resolvida pelo
registry da Tarefa 12.2.

## Contrato fail-closed

O módulo `src/regulatory/doc3040/contract.py` representa:

- cabeçalho `Doc3040`;
- clientes e operações individualizadas;
- vencimentos;
- garantias;
- informações adicionais e Sicor;
- contabilização conforme CMN 4.966, motivos de estágio e perdas reconhecidas;
- grupos de IPOCs conectados;
- informações agregadas.

Cada escalar presente usa `SourcedValue`, composto pelo valor e por `SourceRef` com
sistema, campo de origem e identificador da evidência. Uma origem vazia é erro. Campos
opcionais e condicionais também não têm valor implícito: o chamador precisa fornecer um
valor com origem ou `None` de forma consciente.

`FIELD_CATALOG` registra, para cada escalar, elemento/atributo XML, formato oficial,
obrigatoriedade, anexo de domínio e condição aplicável. O catálogo inclui 90 ou mais
campos e possui teste de cobertura contra os modelos do contrato. Os conteúdos dos
anexos não ficam hard-coded nesta camada; isso impediria selecionar corretamente a
versão aplicável à data-base.

## Campos que não podem ser inventados

Não existem defaults para `PorteCli`, `Cosif`, `CEP`, `DtContr`, `DtVencOp`, modalidade,
natureza, origem de recursos, indexador, variação cambial, metodologia, estágio, carteira
de provisão, motivos de estágio ou de perda. Em particular:

- `postal_code`, `cosif_accounts` e `contract_date` são argumentos obrigatórios;
- `maturity_date=None` significa vencimento indeterminado, conforme o leiaute, e nunca
  vira uma data artificial;
- porte PF/PJ deve vir da fonte declarada;
- metodologia completa/simplificada não é inferida;
- FIDC/SEP usa `fund_type` de forma exclusiva aos atributos de metodologia;
- o contrato não gera IPOC: recebe o identificador com origem e a regra oficial será
  aplicada e verificada na Tarefa 12.3;
- perdas reconhecidas são valores-fonte; nenhuma fração de ECL é calculada pelo contrato.

## Invariantes já aplicadas

Além de tipo e formato estrutural, a entrada rejeita:

- CNPJ da entidade sem oito dígitos, CEP sem oito dígitos e metadados de origem vazios;
- parte/remessa não positivas, valores monetários negativos e percentuais de garantia
  acima de 100%;
- cliente PJ sem tipo de controle ou operação PJ sem detalhamento do cliente;
- identificação de cliente estrangeiro e dados de bônus Sicor parcialmente preenchidos;
- data de vencimento anterior à contratação e relacionamento iniciado na ou após a
  data-base;
- vértice de vencimento duplicado e vértice vencido entre 205 e 330 sem dias de atraso;
- data/valor de próxima parcela preenchidos parcialmente;
- clientes ou IPOCs duplicados, conexão para IPOC inexistente e total de clientes sem
  reconciliação.

## Mapeamento de origem

`iter_sourced_values()` produz caminhos estáveis como
`clients[0].operations[0].postal_code` associados à origem e à evidência. Esses caminhos
serão preservados nos relatórios de erro da Tarefa 12.4. A fábrica sintética pode ser uma
origem válida para demonstração, mas deve continuar identificada como sintética; uma
integração institucional deverá trocar os `SourceRef` pelas tabelas/campos reais e suas
evidências de reconciliação.

## Evidência de teste

`tests/regulatory/test_doc3040_input_contract.py` cobre o requisito
`DOC3040-LAYOUT-001`, inclusive a proibição de defaults silenciosos. O aceite desta tarefa
não afirma que XML, domínios, XSD ou críticas oficiais já foram validados; essas
evidências pertencem às Tarefas 12.2 a 12.5.
