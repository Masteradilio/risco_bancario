-- ============================================================================
-- AUDITORIA_ENVIOS_BACEN - Log de Envios XML Doc3040
-- Resolução CMN 4966/2021
-- ============================================================================

CREATE TABLE IF NOT EXISTS auditoria.auditoria_envios_bacen (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

-- Identificação do envio
codigo_envio VARCHAR(50) NOT NULL UNIQUE,

-- Dados do arquivo
arquivo_nome VARCHAR(255) NOT NULL,
arquivo_tamanho_bytes BIGINT,
arquivo_hash_sha256 VARCHAR(64),

-- Data-base do arquivo
data_base DATE NOT NULL,

-- Instituição
cnpj_instituicao VARCHAR(14) NOT NULL,
nome_instituicao VARCHAR(200),

-- Responsável
responsavel_nome VARCHAR(200) NOT NULL,
responsavel_email VARCHAR(200),
responsavel_telefone VARCHAR(20),

-- Estatísticas do arquivo
total_operacoes INT,
total_ecl DECIMAL(18, 2),
total_ead DECIMAL(18, 2),

-- Status do envio
status ENUM(
    'gerado',
    'validado',
    'enviado',
    'aceito',
    'rejeitado',
    'pendente_correcao'
) NOT NULL DEFAULT 'gerado',

-- Resultado da validação
validacao_status ENUM(
    'aprovado',
    'alertas',
    'erros'
) DEFAULT 'aprovado',
validacao_erros INT DEFAULT 0,
validacao_alertas INT DEFAULT 0,

-- Datas
data_geracao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
data_envio DATETIME,
data_resposta DATETIME,

-- Protocolo BACEN
protocolo_bacen VARCHAR(100),

-- Observações
observacoes TEXT,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
created_by VARCHAR(100),

-- Índices
INDEX idx_codigo (codigo_envio),
    INDEX idx_data_base (data_base),
    INDEX idx_cnpj (cnpj_instituicao),
    INDEX idx_status (status),
    INDEX idx_data_geracao (data_geracao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Log de envios XML Doc3040 para BACEN';