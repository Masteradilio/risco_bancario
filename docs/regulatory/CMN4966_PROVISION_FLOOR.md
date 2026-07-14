# Piso local de provisão após a ECL

## Escopo da implementação

A camada `src/regulatory/cmn4966/provision_floor.py` aplica, após o cálculo econômico/contábil da ECL, o piso de perda incorrida do Anexo I da Resolução BCB nº 352/2023. O resultado mantém separados:

- `calculated_ecl`: perda esperada produzida pelo motor contábil;
- `regulatory_floor`: valor contábil bruto multiplicado pelo percentual oficial aplicável;
- `final_provision`: maior valor entre ECL e piso.

Essa separação impede que a tabela regulatória seja usada como PD, LGD ou ECL contábil. Ela também não transforma LGD downturn de capital IRB em LGD contábil.

## Regra e versionamento

A política `config/regulatory/cmn4966_provision_floor/2025.01.1.json` é selecionada pela data-base, registra fonte, localizador, vigência e hash SHA-256. Datas anteriores a 1º de janeiro de 2025 falham sem fallback silencioso.

O piso desta tarefa alcança somente ativos com atraso superior a 90 dias. A faixa é o número de meses-calendário transcorridos desde o mês do inadimplemento; a última faixa, a partir de 21 meses, permanece em 100%. As carteiras C1 a C5 são entrada explícita. O enquadramento automático por modalidade e garantia não foi inferido e será tratado junto ao perímetro e à aplicabilidade na Tarefa 11.2.

## Fontes e limites

- Fonte normativa vigente: [Resolução BCB nº 352/2023, versão consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=352&tipo=Resolu%C3%A7%C3%A3o+BCB), Anexo I.
- Confirmação operacional oficial: [Cosif, procedimentos contábeis aplicáveis](https://www3.bcb.gov.br/aplica/cosif/manual/0902177186c5797a.htm), capítulo 4, itens 1 a 3 e 13 a 15.
- Contexto oficial: [Relatório de Política Monetária de setembro de 2025](https://www.bcb.gov.br/content/ri/relatorioinflacao/202509/rpm202509p.pdf), seção sobre pisos de provisão.

A presença da regra no software não conclui que uma instituição específica esteja no âmbito da Resolução BCB nº 352. A aplicabilidade institucional exige avaliação documentada. O Anexo II e a provisão adicional da metodologia simplificada estão deliberadamente fora desta entrega e pertencem à Tarefa 11.2.

## Evidência de teste

`tests/regulatory/test_cmn4966_ecl.py` cobre seleção por data-base, hashes, extremos e faixas da tabela, separação ECL/piso/provisão final, ausência de piso antes do inadimplemento e falhas temporais ou monetárias.
