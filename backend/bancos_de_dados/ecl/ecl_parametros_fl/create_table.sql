-- ============================================================================
-- ECL_PARAMETROS_FL - Parâmetros Forward Looking por Produto
-- Fatores K_PD_FL e K_LGD_FL
-- ============================================================================

CREATE TABLE IF NOT EXISTS ecl.ecl_parametros_fl (
    id INT AUTO_INCREMENT PRIMARY KEY,

-- Identificação
tipo_produto VARCHAR(50) NOT NULL, grupo_homogeneo INT,

-- Fatores Forward Looking
k_pd_fl DECIMAL(10, 6) NOT NULL DEFAULT 1.0,
k_lgd_fl DECIMAL(10, 6) NOT NULL DEFAULT 1.0,

-- Limites de variação
k_pd_min DECIMAL(10, 6) DEFAULT 0.75,
k_pd_max DECIMAL(10, 6) DEFAULT 1.25,
k_lgd_min DECIMAL(10, 6) DEFAULT 0.80,
k_lgd_max DECIMAL(10, 6) DEFAULT 1.20,

-- Cenário aplicado
cenario_id INT,

-- Vigência
data_inicio_vigencia DATE NOT NULL,
data_fim_vigencia DATE,
ativo BOOLEAN DEFAULT TRUE,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

-- Índices
INDEX idx_produto (tipo_produto),
INDEX idx_grupo (grupo_homogeneo),
INDEX idx_vigencia (data_inicio_vigencia),

-- FK
CONSTRAINT fk_cenario FOREIGN KEY (cenario_id) REFERENCES ecl.ecl_cenarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Parâmetros Forward Looking K_PD_FL e K_LGD_FL por produto';