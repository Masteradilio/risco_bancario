-- ============================================================================
-- ESTAGIO_TRIGGERS - Script DDL com INSERT de exemplo
-- Registro de eventos de trigger para auditoria
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS estagio;

USE estagio;

SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO
-- ============================================================================

INSERT INTO
    estagio.estagio_triggers (
        contrato_id,
        cliente_id,
        tipo_trigger,
        valor_trigger,
        threshold_atingido,
        threshold_limite,
        trigger_acionado,
        estagio_sugerido,
        estagio_aplicado,
        tipo_operacao,
        modalidade,
        data_evento
    )
VALUES
    -- Trigger de atraso > 30 dias
    (
        'CTR2024002345',
        'CLI000002',
        'atraso',
        '35 dias de atraso',
        35,
        30,
        TRUE,
        2,
        2,
        'Parcelado',
        '108 : Financiamentos diversos',
        '2024-06-20 14:30:00'
    ),
    -- Trigger de PD ratio (aumento significativo)
    (
        'CTR2024002345',
        'CLI000002',
        'pd_ratio',
        'PD atual/concessão = 4.2x',
        4.20,
        3.00,
        TRUE,
        3,
        3,
        'Parcelado',
        '108 : Financiamentos diversos',
        '2024-08-15 09:15:00'
    ),
    -- Trigger qualitativo (reestruturação)
    (
        'CTR2024007890',
        'CLI000007',
        'reestruturacao',
        'Confissão de dívida',
        NULL,
        NULL,
        TRUE,
        3,
        3,
        'Parcelado',
        'CONFISSAO DIVIDA',
        '2024-06-01 10:00:00'
    ),
    -- Trigger de arrasto
    (
        'CTR2024004567',
        'CLI000004',
        'arrasto',
        'Contraparte com outro contrato em Stage 3',
        NULL,
        NULL,
        TRUE,
        3,
        3,
        'Consignado',
        '76 : CONSIGNADO ESTADUAL',
        '2024-09-10 11:20:00'
    ),
    -- Trigger não acionado (atraso abaixo do limite)
    (
        'CTR2024001234',
        'CLI000001',
        'atraso',
        '15 dias de atraso',
        15,
        30,
        FALSE,
        NULL,
        1,
        'Consignado',
        '76 : CONSIGNADO ESTADUAL',
        '2024-11-05 08:45:00'
    );

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT
    contrato_id,
    tipo_trigger,
    valor_trigger,
    CASE
        WHEN trigger_acionado THEN 'Acionado'
        ELSE 'Não acionado'
    END AS status,
    CONCAT('→ Stage ', estagio_aplicado) AS resultado,
    DATE_FORMAT(data_evento, '%d/%m/%Y') AS data
FROM estagio.estagio_triggers
ORDER BY data_evento DESC;