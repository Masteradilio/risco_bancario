"""
Data Consolidator - Unified Data Pipeline for PROLIMITE System.

Creates a single consolidated base mixing real and synthetic data
for all three models: PRINAD, PROPENSÃO, and PROLIMITE.

Pipeline:
1. Load real cadastral data (base_cadastro.csv)
2. Load real limits data (12 months)
3. Load real 3040 portfolio data (12 months)
4. Generate synthetic data for missing fields
5. Output unified base (base_clientes.csv)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import sys
import warnings

warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    PRODUTOS_CREDITO,
    PRODUTOS_PF,
    DADOS_DIR,
    COMPROMETIMENTO_POR_PRODUTO,
    COMPROMETIMENTO_MAXIMO_RENDA,
    DISTRIBUICAO_PRODUTOS,
    PRODUTOS_AUTOMATICOS,
    PRODUTOS_SOB_DEMANDA,
    GARANTIA_POR_PRODUTO,
    LIMITE_MAXIMO_MULTIPLO,
    LGD_POR_PRODUTO,
    CCF_POR_PRODUTO,
    PROPENSAO_CLASSIFICACAO,
    FEATURES_PROPENSAO_TOP15,
    parse_month_from_filename,
    setup_logging,
    get_rating_from_prinad,
    calcular_pd_por_rating,
    calcular_ead,
    calcular_limite_global_fixo,
    get_stage_from_criteria
)

logger = setup_logging(__name__)

# Random seed for reproducibility
np.random.seed(42)


@dataclass
class ConsolidationConfig:
    """Configuration for data consolidation."""
    encoding: str = 'latin-1'
    sep: str = ';'
    target_clients: int = 300000  # Target number of clients
    generate_synthetic_products: bool = True
    synthetic_noise_level: float = 0.15  # 15% noise


class ProductMapper:
    """Maps real product names to system product names."""
    
    MAPPING = {
        # BANPARACARD variations
        'BANPARACARD': 'banparacard',
        'BANPARACARD-PARCELADO': 'banparacard',
        'BANPARACARD-SAQUE': 'banparacard',
        
        # CHEQUE ESPECIAL
        'CHEQUE ESPECIAL': 'cheque_especial',
        'CHEQUE ESPECIAL PF': 'cheque_especial',
        'BANPARÁ CHEQUE': 'cheque_especial',
        
        # CARTÃO
        'CARTÃO DE CRÉDITO': 'cartao_credito_rotativo',
        'CARTÃO DE CRÉDITO - PARCELADO': 'cartao_credito_parcelado',
        
        # CONSIGNADO
        'CONSIG': 'consignado',
        'CONFISSAO PESSOA FÍSICA': 'consignado',
        'CONFISSÃO': 'consignado',
        'BANPARÁ COMUNIDADE': 'consignado',
        'NOVO PARCELADO': 'consignado',
        
        # ANTECIPAÇÃO / SAZONAL
        'ANTECIPAÇÃO': 'credito_sazonal',
        'ANTECIPAÇÃO IRPF': 'credito_sazonal',
        'ANTECIPAÃÃO IRPF': 'credito_sazonal',
        '13': 'credito_sazonal',
        
        # ADIANTAMENTO (cheque especial)
        'ADIANTAMENTO A DEPOSITANTE PF': 'cheque_especial',
        'ADIANTAMENTO A DEPOSITANTE PJ': 'cheque_especial',
        
        # IMOBILIÁRIO
        'IMOBILIÁRIO': 'imobiliario',
        'IMOB': 'imobiliario',
        
        # VEÍCULO
        'VEÍCULO': 'cred_veiculo',
        'VEIC': 'cred_veiculo',
        
        # ENERGIA SOLAR
        'ENERGIA SOLAR': 'energia_solar',
        'SOLAR': 'energia_solar',
    }
    
    @classmethod
    def map_product(cls, linha_credito: str) -> str:
        """Map a credit line to a system product."""
        if pd.isna(linha_credito):
            return 'consignado'  # Default
        
        linha_upper = str(linha_credito).upper()
        
        # Try exact prefix matches first
        for pattern, produto in cls.MAPPING.items():
            if pattern in linha_upper:
                return produto
        
        # Default to consignado if unknown
        return 'consignado'


class SyntheticDataGenerator:
    """Generates synthetic data with realistic noise and distributions."""
    
    def __init__(self, config: ConsolidationConfig):
        self.config = config
        self.noise = config.synthetic_noise_level
    
    def add_noise(self, value: float, noise_pct: float = None) -> float:
        """Add Gaussian noise to a value."""
        if noise_pct is None:
            noise_pct = self.noise
        return value * (1 + np.random.normal(0, noise_pct))
    
    def generate_scr_data(self, n: int, max_atraso_real: np.ndarray = None) -> pd.DataFrame:
        """Generate synthetic SCR (Credit Bureau) data."""
        logger.info(f"Generating synthetic SCR data for {n} records")
        
        # SCR Score (300-900, normal distribution centered at 600)
        scr_score = np.clip(
            np.random.normal(600, 150, n) + np.random.normal(0, 50, n),
            300, 900
        ).astype(int)
        
        # Days in arrears (exponential distribution, correlated with real if available)
        if max_atraso_real is not None and len(max_atraso_real) == n:
            # Correlate with real data + noise
            base_atraso = max_atraso_real * 0.7 + np.random.exponential(5, n)
        else:
            base_atraso = np.random.exponential(10, n)
        
        scr_dias_atraso = np.clip(base_atraso + np.random.normal(0, 2, n), 0, 365).astype(int)
        
        # Has loss record (correlated with score)
        scr_tem_prejuizo = (scr_score < 450) & (np.random.random(n) < 0.3)
        
        return pd.DataFrame({
            'scr_score_risco': scr_score,
            'scr_dias_atraso': scr_dias_atraso,
            'scr_tem_prejuizo': scr_tem_prejuizo.astype(int)
        })
    
    def generate_guarantee_data(
        self, 
        produtos: pd.Series, 
        limites: pd.Series
    ) -> pd.DataFrame:
        """Generate synthetic guarantee data based on product type."""
        n = len(produtos)
        
        tipo_garantia = produtos.map(GARANTIA_POR_PRODUTO).fillna('nenhuma')
        
        # Generate guarantee values based on type
        valor_garantia = np.zeros(n)
        ltv = np.zeros(n)
        
        for i, (tipo, limite) in enumerate(zip(tipo_garantia, limites)):
            if tipo == 'nenhuma':
                valor_garantia[i] = 0
                ltv[i] = 1.0  # No collateral = 100% LTV
            elif tipo in ['imovel_residencial', 'consignacao']:
                # Real estate: guarantee > limit (LTV 60-80%)
                ltv[i] = np.random.uniform(0.60, 0.80)
                valor_garantia[i] = limite / ltv[i] * self.add_noise(1.0, 0.10)
            elif tipo in ['veiculo', 'equipamento']:
                # Vehicle/equipment: guarantee ~= limit (LTV 80-100%)
                ltv[i] = np.random.uniform(0.80, 1.0)
                valor_garantia[i] = limite / ltv[i] * self.add_noise(1.0, 0.15)
            else:
                valor_garantia[i] = 0
                ltv[i] = 1.0
        
        return pd.DataFrame({
            'tipo_garantia': tipo_garantia,
            'valor_garantia': np.maximum(0, valor_garantia),
            'ltv': np.clip(ltv, 0, 1)
        })
    
    def generate_utilization_history(self, n: int) -> pd.DataFrame:
        """Generate synthetic utilization history."""
        # Average utilization over 12 months (0-1)
        utilizacao_media = np.clip(
            np.random.beta(2, 3, n),  # Skewed toward lower utilization
            0, 1
        )
        
        # Quarters without use (0-4)
        # Lower utilization = more quarters without use
        trimestres_sem_uso = np.where(
            utilizacao_media < 0.1,
            np.random.choice([1, 2, 3, 4], n, p=[0.3, 0.3, 0.25, 0.15]),
            np.random.choice([0, 1, 2], n, p=[0.7, 0.2, 0.1])
        )
        
        return pd.DataFrame({
            'utilizacao_media_12m': utilizacao_media,
            'trimestres_sem_uso': trimestres_sem_uso
        })
    
    def generate_products_for_clients(
        self, 
        n_clients: int, 
        existing_products: Dict[str, List[str]] = None
    ) -> pd.DataFrame:
        """Generate product assignments for clients."""
        logger.info(f"Generating product assignments for {n_clients} clients")
        
        records = []
        dist = DISTRIBUICAO_PRODUTOS
        probs = dist['probabilidade']
        
        for i in range(n_clients):
            # Determine number of products (weighted random)
            n_produtos = np.random.choice(
                [1, 2, 3, 4, 5],
                p=[0.10, 0.25, 0.40, 0.20, 0.05]
            )
            
            # Start with most common products
            client_products = []
            
            # Consignado is almost always present
            if np.random.random() < probs['consignado']:
                client_products.append('consignado')
            
            # Add other products based on probability
            for produto in ['banparacard', 'cartao_credito_rotativo', 
                           'cartao_credito_parcelado', 'imobiliario',
                           'credito_sazonal', 'energia_solar', 
                           'cred_veiculo', 'cheque_especial']:
                if len(client_products) >= n_produtos:
                    break
                if np.random.random() < probs.get(produto, 0.05):
                    client_products.append(produto)
            
            # Ensure at least one product
            if not client_products:
                client_products = ['consignado']
            
            for produto in client_products:
                records.append({
                    'client_idx': i,
                    'produto': produto
                })
        
        return pd.DataFrame(records)
    
    def generate_limits(
        self, 
        renda_bruta: float, 
        produto: str
    ) -> Tuple[float, float, float]:
        """Generate realistic limits for a product based on income."""
        multiplo = LIMITE_MAXIMO_MULTIPLO.get(produto, 5)
        
        # Limit total based on income and multiplier
        limite_max = renda_bruta * multiplo
        
        # Apply some randomness (50-100% of max)
        limite_total = limite_max * np.random.uniform(0.5, 1.0)
        
        # Utilization rate varies by product
        if produto in ['consignado', 'imobiliario']:
            # Higher utilization for loans
            taxa_uso = np.random.beta(3, 2)  # Skewed high
        elif produto in ['cheque_especial', 'cartao_credito_rotativo']:
            # Lower typical utilization
            taxa_uso = np.random.beta(1.5, 4)  # Skewed low
        else:
            taxa_uso = np.random.beta(2, 3)  # Balanced
        
        limite_utilizado = limite_total * taxa_uso
        limite_disponivel = limite_total - limite_utilizado
        
        return limite_total, limite_utilizado, limite_disponivel
    
    def generate_installments(
        self, 
        limite_utilizado: float, 
        produto: str,
        renda_bruta: float
    ) -> float:
        """Generate realistic monthly installment."""
        config = COMPROMETIMENTO_POR_PRODUTO.get(produto, {})
        limite_comp = config.get('limite_comprometimento', 0.30)
        
        if limite_comp is None:
            # Cartão/rotativo - no fixed installment
            return 0.0
        
        # Parcela based on limit used and product term
        prazo = PRODUTOS_PF.get(produto, {}).get('prazo_maximo', 48)
        
        # Monthly payment = utilized limit / average term
        termo_medio = prazo * np.random.uniform(0.3, 0.7)
        parcela = limite_utilizado / max(1, termo_medio)
        
        # Cap at product's income limit
        max_parcela = renda_bruta * limite_comp
        
        return min(parcela, max_parcela) * self.add_noise(1.0, 0.10)
    
    def generate_ecl_propensity_data(
        self, 
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate ECL and Propensity fields for BACEN 4966 compliance.
        
        Generates:
        - PRINAD_SCORE (heuristic based on SCR and arrears)
        - RATING (from PRINAD)
        - pd_12m, pd_lifetime (calibrated PD)
        - stage (IFRS 9: 1, 2, or 3)
        - lgd (from product)
        - ead (with CCF)
        - ecl (PD × LGD × EAD based on stage)
        - propensao_score (0-100)
        - propensao_classificacao (ALTA/MEDIA/BAIXA)
        - limite_global (based on income)
        
        Args:
            df: DataFrame with client data
            
        Returns:
            DataFrame with ECL and propensity columns added
        """
        logger.info(f"Generating ECL and Propensity data for {len(df)} records...")
        n = len(df)
        
        # -------------------------------------------------------------------
        # 1. Generate PRINAD (heuristic based on available data)
        # -------------------------------------------------------------------
        prinad_scores = np.zeros(n)
        
        for i in range(n):
            base_score = 20.0  # Base score (low risk)
            
            # SCR score impact
            scr_score = df.iloc[i].get('scr_score_risco', 600)
            if scr_score < 400:
                base_score += 40
            elif scr_score < 500:
                base_score += 25
            elif scr_score < 600:
                base_score += 10
            elif scr_score > 700:
                base_score -= 10
            
            # Arrears impact
            dias_atraso = df.iloc[i].get('scr_dias_atraso', 0)
            if dias_atraso > 90:
                base_score += 50
            elif dias_atraso > 60:
                base_score += 30
            elif dias_atraso > 30:
                base_score += 15
            elif dias_atraso > 15:
                base_score += 5
            
            # Commitment impact
            comprometimento = df.iloc[i].get('comprometimento_renda', 0.5)
            if comprometimento > 0.8:
                base_score += 15
            elif comprometimento > 0.7:
                base_score += 8
            
            # Prejudice impact
            if df.iloc[i].get('scr_tem_prejuizo', 0) == 1:
                base_score += 30
            
            # Add noise
            base_score += np.random.normal(0, 3)
            prinad_scores[i] = np.clip(base_score, 0.5, 100)
        
        df['PRINAD_SCORE'] = prinad_scores
        
        # -------------------------------------------------------------------
        # 2. Calculate Rating from PRINAD
        # -------------------------------------------------------------------
        df['RATING'] = df['PRINAD_SCORE'].apply(get_rating_from_prinad)
        
        # -------------------------------------------------------------------
        # 3. Calculate calibrated PD (12m and lifetime)
        # -------------------------------------------------------------------
        pd_results = df['PRINAD_SCORE'].apply(calcular_pd_por_rating)
        df['pd_12m'] = pd_results.apply(lambda x: x['pd_12m'])
        df['pd_lifetime'] = pd_results.apply(lambda x: x['pd_lifetime'])
        
        # -------------------------------------------------------------------
        # 4. Determine Stage based on criteria
        # -------------------------------------------------------------------
        df['dias_atraso'] = df.get('scr_dias_atraso', pd.Series(np.zeros(n))).fillna(0).astype(int)
        
        def get_stage(row):
            result = get_stage_from_criteria(
                dias_atraso=int(row.get('dias_atraso', 0)),
                rating_atual=row.get('RATING', 'A1')
            )
            return result['stage']
        
        df['stage'] = df.apply(get_stage, axis=1)
        
        # -------------------------------------------------------------------
        # 5. Calculate LGD per product
        # -------------------------------------------------------------------
        df['lgd'] = df['produto'].map(LGD_POR_PRODUTO).fillna(0.45)
        
        # Adjust LGD for Stage 3 (max LGD = 1.5x)
        df['lgd'] = np.where(
            df['stage'] == 3,
            np.minimum(1.0, df['lgd'] * 1.5),
            df['lgd']
        )
        
        # -------------------------------------------------------------------
        # 6. Calculate EAD with CCF
        # -------------------------------------------------------------------
        df['ccf'] = df['produto'].map(CCF_POR_PRODUTO).fillna(0.75)
        
        limite_total = df['limite_total'].fillna(0)
        saldo_utilizado = df['limite_utilizado'].fillna(0)
        limite_disponivel = np.maximum(0, limite_total - saldo_utilizado)
        
        df['ead'] = saldo_utilizado + (limite_disponivel * df['ccf'])
        
        # -------------------------------------------------------------------
        # 7. Calculate ECL based on Stage
        # -------------------------------------------------------------------
        # Stage 1: ECL = pd_12m × LGD × EAD
        # Stage 2/3: ECL = pd_lifetime × LGD × EAD
        df['ecl'] = np.where(
            df['stage'] == 1,
            df['pd_12m'] * df['lgd'] * df['ead'],
            df['pd_lifetime'] * df['lgd'] * df['ead']
        )
        
        df['ecl_horizonte'] = np.where(df['stage'] == 1, '12_meses', 'lifetime')
        
        # -------------------------------------------------------------------
        # 8. Generate Propensity Score
        # -------------------------------------------------------------------
        propensao_scores = np.zeros(n)
        
        for i in range(n):
            base_prop = 50.0
            
            # PRINAD impact (lower = higher propensity)
            prinad = df.iloc[i]['PRINAD_SCORE']
            if prinad < 20:
                base_prop += 25
            elif prinad < 40:
                base_prop += 15
            elif prinad < 60:
                base_prop += 5
            elif prinad > 80:
                base_prop -= 30
            
            # Utilization impact
            utilizacao = df.iloc[i].get('taxa_utilizacao', 0.5)
            if utilizacao > 0.7:
                base_prop += 15
            elif utilizacao > 0.3:
                base_prop += 10
            elif utilizacao < 0.1:
                base_prop -= 20
            
            # Income impact
            renda = df.iloc[i].get('RENDA_BRUTA', 5000)
            if renda > 15000:
                base_prop += 10
            elif renda > 8000:
                base_prop += 5
            elif renda < 3000:
                base_prop -= 10
            
            # Relationship time
            tempo = df.iloc[i].get('TEMPO_RELAC', 12)
            if tempo > 60:
                base_prop += 10
            elif tempo > 24:
                base_prop += 5
            
            # Add noise
            base_prop += np.random.normal(0, 5)
            propensao_scores[i] = np.clip(base_prop, 0, 100)
        
        df['propensao_score'] = propensao_scores
        
        # -------------------------------------------------------------------
        # 9. Classify Propensity
        # -------------------------------------------------------------------
        def classify_propensity(score):
            for classe, bounds in PROPENSAO_CLASSIFICACAO.items():
                if bounds['min'] <= score <= bounds['max']:
                    return classe
            return 'MEDIA'
        
        df['propensao_classificacao'] = df['propensao_score'].apply(classify_propensity)
        
        # -------------------------------------------------------------------
        # 10. Calculate Limite Global per client
        # -------------------------------------------------------------------
        def calc_limite_global(renda):
            if pd.isna(renda) or renda <= 0:
                return 0
            result = calcular_limite_global_fixo(renda)
            return result['limite_global']
        
        # Get unique clients for limite_global (avoid recalculating)
        unique_clients = df[['CLIT', 'RENDA_BRUTA']].drop_duplicates()
        unique_clients['limite_global'] = unique_clients['RENDA_BRUTA'].apply(calc_limite_global)
        
        df = df.merge(
            unique_clients[['CLIT', 'limite_global']], 
            on='CLIT', 
            how='left'
        )
        
        logger.info(f"ECL/Propensity data generated:")
        logger.info(f"  Stage distribution: {df['stage'].value_counts().to_dict()}")
        logger.info(f"  Total ECL: R$ {df['ecl'].sum():,.2f}")
        logger.info(f"  Propensity classification: {df['propensao_classificacao'].value_counts().to_dict()}")
        
        return df


