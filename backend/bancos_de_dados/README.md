# Banco de Dados - Sistema ECL/BACEN 4966

Este diretório contém os scripts DDL de referência para o banco de dados MySQL do sistema de Perda Esperada (ECL) conforme Resolução CMN 4966/2021.

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

## Conformidade Regulatória

Este modelo de dados atende aos requisitos de:
- **CMN 4966/2021** - Perda Esperada IFRS 9
- **BCB 352/2023** - Critérios contábeis
- **Doc3040** - Exportação regulatória BACEN
