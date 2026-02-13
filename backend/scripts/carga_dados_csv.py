# -*- coding: utf-8 -*-
"""
Script de Carga de Dados (ETL)
Lê CSVs da pasta /dados e carrega no PostgreSQL (dbrisco)
"""

import sys
import os
import pandas as pd
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Adicionar raiz do backend ao path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

from agente.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_engine():
    config = get_config()
    # URL Encode user and password to handle special characters
    user = quote_plus(config.database.user)
    password = quote_plus(config.database.password)
    
    # Usando psycopg2 para PostgreSQL
    url = f"postgresql+psycopg2://{user}:{password}@{config.database.host}:{config.database.port}/{config.database.database}"
    return create_engine(url)

def carregar_clientes(engine, csv_path):
    logger.info(f"Carregando clientes de {csv_path}...")
    try:
        # Ler CSV (ponto e vírgula)
        df = pd.read_csv(csv_path, sep=';')
        
        # Limpar nomes de colunas (caixa baixa)
        df.columns = [c.lower() for c in df.columns]
        
        # Inserir no banco (replace para recriar tabela)
        df.to_sql('clientes', engine, if_exists='replace', index=False)
        logger.info(f"✅ Tabela 'clientes' carregada com {len(df)} registros.")
    except Exception as e:
        logger.error(f"Erro ao carregar clientes: {e}")

def carregar_scr(engine, csv_path):
    logger.info(f"Carregando dados SCR de {csv_path}...")
    try:
        # Ler CSV (vírgula)
        df = pd.read_csv(csv_path, sep=',')
        
        # Limpar nomes de colunas
        df.columns = [c.lower() for c in df.columns]
        
        # Inserir no banco
        df.to_sql('scr_dados', engine, if_exists='replace', index=False)
        logger.info(f"✅ Tabela 'scr_dados' carregada com {len(df)} registros.")
    except Exception as e:
        logger.error(f"Erro ao carregar SCR: {e}")

def main():
    logger.info("Iniciando carga de dados no PostgreSQL...")
    
    # Caminho dos dados
    DADOS_DIR = BACKEND_DIR.parent / "dados"
    
    if not DADOS_DIR.exists():
        logger.error(f"Diretório de dados não encontrado: {DADOS_DIR}")
        return

    try:
        engine = get_engine()
        # Testar conexão
        with engine.connect() as conn:
            logger.info("Conexão com banco de dados PostgreSQL estabelecida com sucesso.")
    except Exception as e:
        logger.error(f"Falha na conexão com banco: {e}")
        return
    
    # 1. Base Clientes (Principal)
    path_clientes = DADOS_DIR / "base_clientes.csv"
    if path_clientes.exists():
        carregar_clientes(engine, path_clientes)
    else:
        logger.warning("base_clientes.csv não encontrado")

    # 2. Base SCR Mock
    path_scr = DADOS_DIR / "scr_mock_data.csv"
    if path_scr.exists():
        carregar_scr(engine, path_scr)
    else:
        logger.warning("scr_mock_data.csv não encontrado")

    logger.info("Processo finalizado.")

if __name__ == "__main__":
    main()
