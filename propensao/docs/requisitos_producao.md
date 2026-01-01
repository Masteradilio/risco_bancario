# Requisitos para Produção - Sistema PROLIMITE

## Campos para Agendamento de Execução

### Lógica de Execução

| Cenário | Frequência | Descrição |
|---------|------------|-----------|
| **Clientes novos** | Diária | Todo cliente novo deve passar pelo pipeline no dia seguinte à abertura de conta |
| **Clientes existentes** | Mensal | Reavaliação completa a cada 30 dias |
| **Eventos especiais** | Sob demanda | Reavaliação após atraso >30 dias, solicitação de aumento, etc. |

### Campos Necessários no Banco de Dados

#### Tabela: `tb_clientes_base`

```sql
-- Controle de agendamento
dt_ultima_analise DATE COMMENT 'Data da última execução do pipeline para este cliente',
dt_proxima_analise DATE COMMENT 'Data prevista para próxima reavaliação (dt_ultima_analise + 30)',
requer_reavaliacao TINYINT DEFAULT 0 COMMENT '1=Forçar reavaliação na próxima execução',
motivo_reavaliacao VARCHAR(50) COMMENT 'Motivo se forçado: NOVO, ATRASO, SOLICITACAO, EVENTO',

-- Exemplo de índice para query de agendamento
INDEX idx_proxima_analise (dt_proxima_analise, requer_reavaliacao)
```

### Query para Seleção de Clientes

```sql
-- Clientes que devem ser processados hoje
SELECT *
FROM tb_clientes_base
WHERE requer_reavaliacao = 1                          -- Forçados
   OR dt_proxima_analise <= CURDATE()                 -- Vencidos
   OR dt_ultima_analise IS NULL;                      -- Novos
```

### Atualização Após Processamento

```sql
-- Após execução do pipeline para um cliente
UPDATE tb_clientes_base
SET dt_ultima_analise = CURDATE(),
    dt_proxima_analise = DATE_ADD(CURDATE(), INTERVAL 30 DAY),
    requer_reavaliacao = 0,
    motivo_reavaliacao = NULL
WHERE CLIT IN (lista_de_clientes_processados);
```

### Eventos que Disparam Reavaliação Imediata

```sql
-- Trigger quando cliente entra em atraso > 30 dias
UPDATE tb_clientes_base
SET requer_reavaliacao = 1,
    motivo_reavaliacao = 'ATRASO'
WHERE CLIT = 'cliente_em_atraso';

-- Trigger quando cliente solicita aumento de limite
UPDATE tb_clientes_base
SET requer_reavaliacao = 1,
    motivo_reavaliacao = 'SOLICITACAO'
WHERE CLIT = 'cliente_que_solicitou';
```

---

## Modificações no Pipeline Runner

### Adicionar Filtro de Clientes

```python
# Em PipelineRunner.load_base()
def load_base(self, full_run: bool = False) -> pd.DataFrame:
    """
    Load clients for processing.
    
    Args:
        full_run: If True, process all clients (monthly batch)
                  If False, process only new/pending clients (daily)
    """
    if full_run:
        # Monthly: all clients
        return self._load_all_clients()
    else:
        # Daily: only clients needing evaluation
        return self._load_pending_clients()

def _load_pending_clients(self) -> pd.DataFrame:
    """Load only clients that need evaluation today."""
    query = '''
        SELECT * FROM tb_clientes_produtos cp
        JOIN tb_clientes_base cb ON cp.CLIT = cb.CLIT
        WHERE cb.requer_reavaliacao = 1
           OR cb.dt_proxima_analise <= CURDATE()
           OR cb.dt_ultima_analise IS NULL
    '''
    return pd.read_sql(query, self.db_connection)
```

### Adicionar Atualização de Datas

```python
# Em PipelineRunner.run()
def run(self, full_run: bool = False) -> pd.DataFrame:
    # ... existing code ...
    
    # After processing, update control dates
    self._update_analysis_dates(df['CLIT'].unique())
```

---

## Estimativas de Volume

| Métrica | Valor Estimado |
|---------|----------------|
| Clientes novos/dia | ~500 |
| Clientes vencidos/dia | ~5.200 (156k / 30) |
| Total diário (normal) | ~5.700 clientes |
| Total mensal (full run) | ~156.000 clientes |

---

## Cronograma Sugerido

| Horário | Job | Descrição |
|---------|-----|-----------|
| 06:00 | `daily_incremental.py` | Processa novos + vencidos |
| 07:00 | `send_notifications.py` | Envia notificações D+0 |
| 22:00 (1x/mês) | `monthly_full_run.py` | Reavaliação completa |

---

## Status: PENDENTE PARA PRODUÇÃO

Estas modificações devem ser implementadas quando:
1. Houver conexão com banco de dados MySQL em produção
2. Houver integração com sistema de agendamento (cron/Airflow)
3. Houver integração com sistema de notificações (push/SMS)

Para a **demonstração atual**, o pipeline processa todos os clientes em batch único.
