-- ============================================================================
-- ESTAGIO_HISTORICO - Script DDL com INSERT de exemplo
-- Histórico de migrações para auditoria regulatória
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS estagio;

USE estagio;

SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO
-- ============================================================================

INSERT INTO
    estagio.estagio_historico (
        contrato_id,
        cliente_id,
        estagio_anterior,
        estagio_novo,
        motivo,
        dias_atraso,
        pd_na_migracao,
        pd_concessao,
        trigger_tipo,
        trigger_valor,
        data_migracao
    )
VALUES
    -- Classificação inicial
    (
        'CTR2024001234',
        'CLI000001',
        1,
        1,
        'classificacao_inicial',
        0,
        0.0185,
        0.0185,
        NULL,
        NULL,
        '2024-01-15 10:00:00'
    ),
    -- Migração por atraso
    (
        'CTR2024002345',
        'CLI000002',
        1,
        2,
        'atraso_30_dias',
        35,
        0.0850,
        0.0500,
        'DIAS_ATRASO',
        '35 dias',
        '2024-06-20 14:30:00'
    ),
    -- Migração por aumento significativo de risco
    (
        'CTR2024002345',
        'CLI000002',
        2,
        3,
        'aumento_significativo_risco',
        45,
        0.2100,
        0.0500,
        'PD_RATIO',
        'PD atual/concessão = 4.2x',
        '2024-08-15 09:15:00'
    ),
    -- Cura aplicada (reversão Stage 2 → 1)
    (
        'CTR2024003456',
        'CLI000003',
        2,
        1,
        'cura_aplicada',
        0,
        0.0350,
        0.0400,
        'CURA_6_MESES',
        '6 meses sem atraso + PD melhorou',
        '2024-12-01 16:45:00'
    ),
    -- Arrasto de contraparte
    (
        'CTR2024004567',
        'CLI000004',
        1,
        3,
        'arrasto_contraparte',
        0,
        0.0220,
        0.0200,
        'ARRASTO',
        'Outro contrato da contraparte em Stage 3',
        '2024-09-10 11:20:00'
    );

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT
    contrato_id,
    CONCAT(
        estagio_anterior,
        ' → ',
        estagio_novo
    ) AS migracao,
    motivo,
    dias_atraso,
    DATE_FORMAT(data_migracao, '%d/%m/%Y') AS data
FROM estagio.estagio_historico
ORDER BY data_migracao DESC;