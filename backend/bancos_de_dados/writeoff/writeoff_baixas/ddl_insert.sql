-- ============================================================================
-- WRITEOFF_BAIXAS - Script DDL com INSERT de exemplo
-- Baixas contábeis para acompanhamento de 5 anos
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS writeoff;

USE writeoff;

SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO
-- ============================================================================

INSERT INTO
    writeoff.writeoff_baixas (
        contrato_id,
        cliente_id,
        cpf_cnpj,
        produto,
        modalidade,
        valor_baixado,
        provisao_constituida,
        diferenca_provisao,
        motivo,
        estagio_na_baixa,
        dias_atraso_na_baixa,
        data_baixa,
        status_recuperacao,
        total_recuperado,
        taxa_recuperacao,
        observacoes,
        created_by
    )
VALUES
    -- Baixa por inadimplência prolongada
    (
        'CTR2023001234',
        'CLI000010',
        '11111111111',
        'Crédito Pessoal',
        '108 : Financiamentos diversos',
        15000.00,
        15000.00,
        0.00,
        'inadimplencia_prolongada',
        3,
        365,
        '2023-06-15',
        'recuperacao_parcial',
        3500.00,
        0.2333,
        'Cliente em cobrança judicial desde 2023-01-01',
        'SISTEMA'
    ),
    -- Baixa por falência
    (
        'CTR2022002345',
        'CLI000011',
        '22222222222',
        'Capital de Giro',
        '115 : Capital de giro PJ',
        85000.00,
        85000.00,
        0.00,
        'falencia_rj',
        3,
        180,
        '2022-03-20',
        'em_acompanhamento',
        12000.00,
        0.1412,
        'Recuperação judicial deferida em 2022-02-01',
        'SISTEMA'
    ),
    -- Baixa por óbito
    (
        'CTR2024003456',
        'CLI000012',
        '33333333333',
        'Consignado',
        '76 : CONSIGNADO ESTADUAL',
        8500.00,
        8500.00,
        0.00,
        'obito',
        3,
        90,
        '2024-08-10',
        'irrecuperavel',
        0.00,
        0.0000,
        'Óbito confirmado. Sem espólio identificado.',
        'SISTEMA'
    ),
    -- Baixa por cessão de crédito
    (
        'CTR2021004567',
        'CLI000013',
        '44444444444',
        'Cartão de Crédito',
        '210 : Empréstimos - cartão',
        25000.00,
        25000.00,
        0.00,
        'cessao',
        3,
        270,
        '2021-11-30',
        'periodo_encerrado',
        22500.00,
        0.9000,
        'Crédito cedido para empresa de cobrança por 90% do valor',
        'SISTEMA'
    );

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT
    contrato_id,
    motivo,
    CONCAT(
        'R$ ',
        FORMAT(valor_baixado, 2)
    ) AS baixado,
    CONCAT(
        'R$ ',
        FORMAT(total_recuperado, 2)
    ) AS recuperado,
    CONCAT(
        FORMAT(taxa_recuperacao * 100, 1),
        '%'
    ) AS taxa,
    status_recuperacao,
    DATE_FORMAT(data_baixa, '%d/%m/%Y') AS data_baixa,
    DATE_FORMAT(
        data_fim_acompanhamento,
        '%d/%m/%Y'
    ) AS fim_acompanhamento
FROM writeoff.writeoff_baixas
ORDER BY data_baixa DESC;