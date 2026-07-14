# Materialização da fábrica sintética

O pacote de aceitação versionado está em
`data/synthetic/acceptance-v0.1.0`. Ele contém os Parquets exigidos pelo
estado-alvo e `manifest.json` com seed, parâmetros, versões dos componentes,
hash da política macroeconômica, schemas, contagens e SHA-256 de cada arquivo.

## Reprodução

No diretório raiz, com o `venv` do projeto:

```powershell
.\scripts\generate-synthetic-data.ps1
```

O padrão usa `seed=91`, 40 clientes e dois contratos por cliente. Outro diretório
ou tamanho pode ser informado pelos parâmetros `-Output`, `-Seed`, `-Clients` e
`-ContractsPerClient`.

O exportador ordena tabelas e campos a partir das estruturas canônicas, grava
Parquet 2.6 com Zstandard e não inclui timestamps de execução no manifesto.
Testes materializam duas cópias em diretórios diferentes e exigem igualdade byte
a byte de todos os Parquets e do manifesto.

## Tabelas derivadas

`payments`, `delinquencies` e `limits_and_drawdowns` são projeções dos snapshots,
não implementações paralelas. Suas contagens devem reconciliar com
`monthly_snapshots`; `monthly_drawdown` é somente o aumento positivo de saldo
contra o snapshot anterior do mesmo contrato.

`regulatory_reporting_input` consolida o último snapshot com contrato e
contraparte. Seus nomes são neutros e representam apenas proveniência de origem.
O arquivo não é Documento 3040, não contém campos de leiaute presumidos e não
pode ser transmitido. Mapeamento, XSD, domínios e críticas pertencem à Fase 12.

## Conteúdo

Além das 16 tabelas obrigatórias de entidades, histórico, eventos, macro e
modelagem, o pacote preserva grupos, contrapartes, cronogramas, modificações,
cobranças, curas, histórico macro observado e pesos de cenários. O manifesto é a
fonte de verdade para a lista completa, schema e contagem de linhas.
