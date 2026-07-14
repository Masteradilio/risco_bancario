# Catálogo de fontes oficiais

## Regras de uso

Este catálogo aponta para fontes primárias e registra o estado observado em 14
de julho de 2026. Links e datas não substituem análise jurídica, contábil ou a
publicação oficial. Antes de implementar ou liberar uma regra, deve-se consultar
novamente a fonte, registrar a versão e avaliar alterações, vigências por
dispositivo, público alcançado e normas vinculadas.

Não se mantém neste repositório cópia integral de conteúdo protegido da IFRS
Foundation. Metadados, referências curtas e interpretação própria podem ser
registrados; o texto licenciado deve ser acessado pelos canais autorizados.

## Registro

| ID | Fonte primária | Emissor | Estado e vigência observados | Consulta | Uso no projeto |
|---|---|---|---|---|---|
| `SRC-IFRS9` | [IFRS 9 Financial Instruments](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/) | IASB / IFRS Foundation | Página “Standard 2026 Issued”; norma efetiva para períodos anuais iniciados em ou após 1/1/2018. A página registra emendas posteriores, inclusive de 2024. | 2026-07-14 | Referência internacional para impairment/ECL; texto normativo completo sujeito a licença. |
| `SRC-CMN4966` | [Resolução CMN nº 4.966/2021 — versão consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4966&tipo=Resolu%C3%A7%C3%A3o+CMN) | CMN / BCB | Página marcada como versão vigente, atualizada em 29/8/2025. Publicada em 25/11/2021; vigências e transições devem ser avaliadas por dispositivo e norma alteradora. | 2026-07-14 | Fonte brasileira principal para instituições no âmbito do art. 1º; usar texto consolidado e normas vinculadas. |
| `SRC-BCB352` | [Resolução BCB nº 352/2023 — versão consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=352&tipo=Resolu%C3%A7%C3%A3o+BCB) | BCB | Resolução de 23/11/2023 apresentada pelo catálogo oficial como vigente. O Anexo I e o [Cosif, capítulo 4](https://www3.bcb.gov.br/aplica/cosif/manual/0902177186c5797a.htm), confirmam os pisos de perda incorrida por carteira e mês desde o inadimplemento. A revisão da definição de default/cura considerou também a [Resolução BCB nº 504/2025](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=504&tipo=Resolu%C3%A7%C3%A3o+BCB), vigente desde 1/10/2025. Abrangência e vigência variam por instituição/dispositivo. | 2026-07-14 | Critérios para entidades alcançadas pela regulamentação BCB; não tratar como intercambiável com a CMN 4.966 sem análise de escopo. |
| `SRC-DOC3040` | [Documento 3040 e Documento 3026](https://www.bcb.gov.br/estabilidadefinanceira/scrdoc3040) | BCB / SCR | Página operacional vigente na consulta. Itens marcados “NR” incluem leiaute e instruções do 3040, validador release 13708 e planilha de críticas. A página lista XSD do documento 3045, não um XSD 3040. | 2026-07-14 | Leiaute, preenchimento, críticas, validador, envio, particionamento e exemplos do SCR. Cada artefato deve ter versão/hash próprios. |
| `SRC-IN560` | [Instrução Normativa BCB nº 560/2024](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=560&tipo=Instru%C3%A7%C3%A3o+Normativa+BCB) | BCB | Versão vigente observada, atualizada em 2/9/2025; esclarece critérios de aplicação da CMN 4.966 e BCB 352. | 2026-07-14 | Fonte complementar; não substitui as resoluções. |
| `SRC-IN464` | [Instrução Normativa BCB nº 464/2024](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=464&tipo=Instru%C3%A7%C3%A3o+Normativa+BCB) | BCB | Documento revogado pela Instrução Normativa BCB nº 560/2024; preservado apenas para histórico, não para regra vigente. | 2026-07-14 | Fonte histórica da metodologia completa; a implementação vigente deve usar `SRC-IN560`. |

## Processo de atualização regulatória

1. Revisar este catálogo mensalmente e antes de release que altere cálculo,
   contabilização, disclosure ou reporte.
2. Abrir cada URL oficial e comparar cabeçalho de versão, atualizações, normas
   vinculadas, revogações e vigências futuras.
3. Para arquivos operacionais, baixar de fonte oficial, registrar nome, data,
   tamanho, SHA-256, release e data-base aplicável em manifesto próprio. Não
   substituir silenciosamente artefato já usado.
4. Criar issue/change record para toda mudança; classificar impacto em escopo,
   dados, regra, teste, documentação, migração e reprocessamento.
5. Atualizar a matriz de rastreabilidade e os testes pelo identificador da fonte.
6. Exigir revisão técnica e aprovação definida pela governança antes de promover
   configuração ou código. A ausência de mudança também deve gerar registro da
   data da revisão.
7. Preservar apenas conteúdo cuja licença permita redistribuição. Para material
   restrito, guardar referência, checksum de cópia autorizada fora do Git e
   evidência de acesso, nunca o texto integral no repositório público.

## Pendências controladas

- A Tarefa 2.2 deve decompor fontes em requisitos atômicos e aplicabilidade.
- Artefatos Doc3040 ainda precisam de manifesto de versões e hashes quando forem
  incorporados à implementação; a mera URL desta página não fixa um leiaute.
- Nenhuma fonte deste catálogo, isoladamente, valida os parâmetros demonstrativos
  da política `2026.07.1`.
