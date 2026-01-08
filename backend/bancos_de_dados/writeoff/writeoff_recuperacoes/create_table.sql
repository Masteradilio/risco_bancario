-- ============================================================================
-- WRITEOFF_RECUPERACOES - Recuperações Pós-Baixa
-- Art. 49 CMN 4966/2021 - Acompanhamento por 5 anos
-- ============================================================================

CREATE TABLE IF NOT EXISTS writeoff.writeoff_recuperacoes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

-- Referência à baixa
baixa_id BIGINT NOT NULL, contrato_id VARCHAR(50) NOT NULL,

-- Valor recuperado
valor_recuperado DECIMAL(18, 2) NOT NULL,

-- Tipo de recuperação
tipo ENUM(
    'pagamento',
    'acordo',
    'acordo_judicial',
    'leilao_garantia',
    'seguro',
    'outro'
) NOT NULL DEFAULT 'pagamento',

-- Data
data_recuperacao DATE NOT NULL,

-- Detalhes
forma_pagamento VARCHAR(100), observacoes TEXT,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
created_by VARCHAR(100),

-- Índices
INDEX idx_baixa (baixa_id),
INDEX idx_contrato (contrato_id),
INDEX idx_data (data_recuperacao),
INDEX idx_tipo (tipo),

-- FK
CONSTRAINT fk_baixa FOREIGN KEY (baixa_id) REFERENCES writeoff.writeoff_baixas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Recuperações pós-baixa para acompanhamento de 5 anos - Art. 49 CMN 4966';

-- ============================================================================
-- TRIGGER PARA ATUALIZAR TOTAIS NA TABELA DE BAIXAS
-- ============================================================================

DELIMITER / /

CREATE TRIGGER trg_atualizar_recuperacao_insert
AFTER INSERT ON writeoff.writeoff_recuperacoes
FOR EACH ROW
BEGIN
    UPDATE writeoff.writeoff_baixas b
    SET 
        b.total_recuperado = (
            SELECT COALESCE(SUM(r.valor_recuperado), 0) 
            FROM writeoff.writeoff_recuperacoes r 
            WHERE r.baixa_id = NEW.baixa_id
        ),
        b.taxa_recuperacao = (
            SELECT COALESCE(SUM(r.valor_recuperado), 0) / b.valor_baixado
            FROM writeoff.writeoff_recuperacoes r 
            WHERE r.baixa_id = NEW.baixa_id
        ),
        b.status_recuperacao = CASE
            WHEN (SELECT SUM(r.valor_recuperado) FROM writeoff.writeoff_recuperacoes r WHERE r.baixa_id = NEW.baixa_id) >= b.valor_baixado 
                THEN 'recuperacao_total'
            WHEN (SELECT SUM(r.valor_recuperado) FROM writeoff.writeoff_recuperacoes r WHERE r.baixa_id = NEW.baixa_id) > 0 
                THEN 'recuperacao_parcial'
            ELSE b.status_recuperacao
        END
    WHERE b.id = NEW.baixa_id;
END//

DELIMITER;