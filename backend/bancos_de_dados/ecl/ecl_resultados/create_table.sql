-- ============================================================================
-- ECL_RESULTADOS - Resultados de Cálculo de Perda Esperada
-- Resolução CMN 4966/2021 - IFRS 9
-- ============================================================================

CREATE TABLE IF NOT EXISTS ecl.ecl_resultados (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

-- Identificação da operação
contrato_id VARCHAR(50) NOT NULL,
cliente_id VARCHAR(20) NOT NULL,
cpf_cnpj VARCHAR(14) NOT NULL,

-- Dados do produto
produto VARCHAR(100) NOT NULL,
modalidade VARCHAR(100),
carteira_regulatoria VARCHAR(50),

-- Dados de saldo
saldo_utilizado DECIMAL(18, 2) NOT NULL,
limite_total DECIMAL(18, 2),
limite_disponivel DECIMAL(18, 2),

-- Classificação PRINAD
prinad_score DECIMAL(5, 2) NOT NULL, rating VARCHAR(10) NOT NULL,

-- Stage IFRS 9
stage INT NOT NULL CHECK (stage IN (1, 2, 3)),
horizonte_ecl VARCHAR(10) NOT NULL CHECK (
    horizonte_ecl IN ('12m', 'lifetime')
),

-- Grupos Homogêneos
grupo_homogeneo INT NOT NULL, woe_score DECIMAL(10, 6),

-- Componentes PD
pd_base DECIMAL(10, 6) NOT NULL,
pd_12m DECIMAL(10, 6) NOT NULL,
pd_lifetime DECIMAL(10, 6) NOT NULL,
k_pd_fl DECIMAL(10, 6) DEFAULT 1.0,
pd_ajustado DECIMAL(10, 6) NOT NULL,

-- Componentes LGD
lgd_base DECIMAL(10, 6) NOT NULL,
lgd_segmentado DECIMAL(10, 6),
k_lgd_fl DECIMAL(10, 6) DEFAULT 1.0,
lgd_final DECIMAL(10, 6) NOT NULL,

-- Componentes EAD
ccf DECIMAL(10, 6) DEFAULT 0.75, ead DECIMAL(18, 2) NOT NULL,

-- ECL Calculado
ecl_antes_piso DECIMAL(18, 2) NOT NULL,
ecl_final DECIMAL(18, 2) NOT NULL,
piso_aplicado BOOLEAN DEFAULT FALSE,
piso_percentual DECIMAL(10, 6),

-- Forward Looking Multi-Cenário
usar_multi_cenario BOOLEAN DEFAULT TRUE,
cenario_aplicado VARCHAR(20),

-- Metadados
dias_atraso INT DEFAULT 0,
data_calculo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
data_vencimento DATE,
data_concessao DATE,

-- Auditoria
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

-- Índices
INDEX idx_contrato (contrato_id),
    INDEX idx_cliente (cliente_id),
    INDEX idx_cpf_cnpj (cpf_cnpj),
    INDEX idx_data_calculo (data_calculo),
    INDEX idx_stage (stage),
    INDEX idx_grupo (grupo_homogeneo),
    INDEX idx_produto (produto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Resultados de cálculo ECL conforme CMN 4966 / IFRS 9';