# Pacote sintético de disclosure de risco de crédito

## Conteúdo e reconciliação

`generate_synthetic_disclosure_package` recebe exposições de abertura e fechamento, movimentos assinados, transferências, relatório de sensibilidade e overlays governados. O pacote contém:

- ponte de allowance por estágio, com diferença obrigatoriamente zero;
- totais de originação, remensuração, transferência, desreconhecimento, write-off e outros;
- transferências entre estágios com origem e destino;
- exposição bruta e allowance por rating e segmento;
- ECL base, stress, sensibilidades e deltas;
- overlays, justificativa, versão e estado ativo;
- hash SHA-256 determinístico do pacote.

Contratos, movimentos e overlays duplicados são rejeitados. Uma ponte que não reconcilia falha sem gerar disclosure.

## Fronteiras de regime

O manifesto `RegimeBoundary` acompanha o pacote e explicita:

- ECL contábil IFRS 9 e regras locais aplicáveis da CMN 4.966/BCB 352;
- piso mínimo da BCB 352 como camada separada da ECL;
- capital IRB fora do escopo;
- LGD downturn regulatória não aceita diretamente como LGD contábil.

Essa distinção impede que uma tabela de capital ou um parâmetro downturn seja apresentado como mensuração contábil. Os modelos quantitativos continuam sintéticos ou não aprovados conforme seus model cards.

## Fonte e limite de uso

- [Resolução CMN nº 4.966/2021 consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=4966&tipo=Resolu%C3%A7%C3%A3o+CMN), arts. 65 e 66;
- [Resolução BCB nº 352/2023 consolidada](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=352&tipo=Resolu%C3%A7%C3%A3o+BCB), requisitos de evidenciação aplicáveis ao respectivo perímetro.

O artefato é identificado como `synthetic_demonstrative_not_financial_statements`: ele demonstra dados e controles para futura adaptação, mas não constitui notas explicativas, demonstrações financeiras nem publicação regulatória de uma instituição real.

`tests/regulatory/test_cmn4966_disclosures.py` cobre reconciliação, transferências, agregações, sensitividades, overlays, fronteiras e falhas fechadas.
