"""
PRINAD Tests - pytest configuration
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def sample_cadastral_data():
    """Sample cadastral data for testing."""
    return {
        'IDADE_CLIENTE': 35,
        'RENDA_BRUTA': 5000.0,
        'RENDA_LIQUIDA': 4200.0,
        'OCUPACAO': 'ASSALARIADO',
        'ESCOLARIDADE': 'SUPERIOR',
        'ESTADO_CIVIL': 'CASADO',
        'QT_DEPENDENTES': 2,
        'TEMPO_RELAC': 48.0,
        'TIPO_RESIDENCIA': 'PROPRIA',
        'POSSUI_VEICULO': 'SIM',
        'PORTABILIDADE': 'NAO PORTADO',
        'COMP_RENDA': 0.35
    }


@pytest.fixture
def sample_behavioral_data_clean():
    """Sample behavioral data for a clean client."""
    return {
        'v205': 0.0, 'v210': 0.0, 'v220': 0.0, 'v230': 0.0,
        'v240': 0.0, 'v245': 0.0, 'v250': 0.0, 'v255': 0.0,
        'v260': 0.0, 'v270': 0.0, 'v280': 0.0, 'v290': 0.0
    }


@pytest.fixture
def sample_behavioral_data_delinquent():
    """Sample behavioral data for a delinquent client."""
    return {
        'v205': 1000.0, 'v210': 1000.0, 'v220': 500.0, 'v230': 500.0,
        'v240': 5000.0, 'v245': 5000.0, 'v250': 3000.0, 'v255': 3000.0,
        'v260': 2000.0, 'v270': 1000.0, 'v280': 500.0, 'v290': 10000.0
    }


@pytest.fixture
def sample_client_data(sample_cadastral_data, sample_behavioral_data_clean):
    """Complete client data for testing."""
    return {
        'cpf': '12345678901',
        'dados_cadastrais': sample_cadastral_data,
        'dados_comportamentais': sample_behavioral_data_clean
    }
