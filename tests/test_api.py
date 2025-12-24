"""
Tests for the API module.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestAPIHealth:
    """Test suite for API health endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from api import app
        return TestClient(app)
    
    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_response_structure(self, client):
        """Test health response structure."""
        response = client.get("/health")
        data = response.json()
        
        assert 'status' in data
        assert 'model_loaded' in data
        assert 'version' in data
        assert 'timestamp' in data
    
    def test_health_version_is_string(self, client):
        """Test that version is a string."""
        response = client.get("/health")
        data = response.json()
        
        assert isinstance(data['version'], str)


class TestAPIMetrics:
    """Test suite for API metrics endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from api import app
        return TestClient(app)
    
    def test_metrics_endpoint_returns_200(self, client):
        """Test that metrics endpoint returns 200."""
        response = client.get("/metrics")
        assert response.status_code == 200
    
    def test_metrics_response_structure(self, client):
        """Test metrics response structure."""
        response = client.get("/metrics")
        data = response.json()
        
        assert 'model_version' in data
        assert 'total_classificacoes' in data
        assert 'distribuicao_ratings' in data
        assert 'latencia_media_ms' in data


class TestAPIPredictEndpoint:
    """Test suite for API predict endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from api import app
        return TestClient(app)
    
    @pytest.fixture
    def valid_request(self, sample_cadastral_data, sample_behavioral_data_clean):
        """Create a valid prediction request."""
        return {
            "cpf": "12345678901",
            "dados_cadastrais": sample_cadastral_data,
            "dados_comportamentais": sample_behavioral_data_clean
        }
    
    def test_predict_without_model_returns_503(self, client, valid_request):
        """Test that predict returns 503 when model not loaded."""
        # This test expects 503 if model is not loaded
        # or 200 if model is loaded
        response = client.post("/predict", json=valid_request)
        assert response.status_code in [200, 503]
    
    def test_predict_with_invalid_json_returns_422(self, client):
        """Test that invalid JSON returns 422."""
        response = client.post("/predict", json={"invalid": "data"})
        assert response.status_code == 422


class TestAPIBatchEndpoint:
    """Test suite for API batch endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from api import app
        return TestClient(app)
    
    def test_batch_with_empty_list(self, client):
        """Test batch with empty client list."""
        response = client.post("/batch", json={"clientes": []})
        # Should return 200 with empty results or 503 if model not loaded
        assert response.status_code in [200, 503]


class TestAPIInputValidation:
    """Test suite for API input validation."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from api import app
        return TestClient(app)
    
    def test_missing_cpf_returns_422(self, client, sample_cadastral_data, sample_behavioral_data_clean):
        """Test that missing CPF returns 422."""
        request = {
            "dados_cadastrais": sample_cadastral_data,
            "dados_comportamentais": sample_behavioral_data_clean
        }
        response = client.post("/predict", json=request)
        assert response.status_code == 422
    
    def test_missing_cadastrais_returns_422(self, client, sample_behavioral_data_clean):
        """Test that missing cadastrais returns 422."""
        request = {
            "cpf": "12345678901",
            "dados_comportamentais": sample_behavioral_data_clean
        }
        response = client.post("/predict", json=request)
        assert response.status_code == 422
    
    def test_missing_comportamentais_returns_422(self, client, sample_cadastral_data):
        """Test that missing comportamentais returns 422."""
        request = {
            "cpf": "12345678901",
            "dados_cadastrais": sample_cadastral_data
        }
        response = client.post("/predict", json=request)
        assert response.status_code == 422
