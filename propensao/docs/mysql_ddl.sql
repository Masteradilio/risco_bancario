-- ============================================================================
-- PROLIMITE - MySQL DDL Schema
-- Database: MySQL 8.0+
-- Encoding: utf8mb4
-- ============================================================================

-- Drop tables if exist (for development)
-- DROP TABLE IF EXISTS tb_notificacoes;
-- DROP TABLE IF EXISTS tb_clientes_produtos;
-- DROP TABLE IF EXISTS tb_clientes_base;

-- ============================================================================
-- TABLE: tb_clientes_base (Client Master)
-- Purpose: Store client cadastral and credit data
-- Update: Daily batch from bank's core system
-- ============================================================================

CREATE TABLE tb_clientes_base (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Identification (for audit and lookup only, not used in models)
    CLIT VARCHAR(20) NOT NULL COMMENT 'Internal client ID',
    CPF VARCHAR(11) NOT NULL COMMENT 'Client CPF (masked in production)',
    
    -- Cadastral Data
    IDADE_CLIENTE INT COMMENT 'Client age in years',
    ESCOLARIDADE VARCHAR(30) COMMENT 'Education level',
    RENDA_BRUTA DECIMAL(15,2) COMMENT 'Gross monthly income',
    RENDA_LIQUIDA DECIMAL(15,2) COMMENT 'Net monthly income',
    TEMPO_RELAC DECIMAL(10,2) COMMENT 'Relationship time in months',
    ESTADO_CIVIL VARCHAR(20) COMMENT 'Marital status',
    TIPO_RESIDENCIA VARCHAR(30) COMMENT 'Residence type',
    POSSUI_VEICULO VARCHAR(5) COMMENT 'SIM/NAO - Has vehicle',
    QT_PRODUTOS INT COMMENT 'Number of products contracted',
    
    -- Commitment Data
    comprometimento_renda DECIMAL(5,4) COMMENT 'Income commitment ratio 0-1',
    margem_disponivel DECIMAL(15,2) COMMENT 'Available margin for new credit',
    
    -- Model Scores (calculated by PROLIMITE)
    PRINAD_SCORE INT COMMENT 'PRINAD risk score 0-100',
    RATING VARCHAR(5) COMMENT 'Rating: A1, A2, B1, B2, C1, C2, D',
    RATING_DESC VARCHAR(50) COMMENT 'Rating description',
    
    -- SCR Data (from BACEN API or synthetic)
    scr_score_risco INT COMMENT 'SCR credit score 300-900',
    scr_dias_atraso INT COMMENT 'Days in arrears in SFN',
    scr_tem_prejuizo TINYINT COMMENT '1=Has loss record in SFN',
    scr_exposicao_total DECIMAL(15,2) COMMENT 'Total exposure in SFN',
    
    -- Control
    dt_referencia DATE COMMENT 'Reference date of data',
    dt_processamento DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Processing timestamp',
    versao_modelo VARCHAR(20) DEFAULT '1.0' COMMENT 'Model version used',
    
    -- Indexes
    INDEX idx_clit (CLIT),
    INDEX idx_cpf (CPF),
    INDEX idx_rating (RATING),
    INDEX idx_prinad (PRINAD_SCORE),
    INDEX idx_dt_ref (dt_referencia),
    
    UNIQUE KEY uk_clit_dt (CLIT, dt_referencia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Client master table with cadastral data and PRINAD scores';


-- ============================================================================
-- TABLE: tb_clientes_produtos (Client x Product)
-- Purpose: Store client-product level data with limits and propensity
-- Update: Daily batch synchronized with limits system
-- ============================================================================

CREATE TABLE tb_clientes_produtos (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Foreign key to base
    CLIT VARCHAR(20) NOT NULL COMMENT 'Internal client ID',
    
    -- Product
    produto VARCHAR(30) NOT NULL COMMENT 'Product: consignado, banparacard, etc.',
    
    -- Limits
    limite_total DECIMAL(15,2) COMMENT 'Total granted limit',
    limite_utilizado DECIMAL(15,2) COMMENT 'Currently utilized limit',
    limite_disponivel DECIMAL(15,2) COMMENT 'Available limit',
    taxa_utilizacao DECIMAL(5,4) COMMENT 'Utilization rate 0-1',
    
    -- Monthly payments
    parcelas_mensais DECIMAL(15,2) COMMENT 'Monthly installment for this product',
    
    -- Utilization history
    utilizacao_media_12m DECIMAL(5,4) COMMENT 'Average utilization over 12 months',
    trimestres_sem_uso INT COMMENT 'Quarters without utilization (0-4)',
    max_dias_atraso_12m INT COMMENT 'Max days in arrears in last 12 months',
    
    -- Guarantees
    tipo_garantia VARCHAR(30) COMMENT 'Guarantee type: imovel, veiculo, etc.',
    valor_garantia DECIMAL(15,2) COMMENT 'Guarantee value',
    ltv DECIMAL(5,4) COMMENT 'Loan-to-Value ratio',
    
    -- Calculated by models
    propensao_score INT COMMENT 'Propensity score 0-100',
    propensao_classificacao VARCHAR(10) COMMENT 'ALTA/MEDIA/BAIXA',
    lgd DECIMAL(5,4) COMMENT 'Loss Given Default',
    ecl DECIMAL(15,2) COMMENT 'Expected Credit Loss',
    
    -- Limit Actions
    acao_limite VARCHAR(20) COMMENT 'MANTER/AUMENTAR/REDUZIR/ZERAR',
    limite_recomendado DECIMAL(15,2) COMMENT 'Recommended new limit',
    horizonte_dias INT COMMENT 'Days until action: 0, 30, 60',
    
    -- Control
    dt_referencia DATE COMMENT 'Reference date',
    dt_processamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_clit (CLIT),
    INDEX idx_produto (produto),
    INDEX idx_acao (acao_limite),
    INDEX idx_horizonte (horizonte_dias),
    INDEX idx_dt_ref (dt_referencia),
    
    FOREIGN KEY (CLIT) REFERENCES tb_clientes_base(CLIT)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Client-product table with limits, propensity and ECL';


-- ============================================================================
-- TABLE: tb_notificacoes (Notification Queue)
-- Purpose: Queue of notifications to be sent to clients
-- Update: Generated by PROLIMITE pipeline
-- ============================================================================

CREATE TABLE tb_notificacoes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Client identification
    CLIT VARCHAR(20) NOT NULL,
    CPF VARCHAR(11) NOT NULL,
    
    -- Product
    produto VARCHAR(30) NOT NULL,
    
    -- Action details
    acao_limite VARCHAR(20) NOT NULL COMMENT 'MANTER/AUMENTAR/REDUZIR/ZERAR',
    limite_atual DECIMAL(15,2),
    limite_novo DECIMAL(15,2),
    horizonte_dias INT COMMENT 'Days until action: 0, 30, 60',
    dt_acao_prevista DATE COMMENT 'Date when action will be applied',
    
    -- Notification details
    tipo_notificacao VARCHAR(20) COMMENT 'PUSH/SMS/BANNER/EMAIL',
    status_envio VARCHAR(20) DEFAULT 'PENDENTE' COMMENT 'PENDENTE/ENVIADO/ERRO',
    dt_envio DATETIME,
    tentativas INT DEFAULT 0,
    
    -- Scores for reference
    PRINAD_SCORE INT,
    propensao_score INT,
    
    -- Control
    dt_geracao DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_status (status_envio),
    INDEX idx_horizonte (horizonte_dias),
    INDEX idx_dt_acao (dt_acao_prevista),
    INDEX idx_clit (CLIT)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Notification queue for limit change communications';


-- ============================================================================
-- INSERT EXAMPLES (Daily Load Pattern)
-- ============================================================================

-- Example of daily load from CSV (use LOAD DATA or application insert)
-- Note: In production, use bulk INSERT or LOAD DATA INFILE

/*
-- Clear previous day's data (if full refresh)
DELETE FROM tb_clientes_produtos WHERE dt_referencia = CURDATE();

-- Insert from application:
INSERT INTO tb_clientes_produtos (
    CLIT, produto, limite_total, limite_utilizado, limite_disponivel,
    taxa_utilizacao, parcelas_mensais, utilizacao_media_12m, trimestres_sem_uso,
    max_dias_atraso_12m, tipo_garantia, valor_garantia, ltv,
    propensao_score, propensao_classificacao, lgd, ecl,
    acao_limite, limite_recomendado, horizonte_dias, dt_referencia
) VALUES (
    '1234567', 'consignado', 50000.00, 35000.00, 15000.00,
    0.70, 1500.00, 0.65, 0, 0, 'consignacao', 0, 1.00,
    75, 'ALTA', 0.25, 2625.00,
    'MANTER', 50000.00, 0, CURDATE()
);

-- Bulk load using LOAD DATA (faster for large datasets):
LOAD DATA LOCAL INFILE '/path/to/base_clientes_processada.csv'
INTO TABLE tb_clientes_produtos
FIELDS TERMINATED BY ';'
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(CLIT, CPF, IDADE_CLIENTE, ESCOLARIDADE, RENDA_BRUTA, TEMPO_RELAC,
 ESTADO_CIVIL, POSSUI_VEICULO, QT_PRODUTOS, produto, limite_total,
 limite_utilizado, limite_disponivel, taxa_utilizacao, parcelas_mensais,
 comprometimento_renda, margem_disponivel, utilizacao_media_12m,
 trimestres_sem_uso, max_dias_atraso_12m, scr_score_risco, scr_dias_atraso,
 scr_tem_prejuizo, tipo_garantia, valor_garantia, ltv, PRINAD_SCORE,
 RATING, RATING_DESC, propensao_score, propensao_classificacao, lgd, ecl,
 acao_limite, limite_recomendado, horizonte_dias)
SET dt_referencia = CURDATE(), dt_processamento = NOW();
*/


-- ============================================================================
-- USEFUL QUERIES
-- ============================================================================

-- Clients to notify today (D+0 actions)
/*
SELECT CLIT, CPF, produto, acao_limite, limite_total, limite_recomendado
FROM tb_clientes_produtos
WHERE horizonte_dias = 0
  AND acao_limite IN ('REDUZIR', 'ZERAR')
  AND dt_referencia = CURDATE();
*/

-- High risk clients requiring attention
/*
SELECT cb.CLIT, cb.PRINAD_SCORE, cb.RATING, 
       SUM(cp.ecl) as ecl_total, COUNT(*) as n_produtos
FROM tb_clientes_base cb
JOIN tb_clientes_produtos cp ON cb.CLIT = cp.CLIT
WHERE cb.RATING IN ('C2', 'D')
GROUP BY cb.CLIT, cb.PRINAD_SCORE, cb.RATING
ORDER BY ecl_total DESC
LIMIT 100;
*/

-- ECL by product
/*
SELECT produto, 
       COUNT(*) as exposicoes,
       SUM(ecl) as ecl_total,
       AVG(lgd) as lgd_medio
FROM tb_clientes_produtos
WHERE dt_referencia = CURDATE()
GROUP BY produto
ORDER BY ecl_total DESC;
*/
