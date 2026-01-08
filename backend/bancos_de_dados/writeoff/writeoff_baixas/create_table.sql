-- ============================================================================
-- WRITEOFF_BAIXAS - Registro de Baixas Contábeis (Write-off)
-- Art. 49 CMN 4966/2021 - Acompanhamento por 5 anos
-- ============================================================================

CREATE TABLE IF NOT EXISTS writeoff.writeoff_baixas (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

-- Identificação
contrato_id VARCHAR(50) NOT NULL,
cliente_id VARCHAR(20) NOT NULL,
cpf_cnpj VARCHAR(14) NOT NULL,

-- Dados do produto
produto VARCHAR(100), modalidade VARCHAR(100),

-- Valores da baixa
valor_baixado DECIMAL(18, 2) NOT NULL,
provisao_constituida DECIMAL(18, 2) NOT NULL,
diferenca_provisao DECIMAL(18, 2),

-- Motivo da baixa
motivo ENUM(
    'inadimplencia_prolongada',
    'falencia_rj',
    'obito',
    'prescricao',
    'acordo_judicial',
    'cessao',
    'outro'
) NOT NULL,

-- Estágio na baixa
estagio_na_baixa INT NOT NULL DEFAULT 3 CHECK (estagio_na_baixa IN (1, 2, 3)),
dias_atraso_na_baixa INT DEFAULT 0,

-- Datas
data_baixa DATE NOT NULL,
data_fim_acompanhamento DATE GENERATED ALWAYS AS (
    DATE_ADD(data_baixa, INTERVAL 5 YEAR)
) STORED,

-- Status de recuperação
status_recuperacao ENUM(
    'em_acompanhamento',
    'recuperacao_parcial',
    'recuperacao_total',
    'irrecuperavel',
    'periodo_encerrado'
) DEFAULT 'em_acompanhamento',

-- Totais de recuperação (calculados)
total_recuperado DECIMAL(18, 2) DEFAULT 0,
taxa_recuperacao DECIMAL(10, 6) DEFAULT 0,

-- Observações
observacoes TEXT,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
created_by VARCHAR(100),

-- Índices
INDEX idx_contrato (contrato_id),
    INDEX idx_cliente (cliente_id),
    INDEX idx_cpf_cnpj (cpf_cnpj),
    INDEX idx_data_baixa (data_baixa),
    INDEX idx_status (status_recuperacao),
    INDEX idx_motivo (motivo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Registro de baixas contábeis com acompanhamento de 5 anos - Art. 49 CMN 4966';