-- ============================================================================
-- ESTAGIO_CURA - Script DDL com INSERT de exemplo
-- Contratos em período de observação para reversão de estágio
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS estagio;

USE estagio;

SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO
-- ============================================================================

INSERT INTO
    estagio.estagio_cura (
        contrato_id,
        cliente_id,
        estagio_atual,
        estagio_destino,
        data_inicio_cura,
        meses_em_observacao,
        meses_necessarios,
        dias_atraso_atual,
        dias_atraso_maximo,
        pd_na_entrada,
        pd_atual,
        percentual_amortizacao,
        amortizacao_necessaria,
        eh_reestruturacao,
        elegivel_cura,
        cura_aplicada,
        motivo_inelegivel
    )
VALUES
    -- Contrato Stage 2 → 1, 4 meses de observação (faltam 2)
    (
        'CTR2024005678',
        'CLI000005',
        2,
        1,
        '2025-09-01',
        4,
        6,
        0,
        30,
        0.0850,
        0.0720,
        0.00,
        0.00,
        FALSE,
        FALSE,
        FALSE,
        'Período de observação incompleto (4/6 meses)'
    ),
    -- Contrato Stage 2 → 1, já elegível para cura
    (
        'CTR2024006789',
        'CLI000006',
        2,
        1,
        '2025-07-01',
        6,
        6,
        0,
        30,
        0.0650,
        0.0520,
        0.00,
        0.00,
        FALSE,
        TRUE,
        FALSE,
        NULL
    ),
    -- Contrato Stage 3 → 2, reestruturação (24 meses)
    (
        'CTR2024007890',
        'CLI000007',
        3,
        2,
        '2024-06-01',
        19,
        24,
        0,
        0,
        0.2500,
        0.1500,
        0.42,
        0.50,
        TRUE,
        FALSE,
        FALSE,
        'Amortização insuficiente (42% < 50% necessário para reestruturação)'
    ),
    -- Contrato Stage 3 → 2, cura já aplicada
    (
        'CTR2024008901',
        'CLI000008',
        3,
        2,
        '2024-01-01',
        12,
        12,
        0,
        0,
        0.2000,
        0.1200,
        0.35,
        0.30,
        FALSE,
        TRUE,
        TRUE,
        NULL
    );

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT
    contrato_id,
    CONCAT(
        'Stage ',
        estagio_atual,
        ' → ',
        estagio_destino
    ) AS transicao,
    CONCAT(
        meses_em_observacao,
        '/',
        meses_necessarios,
        ' meses'
    ) AS periodo,
    CASE
        WHEN cura_aplicada THEN 'Cura Aplicada'
        WHEN elegivel_cura THEN 'Elegível'
        ELSE 'Em Observação'
    END AS status,
    CASE
        WHEN eh_reestruturacao THEN 'Sim'
        ELSE 'Não'
    END AS reestruturacao
FROM estagio.estagio_cura
ORDER BY
    elegivel_cura DESC,
    meses_em_observacao DESC;