-- ============================================================================
-- ECL_CENARIOS - Script DDL com INSERT de exemplo
-- Cenários padrão: Otimista (15%), Base (70%), Pessimista (15%)
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS ecl;

USE ecl;

SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO - Cenários padrão CMN 4966
-- ============================================================================

INSERT INTO
    ecl.ecl_cenarios (
        nome,
        tipo,
        peso,
        spread_pd,
        spread_lgd,
        selic_projetada,
        pib_projetado,
        ipca_projetado,
        desemprego_projetado,
        data_inicio_vigencia,
        ativo,
        created_by
    )
VALUES
    -- Cenário Otimista (15%)
    (
        'Cenário Otimista',
        'otimista',
        0.15,
        0.85,
        0.90,
        10.50,
        3.50,
        3.80,
        6.50,
        '2026-01-01',
        TRUE,
        'SISTEMA'
    ),
    -- Cenário Base (70%)
    (
        'Cenário Base',
        'base',
        0.70,
        1.00,
        1.00,
        12.25,
        2.20,
        4.50,
        7.80,
        '2026-01-01',
        TRUE,
        'SISTEMA'
    ),
    -- Cenário Pessimista (15%)
    (
        'Cenário Pessimista',
        'pessimista',
        0.15,
        1.25,
        1.15,
        14.50,
        -0.50,
        6.00,
        9.50,
        '2026-01-01',
        TRUE,
        'SISTEMA'
    );

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT
    nome,
    tipo,
    CONCAT(FORMAT(peso * 100, 0), '%') AS peso,
    spread_pd,
    spread_lgd,
    CONCAT(
        FORMAT(selic_projetada, 2),
        '%'
    ) AS selic
FROM ecl.ecl_cenarios
WHERE
    ativo = TRUE
ORDER BY tipo;