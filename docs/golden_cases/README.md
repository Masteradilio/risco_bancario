# Pacote de golden cases

Este diretório publica oito casos sintéticos com inputs, fórmula, resultado
esperado e tolerância monetária zero:

- `golden_cases.json`: contrato legível por máquina;
- `ecl_golden_cases.xlsx`: verificação independente, com fórmulas visíveis,
  schedule da modificação e aba de checks;
- `tests/fixtures/golden/ecl_cases.csv`: baseline mínimo consumido pelo motor;
- `src/validation/golden_cases.py`: cálculo `Decimal` independente, sem importar
  o motor ECL de produção.

O CI executa tanto os oito testes do motor quanto a comparação independente
JSON/CSV. A planilha foi recalculada, inspecionada sem erros de fórmula e
renderizada integralmente antes da publicação.

Todos os valores são sintéticos e demonstrativos. O pacote prova mecânica e
reprodutibilidade; não constitui validação de modelos ou homologação regulatória.
