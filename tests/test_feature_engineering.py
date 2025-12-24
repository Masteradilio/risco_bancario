"""
Tests for the Feature Engineering module.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from feature_engineering import FeatureEngineer, create_features


class TestFeatureEngineer:
    """Test suite for FeatureEngineer class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.fe = FeatureEngineer()
    
    def test_initialization(self):
        """Test that FeatureEngineer initializes correctly."""
        assert self.fe.feature_names_ == []
    
    def test_fit_transform_returns_dataframe(self, sample_cadastral_data, sample_behavioral_data_clean):
        """Test that fit_transform returns a DataFrame."""
        data = {**sample_cadastral_data, **sample_behavioral_data_clean}
        df = pd.DataFrame([data])
        
        result = self.fe.fit_transform(df)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
    
    def test_creates_financial_features(self, sample_cadastral_data):
        """Test creation of financial ratio features."""
        df = pd.DataFrame([sample_cadastral_data])
        
        result = self.fe.fit_transform(df)
        
        # Check for expected financial features
        assert 'renda_por_dependente' in result.columns
        assert 'log_renda_liquida' in result.columns
        assert 'ratio_liquida_bruta' in result.columns
    
    def test_creates_behavioral_features(self, sample_behavioral_data_delinquent):
        """Test creation of behavioral score features."""
        df = pd.DataFrame([sample_behavioral_data_delinquent])
        
        result = self.fe.fit_transform(df)
        
        # Check for expected behavioral features
        assert 'max_atraso_dias' in result.columns
        assert 'score_atraso' in result.columns
        assert 'tem_atraso_curto' in result.columns
        assert 'tem_atraso_longo' in result.columns
        assert 'tem_inadimplencia' in result.columns
    
    def test_creates_categorical_scores(self, sample_cadastral_data):
        """Test creation of categorical score features."""
        df = pd.DataFrame([sample_cadastral_data])
        
        result = self.fe.fit_transform(df)
        
        # Check for expected categorical features
        if 'OCUPACAO' in sample_cadastral_data:
            assert 'score_ocupacao' in result.columns
        if 'ESCOLARIDADE' in sample_cadastral_data:
            assert 'score_escolaridade' in result.columns
    
    def test_creates_age_features(self, sample_cadastral_data):
        """Test creation of age-related features."""
        df = pd.DataFrame([sample_cadastral_data])
        
        result = self.fe.fit_transform(df)
        
        if 'IDADE_CLIENTE' in sample_cadastral_data:
            assert 'faixa_etaria' in result.columns
            assert 'idade_squared' in result.columns
            assert 'em_idade_ativa' in result.columns
    
    def test_creates_relationship_features(self, sample_cadastral_data):
        """Test creation of relationship tenure features."""
        df = pd.DataFrame([sample_cadastral_data])
        
        result = self.fe.fit_transform(df)
        
        if 'TEMPO_RELAC' in sample_cadastral_data:
            assert 'faixa_relacionamento' in result.columns
            assert 'log_tempo_relac' in result.columns
            assert 'cliente_novo' in result.columns
    
    def test_handles_missing_values(self):
        """Test handling of missing values."""
        data = {
            'IDADE_CLIENTE': None,
            'RENDA_BRUTA': 5000.0,
            'RENDA_LIQUIDA': None
        }
        df = pd.DataFrame([data])
        
        # Should not raise error
        result = self.fe.fit_transform(df)
        assert isinstance(result, pd.DataFrame)
    
    def test_get_feature_names(self, sample_cadastral_data):
        """Test getting feature names after transform."""
        df = pd.DataFrame([sample_cadastral_data])
        self.fe.fit_transform(df)
        
        names = self.fe.get_feature_names()
        
        assert isinstance(names, list)
        assert len(names) > 0
    
    def test_convenience_function(self, sample_cadastral_data):
        """Test the create_features convenience function."""
        df = pd.DataFrame([sample_cadastral_data])
        
        result = create_features(df)
        
        assert isinstance(result, pd.DataFrame)


class TestBehavioralFeatures:
    """Test suite for behavioral feature calculations."""
    
    def test_max_atraso_dias_clean(self, sample_behavioral_data_clean):
        """Test max_atraso_dias for clean client."""
        fe = FeatureEngineer()
        df = pd.DataFrame([sample_behavioral_data_clean])
        
        result = fe.fit_transform(df)
        
        assert result['max_atraso_dias'].iloc[0] == 0
    
    def test_max_atraso_dias_delinquent(self, sample_behavioral_data_delinquent):
        """Test max_atraso_dias for delinquent client."""
        fe = FeatureEngineer()
        df = pd.DataFrame([sample_behavioral_data_delinquent])
        
        result = fe.fit_transform(df)
        
        assert result['max_atraso_dias'].iloc[0] > 0
    
    def test_severidade_atraso_categories(self):
        """Test severidade_atraso categorical values."""
        fe = FeatureEngineer()
        
        # Clean client
        clean_df = pd.DataFrame([{f'v{i}': 0.0 for i in [205, 210, 220, 230, 240, 245, 250, 255, 260, 270, 280, 290]}])
        result_clean = fe.fit_transform(clean_df)
        assert result_clean['severidade_atraso'].iloc[0] == 'sem_atraso'
