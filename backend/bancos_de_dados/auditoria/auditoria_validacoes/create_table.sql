-- ============================================================================
-- AUDITORIA_VALIDACOES - Log de Validações Realizadas
-- Validações de arquivos XML e dados regulatórios
-- ============================================================================

CREATE TABLE IF NOT EXISTS auditoria.auditoria_validacoes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

-- Referência ao envio (se aplicável)
envio_id BIGINT,

-- Identificação
arquivo_nome VARCHAR(255),
tipo_validacao ENUM(
    'schema_xsd',
    'regras_negocio',
    'integridade_dados',
    'limites_valores',
    'consistencia'
) NOT NULL,

-- Resultado
resultado ENUM( 'aprovado', 'alertas', 'reprovado' ) NOT NULL,

-- Contadores
total_regras INT DEFAULT 0,
regras_aprovadas INT DEFAULT 0,
regras_alertas INT DEFAULT 0,
regras_reprovadas INT DEFAULT 0,

-- Detalhes dos erros (JSON)
erros_detalhes JSON, alertas_detalhes JSON,

-- Data
data_validacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
tempo_processamento_ms INT,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
created_by VARCHAR(100),

-- Índices
INDEX idx_envio (envio_id),
INDEX idx_tipo (tipo_validacao),
INDEX idx_resultado (resultado),
INDEX idx_data (data_validacao),

-- FK
CONSTRAINT fk_envio FOREIGN KEY (envio_id) REFERENCES auditoria.auditoria_envios_bacen(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Log de validações de arquivos regulatórios';