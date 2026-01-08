-- ============================================================================
-- WRITEOFF_RECUPERACOES - Script DDL com INSERT de exemplo
-- Recuperações pós-baixa
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS writeoff;

USE writeoff;

SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO
-- (Assumindo que os IDs das baixas são 1, 2, 3, 4)
-- ============================================================================

INSERT INTO
    writeoff.writeoff_recuperacoes (
        baixa_id,
        contrato_id,
        valor_recuperado,
        tipo,
        data_recuperacao,
        forma_pagamento,
        observacoes,
        created_by
    )
VALUES
    -- Recuperações do contrato CTR2023001234 (baixa_id = 1)
    (
        1,
        'CTR2023001234',
        1500.00,
        'acordo',
        '2023-09-15',
        'PIX',
        'Acordo de 3 parcelas - 1/3',
        'COBRANCA'
    ),
    (
        1,
        'CTR2023001234',
        1000.00,
        'acordo',
        '2023-10-15',
        'PIX',
        'Acordo de 3 parcelas - 2/3',
        'COBRANCA'
    ),
    (
        1,
        'CTR2023001234',
        1000.00,
        'acordo',
        '2023-11-15',
        'PIX',
        'Acordo de 3 parcelas - 3/3',
        'COBRANCA'
    ),

-- Recuperações do contrato CTR2022002345 (baixa_id = 2) - Falência
(
    2,
    'CTR2022002345',
    5000.00,
    'acordo_judicial',
    '2023-06-01',
    'TED',
    'Pagamento via plano de recuperação judicial',
    'JURIDICO'
),
(
    2,
    'CTR2022002345',
    4000.00,
    'acordo_judicial',
    '2024-01-15',
    'TED',
    'Segunda parcela do plano',
    'JURIDICO'
),
(
    2,
    'CTR2022002345',
    3000.00,
    'acordo_judicial',
    '2024-06-20',
    'TED',
    'Terceira parcela do plano',
    'JURIDICO'
),

-- Recuperações do contrato CTR2021004567 (baixa_id = 4) - Cessão
(
    4,
    'CTR2021004567',
    22500.00,
    'outro',
    '2021-11-30',
    'TED',
    'Valor da cessão do crédito (90%)',
    'CESSAO'
);

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT r.contrato_id, r.tipo, CONCAT(
        'R$ ', FORMAT(r.valor_recuperado, 2)
    ) AS valor, DATE_FORMAT(
        r.data_recuperacao, '%d/%m/%Y'
    ) AS data, r.observacoes
FROM writeoff.writeoff_recuperacoes r
ORDER BY r.contrato_id, r.data_recuperacao;

-- ============================================================================
-- QUERY DE RESUMO POR CONTRATO
-- ============================================================================

SELECT
    b.contrato_id,
    CONCAT(
        'R$ ',
        FORMAT(b.valor_baixado, 2)
    ) AS baixado,
    CONCAT(
        'R$ ',
        FORMAT(b.total_recuperado, 2)
    ) AS recuperado,
    CONCAT(
        FORMAT(b.taxa_recuperacao * 100, 1),
        '%'
    ) AS taxa,
    COUNT(r.id) AS qtd_recuperacoes
FROM writeoff.writeoff_baixas b
    LEFT JOIN writeoff.writeoff_recuperacoes r ON r.baixa_id = b.id
GROUP BY
    b.id
ORDER BY b.taxa_recuperacao DESC;