# -*- coding: utf-8 -*-
"""
Testes de Validação de Scripts DDL
==================================

Valida a sintaxe e estrutura dos scripts DDL para o banco de dados MySQL.

Autor: Sistema ECL
Data: Janeiro 2026
"""

import pytest
import os
import re
from pathlib import Path


# Caminho base dos scripts DDL
BASE_PATH = Path(__file__).parent.parent


class TestDDLSyntax:
    """Testes de sintaxe SQL dos scripts DDL."""
    
    @pytest.fixture
    def esquema_completo(self) -> str:
        """Carrega o script esquema_completo.sql."""
        sql_path = BASE_PATH / "esquema_completo.sql"
        if sql_path.exists():
            return sql_path.read_text(encoding="utf-8")
        return ""
    
    def test_esquema_completo_exists(self):
        """Verifica se o arquivo esquema_completo.sql existe."""
        sql_path = BASE_PATH / "esquema_completo.sql"
        assert sql_path.exists(), "Arquivo esquema_completo.sql não encontrado"
    
    def test_esquema_completo_not_empty(self, esquema_completo):
        """Verifica se o arquivo não está vazio."""
        assert len(esquema_completo) > 0, "Arquivo esquema_completo.sql está vazio"
    
    def test_create_schema_statements(self, esquema_completo):
        """Verifica se os 5 esquemas são criados."""
        schemas_esperados = ["ecl", "estagio", "writeoff", "auditoria", "usuarios"]
        
        for schema in schemas_esperados:
            pattern = rf"CREATE\s+SCHEMA\s+IF\s+NOT\s+EXISTS\s+{schema}"
            assert re.search(pattern, esquema_completo, re.IGNORECASE), \
                f"Schema '{schema}' não encontrado no script"
    
    def test_create_table_statements(self, esquema_completo):
        """Verifica se todas as tabelas são criadas."""
        tabelas_esperadas = [
            "ecl.ecl_resultados",
            "ecl.ecl_cenarios",
            "ecl.ecl_parametros_fl",
            "ecl.ecl_grupos_homogeneos",
            "estagio.estagio_historico",
            "estagio.estagio_cura",
            "estagio.estagio_triggers",
            "writeoff.writeoff_baixas",
            "writeoff.writeoff_recuperacoes",
            "auditoria.auditoria_envios_bacen",
            "auditoria.auditoria_validacoes"
        ]
        
        for tabela in tabelas_esperadas:
            pattern = rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+{tabela.replace('.', r'\.')}"
            assert re.search(pattern, esquema_completo, re.IGNORECASE), \
                f"Tabela '{tabela}' não encontrada no script"
    
    def test_foreign_keys_defined(self, esquema_completo):
        """Verifica se as foreign keys estão definidas."""
        # FK de writeoff_recuperacoes para writeoff_baixas
        assert "CONSTRAINT fk_baixa FOREIGN KEY" in esquema_completo, \
            "FK fk_baixa não encontrada"
        
        # FK de auditoria_validacoes para auditoria_envios_bacen
        assert "CONSTRAINT fk_envio FOREIGN KEY" in esquema_completo, \
            "FK fk_envio não encontrada"
    
    def test_indexes_defined(self, esquema_completo):
        """Verifica se os índices importantes estão definidos."""
        indices = [
            "idx_contrato",
            "idx_cliente",
            "idx_data_calculo",
            "idx_stage",
            "idx_grupo"
        ]
        
        for idx in indices:
            assert idx in esquema_completo, f"Índice '{idx}' não encontrado"
    
    def test_engine_innodb(self, esquema_completo):
        """Verifica se o engine InnoDB é utilizado."""
        count = esquema_completo.count("ENGINE = InnoDB")
        assert count >= 11, f"Esperado 11+ tabelas com InnoDB, encontrado {count}"
    
    def test_charset_utf8mb4(self, esquema_completo):
        """Verifica se o charset utf8mb4 é utilizado."""
        count = esquema_completo.count("utf8mb4")
        assert count >= 11, f"Esperado utf8mb4 em 11+ tabelas, encontrado {count}"
    
    def test_check_constraints(self, esquema_completo):
        """Verifica se os CHECK constraints estão definidos."""
        # Stage deve ser 1, 2 ou 3
        assert "CHECK (stage IN (1, 2, 3))" in esquema_completo, \
            "CHECK constraint para stage não encontrado"
        
        # Peso deve estar entre 0 e 1
        assert "peso >= 0" in esquema_completo.lower(), \
            "CHECK constraint para peso não encontrado"


