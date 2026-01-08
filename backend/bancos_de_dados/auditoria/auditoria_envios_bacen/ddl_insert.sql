-- ============================================================================
-- AUDITORIA_ENVIOS_BACEN - Script DDL com INSERT de exemplo
-- Log de envios regulatórios
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS auditoria;

USE auditoria;

SOURCE create_table.sql;

-- ============================================================================
-- INSERT DE EXEMPLO
-- ============================================================================

INSERT INTO
    auditoria.auditoria_envios_bacen (
        codigo_envio,
        arquivo_nome,
        arquivo_tamanho_bytes,
        arquivo_hash_sha256,
        data_base,
        cnpj_instituicao,
        nome_instituicao,
        responsavel_nome,
        responsavel_email,
        responsavel_telefone,
        total_operacoes,
        total_ecl,
        total_ead,
        status,
        validacao_status,
        validacao_erros,
        validacao_alertas,
        data_geracao,
        data_envio,
        protocolo_bacen,
        observacoes,
        created_by
    )
VALUES
    -- Envio de Dezembro 2025
    (
        'ENV202512001',
        'Doc3040_202512_12345678.xml',
        1245678,
        'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6',
        '2025-12-31',
        '12345678',
        'Banco Exemplo S.A.',
        'João da Silva',
        'joao.silva@bancoexemplo.com.br',
        '9199999999',
        15847,
        2430000.00,
        156000000.00,
        'aceito',
        'aprovado',
        0,
        2,
        '2026-01-02 10:30:00',
        '2026-01-02 11:00:00',
        'BCB2026010200001',
        'Envio mensal regular',
        'SISTEMA'
    ),
    -- Envio de Novembro 2025
    (
        'ENV202511001',
        'Doc3040_202511_12345678.xml',
        1198432,
        'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1',
        '2025-11-30',
        '12345678',
        'Banco Exemplo S.A.',
        'Maria Santos',
        'maria.santos@bancoexemplo.com.br',
        '9188888888',
        15234,
        2350000.00,
        152000000.00,
        'aceito',
        'aprovado',
        0,
        0,
        '2025-12-02 09:15:00',
        '2025-12-02 10:00:00',
        'BCB2025120200001',
        'Envio mensal regular',
        'SISTEMA'
    );

-- ============================================================================
-- QUERY DE VERIFICAÇÃO
-- ============================================================================

SELECT
    codigo_envio,
    DATE_FORMAT(data_base, '%m/%Y') AS competencia,
    FORMAT(total_operacoes, 0) AS operacoes,
    CONCAT(
        'R$ ',
        FORMAT(total_ecl / 1000000, 2),
        'M'
    ) AS ecl_total,
    status,
    protocolo_bacen,
    DATE_FORMAT(data_envio, '%d/%m/%Y %H:%i') AS enviado_em
FROM auditoria.auditoria_envios_bacen
ORDER BY data_base DESC;