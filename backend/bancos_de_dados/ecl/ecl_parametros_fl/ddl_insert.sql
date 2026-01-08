-- ============================================================================
-- ECL_PARAMETROS_FL - Script DDL com INSERT de exemplo
-- Parâmetros por tipo de produto e grupo homogêneo
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS ecl;

USE ecl;

SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO
-- ============================================================================

INSERT INTO
    ecl.ecl_parametros_fl (
        tipo_produto,
        grupo_homogeneo,
        k_pd_fl,
        k_lgd_fl,
        k_pd_min,
        k_pd_max,
        k_lgd_min,
        k_lgd_max,
        data_inicio_vigencia,
        ativo
    )
VALUES
    -- Consignado por grupo
    (
        'consignado',
        1,
        0.98,
        0.99,
        0.75,
        1.25,
        0.80,
        1.20,
        '2026-01-01',
        TRUE
    ),
    (
        'consignado',
        2,
        1.00,
        1.00,
        0.75,
        1.25,
        0.80,
        1.20,
        '2026-01-01',
        TRUE
    ),
    (
        'consignado',
        3,
        1.02,
        1.02,
        0.75,
        1.25,
        0.80,
        1.20,
        '2026-01-01',
        TRUE
    ),
    (
        'consignado',
        4,
        1.05,
        1.05,
        0.75,
        1.25,
        0.80,
        1.20,
        '2026-01-01',
        TRUE
    ),

-- Parcelados por grupo
(
    'parcelados',
    1,
    0.95,
    0.98,
    0.75,
    1.25,
    0.80,
    1.20,
    '2026-01-01',
    TRUE
),
(
    'parcelados',
    2,
    1.00,
    1.00,
    0.75,
    1.25,
    0.80,
    1.20,
    '2026-01-01',
    TRUE
),
(
    'parcelados',
    3,
    1.05,
    1.03,
    0.75,
    1.25,
    0.80,
    1.20,
    '2026-01-01',
    TRUE
),
(
    'parcelados',
    4,
    1.10,
    1.08,
    0.75,
    1.25,
    0.80,
    1.20,
    '2026-01-01',
    TRUE
),

-- Rotativos por grupo
(
    'rotativos',
    1,
    1.00,
    1.00,
    0.75,
    1.25,
    0.80,
    1.20,
    '2026-01-01',
    TRUE
),
(
    'rotativos',
    2,
    1.05,
    1.02,
    0.75,
    1.25,
    0.80,
    1.20,
    '2026-01-01',
    TRUE
),
(
    'rotativos',
    3,
    1.12,
    1.05,
    0.75,
    1.25,
    0.80,
    1.20,
    '2026-01-01',
    TRUE
),
(
    'rotativos',
    4,
    1.20,
    1.10,
    0.75,
    1.25,
    0.80,
    1.20,
    '2026-01-01',
    TRUE
);

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT
    tipo_produto,
    grupo_homogeneo AS gh,
    k_pd_fl,
    k_lgd_fl
FROM ecl.ecl_parametros_fl
WHERE
    ativo = TRUE
ORDER BY tipo_produto, grupo_homogeneo;