class TestDDLTableStructure:
    """Testes de estrutura das tabelas."""
    
    @pytest.fixture
    def esquema_completo(self) -> str:
        """Carrega o script esquema_completo.sql."""
        sql_path = BASE_PATH / "esquema_completo.sql"
        if sql_path.exists():
            return sql_path.read_text(encoding="utf-8")
        return ""
    
    def test_ecl_resultados_columns(self, esquema_completo):
        """Verifica colunas obrigatórias da tabela ecl_resultados."""
        colunas_obrigatorias = [
            "contrato_id",
            "cliente_id",
            "prinad_score",
            "rating",
            "stage",
            "pd_base",
            "pd_12m",
            "pd_lifetime",
            "lgd_final",
            "ead",
            "ecl_final"
        ]
        
        for coluna in colunas_obrigatorias:
            assert coluna in esquema_completo, \
                f"Coluna '{coluna}' não encontrada em ecl_resultados"
    
    def test_ecl_cenarios_columns(self, esquema_completo):
        """Verifica colunas obrigatórias da tabela ecl_cenarios."""
        colunas = ["tipo", "peso", "spread_pd", "spread_lgd"]
        
        for coluna in colunas:
            assert coluna in esquema_completo, \
                f"Coluna '{coluna}' não encontrada em ecl_cenarios"
    
    def test_writeoff_baixas_columns(self, esquema_completo):
        """Verifica colunas obrigatórias da tabela writeoff_baixas."""
        colunas = [
            "contrato_id",
            "valor_baixado",
            "motivo",
            "data_baixa",
            "status_recuperacao",
            "total_recuperado",
            "taxa_recuperacao"
        ]
        
        for coluna in colunas:
            assert coluna in esquema_completo, \
                f"Coluna '{coluna}' não encontrada em writeoff_baixas"
    
    def test_estagio_cura_columns(self, esquema_completo):
        """Verifica colunas da tabela estagio_cura para sistema de cura Art. 41."""
        colunas = [
            "meses_em_observacao",
            "meses_necessarios",
            "pd_na_entrada",
            "pd_atual",
            "percentual_amortizacao",
            "elegivel_cura",
            "cura_aplicada"
        ]
        
        for coluna in colunas:
            assert coluna in esquema_completo, \
                f"Coluna '{coluna}' não encontrada em estagio_cura"
    
    def test_auditoria_envios_columns(self, esquema_completo):
        """Verifica colunas da tabela auditoria_envios_bacen."""
        colunas = [
            "codigo_envio",
            "arquivo_nome",
            "data_base",
            "cnpj_instituicao",
            "total_ecl",
            "status",
            "protocolo_bacen"
        ]
        
        for coluna in colunas:
            assert coluna in esquema_completo, \
                f"Coluna '{coluna}' não encontrada em auditoria_envios_bacen"


class TestDDLDirectoryStructure:
    """Testes de estrutura de diretórios."""
    
    def test_ecl_directory_exists(self):
        """Verifica se o diretório ecl/ existe."""
        dir_path = BASE_PATH / "ecl"
        assert dir_path.exists() and dir_path.is_dir(), "Diretório ecl/ não encontrado"
    
    def test_estagio_directory_exists(self):
        """Verifica se o diretório estagio/ existe."""
        dir_path = BASE_PATH / "estagio"
        assert dir_path.exists() and dir_path.is_dir(), "Diretório estagio/ não encontrado"
    
    def test_writeoff_directory_exists(self):
        """Verifica se o diretório writeoff/ existe."""
        dir_path = BASE_PATH / "writeoff"
        assert dir_path.exists() and dir_path.is_dir(), "Diretório writeoff/ não encontrado"
    
    def test_auditoria_directory_exists(self):
        """Verifica se o diretório auditoria/ existe."""
        dir_path = BASE_PATH / "auditoria"
        assert dir_path.exists() and dir_path.is_dir(), "Diretório auditoria/ não encontrado"
    
    def test_usuarios_directory_exists(self):
        """Verifica se o diretório usuarios/ existe."""
        dir_path = BASE_PATH / "usuarios"
        assert dir_path.exists() and dir_path.is_dir(), "Diretório usuarios/ não encontrado"


class TestDDLCompliance:
    """Testes de conformidade regulatória nos scripts DDL."""
    
    @pytest.fixture
    def esquema_completo(self) -> str:
        """Carrega o script esquema_completo.sql."""
        sql_path = BASE_PATH / "esquema_completo.sql"
        if sql_path.exists():
            return sql_path.read_text(encoding="utf-8")
        return ""
    
    def test_ifrs9_stage_values(self, esquema_completo):
        """Verifica se os valores de stage IFRS 9 são validados (1, 2, 3)."""
        assert "stage IN (1, 2, 3)" in esquema_completo, \
            "Validação de stage IFRS 9 não encontrada"
    
    def test_cenario_types_enum(self, esquema_completo):
        """Verifica se os tipos de cenário incluem otimista, base, pessimista."""
        cenarios = ["otimista", "base", "pessimista"]
        for cenario in cenarios:
            assert cenario in esquema_completo, \
                f"Tipo de cenário '{cenario}' não encontrado"
    
    def test_motivo_baixa_enum(self, esquema_completo):
        """Verifica se os motivos de baixa estão definidos."""
        motivos = [
            "inadimplencia_prolongada",
            "falencia_rj",
            "obito",
            "prescricao",
            "acordo_judicial",
            "cessao"
        ]
        for motivo in motivos:
            assert motivo in esquema_completo, \
                f"Motivo de baixa '{motivo}' não encontrado"
    
    def test_writeoff_5_year_tracking(self, esquema_completo):
        """Verifica se o acompanhamento de 5 anos está implementado."""
        assert "INTERVAL 5 YEAR" in esquema_completo, \
            "Acompanhamento de 5 anos (Art. 49 CMN 4966) não implementado"
    
    def test_horizonte_ecl_values(self, esquema_completo):
        """Verifica se os horizontes ECL são validados (12m, lifetime)."""
        assert "12m" in esquema_completo and "lifetime" in esquema_completo, \
            "Horizontes ECL (12m, lifetime) não encontrados"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
