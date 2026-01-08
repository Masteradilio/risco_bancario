-- ============================================================================
-- ESQUEMA COMPLETO - Sistema ECL/BACEN 4966
-- Deploy unificado de todos os esquemas e tabelas
-- ============================================================================
--
-- Como usar:
--   mysql -u root -p < esquema_completo.sql
--
-- Ou via cliente MySQL:
--   SOURCE /path/to/esquema_completo.sql;
--
-- ============================================================================

-- Configurações
SET NAMES utf8mb4;

SET CHARACTER SET utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- CRIAR ESQUEMAS
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS ecl;

CREATE SCHEMA IF NOT EXISTS estagio;

CREATE SCHEMA IF NOT EXISTS writeoff;

CREATE SCHEMA IF NOT EXISTS auditoria;

-- ============================================================================
-- ESQUEMA ECL - CÁLCULOS DE PERDA ESPERADA
-- ============================================================================

-- Tabela: ecl_resultados
CREATE TABLE IF NOT EXISTS ecl.ecl_resultados (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contrato_id VARCHAR(50) NOT NULL,
    cliente_id VARCHAR(20) NOT NULL,
    cpf_cnpj VARCHAR(14) NOT NULL,
    produto VARCHAR(100) NOT NULL,
    modalidade VARCHAR(100),
    carteira_regulatoria VARCHAR(50),
    saldo_utilizado DECIMAL(18, 2) NOT NULL,
    limite_total DECIMAL(18, 2),
    limite_disponivel DECIMAL(18, 2),
    prinad_score DECIMAL(5, 2) NOT NULL,
    rating VARCHAR(10) NOT NULL,
    stage INT NOT NULL CHECK (stage IN (1, 2, 3)),
    horizonte_ecl VARCHAR(10) NOT NULL CHECK (
        horizonte_ecl IN ('12m', 'lifetime')
    ),
    grupo_homogeneo INT NOT NULL,
    woe_score DECIMAL(10, 6),
    pd_base DECIMAL(10, 6) NOT NULL,
    pd_12m DECIMAL(10, 6) NOT NULL,
    pd_lifetime DECIMAL(10, 6) NOT NULL,
    k_pd_fl DECIMAL(10, 6) DEFAULT 1.0,
    pd_ajustado DECIMAL(10, 6) NOT NULL,
    lgd_base DECIMAL(10, 6) NOT NULL,
    lgd_segmentado DECIMAL(10, 6),
    k_lgd_fl DECIMAL(10, 6) DEFAULT 1.0,
    lgd_final DECIMAL(10, 6) NOT NULL,
    ccf DECIMAL(10, 6) DEFAULT 0.75,
    ead DECIMAL(18, 2) NOT NULL,
    ecl_antes_piso DECIMAL(18, 2) NOT NULL,
    ecl_final DECIMAL(18, 2) NOT NULL,
    piso_aplicado BOOLEAN DEFAULT FALSE,
    piso_percentual DECIMAL(10, 6),
    usar_multi_cenario BOOLEAN DEFAULT TRUE,
    cenario_aplicado VARCHAR(20),
    dias_atraso INT DEFAULT 0,
    data_calculo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_vencimento DATE,
    data_concessao DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_contrato (contrato_id),
    INDEX idx_cliente (cliente_id),
    INDEX idx_data_calculo (data_calculo),
    INDEX idx_stage (stage),
    INDEX idx_grupo (grupo_homogeneo)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Tabela: ecl_cenarios
CREATE TABLE IF NOT EXISTS ecl.ecl_cenarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    tipo ENUM(
        'otimista',
        'base',
        'pessimista'
    ) NOT NULL,
    peso DECIMAL(5, 4) NOT NULL CHECK (
        peso >= 0
        AND peso <= 1
    ),
    spread_pd DECIMAL(6, 4) NOT NULL DEFAULT 1.0,
    spread_lgd DECIMAL(6, 4) NOT NULL DEFAULT 1.0,
    selic_projetada DECIMAL(6, 4),
    pib_projetado DECIMAL(10, 2),
    ipca_projetado DECIMAL(6, 4),
    desemprego_projetado DECIMAL(6, 4),
    data_inicio_vigencia DATE NOT NULL,
    data_fim_vigencia DATE,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    INDEX idx_tipo (tipo),
    INDEX idx_ativo (ativo)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Tabela: ecl_parametros_fl
CREATE TABLE IF NOT EXISTS ecl.ecl_parametros_fl (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo_produto VARCHAR(50) NOT NULL,
    grupo_homogeneo INT,
    k_pd_fl DECIMAL(10, 6) NOT NULL DEFAULT 1.0,
    k_lgd_fl DECIMAL(10, 6) NOT NULL DEFAULT 1.0,
    k_pd_min DECIMAL(10, 6) DEFAULT 0.75,
    k_pd_max DECIMAL(10, 6) DEFAULT 1.25,
    k_lgd_min DECIMAL(10, 6) DEFAULT 0.80,
    k_lgd_max DECIMAL(10, 6) DEFAULT 1.20,
    cenario_id INT,
    data_inicio_vigencia DATE NOT NULL,
    data_fim_vigencia DATE,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_produto (tipo_produto),
    INDEX idx_grupo (grupo_homogeneo)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Tabela: ecl_grupos_homogeneos
CREATE TABLE IF NOT EXISTS ecl.ecl_grupos_homogeneos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grupo_id INT NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    pd_min DECIMAL(10, 6) NOT NULL,
    pd_max DECIMAL(10, 6) NOT NULL,
    woe_score DECIMAL(10, 6),
    quantidade_clientes INT DEFAULT 0,
    volume_carteira DECIMAL(18, 2) DEFAULT 0,
    ecl_medio DECIMAL(10, 6),
    nivel_risco ENUM(
        'baixo',
        'moderado',
        'alto',
        'muito_alto'
    ) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_grupo_id (grupo_id),
    INDEX idx_nivel_risco (nivel_risco)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================================================
-- ESQUEMA ESTAGIO - CLASSIFICAÇÃO IFRS 9
-- ============================================================================

-- Tabela: estagio_historico
CREATE TABLE IF NOT EXISTS estagio.estagio_historico (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contrato_id VARCHAR(50) NOT NULL,
    cliente_id VARCHAR(20) NOT NULL,
    estagio_anterior INT NOT NULL CHECK (estagio_anterior IN (1, 2, 3)),
    estagio_novo INT NOT NULL CHECK (estagio_novo IN (1, 2, 3)),
    motivo ENUM(
        'atraso_30_dias',
        'atraso_60_dias',
        'atraso_90_dias',
        'aumento_significativo_risco',
        'reestruturacao',
        'trigger_qualitativo',
        'arrasto_contraparte',
        'cura_aplicada',
        'classificacao_inicial'
    ) NOT NULL,
    dias_atraso INT DEFAULT 0,
    pd_na_migracao DECIMAL(10, 6),
    pd_concessao DECIMAL(10, 6),
    trigger_tipo VARCHAR(50),
    trigger_valor VARCHAR(100),
    data_migracao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    origem_sistema VARCHAR(50) DEFAULT 'ECL_ENGINE',
    INDEX idx_contrato (contrato_id),
    INDEX idx_data (data_migracao),
    INDEX idx_motivo (motivo)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Tabela: estagio_cura
CREATE TABLE IF NOT EXISTS estagio.estagio_cura (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contrato_id VARCHAR(50) NOT NULL,
    cliente_id VARCHAR(20) NOT NULL,
    estagio_atual INT NOT NULL CHECK (estagio_atual IN (2, 3)),
    estagio_destino INT NOT NULL CHECK (estagio_destino IN (1, 2)),
    data_inicio_cura DATE NOT NULL,
    meses_em_observacao INT DEFAULT 0,
    meses_necessarios INT NOT NULL,
    dias_atraso_atual INT DEFAULT 0,
    dias_atraso_maximo INT DEFAULT 30,
    pd_na_entrada DECIMAL(10, 6),
    pd_atual DECIMAL(10, 6),
    percentual_amortizacao DECIMAL(10, 6) DEFAULT 0,
    amortizacao_necessaria DECIMAL(10, 6) DEFAULT 0.30,
    eh_reestruturacao BOOLEAN DEFAULT FALSE,
    elegivel_cura BOOLEAN DEFAULT FALSE,
    cura_aplicada BOOLEAN DEFAULT FALSE,
    motivo_inelegivel VARCHAR(500),
    data_ultima_avaliacao DATETIME,
    data_cura_aplicada DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_contrato (contrato_id),
    INDEX idx_elegivel (elegivel_cura)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Tabela: estagio_triggers
CREATE TABLE IF NOT EXISTS estagio.estagio_triggers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contrato_id VARCHAR(50) NOT NULL,
    cliente_id VARCHAR(20) NOT NULL,
    tipo_trigger ENUM(
        'atraso',
        'pd_ratio',
        'qualitativo',
        'reestruturacao',
        'arrasto',
        'watch_list',
        'evento_credito'
    ) NOT NULL,
    valor_trigger VARCHAR(255),
    threshold_atingido DECIMAL(10, 6),
    threshold_limite DECIMAL(10, 6),
    trigger_acionado BOOLEAN DEFAULT FALSE,
    estagio_sugerido INT CHECK (estagio_sugerido IN (1, 2, 3)),
    estagio_aplicado INT CHECK (estagio_aplicado IN (1, 2, 3)),
    tipo_operacao VARCHAR(50),
    modalidade VARCHAR(100),
    data_evento DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    origem_sistema VARCHAR(50) DEFAULT 'ECL_ENGINE',
    INDEX idx_contrato (contrato_id),
    INDEX idx_tipo (tipo_trigger),
    INDEX idx_data (data_evento)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================================================
-- ESQUEMA WRITEOFF - BAIXAS E RECUPERAÇÕES
-- ============================================================================

-- Tabela: writeoff_baixas
CREATE TABLE IF NOT EXISTS writeoff.writeoff_baixas (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contrato_id VARCHAR(50) NOT NULL,
    cliente_id VARCHAR(20) NOT NULL,
    cpf_cnpj VARCHAR(14) NOT NULL,
    produto VARCHAR(100),
    modalidade VARCHAR(100),
    valor_baixado DECIMAL(18, 2) NOT NULL,
    provisao_constituida DECIMAL(18, 2) NOT NULL,
    diferenca_provisao DECIMAL(18, 2),
    motivo ENUM(
        'inadimplencia_prolongada',
        'falencia_rj',
        'obito',
        'prescricao',
        'acordo_judicial',
        'cessao',
        'outro'
    ) NOT NULL,
    estagio_na_baixa INT NOT NULL DEFAULT 3,
    dias_atraso_na_baixa INT DEFAULT 0,
    data_baixa DATE NOT NULL,
    data_fim_acompanhamento DATE GENERATED ALWAYS AS (
        DATE_ADD(data_baixa, INTERVAL 5 YEAR)
    ) STORED,
    status_recuperacao ENUM(
        'em_acompanhamento',
        'recuperacao_parcial',
        'recuperacao_total',
        'irrecuperavel',
        'periodo_encerrado'
    ) DEFAULT 'em_acompanhamento',
    total_recuperado DECIMAL(18, 2) DEFAULT 0,
    taxa_recuperacao DECIMAL(10, 6) DEFAULT 0,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    INDEX idx_contrato (contrato_id),
    INDEX idx_data_baixa (data_baixa),
    INDEX idx_status (status_recuperacao)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Tabela: writeoff_recuperacoes
CREATE TABLE IF NOT EXISTS writeoff.writeoff_recuperacoes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    baixa_id BIGINT NOT NULL,
    contrato_id VARCHAR(50) NOT NULL,
    valor_recuperado DECIMAL(18, 2) NOT NULL,
    tipo ENUM(
        'pagamento',
        'acordo',
        'acordo_judicial',
        'leilao_garantia',
        'seguro',
        'outro'
    ) NOT NULL DEFAULT 'pagamento',
    data_recuperacao DATE NOT NULL,
    forma_pagamento VARCHAR(100),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    INDEX idx_baixa (baixa_id),
    INDEX idx_contrato (contrato_id),
    INDEX idx_data (data_recuperacao),
    CONSTRAINT fk_baixa FOREIGN KEY (baixa_id) REFERENCES writeoff.writeoff_baixas (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================================================
-- ESQUEMA AUDITORIA - LOGS REGULATÓRIOS
-- ============================================================================

-- Tabela: auditoria_envios_bacen
CREATE TABLE IF NOT EXISTS auditoria.auditoria_envios_bacen (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    codigo_envio VARCHAR(50) NOT NULL UNIQUE,
    arquivo_nome VARCHAR(255) NOT NULL,
    arquivo_tamanho_bytes BIGINT,
    arquivo_hash_sha256 VARCHAR(64),
    data_base DATE NOT NULL,
    cnpj_instituicao VARCHAR(14) NOT NULL,
    nome_instituicao VARCHAR(200),
    responsavel_nome VARCHAR(200) NOT NULL,
    responsavel_email VARCHAR(200),
    responsavel_telefone VARCHAR(20),
    total_operacoes INT,
    total_ecl DECIMAL(18, 2),
    total_ead DECIMAL(18, 2),
    status ENUM(
        'gerado',
        'validado',
        'enviado',
        'aceito',
        'rejeitado',
        'pendente_correcao'
    ) NOT NULL DEFAULT 'gerado',
    validacao_status ENUM(
        'aprovado',
        'alertas',
        'erros'
    ) DEFAULT 'aprovado',
    validacao_erros INT DEFAULT 0,
    validacao_alertas INT DEFAULT 0,
    data_geracao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_envio DATETIME,
    data_resposta DATETIME,
    protocolo_bacen VARCHAR(100),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    INDEX idx_codigo (codigo_envio),
    INDEX idx_data_base (data_base),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- Tabela: auditoria_validacoes
CREATE TABLE IF NOT EXISTS auditoria.auditoria_validacoes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    envio_id BIGINT,
    arquivo_nome VARCHAR(255),
    tipo_validacao ENUM(
        'schema_xsd',
        'regras_negocio',
        'integridade_dados',
        'limites_valores',
        'consistencia'
    ) NOT NULL,
    resultado ENUM(
        'aprovado',
        'alertas',
        'reprovado'
    ) NOT NULL,
    total_regras INT DEFAULT 0,
    regras_aprovadas INT DEFAULT 0,
    regras_alertas INT DEFAULT 0,
    regras_reprovadas INT DEFAULT 0,
    erros_detalhes JSON,
    alertas_detalhes JSON,
    data_validacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tempo_processamento_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    INDEX idx_envio (envio_id),
    INDEX idx_tipo (tipo_validacao),
    INDEX idx_resultado (resultado),
    CONSTRAINT fk_envio FOREIGN KEY (envio_id) REFERENCES auditoria.auditoria_envios_bacen (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================================================
-- REABILITAR FOREIGN KEYS
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================

SELECT 'Esquemas criados:' AS info;

SHOW SCHEMAS LIKE 'ecl';

SHOW SCHEMAS LIKE 'estagio';

SHOW SCHEMAS LIKE 'writeoff';

SHOW SCHEMAS LIKE 'auditoria';

SELECT 'Deploy concluído com sucesso!' AS status;