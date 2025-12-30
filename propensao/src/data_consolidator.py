"""
Data Consolidator - Integrates 3040 credit portfolio and limits data.

This module reads monthly CSV files from:
- dados/bases_banco/3040/ - Credit portfolio data (Carteira de Crédito)
- dados/bases_banco/limites/ - Credit limits data

It consolidates them into a unified analytical base for propensity modeling.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import sys

# Add parent to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    PRODUTOS_CREDITO,
    DADOS_DIR,
    parse_month_from_filename,
    setup_logging
)

logger = setup_logging(__name__)


class DataConsolidator:
    """
    Consolidates 3040 portfolio data with limits data for propensity analysis.
    """
    
    # Column mappings for 3040 files
    COLUNAS_3040 = {
        'Ident. Cliente': 'cliente_id',
        'Linha de Crédito': 'linha_credito',
        'Modalidade Oper.': 'modalidade',
        'Saldo Devedor': 'saldo_devedor',
        'Valor Original Contr.': 'valor_original',
        'Dias de Atraso': 'dias_atraso',
        'Qtd. Parc. a Vencer': 'parcelas_vencer',
        'Qtd. Parc. Vencidas': 'parcelas_vencidas',
        'Valor Próxima Parcela': 'valor_parcela'
    }
    
    # Column mappings for limits files
    COLUNAS_LIMITES = {
        'Ident. Cliente': 'cliente_id',
        'Linha de Crédito': 'linha_credito',
        'Modalidade Oper.': 'modalidade',
        'Limite Disponível': 'limite_disponivel',
        'Li': 'limite_utilizado'  # Truncated in CSV
    }
    
    # Mapping from linha_credito to product
    MAPA_PRODUTOS = {
        'CONSIGNADO': 'consignado',
        'CONSIG': 'consignado',
        'BANPARACARD': 'banparacard',
        'CARTAO': 'cartao_credito',
        'CARTÃO': 'cartao_credito',
        'IMOBILIARIO': 'imobiliario',
        'IMOB': 'imobiliario',
        'VEICULO': 'cred_veiculo',
        'VEÍCULO': 'cred_veiculo',
        'ANTECIP': 'antecipacao_13_sal',
        '13': 'antecipacao_13_sal',
        'INVESTIMENTO': 'outros',
        'INVEST': 'outros',
        'RURAL': 'outros'
    }
    
    def __init__(self, dados_dir: Optional[Path] = None):
        """
        Initialize the data consolidator.
        
        Args:
            dados_dir: Path to dados directory
        """
        self.dados_dir = dados_dir or DADOS_DIR
        self.dir_3040 = self.dados_dir / "bases_banco" / "3040"
        self.dir_limites = self.dados_dir / "bases_banco" / "limites"
        
        logger.info(f"DataConsolidator initialized with dados_dir: {self.dados_dir}")
    
    def _mapear_produto(self, linha_credito: str) -> str:
        """Map linha_credito string to product name."""
        if pd.isna(linha_credito):
            return 'outros'
        
        linha_upper = str(linha_credito).upper()
        for key, produto in self.MAPA_PRODUTOS.items():
            if key in linha_upper:
                return produto
        return 'outros'
    
    def carregar_arquivo_3040(self, filepath: Path) -> pd.DataFrame:
        """
        Load a single 3040 file.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            DataFrame with standardized columns
        """
        logger.info(f"Loading 3040 file: {filepath.name}")
        
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, sep=';', encoding=encoding, low_memory=False)
                    break
                except UnicodeDecodeError:
                    continue
            
            # Rename columns
            df = df.rename(columns=self.COLUNAS_3040)
            
            # Parse month from filename
            mes_ref = parse_month_from_filename(filepath.name)
            df['mes_referencia'] = mes_ref
            
            # Map to product
            df['produto'] = df['linha_credito'].apply(self._mapear_produto)
            
            # Convert numeric columns
            for col in ['saldo_devedor', 'valor_original', 'dias_atraso', 'valor_parcela']:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(',', '.').str.replace(' ', ''),
                        errors='coerce'
                    ).fillna(0)
            
            logger.info(f"Loaded {len(df)} records from {filepath.name}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return pd.DataFrame()
    
    def carregar_arquivo_limites(self, filepath: Path) -> pd.DataFrame:
        """
        Load a single limits file.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            DataFrame with standardized columns
        """
        logger.info(f"Loading limits file: {filepath.name}")
        
        try:
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, sep=';', encoding=encoding, low_memory=False)
                    break
                except UnicodeDecodeError:
                    continue
            
            # Handle truncated column names
            col_map = {}
            for old_col in df.columns:
                for expected, new_name in self.COLUNAS_LIMITES.items():
                    if expected in old_col or old_col.startswith(expected[:5]):
                        col_map[old_col] = new_name
                        break
            
            df = df.rename(columns=col_map)
            
            # Parse month from filename
            mes_ref = parse_month_from_filename(filepath.name)
            df['mes_referencia'] = mes_ref
            
            # Map to product
            if 'linha_credito' in df.columns:
                df['produto'] = df['linha_credito'].apply(self._mapear_produto)
            
            # Convert numeric columns
            for col in ['limite_disponivel', 'limite_utilizado']:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col].astype(str).str.replace(',', '.').str.replace(' ', ''),
                        errors='coerce'
                    ).fillna(0)
            
            logger.info(f"Loaded {len(df)} records from {filepath.name}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return pd.DataFrame()
    
    def carregar_todos_3040(self) -> pd.DataFrame:
        """Load all 3040 files and concatenate."""
        files = list(self.dir_3040.glob("*.csv"))
        # Exclude auxiliary files
        files = [f for f in files if 'corrigidos' not in f.name.lower()]
        
        logger.info(f"Found {len(files)} 3040 files")
        
        dfs = []
        for f in sorted(files):
            df = self.carregar_arquivo_3040(f)
            if not df.empty:
                dfs.append(df)
        
        if dfs:
            result = pd.concat(dfs, ignore_index=True)
            logger.info(f"Total 3040 records: {len(result)}")
            return result
        return pd.DataFrame()
    
    def carregar_todos_limites(self) -> pd.DataFrame:
        """Load all limits files and concatenate."""
        files = list(self.dir_limites.glob("*.csv"))
        
        logger.info(f"Found {len(files)} limits files")
        
        dfs = []
        for f in sorted(files):
            df = self.carregar_arquivo_limites(f)
            if not df.empty:
                dfs.append(df)
        
        if dfs:
            result = pd.concat(dfs, ignore_index=True)
            logger.info(f"Total limits records: {len(result)}")
            return result
        return pd.DataFrame()
    
    def calcular_taxa_utilizacao(
        self, 
        df_limites: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate utilization rate per client/product/month.
        
        Returns:
            DataFrame with utilization rates
        """
        if df_limites.empty:
            return pd.DataFrame()
        
        # Calculate total limit and utilization
        df = df_limites.copy()
        df['limite_total'] = df['limite_disponivel'] + df.get('limite_utilizado', 0)
        
        # Utilization rate
        df['taxa_utilizacao'] = np.where(
            df['limite_total'] > 0,
            df.get('limite_utilizado', 0) / df['limite_total'],
            0
        )
        
        return df
    
    def consolidar_por_cliente(
        self,
        df_3040: pd.DataFrame,
        df_limites: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Consolidate data by client, creating features for propensity model.
        
        Args:
            df_3040: Credit portfolio data
            df_limites: Limits data
            
        Returns:
            Consolidated DataFrame with client-level features
        """
        logger.info("Consolidating data by client...")
        
        features = []
        
        # Get unique clients from both sources
        clients_3040 = set(df_3040['cliente_id'].unique()) if not df_3040.empty else set()
        clients_limites = set(df_limites['cliente_id'].unique()) if not df_limites.empty else set()
        all_clients = clients_3040.union(clients_limites)
        
        logger.info(f"Processing {len(all_clients)} unique clients")
        
        # For each product, calculate features
        for produto in PRODUTOS_CREDITO:
            if not df_limites.empty:
                # Filter limits for this product
                limites_prod = df_limites[df_limites['produto'] == produto]
                
                if not limites_prod.empty:
                    # Group by client
                    agg_limites = limites_prod.groupby('cliente_id').agg({
                        'limite_disponivel': ['mean', 'max', 'min', 'std'],
                        'limite_utilizado': ['mean', 'max', 'sum'] if 'limite_utilizado' in limites_prod.columns else ['count'],
                        'mes_referencia': 'nunique'
                    }).reset_index()
                    
                    # Flatten column names
                    agg_limites.columns = ['cliente_id'] + [
                        f"{produto}_{col[0]}_{col[1]}" 
                        for col in agg_limites.columns[1:]
                    ]
                    
                    features.append(agg_limites)
            
            if not df_3040.empty:
                # Filter 3040 for this product
                carteira_prod = df_3040[df_3040['produto'] == produto]
                
                if not carteira_prod.empty:
                    # Group by client
                    agg_carteira = carteira_prod.groupby('cliente_id').agg({
                        'saldo_devedor': ['sum', 'mean'],
                        'dias_atraso': ['max', 'mean'],
                        'valor_parcela': ['sum', 'mean'],
                        'mes_referencia': 'nunique'
                    }).reset_index()
                    
                    # Flatten column names
                    agg_carteira.columns = ['cliente_id'] + [
                        f"{produto}_3040_{col[0]}_{col[1]}" 
                        for col in agg_carteira.columns[1:]
                    ]
                    
                    features.append(agg_carteira)
        
        if not features:
            logger.warning("No features generated")
            return pd.DataFrame()
        
        # Merge all feature DataFrames
        result = features[0]
        for df in features[1:]:
            result = result.merge(df, on='cliente_id', how='outer')
        
        result = result.fillna(0)
        
        logger.info(f"Generated {len(result)} client records with {len(result.columns)} features")
        return result
    
    def calcular_utilizacao_trimestral(
        self,
        df_limites: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate quarterly utilization for each client/product.
        Used to identify clients for limit reduction.
        
        Returns:
            DataFrame with quarterly utilization flags
        """
        if df_limites.empty:
            return pd.DataFrame()
        
        df = df_limites.copy()
        
        # Extract year-quarter from mes_referencia
        df['ano_mes'] = pd.to_datetime(df['mes_referencia'] + '-01')
        df['trimestre'] = df['ano_mes'].dt.to_period('Q')
        
        # Calculate if there was any utilization in the quarter
        utilizacao_trim = df.groupby(['cliente_id', 'produto', 'trimestre']).agg({
            'limite_utilizado': 'max'
        }).reset_index()
        
        utilizacao_trim['utilizou_no_trimestre'] = utilizacao_trim['limite_utilizado'] > 0
        
        return utilizacao_trim
    
    def executar_consolidacao(
        self, 
        salvar: bool = True,
        output_path: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Run the full consolidation pipeline.
        
        Args:
            salvar: Whether to save output to CSV
            output_path: Custom output path
            
        Returns:
            Consolidated DataFrame
        """
        logger.info("Starting data consolidation...")
        
        # Load all data
        df_3040 = self.carregar_todos_3040()
        df_limites = self.carregar_todos_limites()
        
        # Calculate utilization
        df_limites = self.calcular_taxa_utilizacao(df_limites)
        
        # Consolidate by client
        df_consolidated = self.consolidar_por_cliente(df_3040, df_limites)
        
        # Calculate quarterly utilization
        df_trimestral = self.calcular_utilizacao_trimestral(df_limites)
        
        if salvar and not df_consolidated.empty:
            output_dir = output_path or (self.dados_dir / "consolidado")
            output_dir.mkdir(exist_ok=True)
            
            # Save consolidated
            out_file = output_dir / "base_consolidada.csv"
            df_consolidated.to_csv(out_file, index=False, sep=';')
            logger.info(f"Saved consolidated data to {out_file}")
            
            # Save quarterly utilization
            if not df_trimestral.empty:
                out_trim = output_dir / "utilizacao_trimestral.csv"
                df_trimestral.to_csv(out_trim, index=False, sep=';')
                logger.info(f"Saved quarterly utilization to {out_trim}")
        
        return df_consolidated


def consolidar_dados(salvar: bool = True) -> pd.DataFrame:
    """
    Convenience function to run consolidation.
    
    Args:
        salvar: Whether to save output
        
    Returns:
        Consolidated DataFrame
    """
    consolidator = DataConsolidator()
    return consolidator.executar_consolidacao(salvar=salvar)


if __name__ == "__main__":
    # Run consolidation when executed directly
    df = consolidar_dados()
    print(f"\nConsolidation complete. Shape: {df.shape}")
    if not df.empty:
        print(f"Columns: {list(df.columns)}")
