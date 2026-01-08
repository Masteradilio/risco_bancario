-- ============================================================================
-- ESQUEMA USUARIOS - GESTÃO DE ACESSO E RBAC
-- Sistema de Gestão de Risco Bancário
-- ============================================================================
--
-- Criado em: 2026-01-08
-- Descrição: Gerenciamento de usuários, sessões e auditoria de atividades
-- Perfis: ANALISTA, GESTOR, AUDITOR, ADMIN
--
-- Integração: Windows NTLM/SSO (senha gerenciada pelo AD)
-- ============================================================================

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- CRIAR ESQUEMA
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS usuarios;

-- ============================================================================
-- TABELA: USUARIOS
-- Dados do usuário integrado com Windows AD
-- ============================================================================

CREATE TABLE IF NOT EXISTS usuarios.usuarios (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    
    -- Dados de identificação (sincronizados com AD)
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    matricula VARCHAR(20) UNIQUE NOT NULL,
    login_windows VARCHAR(50) UNIQUE NOT NULL,  -- sAMAccountName do AD
    
    -- Perfil de acesso RBAC
    role ENUM('ANALISTA', 'GESTOR', 'AUDITOR', 'ADMIN') NOT NULL DEFAULT 'ANALISTA',
    departamento VARCHAR(100),
    cargo VARCHAR(100),
    
    -- Flags especiais
    is_externo BOOLEAN DEFAULT FALSE,           -- Auditor externo BACEN
    data_expiracao DATE NULL,                    -- Para usuários temporários (30 dias para externos)
    
    -- Status da conta
    ativo BOOLEAN DEFAULT TRUE,
    ultimo_login DATETIME,
    
    -- Auditoria
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    criado_por CHAR(36),
    
    -- Índices
    INDEX idx_matricula (matricula),
    INDEX idx_login_windows (login_windows),
    INDEX idx_role (role),
    INDEX idx_ativo (ativo),
    INDEX idx_externo (is_externo)
    
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================================================
-- TABELA: USUARIOS_SESSOES
-- Controle de sessões ativas (timeout 30 minutos)
-- ============================================================================

CREATE TABLE IF NOT EXISTS usuarios.usuarios_sessoes (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    usuario_id CHAR(36) NOT NULL,
    
    -- Dados da sessão
    token_hash VARCHAR(64) NOT NULL,            -- SHA256 do JWT
    ip_address VARCHAR(45),                      -- IPv4 ou IPv6
    user_agent TEXT,
    
    -- Controle de validade
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    expira_em DATETIME NOT NULL,                 -- 30 minutos após login/atividade
    ultima_atividade DATETIME DEFAULT CURRENT_TIMESTAMP,
    revogado_em DATETIME,
    
    -- Índices
    INDEX idx_usuario (usuario_id),
    INDEX idx_token (token_hash),
    INDEX idx_expira (expira_em),
    
    CONSTRAINT fk_sessao_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios.usuarios(id)
    
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================================================
-- TABELA: AUDITORIA_ATIVIDADES
-- Log de todas as ações de usuários no sistema
-- ============================================================================

CREATE TABLE IF NOT EXISTS usuarios.auditoria_atividades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Identificação do usuário
    usuario_id CHAR(36),
    usuario_nome VARCHAR(255) NOT NULL,
    usuario_role ENUM('ANALISTA', 'GESTOR', 'AUDITOR', 'ADMIN'),
    
    -- Detalhes da ação
    acao VARCHAR(100) NOT NULL,                  -- LOGIN, LOGOUT, CLASSIFICAR_PRINAD, CALCULAR_ECL, EXPORTAR_BACEN, etc.
    recurso VARCHAR(255),                        -- Módulo ou endpoint acessado
    detalhes JSON,                               -- Dados específicos da ação
    
    -- Contexto de rede
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    
    -- Resultado da ação
    status ENUM('SUCESSO', 'FALHA', 'NEGADO') DEFAULT 'SUCESSO',
    erro_mensagem TEXT,
    
    -- Timestamp
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices para consultas de auditoria
    INDEX idx_usuario (usuario_id),
    INDEX idx_acao (acao),
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (status),
    INDEX idx_acao_data (acao, timestamp)
    
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================================================
-- TABELA: SISTEMA_ERROS
-- Log de erros do sistema (visível apenas para Admin)
-- ============================================================================

CREATE TABLE IF NOT EXISTS usuarios.sistema_erros (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Detalhes do erro
    nivel ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL DEFAULT 'ERROR',
    modulo VARCHAR(100),                         -- prinad, ecl, propensao, auth
    funcao VARCHAR(255),
    mensagem TEXT NOT NULL,
    stacktrace TEXT,
    
    -- Contexto
    usuario_id CHAR(36),
    request_id VARCHAR(50),
    ip_address VARCHAR(45),
    request_path VARCHAR(500),
    request_body JSON,
    
    -- Timestamp
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices
    INDEX idx_nivel (nivel),
    INDEX idx_modulo (modulo),
    INDEX idx_timestamp (timestamp)
    
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================================================
-- TABELA: PERMISSOES_PERFIL
-- Mapeamento de permissões por perfil (configurável)
-- ============================================================================

CREATE TABLE IF NOT EXISTS usuarios.permissoes_perfil (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    role ENUM('ANALISTA', 'GESTOR', 'AUDITOR', 'ADMIN') NOT NULL,
    permissao VARCHAR(100) NOT NULL,             -- view:prinad, export:bacen, manage:users, etc.
    descricao VARCHAR(255),
    
    -- Controle
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices
    UNIQUE KEY unique_role_permissao (role, permissao),
    INDEX idx_role (role)
    
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================================================
-- DADOS INICIAIS - PERMISSÕES POR PERFIL
-- ============================================================================

-- Analista: Operações diárias
INSERT INTO usuarios.permissoes_perfil (role, permissao, descricao) VALUES
('ANALISTA', 'view:prinad', 'Visualizar módulo PRINAD'),
('ANALISTA', 'view:ecl', 'Visualizar módulo Perda Esperada'),
('ANALISTA', 'view:propensao', 'Visualizar módulo Propensão'),
('ANALISTA', 'classify:individual', 'Classificar cliente individual'),
('ANALISTA', 'classify:batch', 'Classificar lote de clientes'),
('ANALISTA', 'calculate:ecl', 'Calcular ECL');

-- Gestor: Analista + Exportações + Analytics
INSERT INTO usuarios.permissoes_perfil (role, permissao, descricao) VALUES
('GESTOR', 'view:prinad', 'Visualizar módulo PRINAD'),
('GESTOR', 'view:ecl', 'Visualizar módulo Perda Esperada'),
('GESTOR', 'view:propensao', 'Visualizar módulo Propensão'),
('GESTOR', 'classify:individual', 'Classificar cliente individual'),
('GESTOR', 'classify:batch', 'Classificar lote de clientes'),
('GESTOR', 'calculate:ecl', 'Calcular ECL'),
('GESTOR', 'view:dashboard', 'Visualizar dashboard executivo'),
('GESTOR', 'view:analytics', 'Visualizar analytics avançados'),
('GESTOR', 'export:pdf', 'Exportar relatórios em PDF'),
('GESTOR', 'export:csv', 'Exportar dados em CSV'),
('GESTOR', 'export:bacen', 'Exportar XML para BACEN'),
('GESTOR', 'generate:xml', 'Gerar arquivo Doc3040');

-- Auditor: Leitura completa + Logs + Relatórios de auditoria
INSERT INTO usuarios.permissoes_perfil (role, permissao, descricao) VALUES
('AUDITOR', 'view:prinad', 'Visualizar módulo PRINAD'),
('AUDITOR', 'view:ecl', 'Visualizar módulo Perda Esperada'),
('AUDITOR', 'view:propensao', 'Visualizar módulo Propensão'),
('AUDITOR', 'view:dashboard', 'Visualizar dashboard executivo'),
('AUDITOR', 'view:audit', 'Visualizar logs de auditoria'),
('AUDITOR', 'view:user_activity_logs', 'Visualizar logs de atividade de usuários'),
('AUDITOR', 'export:audit_reports', 'Exportar relatórios de auditoria'),
('AUDITOR', 'export:compliance_reports', 'Exportar relatórios de conformidade');

-- Admin: Acesso total
INSERT INTO usuarios.permissoes_perfil (role, permissao, descricao) VALUES
('ADMIN', '*', 'Acesso total ao sistema'),
('ADMIN', 'manage:users', 'Gerenciar usuários (CRUD)'),
('ADMIN', 'manage:permissions', 'Gerenciar permissões'),
('ADMIN', 'view:system_errors', 'Visualizar logs de erros do sistema'),
('ADMIN', 'manage:system_config', 'Gerenciar configurações do sistema');

-- ============================================================================
-- DADOS INICIAIS - USUÁRIOS DE TESTE
-- ============================================================================

INSERT INTO usuarios.usuarios (id, nome, email, matricula, login_windows, role, departamento, cargo) VALUES
(UUID(), 'Maria Silva', 'maria.silva@banco.local', 'A12345', 'maria.silva', 'ANALISTA', 'Crédito', 'Analista de Crédito Jr'),
(UUID(), 'João Santos', 'joao.santos@banco.local', 'G54321', 'joao.santos', 'GESTOR', 'Riscos', 'Gerente de Riscos'),
(UUID(), 'Ana Costa', 'ana.costa@banco.local', 'AU9999', 'ana.costa', 'AUDITOR', 'Auditoria Interna', 'Auditora Sênior'),
(UUID(), 'Carlos Admin', 'carlos.admin@banco.local', 'ADM001', 'carlos.admin', 'ADMIN', 'TI', 'Administrador de Sistemas');

-- ============================================================================
-- REABILITAR FOREIGN KEYS
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================

SELECT 'Esquema usuarios criado com sucesso!' AS status;
SELECT COUNT(*) AS total_permissoes FROM usuarios.permissoes_perfil;
SELECT COUNT(*) AS total_usuarios FROM usuarios.usuarios;
