-- ============================================================================
-- AUDITORIA_VALIDACOES - Script DDL com INSERT de exemplo
-- Log de validações de arquivos regulatórios
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS auditoria;

USE auditoria;

SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO
-- (Assumindo que os IDs de envio são 1 e 2)
-- ============================================================================

INSERT INTO
    auditoria.auditoria_validacoes (
        envio_id,
        arquivo_nome,
        tipo_validacao,
        resultado,
        total_regras,
        regras_aprovadas,
        regras_alertas,
        regras_reprovadas,
        erros_detalhes,
        alertas_detalhes,
        tempo_processamento_ms,
        created_by
    )
VALUES
    -- Validação de schema XSD
    (
        1,
        'Doc3040_202512_12345678.xml',
        'schema_xsd',
        'aprovado',
        45,
        45,
        0,
        0,
        NULL,
        NULL,
        1250,
        'VALIDADOR'
    ),

-- Validação de regras de negócio
(
    1,
    'Doc3040_202512_12345678.xml',
    'regras_negocio',
    'alertas',
    28,
    26,
    2,
    0,
    NULL,
    '{"alertas": [{"codigo": "RN015", "mensagem": "ECL superior a 50% do saldo em 3 operações"}, {"codigo": "RN022", "mensagem": "LGD acima do esperado para produto 76"}]}',
    3420,
    'VALIDADOR'
),

-- Validação de integridade
(
    1,
    'Doc3040_202512_12345678.xml',
    'integridade_dados',
    'aprovado',
    52,
    52,
    0,
    0,
    NULL,
    NULL,
    2100,
    'VALIDADOR'
),

-- Validação de limites
(
    1,
    'Doc3040_202512_12345678.xml',
    'limites_valores',
    'aprovado',
    18,
    18,
    0,
    0,
    NULL,
    NULL,
    890,
    'VALIDADOR'
),

-- Validação envio anterior
(
    2,
    'Doc3040_202511_12345678.xml',
    'schema_xsd',
    'aprovado',
    45,
    45,
    0,
    0,
    NULL,
    NULL,
    1180,
    'VALIDADOR'
),
(
    2,
    'Doc3040_202511_12345678.xml',
    'regras_negocio',
    'aprovado',
    28,
    28,
    0,
    0,
    NULL,
    NULL,
    3250,
    'VALIDADOR'
);

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT
    v.arquivo_nome,
    v.tipo_validacao,
    v.resultado,
    CONCAT(
        v.regras_aprovadas,
        '/',
        v.total_regras
    ) AS regras,
    v.regras_alertas AS alertas,
    v.regras_reprovadas AS erros,
    CONCAT(
        v.tempo_processamento_ms,
        'ms'
    ) AS tempo
FROM auditoria.auditoria_validacoes v
ORDER BY v.data_validacao DESC;