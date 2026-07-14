# Reconciliação e ledger imutável de ECL

## Unidade do ledger

Cada linha identifica contrato, cliente, produto, período, cenário, peso e ECL do
período. O valor ponderado é derivado da própria linha. Metadados contratuais devem ser
estáveis e cada contrato precisa cobrir o mesmo conjunto de cenários.

Uma segunda estrutura, única por contrato, preserva:

- ECL econômico;
- management overlay positivo ou negativo;
- piso regulatório;
- ECL final, obrigatoriamente `max(econômico + overlay, piso, zero)`.

## Reconciliação multinível

Antes de criar o ledger, o serviço reconcilia:

- períodos: soma dos ECLs ponderados;
- cenários: ECL integral, peso e contribuição;
- contratos: períodos/cenários contra ECL econômico;
- clientes e produtos: soma dos contratos;
- portfólio: econômico, overlay, piso e final.

No golden case:

| Nível | ECL econômico/ponderado |
|---|---:|
| cenário base: R$ 40 × 70% | R$ 28 |
| cenário pessimista: R$ 70 × 30% | R$ 21 |
| contrato 1 | R$ 13 |
| contrato 2 | R$ 36 |
| portfólio | R$ 49 |

O contrato 1 tem overlay R$ 2, piso R$ 20 e final R$ 20. O contrato 2 tem overlay
-R$ 1, piso zero e final R$ 35. No portfólio: econômico R$ 49, overlays R$ 1, pisos
somados R$ 20 e finais contratuais somados R$ 55. O piso é aplicado por contrato, não
novamente sobre o agregado.

## Imutabilidade e cadeia

`create_ecl_execution_ledger` ordena entradas/ajustes, normaliza timestamps para UTC e
calcula SHA-256 sobre conteúdo, versões, relatório e hash anterior. A ordem de entrada
não muda o hash. `previous_ledger_hash` permite uma cadeia verificável de execuções.

As dataclasses são congeladas. Entradas duplicadas, pesos inconsistentes, cenários
ausentes, metadata divergente, timestamp sem fuso, ajuste sem contrato ou qualquer
diferença de reconciliação impedem a criação do ledger.

## Limitações

O ledger é armazenamento lógico imutável em memória. Persistência transacional,
assinatura, retenção e controle de acesso pertencem às fases de infraestrutura,
segurança e operação. Pisos regulatórios reais serão implementados na Fase 11.
