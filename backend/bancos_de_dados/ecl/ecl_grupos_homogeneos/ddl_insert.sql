-- ============================================================================
-- ECL_GRUPOS_HOMOGENEOS - Script DDL com INSERT de exemplo
-- Configuração padrão: 4 grupos por faixas de PD
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS ecl;

USE ecl;

SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO - 4 Grupos Homogêneos padrão
-- ============================================================================

INSERT INTO
    ecl.ecl_grupos_homogeneos (
        grupo_id,
        nome,
        descricao,
        pd_min,
        pd_max,
        woe_score,
        quantidade_clientes,
        volume_carteira,
        ecl_medio,
        nivel_risco,
        ativo
    )
VALUES
    -- Grupo 1: Baixo Risco (0-25% PRINAD)
    (
        1,
        'GH 1 - Baixo Risco',
        'Clientes com score PRINAD entre 0% e 25%. Perfil de baixíssima inadimplência.',
        0.000000,
        0.025000,
        -0.850000,
        4500,
        85000000.00,
        0.0050,
        'baixo',
        TRUE
    ),
    -- Grupo 2: Risco Moderado (25-50% PRINAD)
    (
        2,
        'GH 2 - Risco Moderado',
        'Clientes com score PRINAD entre 25% e 50%. Perfil de risco controlado.',
        0.025001,
        0.080000,
        -0.150000,
        1800,
        42000000.00,
        0.0150,
        'moderado',
        TRUE
    ),
    -- Grupo 3: Risco Alto (50-75% PRINAD)
    (
        3,
        'GH 3 - Risco Alto',
        'Clientes com score PRINAD entre 50% e 75%. Requer monitoramento intensivo.',
        0.080001,
        0.200000,
        0.250000,
        850,
        18000000.00,
        0.0450,
        'alto',
        TRUE
    ),
    -- Grupo 4: Risco Muito Alto (75-100% PRINAD)
    (
        4,
        'GH 4 - Risco Muito Alto',
        'Clientes com score PRINAD acima de 75%. Alto potencial de inadimplência.',
        0.200001,
        1.000000,
        0.650000,
        350,
        5000000.00,
        0.1200,
        'muito_alto',
        TRUE
    );

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT
    grupo_id AS gh,
    nome,
    CONCAT(
        FORMAT(pd_min * 100, 2),
        '% - ',
        FORMAT(pd_max * 100, 2),
        '%'
    ) AS faixa_pd,
    nivel_risco,
    FORMAT(quantidade_clientes, 0) AS clientes,
    CONCAT(
        'R$ ',
        FORMAT(volume_carteira / 1000000, 1),
        'M'
    ) AS carteira
FROM ecl.ecl_grupos_homogeneos
WHERE
    ativo = TRUE
ORDER BY grupo_id;