class UnifiedDataConsolidator:
    """
    Main consolidator that creates the unified base for all models.
    """
    
    def __init__(
        self, 
        dados_dir: Optional[Path] = None,
        config: Optional[ConsolidationConfig] = None
    ):
        self.dados_dir = Path(dados_dir) if dados_dir else DADOS_DIR
        self.config = config or ConsolidationConfig()
        self.generator = SyntheticDataGenerator(self.config)
        self.mapper = ProductMapper()
        
        logger.info(f"UnifiedDataConsolidator initialized")
        logger.info(f"Data directory: {self.dados_dir}")
    
    def load_cadastro(self) -> pd.DataFrame:
        """Load and process cadastral data."""
        cadastro_path = self.dados_dir / 'base_cadastro.csv'
        logger.info(f"Loading cadastro from {cadastro_path}")
        
        df = pd.read_csv(
            cadastro_path,
            sep=self.config.sep,
            encoding=self.config.encoding
        )
        
        # Remove duplicates, keep first occurrence
        df = df.drop_duplicates(subset=['CLIT'], keep='first')
        
        logger.info(f"Loaded {len(df)} unique clients from cadastro")
        return df
    
    def load_limits(self, months: int = 12) -> pd.DataFrame:
        """Load limits data from multiple months."""
        limits_dir = self.dados_dir / 'bases_banco' / 'limites'
        logger.info(f"Loading limits from {limits_dir}")
        
        all_limits = []
        
        for file_path in sorted(limits_dir.glob('limites_*.csv'))[:months]:
            try:
                df = pd.read_csv(
                    file_path,
                    sep=self.config.sep,
                    encoding=self.config.encoding
                )
                
                # Parse month from filename
                month_ref = parse_month_from_filename(file_path.name)
                df['mes_referencia'] = month_ref
                
                all_limits.append(df)
                logger.info(f"  Loaded {len(df)} records from {file_path.name}")
            except Exception as e:
                logger.warning(f"  Error loading {file_path.name}: {e}")
        
        if not all_limits:
            logger.warning("No limits files loaded")
            return pd.DataFrame()
        
        df = pd.concat(all_limits, ignore_index=True)
        logger.info(f"Total limits records: {len(df)}")
        
        return df
    
    def load_portfolio_3040(self, months: int = 12, sample_size: int = 50000) -> pd.DataFrame:
        """Load 3040 portfolio data (sampled due to large size)."""
        portfolio_dir = self.dados_dir / 'bases_banco' / '3040'
        logger.info(f"Loading 3040 portfolio from {portfolio_dir}")
        
        all_portfolio = []
        
        for file_path in sorted(portfolio_dir.glob('01. Carteira*.csv'))[:months]:
            try:
                df = pd.read_csv(
                    file_path,
                    sep=self.config.sep,
                    encoding=self.config.encoding,
                    nrows=sample_size  # Sample to avoid memory issues
                )
                
                # Rename columns (handle encoding issues)
                col_mapping = {}
                for col in df.columns:
                    if 'Ident' in col:
                        col_mapping[col] = 'cliente_id'
                    elif 'Linha' in col:
                        col_mapping[col] = 'linha_credito'
                    elif 'Dias' in col and 'Atraso' in col:
                        col_mapping[col] = 'dias_atraso'
                    elif 'Saldo' in col:
                        col_mapping[col] = 'saldo_devedor'
                
                df = df.rename(columns=col_mapping)
                
                # Parse month
                month_ref = parse_month_from_filename(file_path.name)
                df['mes_referencia'] = month_ref
                
                all_portfolio.append(df)
                logger.info(f"  Loaded {len(df)} records from {file_path.name}")
            except Exception as e:
                logger.warning(f"  Error loading {file_path.name}: {e}")
        
        if not all_portfolio:
            logger.warning("No 3040 files loaded")
            return pd.DataFrame()
        
        df = pd.concat(all_portfolio, ignore_index=True)
        logger.info(f"Total 3040 records: {len(df)}")
        
        return df
    
    def process_limits_by_client(self, df_limits: pd.DataFrame) -> pd.DataFrame:
        """Process limits to get last available values per client/product."""
        if df_limits.empty:
            return pd.DataFrame()
        
        # Standardize column names
        col_mapping = {}
        for col in df_limits.columns:
            if 'Ident' in col:
                col_mapping[col] = 'cliente_id'
            elif 'Linha' in col:
                col_mapping[col] = 'linha_credito'
            elif 'Limite' in col and 'Total' in col:
                col_mapping[col] = 'limite_total'
            elif 'Limite' in col and 'Utiliz' in col:
                col_mapping[col] = 'limite_utilizado'
            elif 'Limite' in col and 'Dispon' in col:
                col_mapping[col] = 'limite_disponivel'
        
        df_limits = df_limits.rename(columns=col_mapping)
        
        # Map product names
        if 'linha_credito' in df_limits.columns:
            df_limits['produto'] = df_limits['linha_credito'].apply(
                self.mapper.map_product
            )
        
        # Get latest values per client/product
        if 'mes_referencia' in df_limits.columns:
            df_limits = df_limits.sort_values('mes_referencia', ascending=False)
            df_limits = df_limits.drop_duplicates(
                subset=['cliente_id', 'produto'], 
                keep='first'
            )
        
        return df_limits
    
    def calculate_arrears_history(self, df_portfolio: pd.DataFrame) -> pd.DataFrame:
        """Calculate arrears history per client."""
        if df_portfolio.empty or 'dias_atraso' not in df_portfolio.columns:
            return pd.DataFrame()
        
        # Ensure numeric
        df_portfolio['dias_atraso'] = pd.to_numeric(
            df_portfolio['dias_atraso'], errors='coerce'
        ).fillna(0)
        
        # Aggregate by client
        agg = df_portfolio.groupby('cliente_id').agg({
            'dias_atraso': ['max', 'mean'],
            'saldo_devedor': 'sum' if 'saldo_devedor' in df_portfolio.columns else 'count'
        })
        
        agg.columns = ['max_dias_atraso_12m', 'media_dias_atraso', 'valor_carteira_total']
        agg = agg.reset_index()
        
        return agg
    
    def consolidate(self, output_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Execute full consolidation pipeline.
        
        Returns a unified DataFrame with all data for the models.
        """
        logger.info("=" * 60)
        logger.info("STARTING DATA CONSOLIDATION")
        logger.info("=" * 60)
        
        # Step 1: Load cadastral data
        df_cadastro = self.load_cadastro()
        
        # Step 2: Load and process limits
        df_limits_raw = self.load_limits()
        df_limits = self.process_limits_by_client(df_limits_raw)
        
        # Step 3: Load and process 3040 portfolio
        df_portfolio = self.load_portfolio_3040()
        df_arrears = self.calculate_arrears_history(df_portfolio)
        
        # Step 4: Create base structure (one row per client × product)
        logger.info("Creating unified base structure...")
        
        # Generate product assignments for all clients
        n_clients = min(len(df_cadastro), self.config.target_clients)
        df_products = self.generator.generate_products_for_clients(n_clients)
        
        # Merge cadastro with products
        df_cadastro_sample = df_cadastro.head(n_clients).reset_index(drop=True)
        df_cadastro_sample['client_idx'] = df_cadastro_sample.index
        
        df_base = df_products.merge(df_cadastro_sample, on='client_idx', how='left')
        
        logger.info(f"Base structure: {len(df_base)} rows (client × product)")
        
        # Step 5: Add real limits where available
        if not df_limits.empty:
            df_base = df_base.merge(
                df_limits[['cliente_id', 'produto', 'limite_total', 
                          'limite_utilizado', 'limite_disponivel']],
                left_on=['CLIT', 'produto'],
                right_on=['cliente_id', 'produto'],
                how='left',
                suffixes=('', '_real')
            )
        
        # Step 6: Generate synthetic limits where missing
        logger.info("Generating synthetic data for missing fields...")
        
        # Fill missing limits with synthetic data
        for idx in df_base[df_base['limite_total'].isna()].index:
            renda = df_base.loc[idx, 'RENDA_BRUTA']
            produto = df_base.loc[idx, 'produto']
            
            lim_total, lim_usado, lim_disp = self.generator.generate_limits(
                renda if pd.notna(renda) else 5000,
                produto
            )
            
            df_base.loc[idx, 'limite_total'] = lim_total
            df_base.loc[idx, 'limite_utilizado'] = lim_usado
            df_base.loc[idx, 'limite_disponivel'] = lim_disp
        
        # Step 7: Calculate derived fields
        logger.info("Calculating derived fields...")
        
        # Taxa de utilização
        df_base['taxa_utilizacao'] = (
            df_base['limite_utilizado'] / df_base['limite_total'].replace(0, 1)
        ).clip(0, 1)
        
        # Generate installments
        df_base['parcelas_mensais'] = df_base.apply(
            lambda row: self.generator.generate_installments(
                row['limite_utilizado'],
                row['produto'],
                row['RENDA_BRUTA'] if pd.notna(row['RENDA_BRUTA']) else 5000
            ),
            axis=1
        )
        
        # Comprometimento (only products that count)
        def calc_comprometimento_total(group):
            renda = group['RENDA_BRUTA'].iloc[0]
            if pd.isna(renda) or renda <= 0:
                return 1.0
            
            parcelas_que_contam = 0
            for _, row in group.iterrows():
                config = COMPROMETIMENTO_POR_PRODUTO.get(row['produto'], {})
                if config.get('conta_no_total', True):
                    parcelas_que_contam += row['parcelas_mensais']
            
            return min(1.0, parcelas_que_contam / renda)
        
        # Calculate per client then merge back
        comp_por_cliente = df_base.groupby('CLIT').apply(calc_comprometimento_total)
        comp_por_cliente.name = 'comprometimento_renda'
        df_base = df_base.merge(comp_por_cliente, on='CLIT', how='left')
        
        # Margem disponível
        df_base['margem_disponivel'] = (
            df_base['RENDA_BRUTA'].fillna(5000) * COMPROMETIMENTO_MAXIMO_RENDA -
            df_base.groupby('CLIT')['parcelas_mensais'].transform('sum')
        ).clip(0)
        
        # Step 8: Add SCR synthetic data
        scr_data = self.generator.generate_scr_data(len(df_base))
        df_base = pd.concat([df_base, scr_data], axis=1)
        
        # Step 9: Add guarantee data
        guarantee_data = self.generator.generate_guarantee_data(
            df_base['produto'],
            df_base['limite_total']
        )
        df_base = pd.concat([df_base, guarantee_data], axis=1)
        
        # Step 10: Add utilization history
        util_data = self.generator.generate_utilization_history(len(df_base))
        df_base = pd.concat([df_base, util_data], axis=1)
        
        # Step 11: Add arrears history from real data
        if not df_arrears.empty:
            df_base = df_base.merge(
                df_arrears,
                left_on='CLIT',
                right_on='cliente_id',
                how='left'
            )
        
        # Fill missing arrears with synthetic
        if 'max_dias_atraso_12m' not in df_base.columns:
            df_base['max_dias_atraso_12m'] = np.random.exponential(5, len(df_base)).astype(int)
        else:
            # Generate synthetic values for missing
            missing_mask = df_base['max_dias_atraso_12m'].isna()
            n_missing = missing_mask.sum()
            if n_missing > 0:
                synthetic_values = np.random.exponential(5, n_missing).astype(int)
                df_base.loc[missing_mask, 'max_dias_atraso_12m'] = synthetic_values
            df_base['max_dias_atraso_12m'] = df_base['max_dias_atraso_12m'].fillna(0).astype(int)
        
        # Step 12: Generate ECL and Propensity data (BACEN 4966)
        logger.info("Generating ECL and Propensity data (BACEN 4966)...")
        df_base = self.generator.generate_ecl_propensity_data(df_base)
        
        # Step 13: Clean up and finalize
        logger.info("Finalizing base...")
        
        # Select and order final columns
        final_columns = [
            # Identification
            'CLIT', 'CPF', 
            # Cadastral
            'IDADE_CLIENTE', 'ESCOLARIDADE', 'RENDA_BRUTA', 'TEMPO_RELAC',
            'ESTADO_CIVIL', 'POSSUI_VEICULO', 'QT_PRODUTOS',
            # Product
            'produto', 'limite_total', 'limite_utilizado', 'limite_disponivel',
            'taxa_utilizacao',
            # Commitment
            'parcelas_mensais', 'comprometimento_renda', 'margem_disponivel',
            # History
            'utilizacao_media_12m', 'trimestres_sem_uso', 'max_dias_atraso_12m',
            # SCR (synthetic)
            'scr_score_risco', 'scr_dias_atraso', 'scr_tem_prejuizo',
            # Guarantees
            'tipo_garantia', 'valor_garantia', 'ltv',
            # BACEN 4966 - ECL
            'PRINAD_SCORE', 'RATING', 'pd_12m', 'pd_lifetime',
            'stage', 'lgd', 'ead', 'ecl', 'ecl_horizonte', 'ccf', 'dias_atraso',
            # Propensity
            'propensao_score', 'propensao_classificacao',
            # Global Limit
            'limite_global'
        ]
        
        # Keep only existing columns
        final_columns = [c for c in final_columns if c in df_base.columns]
        df_final = df_base[final_columns].copy()
        
        # Round numerical columns
        for col in ['limite_total', 'limite_utilizado', 'limite_disponivel', 
                    'parcelas_mensais', 'margem_disponivel', 'valor_garantia']:
            if col in df_final.columns:
                df_final[col] = df_final[col].round(2)
        
        for col in ['taxa_utilizacao', 'comprometimento_renda', 'utilizacao_media_12m', 'ltv']:
            if col in df_final.columns:
                df_final[col] = df_final[col].round(4)
        
        # Step 13: Save output
        if output_path is None:
            output_path = self.dados_dir / 'base_clientes.csv'
        
        df_final.to_csv(
            output_path,
            sep=self.config.sep,
            encoding=self.config.encoding,
            index=False
        )
        
        logger.info("=" * 60)
        logger.info("CONSOLIDATION COMPLETE")
        logger.info(f"Output: {output_path}")
        logger.info(f"Total rows: {len(df_final)}")
        logger.info(f"Unique clients: {df_final['CLIT'].nunique()}")
        logger.info(f"Products: {df_final['produto'].unique().tolist()}")
        logger.info("=" * 60)
        
        return df_final


def consolidar_dados(
    salvar: bool = True,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Convenience function to run consolidation.
    
    Args:
        salvar: Whether to save output
        output_path: Custom output path
        
    Returns:
        Consolidated DataFrame
    """
    consolidator = UnifiedDataConsolidator()
    return consolidator.consolidate(output_path if salvar else None)


if __name__ == "__main__":
    # Run consolidation when executed directly
    print("=" * 60)
    print("PROLIMITE - Data Consolidation Pipeline")
    print("=" * 60)
    
    df = consolidar_dados()
    
    print(f"\nFinal shape: {df.shape}")
    print(f"\nSample data:")
    print(df.head(10).to_string())
    
    print("\n=== Statistics ===")
    print(f"Clients: {df['CLIT'].nunique()}")
    print(f"Products distribution:")
    print(df['produto'].value_counts())
