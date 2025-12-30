"""
Tests for the Data Pipeline module.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_pipeline import normalize_cpf


class TestNormalizeCPF:
    """Test suite for CPF normalization function."""
    
    def test_normalize_string_cpf(self):
        """Test normalizing a string CPF."""
        result = normalize_cpf("12345678901")
        assert result == "12345678901"
    
    def test_normalize_numeric_cpf(self):
        """Test normalizing a numeric CPF."""
        result = normalize_cpf(12345678901)
        assert result == "12345678901"
    
    def test_normalize_short_cpf_pads_zeros(self):
        """Test that short CPFs are padded with zeros."""
        result = normalize_cpf(123456789)
        assert len(result) == 11
        assert result.startswith('0')  # Should have leading zeros
    
    def test_normalize_cpf_with_dots_dashes(self):
        """Test normalizing CPF with formatting."""
        result = normalize_cpf("123.456.789-01")
        assert result == "12345678901"
    
    def test_normalize_float_cpf(self):
        """Test normalizing a float CPF."""
        result = normalize_cpf(12345678901.0)
        assert result == "12345678901"
    
    def test_normalize_none_returns_none(self):
        """Test that None input returns None."""
        result = normalize_cpf(None)
        assert result is None
    
    def test_normalize_nan_returns_none(self):
        """Test that NaN input returns None."""
        result = normalize_cpf(np.nan)
        assert result is None
    
    def test_normalize_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = normalize_cpf("")
        assert result is None
    
    def test_normalize_whitespace_cpf(self):
        """Test normalizing CPF with whitespace."""
        result = normalize_cpf("  12345678901  ")
        assert result == "12345678901"


class TestDataPipelineIntegration:
    """Integration tests for data pipeline (require data files)."""
    
    @pytest.fixture
    def data_dir(self):
        """Get data directory path."""
        return Path(__file__).parent.parent / "dados"
    
    def test_data_directory_exists(self, data_dir):
        """Test that data directory exists."""
        # Skip if directory doesn't exist - this might be a clean checkout
        if not data_dir.exists():
            pytest.skip(f"Data directory not found: {data_dir}")
    
    def test_cadastro_file_exists(self, data_dir):
        """Test that cadastro file exists if data dir exists."""
        if not data_dir.exists():
            pytest.skip("Data directory not available")
        cadastro_path = data_dir / "base_cadastro.csv"
        assert cadastro_path.exists(), f"Cadastro file not found: {cadastro_path}"
    
    def test_comportamental_file_exists(self, data_dir):
        """Test that behavioral file exists if data dir exists."""
        if not data_dir.exists():
            pytest.skip("Data directory not available")
        comportamental_path = data_dir / "base_3040.csv"
        assert comportamental_path.exists(), f"Behavioral file not found: {comportamental_path}"
    
    def test_cadastro_has_expected_columns(self, data_dir):
        """Test that cadastro has expected columns."""
        cadastro_path = data_dir / "base_cadastro.csv"
        if not cadastro_path.exists():
            pytest.skip("Cadastro file not available")
        df = pd.read_csv(cadastro_path, sep=';', nrows=5)
        expected_cols = ['CPF', 'IDADE_CLIENTE', 'RENDA_BRUTA']
        for col in expected_cols:
            assert col in df.columns, f"Expected column {col} not found in cadastro"
    
    def test_comportamental_has_expected_columns(self, data_dir):
        """Test that behavioral data has expected columns."""
        comportamental_path = data_dir / "base_3040.csv"
        if not comportamental_path.exists():
            pytest.skip("Behavioral file not available")
        df = pd.read_csv(comportamental_path, sep=';', nrows=5)
        expected_cols = ['CPF', 'v205', 'v290', 'CLASSE']
        for col in expected_cols:
            assert col in df.columns, f"Expected column {col} not found in comportamental"
