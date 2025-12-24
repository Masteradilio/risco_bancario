"""
PRINAD - Classifier Module
Complete classification pipeline for credit risk scoring.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
import joblib
from datetime import datetime
from dataclasses import dataclass, asdict

# Local imports  
from historical_penalty import HistoricalPenaltyCalculator, HistoricalAnalysis

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODELO_DIR = BASE_DIR / "modelo"


@dataclass
class ClassificationResult:
    """Result of a PRINAD classification."""
    cpf: str
    prinad: float
    rating: str
    rating_descricao: str
    cor: str
    pd_base: float
    penalidade_historica: float
    peso_atual: float
    peso_historico: float
    acao_sugerida: str
    explicacao_shap: List[Dict[str, Any]]
    timestamp: str
    model_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RatingMapper:
    """Maps PRINAD scores to ratings with custom bands."""
    
    RATING_CONFIG = [
        # (rating, lower, upper, description, color, action)
        ('A1', 0, 2, 'Risco Mínimo', 'verde', 'Aprovação automática, melhores taxas'),
        ('A2', 2, 5, 'Risco Muito Baixo', 'verde', 'Aprovação automática'),
        ('A3', 5, 10, 'Risco Baixo', 'verde', 'Aprovação com análise simplificada'),
        ('B1', 10, 20, 'Risco Baixo-Moderado', 'amarelo', 'Análise padrão'),
        ('B2', 20, 35, 'Risco Moderado', 'amarelo', 'Análise detalhada'),
        ('B3', 35, 50, 'Risco Moderado-Alto', 'laranja', 'Análise rigorosa, possíveis garantias'),
        ('C1', 50, 70, 'Risco Alto', 'vermelho', 'Exige garantias ou fiador'),
        ('C2', 70, 90, 'Risco Muito Alto', 'vermelho', 'Negação ou condições especiais'),
        ('D', 90, 100.01, 'Default/Iminente', 'preto', 'Negação, encaminhar para cobrança'),
    ]
    
    @classmethod
    def get_rating(cls, prinad: float) -> Dict[str, str]:
        """Get rating information for a PRINAD score."""
        prinad = max(0, min(100, prinad))
        
        for rating, lower, upper, desc, color, action in cls.RATING_CONFIG:
            if lower <= prinad < upper:
                return {
                    'rating': rating,
                    'descricao': desc,
                    'cor': color,
                    'acao_sugerida': action,
                    'faixa': f'{lower}% - {upper}%'
                }
        
        # Default to worst rating
        return {
            'rating': 'D',
            'descricao': 'Default/Iminente',
            'cor': 'preto',
            'acao_sugerida': 'Negação, encaminhar para cobrança',
            'faixa': '90% - 100%'
        }


class PRINADClassifier:
    """
    Complete PRINAD classification pipeline.
    Combines ML model prediction with historical penalty.
    """
    
    MODEL_VERSION = "1.0.0"
    PESO_ATUAL = 0.5
    PESO_HISTORICO = 0.5
    
    def __init__(self, modelo_dir: Optional[Path] = None):
        """
        Initialize the classifier.
        
        Args:
            modelo_dir: Path to model artifacts directory
        """
        self.modelo_dir = modelo_dir or MODELO_DIR
        self.model = None
        self.preprocessor = None
        self.feature_engineer = None
        self.shap_explainer = None
        self.historical_calculator = HistoricalPenaltyCalculator(
            forgiveness_months=6,
            max_penalty_internal=0.75,
            max_penalty_external=0.75
        )
        
        self._load_artifacts()
    
    def _load_artifacts(self):
        """Load model artifacts from disk."""
        
        # Load model
        model_path = self.modelo_dir / "ensemble_model.joblib"
        if model_path.exists():
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.model_version = model_data.get('version', self.MODEL_VERSION)
            logger.info(f"Model loaded from {model_path}")
        else:
            logger.warning(f"Model not found at {model_path}")
        
        # Load preprocessor
        preproc_path = self.modelo_dir / "preprocessor.joblib"
        if preproc_path.exists():
            preproc_data = joblib.load(preproc_path)
            self.preprocessor = preproc_data['preprocessor']
            self.feature_engineer = preproc_data['feature_engineer']
            logger.info(f"Preprocessor loaded from {preproc_path}")
        else:
            logger.warning(f"Preprocessor not found at {preproc_path}")
        
        # Load SHAP explainer
        shap_path = self.modelo_dir / "shap_explainer.joblib"
        if shap_path.exists():
            self.shap_explainer = joblib.load(shap_path)
            logger.info(f"SHAP explainer loaded from {shap_path}")
    
    def is_ready(self) -> bool:
        """Check if classifier is ready for predictions."""
        return all([
            self.model is not None,
            self.preprocessor is not None
        ])
    
    def classify(self, client_data: Dict[str, Any]) -> ClassificationResult:
        """
        Classify a single client.
        
        Args:
            client_data: Dictionary with client data
                Required keys: dados_cadastrais, dados_comportamentais
                Optional: cpf
                
        Returns:
            ClassificationResult with full classification details
        """
        if not self.is_ready():
            raise RuntimeError("Classifier not ready. Model artifacts missing.")
        
        cpf = client_data.get('cpf', 'unknown')
        
        # Extract data components
        dados_cadastrais = client_data.get('dados_cadastrais', {})
        dados_comportamentais = client_data.get('dados_comportamentais', {})
        
        # Merge into single dict for feature engineering
        merged_data = {**dados_cadastrais, **dados_comportamentais}
        
        # Convert to DataFrame for prediction
        df = pd.DataFrame([merged_data])
        
        # Get PD Base from model
        pd_base = self._predict_pd_base(df)
        
        # Calculate historical penalty
        prinad_final, historical_analysis = self.historical_calculator.apply_penalty(
            pd_base, dados_comportamentais
        )
        
        # Get rating
        rating_info = RatingMapper.get_rating(prinad_final)
        
        # Get SHAP explanation
        shap_explanation = self._get_shap_explanation(df)
        
        # Build result
        result = ClassificationResult(
            cpf=cpf,
            prinad=round(prinad_final, 2),
            rating=rating_info['rating'],
            rating_descricao=rating_info['descricao'],
            cor=rating_info['cor'],
            pd_base=round(pd_base, 2),
            penalidade_historica=round(historical_analysis.penalidade_total, 2),
            peso_atual=self.PESO_ATUAL,
            peso_historico=self.PESO_HISTORICO,
            acao_sugerida=rating_info['acao_sugerida'],
            explicacao_shap=shap_explanation,
            timestamp=datetime.now().isoformat(),
            model_version=self.MODEL_VERSION
        )
        
        return result
    
    def _predict_pd_base(self, df: pd.DataFrame) -> float:
        """Get base PD from ML model."""
        
        try:
            # Apply feature engineering
            if self.feature_engineer:
                df_engineered = self.feature_engineer.transform(df)
            else:
                df_engineered = df
            
            df_engineered = df_engineered.fillna(0)
            
            # Preprocess
            X_processed = self.preprocessor.transform(df_engineered)
            
            # Predict probability
            proba = self.model.predict_proba(X_processed)[0, 1]
            
            # Convert to percentage
            pd_base = proba * 100
            
            return pd_base
            
        except Exception as e:
            logger.error(f"Error predicting PD base: {e}")
            # Return moderate risk as fallback
            return 25.0
    
    def _get_shap_explanation(self, df: pd.DataFrame, max_features: int = 5) -> List[Dict[str, Any]]:
        """Generate SHAP explanation for the prediction."""
        
        if self.shap_explainer is None:
            return []
        
        try:
            # Apply feature engineering
            if self.feature_engineer:
                df_engineered = self.feature_engineer.transform(df)
            else:
                df_engineered = df
            
            df_engineered = df_engineered.fillna(0)
            X_processed = self.preprocessor.transform(df_engineered)
            
            # Get SHAP values
            shap_values = self.shap_explainer(X_processed)
            
            # Get feature names
            try:
                feature_names = self.preprocessor.get_feature_names_out().tolist()
            except:
                feature_names = [f'feature_{i}' for i in range(X_processed.shape[1])]
            
            # Extract values
            values = shap_values.values[0] if hasattr(shap_values, 'values') else shap_values[0]
            
            # Sort by importance
            importance = list(zip(feature_names, values))
            importance.sort(key=lambda x: abs(x[1]), reverse=True)
            
            # Build explanation
            explanation = []
            for feat, val in importance[:max_features]:
                explanation.append({
                    'feature': feat,
                    'contribuicao': round(float(val) * 100, 2),  # Convert to percentage points
                    'direcao': 'aumenta_risco' if val > 0 else 'reduz_risco'
                })
            
            return explanation
            
        except Exception as e:
            logger.warning(f"Could not generate SHAP explanation: {e}")
            return []
    
    def classify_batch(self, clients: List[Dict[str, Any]]) -> List[ClassificationResult]:
        """
        Classify multiple clients.
        
        Args:
            clients: List of client data dictionaries
            
        Returns:
            List of ClassificationResults
        """
        results = []
        for client_data in clients:
            try:
                result = self.classify(client_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error classifying client: {e}")
                # Create error result
                results.append(ClassificationResult(
                    cpf=client_data.get('cpf', 'unknown'),
                    prinad=50.0,
                    rating='B3',
                    rating_descricao='Erro na classificação',
                    cor='laranja',
                    pd_base=50.0,
                    penalidade_historica=0.0,
                    peso_atual=0.5,
                    peso_historico=0.5,
                    acao_sugerida='Reprocessar manualmente',
                    explicacao_shap=[],
                    timestamp=datetime.now().isoformat(),
                    model_version=self.MODEL_VERSION
                ))
        
        return results


# Global classifier instance
_classifier: Optional[PRINADClassifier] = None


def get_classifier() -> PRINADClassifier:
    """Get or create global classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = PRINADClassifier()
    return _classifier


