-- ============================================================================
-- ECL_CENARIOS - Cenários Macroeconômicos Forward Looking
-- Art. 36 §5º CMN 4966/2021
-- ============================================================================

CREATE TABLE IF NOT EXISTS ecl.ecl_cenarios (
    id INT AUTO_INCREMENT PRIMARY KEY,

-- Identificação do cenário
nome VARCHAR(50) NOT NULL,
tipo ENUM(
    'otimista',
    'base',
    'pessimista'
) NOT NULL,

-- Ponderação
peso DECIMAL(5, 4) NOT NULL CHECK ( peso >= 0 AND peso <= 1 ),

-- Spreads aplicados
spread_pd DECIMAL(6, 4) NOT NULL DEFAULT 1.0,
spread_lgd DECIMAL(6, 4) NOT NULL DEFAULT 1.0,

-- Dados macroeconômicos
selic_projetada DECIMAL(6, 4),
pib_projetado DECIMAL(10, 2),
ipca_projetado DECIMAL(6, 4),
desemprego_projetado DECIMAL(6, 4),

-- Vigência
data_inicio_vigencia DATE NOT NULL,
data_fim_vigencia DATE,
ativo BOOLEAN DEFAULT TRUE,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
created_by VARCHAR(100),

-- Índices
INDEX idx_tipo (tipo),
    INDEX idx_vigencia (data_inicio_vigencia, data_fim_vigencia),
    INDEX idx_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Cenários macroeconômicos para Forward Looking - Art. 36 §5º CMN 4966';