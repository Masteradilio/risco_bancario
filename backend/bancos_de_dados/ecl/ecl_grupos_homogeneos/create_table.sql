-- ============================================================================
-- ECL_GRUPOS_HOMOGENEOS - Configuração de Grupos de Risco
-- Segmentação por PD conforme Art. 42 CMN 4966
-- ============================================================================

CREATE TABLE IF NOT EXISTS ecl.ecl_grupos_homogeneos (
    id INT AUTO_INCREMENT PRIMARY KEY,

-- Identificação do grupo
grupo_id INT NOT NULL UNIQUE,
nome VARCHAR(100) NOT NULL,
descricao TEXT,

-- Faixas de PD
pd_min DECIMAL(10, 6) NOT NULL, pd_max DECIMAL(10, 6) NOT NULL,

-- WOE (Weight of Evidence)
woe_score DECIMAL(10, 6),

-- Estatísticas do grupo
quantidade_clientes INT DEFAULT 0,
volume_carteira DECIMAL(18, 2) DEFAULT 0,
ecl_medio DECIMAL(10, 6),

-- Classificação de risco
nivel_risco ENUM( 'baixo', 'moderado', 'alto', 'muito_alto' ) NOT NULL,

-- Configuração
ativo BOOLEAN DEFAULT TRUE,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

-- Índices
INDEX idx_grupo_id (grupo_id),
INDEX idx_nivel_risco (nivel_risco),

-- Constraints
CONSTRAINT chk_pd_range CHECK (pd_min < pd_max)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Configuração de Grupos Homogêneos por PD - Art. 42 CMN 4966';