# Desempenho e processamento em lote

## Escopo da evidência

O benchmark da Tarefa 15.4 mede capacidade demonstrativa do cálculo agregado de
ECL Stage 1 com dados integralmente sintéticos. Cada execução gera identificadores
de contrato únicos a partir de 64 perfis determinísticos de risco. O resultado
prova que o mecanismo particionado processa o volume-alvo declarado; não representa
SLA, dimensionamento produtivo, carteira institucional nem desempenho com um milhão
de perfis quantitativos distintos.

O alvo versionado em `config/performance/targets.json` exige que um milhão de
contratos seja processado em até 120 segundos e que as alocações Python medidas por
`tracemalloc` permaneçam abaixo de 512 MiB. Memória nativa de bibliotecas, sistema
operacional e banco de dados não estão incluídos nessa medição.

## Execução reproduzível

No PowerShell, a partir da raiz e com o ambiente virtual do projeto:

```powershell
.\venv\Scripts\python.exe scripts\performance_benchmark.py
.\venv\Scripts\python.exe -m pytest tests\performance -q
```

O primeiro comando executa obrigatoriamente 10 mil, 100 mil e 1 milhão de contratos
e grava `evidence/performance/batch-benchmark.json`. Ele termina com código diferente
de zero se o volume de um milhão exceder qualquer alvo.

## Resultado de referência

Em 15 de julho de 2026, no CPython 3.13.7 sobre Windows 11, a evidência versionada
registrou:

| Contratos | Tempo | Vazão | Pico Python |
| ---: | ---: | ---: | ---: |
| 10.000 | 1,148983 s | 8.703,35/s | 7.656.284 bytes |
| 100.000 | 8,430652 s | 11.861,48/s | 10.106.948 bytes |
| 1.000.000 | 69,049503 s | 14.482,36/s | 10.107.428 bytes |

O maior lote residente teve 10 mil contratos. No volume máximo foram calculados 64
perfis e reutilizados 999.936 resultados sob a mesma versão e os mesmos hashes de
cenários e política macroeconômica.

## Controles técnicos

- O processador consome qualquer iterável em partições limitadas e não retém a
  coleção completa nem uma lista completa de resultados.
- A soma monetária usa vetores NumPy em centavos, verifica o limite de `int64` por
  partição e acumula totais em inteiros Python antes de retornar `Decimal`.
- O cache LRU é limitado, protegido para concorrência e sua chave inclui todos os
  dados do perfil, versão e hash de cenários e da política macroeconômica.
- A API usa fila local limitada por `BATCH_QUEUE_WORKERS` e
  `BATCH_QUEUE_CAPACITY`. Saturação retorna HTTP 503 e código auditável
  `QUEUE_CAPACITY_EXCEEDED`, em vez de aceitar trabalho sem capacidade.
- Jobs que estavam pendentes ou em execução durante reinício são marcados como
  `FAILED/PROCESS_RESTARTED`, permitindo reenvio explícito sem apresentar cálculo
  incompleto como concluído.

## Limitações e evolução

A fila é deliberadamente local ao processo e adequada à demonstração atual, que
executa um único processo da API. Uma implantação com múltiplos workers ou nós deve
substituí-la por um broker persistente e coordenação distribuída antes de alegar
recuperação automática. Threads paralelizam perfis independentes, mas o cálculo
canônico em `Decimal` continua sujeito ao GIL; o ganho principal desta evidência vem
do particionamento, agregação vetorizada e reutilização segura de perfis.
