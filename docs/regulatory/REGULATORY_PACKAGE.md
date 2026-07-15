# Pacote regulatório exportável

O comando abaixo gera um snapshot determinístico das evidências regulatórias:

```powershell
.\venv\Scripts\python.exe scripts/export_regulatory_package.py
```

O diretório `evidence/regulatory/` contém a matriz integral, relatório de
cobertura, contagem de testes por requisito, limitações e itens não aplicáveis,
fontes consultadas, versões de leiaute e manifesto SHA-256.

O snapshot registra 27 requisitos, dois itens não aplicáveis e seis bloqueadores
de release. Esses bloqueadores correspondem a requisitos parciais ou planejados
e impedem qualquer alegação de certificação integral. O pacote descreve o estado
técnico demonstrativo; não substitui análise jurídica, validação independente,
XSD/críticas oficiais do BCB ou homologação institucional.
