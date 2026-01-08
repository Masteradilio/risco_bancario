-- ============================================================================
-- ESTAGIO_CURA - Contratos em Período de Cura
-- Art. 41 CMN 4966/2021 - Sistema de Cura Formal
-- ============================================================================

CREATE TABLE IF NOT EXISTS estagio.estagio_cura (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

-- Identificação
contrato_id VARCHAR(50) NOT NULL,
cliente_id VARCHAR(20) NOT NULL,

-- Estado atual
estagio_atual INT NOT NULL CHECK (estagio_atual IN (2, 3)),
estagio_destino INT NOT NULL CHECK (estagio_destino IN (1, 2)),

-- Período de observação
data_inicio_cura DATE NOT NULL,
meses_em_observacao INT DEFAULT 0,
meses_necessarios INT NOT NULL,

-- Critérios de elegibilidade
dias_atraso_atual INT DEFAULT 0,
dias_atraso_maximo INT DEFAULT 30,
pd_na_entrada DECIMAL(10, 6),
pd_atual DECIMAL(10, 6),

-- Para Stage 3 → 2
percentual_amortizacao DECIMAL(10, 6) DEFAULT 0,
amortizacao_necessaria DECIMAL(10, 6) DEFAULT 0.30,

-- Flags
eh_reestruturacao BOOLEAN DEFAULT FALSE,
elegivel_cura BOOLEAN DEFAULT FALSE,
cura_aplicada BOOLEAN DEFAULT FALSE,

-- Motivo de não elegibilidade
motivo_inelegivel VARCHAR(500),

-- Datas
data_ultima_avaliacao DATETIME, data_cura_aplicada DATETIME,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

-- Índices
INDEX idx_contrato (contrato_id),
    INDEX idx_cliente (cliente_id),
    INDEX idx_estagio (estagio_atual),
    INDEX idx_data_inicio (data_inicio_cura),
    INDEX idx_elegivel (elegivel_cura),
    INDEX idx_cura_aplicada (cura_aplicada)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Contratos em período de cura - Art. 41 CMN 4966';