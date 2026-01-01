"""
Unit tests for Model Validator.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from propensao.src.model_validator import (
    ModelValidator,
    SemaforoStatus,
    MetricaExplicada,
    RelatorioValidacao,
    get_model_validator
)


class TestModelValidator:
    """Test Model Validator."""
    
    @pytest.fixture
    def validator(self):
        """Create validator fixture."""
        return ModelValidator()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        np.random.seed(42)
        n = 5000
        y_true = np.random.binomial(1, 0.03, n)  # 3% default
        # Good model predictions
        noise = np.random.normal(0, 0.1, n)
        y_pred = np.clip(y_true * 0.85 + (1 - y_true) * 0.05 + noise * 0.1, 0.001, 0.999)
        return y_true, y_pred
    
    def test_initialization(self, validator):
        """Validator should initialize correctly."""
        assert validator is not None
    
    def test_thresholds_auc(self, validator):
        """AUC thresholds should be 0.90/0.95."""
        assert validator.THRESHOLDS['auc_roc']['minimo'] == 0.90
        assert validator.THRESHOLDS['auc_roc']['desejavel'] == 0.95
    
    def test_calcular_auc_roc(self, validator, sample_data):
        """AUC should be calculated correctly."""
        y_true, y_pred = sample_data
        auc = validator.calcular_auc_roc(y_true, y_pred)
        
        assert 0.5 <= auc <= 1.0
        assert auc > 0.8  # Good model should have high AUC
    
    def test_calcular_gini(self, validator, sample_data):
        """Gini should be 2*AUC - 1."""
        y_true, y_pred = sample_data
        auc = validator.calcular_auc_roc(y_true, y_pred)
        gini = validator.calcular_gini(y_true, y_pred)
        
        assert gini == pytest.approx(2 * auc - 1, rel=1e-6)
    
    def test_calcular_ks(self, validator, sample_data):
        """KS should be between 0 and 1."""
        y_true, y_pred = sample_data
        ks, threshold = validator.calcular_ks(y_true, y_pred)
        
        assert 0 <= ks <= 1
        assert 0 <= threshold <= 1
    
    def test_calcular_psi_stable(self, validator):
        """PSI should be low for stable distributions."""
        np.random.seed(42)
        scores_dev = np.random.normal(0.5, 0.2, 1000)
        scores_atual = np.random.normal(0.5, 0.2, 1000)  # Same distribution
        
        psi = validator.calcular_psi(scores_dev, scores_atual)
        
        assert psi < 0.10  # Low PSI for stable distribution
    
    def test_calcular_psi_drift(self, validator):
        """PSI should be high for drifted distributions."""
        np.random.seed(42)
        scores_dev = np.random.normal(0.3, 0.1, 1000)
        scores_atual = np.random.normal(0.7, 0.2, 1000)  # Different distribution
        
        psi = validator.calcular_psi(scores_dev, scores_atual)
        
        assert psi > 0.25  # High PSI for drift
    
    def test_calcular_brier(self, validator, sample_data):
        """Brier score should be between 0 and 1."""
        y_true, y_pred = sample_data
        brier = validator.calcular_brier(y_true, y_pred)
        
        assert 0 <= brier <= 1
        assert brier < 0.20  # Good model should have low Brier
    
    def test_determinar_status_verde(self, validator):
        """High AUC should be green."""
        status = validator.determinar_status('auc_roc', 0.96)
        assert status == SemaforoStatus.VERDE
    
    def test_determinar_status_amarelo(self, validator):
        """Medium AUC should be yellow."""
        status = validator.determinar_status('auc_roc', 0.92)
        assert status == SemaforoStatus.AMARELO
    
    def test_determinar_status_vermelho(self, validator):
        """Low AUC should be red."""
        status = validator.determinar_status('auc_roc', 0.85)
        assert status == SemaforoStatus.VERMELHO
    
    def test_determinar_status_psi_verde(self, validator):
        """Low PSI should be green."""
        status = validator.determinar_status('psi', 0.05)
        assert status == SemaforoStatus.VERDE
    
    def test_determinar_status_psi_vermelho(self, validator):
        """High PSI should be red."""
        status = validator.determinar_status('psi', 0.30)
        assert status == SemaforoStatus.VERMELHO
    
    def test_gerar_metrica_explicada(self, validator):
        """Should generate explained metric."""
        metrica = validator.gerar_metrica_explicada('auc_roc', 0.93)
        
        assert isinstance(metrica, MetricaExplicada)
        assert metrica.nome == 'AUC_ROC'
        assert metrica.valor == 0.93
        assert metrica.threshold_minimo == 0.90
        assert metrica.threshold_desejavel == 0.95
        assert metrica.status == SemaforoStatus.AMARELO
        assert len(metrica.explicacao_tecnica) > 0
    
    def test_validar_modelo(self, validator, sample_data):
        """Should generate complete validation report."""
        y_true, y_pred = sample_data
        
        relatorio = validator.validar_modelo(
            nome_modelo="TestModel",
            y_true=y_true,
            y_pred_proba=y_pred
        )
        
        assert isinstance(relatorio, RelatorioValidacao)
        assert relatorio.modelo == "TestModel"
        assert len(relatorio.metricas) == 5  # AUC, Gini, KS, PSI, Brier
        assert relatorio.status_geral in SemaforoStatus
    
    def test_hosmer_lemeshow(self, validator, sample_data):
        """Hosmer-Lemeshow test should run."""
        y_true, y_pred = sample_data
        chi2, p_value = validator.hosmer_lemeshow_test(y_true, y_pred)
        
        assert chi2 >= 0
        assert 0 <= p_value <= 1


class TestModuleFunctions:
    """Test module-level functions."""
    
    def test_get_model_validator(self):
        """Should return validator instance."""
        val = get_model_validator()
        assert isinstance(val, ModelValidator)
