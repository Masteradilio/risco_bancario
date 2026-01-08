-- ============================================================================
-- ECL_RESULTADOS - Script DDL com INSERT de exemplo
-- Referência para equipe de TI na integração com sistemas legados
-- ============================================================================

-- Criar esquema se não existir
CREATE SCHEMA IF NOT EXISTS ecl;

USE ecl;

-- Criar tabela
SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO - Dados fictícios para demonstração
-- ============================================================================

INSERT INTO
    ecl.ecl_resultados (
        contrato_id,
        cliente_id,
        cpf_cnpj,
        produto,
        modalidade,
        carteira_regulatoria,
        saldo_utilizado,
        limite_total,
        limite_disponivel,
        prinad_score,
        rating,
        stage,
        horizonte_ecl,
        grupo_homogeneo,
        woe_score,
        pd_base,
        pd_12m,
        pd_lifetime,
        k_pd_fl,
        pd_ajustado,
        lgd_base,
        lgd_segmentado,
        k_lgd_fl,
        lgd_final,
        ccf,
        ead,
        ecl_antes_piso,
        ecl_final,
        piso_aplicado,
        piso_percentual,
        usar_multi_cenario,
        cenario_aplicado,
        dias_atraso
    )
VALUES
    -- Exemplo 1: Consignado Stage 1 (baixo risco)
    (
        'CTR2024001234',
        'CLI000001',
        '12345678901',
        'Consignado INSS',
        '76 : CONSIGNADO ESTADUAL',
        'VAREJO',
        15000.00,
        20000.00,
        5000.00,
        18.50,
        'A2',
        1,
        '12m',
        1,
        -0.85,
        0.0185,
        0.0185,
        0.0890,
        1.015,
        0.0188,
        0.25,
        0.22,
        1.01,
        0.2222,
        0.75,
        18750.00,
        78.17,
        78.17,
        FALSE,
        NULL,
        TRUE,
        'base',
        0
    ),
    -- Exemplo 2: Cartão de Crédito Stage 2 (risco moderado)
    (
        'CTR2024002345',
        'CLI000002',
        '98765432101',
        'Cartão de Crédito',
        '210 : Empréstimos - cartão de crédito',
        'VAREJO',
        5000.00,
        8000.00,
        3000.00,
        52.30,
        'C2',
        2,
        'lifetime',
        3,
        0.15,
        0.0850,
        0.0850,
        0.2100,
        1.025,
        0.2153,
        0.80,
        0.78,
        1.02,
        0.7956,
        0.90,
        7700.00,
        1318.06,
        1318.06,
        FALSE,
        NULL,
        TRUE,
        'base',
        35
    ),
    -- Exemplo 3: Imobiliário Stage 3 com piso aplicado
    (
        'CTR2024003456',
        'CLI000003',
        '11122233344',
        'Crédito Imobiliário',
        '108 : Financiamentos imobiliários',
        'IMOBILIARIO',
        250000.00,
        250000.00,
        0.00,
        78.90,
        'E1',
        3,
        'lifetime',
        4,
        0.45,
        0.1500,
        0.1500,
        0.3500,
        1.10,
        0.3850,
        0.10,
        0.12,
        1.05,
        0.1260,
        1.00,
        250000.00,
        12127.50,
        37500.00,
        TRUE,
        0.15,
        TRUE,
        'pessimista',
        95
    );

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT
    contrato_id,
    produto,
    stage,
    CONCAT('R$ ', FORMAT(ecl_final, 2)) AS ecl,
    rating,
    grupo_homogeneo AS gh,
    CASE
        WHEN piso_aplicado THEN 'Sim'
        ELSE 'Não'
    END AS piso
FROM ecl.ecl_resultados
ORDER BY ecl_final DESC;