def classify_client(cpf: str, dados_cadastrais: Dict[str, Any], 
                    dados_comportamentais: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to classify a client.
    
    Args:
        cpf: Client CPF
        dados_cadastrais: Cadastral data dictionary
        dados_comportamentais: Behavioral data dictionary
        
    Returns:
        Classification result as dictionary
    """
    classifier = get_classifier()
    result = classifier.classify({
        'cpf': cpf,
        'dados_cadastrais': dados_cadastrais,
        'dados_comportamentais': dados_comportamentais
    })
    return result.to_dict()


if __name__ == "__main__":
    # Test classification
    logging.basicConfig(level=logging.INFO)
    
    # Test data
    test_client = {
        'cpf': '12345678901',
        'dados_cadastrais': {
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
        },
        'dados_comportamentais': {
            'v205': 0.0,
            'v210': 0.0,
            'v220': 0.0,
            'v230': 0.0,
            'v240': 0.0,
            'v245': 0.0,
            'v250': 0.0,
            'v255': 0.0,
            'v260': 0.0,
            'v270': 0.0,
            'v280': 0.0,
            'v290': 0.0
        }
    }
    
    print("\n" + "="*60)
    print("PRINAD CLASSIFICATION TEST")
    print("="*60)
    
    try:
        classifier = PRINADClassifier()
        
        if classifier.is_ready():
            result = classifier.classify(test_client)
            
            print(f"\nCPF: {result.cpf}")
            print(f"PRINAD: {result.prinad}%")
            print(f"Rating: {result.rating} - {result.rating_descricao}")
            print(f"Cor: {result.cor}")
            print(f"PD Base: {result.pd_base}%")
            print(f"Penalidade Histórica: {result.penalidade_historica}")
            print(f"Ação Sugerida: {result.acao_sugerida}")
            print(f"\nExplicação SHAP:")
            for exp in result.explicacao_shap:
                print(f"  - {exp['feature']}: {exp['contribuicao']:+.2f}% ({exp['direcao']})")
        else:
            print("Classifier not ready. Train the model first.")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Run train_model.py first to create model artifacts.")
