-- ============================================================================
-- ESTAGIO_HISTORICO - Histórico de Migrações de Estágio IFRS 9
-- Art. 37-40 CMN 4966/2021
-- ============================================================================

CREATE TABLE IF NOT EXISTS estagio.estagio_historico (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

-- Identificação
contrato_id VARCHAR(50) NOT NULL,
cliente_id VARCHAR(20) NOT NULL,

-- Migração
estagio_anterior INT NOT NULL CHECK (estagio_anterior IN (1, 2, 3)),
estagio_novo INT NOT NULL CHECK (estagio_novo IN (1, 2, 3)),

-- Motivo da migração
motivo ENUM(
    'atraso_30_dias',
    'atraso_60_dias',
    'atraso_90_dias',
    'aumento_significativo_risco',
    'reestruturacao',
    'trigger_qualitativo',
    'arrasto_contraparte',
    'cura_aplicada',
    'classificacao_inicial'
) NOT NULL,

-- Dados no momento da migração
dias_atraso INT DEFAULT 0,
pd_na_migracao DECIMAL(10, 6),
pd_concessao DECIMAL(10, 6),

-- Trigger específico
trigger_tipo VARCHAR(50), trigger_valor VARCHAR(100),

-- Data
data_migracao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
origem_sistema VARCHAR(50) DEFAULT 'ECL_ENGINE',

-- Índices
INDEX idx_contrato (contrato_id),
    INDEX idx_cliente (cliente_id),
    INDEX idx_data (data_migracao),
    INDEX idx_estagios (estagio_anterior, estagio_novo),
    INDEX idx_motivo (motivo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Histórico de migrações de estágio IFRS 9 - CMN 4966';