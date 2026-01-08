-- ============================================================================
-- ESTAGIO_TRIGGERS - Eventos de Trigger para Migração de Estágio
-- Art. 37-40 CMN 4966/2021
-- ============================================================================

CREATE TABLE IF NOT EXISTS estagio.estagio_triggers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

-- Identificação
contrato_id VARCHAR(50) NOT NULL,
cliente_id VARCHAR(20) NOT NULL,

-- Tipo de trigger
tipo_trigger ENUM(
    'atraso',
    'pd_ratio',
    'qualitativo',
    'reestruturacao',
    'arrasto',
    'watch_list',
    'evento_credito'
) NOT NULL,

-- Detalhes do trigger
valor_trigger VARCHAR(255),
threshold_atingido DECIMAL(10, 6),
threshold_limite DECIMAL(10, 6),

-- Resultado
trigger_acionado BOOLEAN DEFAULT FALSE,
estagio_sugerido INT CHECK (estagio_sugerido IN (1, 2, 3)),
estagio_aplicado INT CHECK (estagio_aplicado IN (1, 2, 3)),

-- Contexto
tipo_operacao VARCHAR(50), modalidade VARCHAR(100),

-- Data do evento
data_evento DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
origem_sistema VARCHAR(50) DEFAULT 'ECL_ENGINE',

-- Índices
INDEX idx_contrato (contrato_id),
    INDEX idx_cliente (cliente_id),
    INDEX idx_tipo (tipo_trigger),
    INDEX idx_data (data_evento),
    INDEX idx_acionado (trigger_acionado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Eventos de trigger para migração de estágio - CMN 4966';