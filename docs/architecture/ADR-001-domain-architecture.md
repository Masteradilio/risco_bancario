# ADR-001 — Arquitetura do domínio canônico

- Status: aceito
- Data: 14 de julho de 2026
- Decisores: mantenedores do projeto

## Contexto

O repositório possui entidades implícitas em DataFrames, payloads FastAPI e
classes específicas de módulos. Isso duplica conceitos, permite números em
`float`, mistura datas de negócio com timestamps e acopla regras quantitativas
a arquivos, APIs e bancos.

## Decisão

O domínio canônico começa em `src/domain` e é implementado com tipos da
biblioteca padrão. Ele não importa FastAPI, Pydantic, pandas, banco, frontend ou
leitores de arquivo. Adaptadores externos são responsáveis por converter seus
payloads para estes tipos.

Entidades iniciais:

- cliente e contraparte;
- contrato e garantia;
- fluxo de caixa;
- snapshot de risco e estágio;
- cenário macroeconômico;
- componentes e resultado de ECL em `src/ecl/calculation`.

Convenções obrigatórias:

- moeda é `Decimal`, atualmente apenas BRL, quantizada em centavos com
  `ROUND_HALF_EVEN`;
- `float` é recusado nas fronteiras do domínio para evitar conversão binária
  silenciosa;
- percentuais são frações decimais entre zero e um, com oito casas;
- datas-base, vencimentos e datas contratuais usam `date`;
- timestamps de eventos são timezone-aware e normalizados para UTC;
- entidades são imutáveis (`frozen=True`) e validam invariantes na criação;
- resultado ECL registra versões de modelo e configuração, hash da configuração
  e separa ECL econômico, overlay gerencial, piso regulatório e valor reportado.

O domínio não decide nesta ADR quais thresholds, pesos, curvas ou pisos são
corretos. Esses valores serão schemas de configuração versionados na Tarefa 1.3.

## Consequências

### Positivas

- regras podem ser testadas sem infraestrutura;
- dinheiro, percentuais e datas têm semântica única;
- erros aparecem como exceções de domínio explícitas;
- APIs e pipelines passam a depender de contratos estáveis.

### Custos e riscos

- módulos existentes precisarão de adaptadores durante a migração;
- rejeitar `float` exige conversão explícita nos limites com pandas/JSON;
- somente BRL é aceito até existir decisão de produto e política cambial.

## Alternativas rejeitadas

- Reutilizar diretamente os modelos FastAPI: manteria o domínio acoplado à API.
- Manter DataFrames como contrato interno: não expressaria invariantes por
  entidade e continuaria permissivo a schemas divergentes.
- Aceitar `float` e converter com `Decimal(value)`: preservaria o erro binário e
  tornaria o arredondamento dependente da origem do dado.
