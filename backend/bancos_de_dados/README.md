# Banco de Dados legado — referência de transição

> Esquemas MySQL históricos preservados para regressão. A persistência canônica
> está em `src/infrastructure/database`, com migrations SQLite/PostgreSQL. Estes
> DDLs não são usados pela jornada E2E e não comprovam aderência regulatória.

Este diretório contém scripts DDL MySQL históricos inspirados no protótipo de
Perda Esperada (ECL) e em conceitos associados à Resolução CMN 4.966/2021.

## Estrutura de Esquemas

```
bancos_de_dados/
├── esquema_completo.sql     # Script completo para deploy
├── ecl/                     # Esquema de cálculos ECL
├── estagio/                 # Esquema de estágios IFRS 9
├── writeoff/                # Esquema de baixas e recuperações
└── auditoria/               # Esquema de logs regulatórios
```

## Esquemas e Tabelas

| Esquema | Tabela | Descrição |
|---------|--------|-----------|
| `ecl` | `ecl_resultados` | Resultados de cálculo ECL por operação |
| `ecl` | `ecl_cenarios` | Cenários macroeconômicos Forward Looking |
| `ecl` | `ecl_parametros_fl` | Parâmetros K_PD_FL e K_LGD_FL |
| `ecl` | `ecl_grupos_homogeneos` | Configuração de grupos de risco |
| `estagio` | `estagio_historico` | Histórico de migrações de estágio |
| `estagio` | `estagio_cura` | Contratos em período de cura |
| `estagio` | `estagio_triggers` | Eventos de trigger registrados |
| `writeoff` | `writeoff_baixas` | Registro de baixas contábeis |
| `writeoff` | `writeoff_recuperacoes` | Recuperações pós-baixa (5 anos) |
| `auditoria` | `auditoria_envios_bacen` | Log de envios XML Doc3040 |
| `auditoria` | `auditoria_validacoes` | Validações realizadas |

## Como Usar

### Deploy Completo
```sql
SOURCE esquema_completo.sql;
```

### Deploy por Esquema
```sql
SOURCE ecl/ecl_resultados/create_table.sql;
SOURCE ecl/ecl_resultados/ddl_insert.sql;
-- ... repetir para cada tabela
```

## Compatibilidade

- **Banco:** MySQL 8.0+
- **Charset:** utf8mb4
- **Collation:** utf8mb4_unicode_ci

## Referências regulatórias históricas

Os nomes de tabelas mencionam CMN 4.966, BCB 352 e Documento 3040, mas não existe
matriz de rastreabilidade deste schema legado nem validação de leiaute que permita
afirmar atendimento. Use `docs/regulatory/TRACEABILITY_MATRIX.csv` e o pacote
canônico em `evidence/regulatory/` para o escopo efetivamente evidenciado.
