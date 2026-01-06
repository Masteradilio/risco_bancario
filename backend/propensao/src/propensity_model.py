"""
Propensity Model - Multi-product credit propensity scoring.

Predicts the likelihood of each client to consume credit
for each product type using XGBoost ensemble.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import joblib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.utils import (
    PRODUTOS_CREDITO,
    PROPENSAO_DIR,
    setup_logging
)

logger = setup_logging(__name__)

# ML imports
try:
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import roc_auc_score, precision_score, recall_score
    import xgboost as xgb
    import lightgbm as lgb
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("ML libraries not available. Install xgboost, lightgbm, sklearn.")


@dataclass
class PropensityScore:
    """Propensity score for a single client/product."""
    cliente_id: str
    produto: str
    score: float  # 0-100
    probabilidade: float  # 0-1
    classificacao: str  # Alta, Media, Baixa
    features_importantes: List[Tuple[str, float]]


@dataclass
class ClientePropensity:
    """Complete propensity profile for a client."""
    cliente_id: str
    scores: Dict[str, float]  # produto -> score
    ranking_produtos: List[str]  # Ordered by propensity
    score_agregado: float
    prinad: Optional[float] = None


class PropensityModel:
    """
    Multi-product propensity model using XGBoost/LightGBM ensemble.
    
    Trains separate models for each product to predict credit consumption.
    """
    
    # Classification thresholds
    THRESHOLD_ALTA = 70
    THRESHOLD_MEDIA = 40
    
    # Model hyperparameters
    XGBOOST_PARAMS = {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'use_label_encoder': False,
        'eval_metric': 'logloss'
    }
    
    LIGHTGBM_PARAMS = {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'verbose': -1
    }
    
    def __init__(self, modelo_dir: Optional[Path] = None):
        """
        Initialize propensity model.
        
        Args:
            modelo_dir: Directory for model artifacts
        """
        self.modelo_dir = modelo_dir or (PROPENSAO_DIR / "modelo")
        self.modelo_dir.mkdir(exist_ok=True)
        
        self.modelos: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_names: Dict[str, List[str]] = {}
        self.is_trained = False
        
        logger.info(f"PropensityModel initialized (modelo_dir: {self.modelo_dir})")
    
    def _classificar_score(self, score: float) -> str:
        """Classify propensity score."""
        if score >= self.THRESHOLD_ALTA:
            return "Alta"
        elif score >= self.THRESHOLD_MEDIA:
            return "Média"
        return "Baixa"
    
    def _create_model(self, use_lgb: bool = False):
        """Create a model instance."""
        if not ML_AVAILABLE:
            raise ImportError("ML libraries required for training")
        
        if use_lgb:
            return lgb.LGBMClassifier(**self.LIGHTGBM_PARAMS)
        return xgb.XGBClassifier(**self.XGBOOST_PARAMS)
    
    def treinar_produto(
        self,
        produto: str,
        X: pd.DataFrame,
        y: pd.Series,
        validar: bool = True
    ) -> Dict[str, float]:
        """
        Train model for a single product.
        
        Args:
            produto: Product name
            X: Features DataFrame
            y: Target variable (1=used credit, 0=did not use)
            validar: Whether to perform validation
            
        Returns:
            Dict with training metrics
        """
        if not ML_AVAILABLE:
            raise ImportError("ML libraries required")
        
        logger.info(f"Training model for {produto}...")
        
        # Store feature names
        self.feature_names[produto] = list(X.columns)
        
        # Create scaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers[produto] = scaler
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        model = self._create_model()
        model.fit(X_train, y_train)
        
        self.modelos[produto] = model
        
        # Evaluate
        metrics = {}
        if validar:
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            y_pred = model.predict(X_test)
            
            metrics = {
                'auc_roc': roc_auc_score(y_test, y_pred_proba),
                'precision': precision_score(y_test, y_pred, zero_division=0),
                'recall': recall_score(y_test, y_pred, zero_division=0),
                'samples_train': len(X_train),
                'samples_test': len(X_test),
                'positive_rate': y.mean()
            }
            
            logger.info(f"{produto}: AUC={metrics['auc_roc']:.3f}, "
                       f"Prec={metrics['precision']:.3f}, Rec={metrics['recall']:.3f}")
        
        return metrics
    
    def treinar_todos(
        self,
        df: pd.DataFrame,
        target_columns: Dict[str, str],
        feature_columns: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Train models for all products.
        
        Args:
            df: DataFrame with features and targets
            target_columns: Mapping of produto -> target column name
            feature_columns: List of feature column names
            
        Returns:
            Dict of produto -> metrics
        """
        all_metrics = {}
        
        for produto in PRODUTOS_CREDITO:
            if produto not in target_columns:
                logger.warning(f"No target column for {produto}, skipping")
                continue
            
            target_col = target_columns[produto]
            if target_col not in df.columns:
                logger.warning(f"Target column {target_col} not found, skipping {produto}")
                continue
            
            # Prepare data
            X = df[feature_columns].copy()
            y = df[target_col].copy()
            
            # Remove missing values
            mask = ~(X.isna().any(axis=1) | y.isna())
            X = X[mask]
            y = y[mask]
            
            if len(y) < 100:
                logger.warning(f"Insufficient data for {produto} ({len(y)} samples)")
                continue
            
            metrics = self.treinar_produto(produto, X, y)
            all_metrics[produto] = metrics
        
        self.is_trained = len(self.modelos) > 0
        logger.info(f"Training complete. Models trained: {list(self.modelos.keys())}")
        
        return all_metrics
    
    def prever_propensao(
        self,
        cliente_id: str,
        features: Dict[str, float],
        prinad: Optional[float] = None
    ) -> ClientePropensity:
        """
        Predict propensity scores for a client.
        
        Args:
            cliente_id: Client identifier
            features: Feature values dict
            prinad: Optional PRINAD score for adjustment
            
        Returns:
            ClientePropensity with scores for all products
        """
        scores = {}
        
        for produto in PRODUTOS_CREDITO:
            if produto not in self.modelos:
                scores[produto] = 50.0  # Default neutral score
                continue
            
            # Get features for this product
            feature_names = self.feature_names.get(produto, [])
            X = np.array([[features.get(f, 0) for f in feature_names]])
            
            # Scale
            scaler = self.scalers.get(produto)
            if scaler:
                X = scaler.transform(X)
            
            # Predict
            model = self.modelos[produto]
            prob = model.predict_proba(X)[0, 1]
            
            # Convert to score (0-100)
            score = prob * 100
            
            # Adjust by PRINAD if provided (reduce propensity for high-risk clients)
            if prinad is not None and prinad > 70:
                # Reduce propensity for high-risk clients
                adjustment = (prinad - 70) / 30  # 0 to 1 for PRINAD 70-100
                score = score * (1 - adjustment * 0.5)  # Up to 50% reduction
            
            scores[produto] = score
        
        # Rank products by propensity
        ranking = sorted(scores.keys(), key=lambda p: scores[p], reverse=True)
        
        # Aggregate score (weighted average)
        score_agregado = np.mean(list(scores.values()))
        
        return ClientePropensity(
            cliente_id=cliente_id,
            scores=scores,
            ranking_produtos=ranking,
            score_agregado=score_agregado,
            prinad=prinad
        )
    
    def get_propensity_score(
        self,
        cliente_id: str,
        produto: str,
        features: Dict[str, float],
        prinad: Optional[float] = None
    ) -> PropensityScore:
        """
        Get detailed propensity score for a single product.
        
        Args:
            cliente_id: Client identifier
            produto: Product name
            features: Feature values
            prinad: Optional PRINAD score
            
        Returns:
            PropensityScore with details
        """
        propensity = self.prever_propensao(cliente_id, features, prinad)
        score = propensity.scores.get(produto, 50.0)
        
        # Get feature importances if available
        feature_imp = []
        if produto in self.modelos and hasattr(self.modelos[produto], 'feature_importances_'):
            importances = self.modelos[produto].feature_importances_
            names = self.feature_names.get(produto, [])
            feature_imp = sorted(
                zip(names, importances),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:5]
        
        return PropensityScore(
            cliente_id=cliente_id,
            produto=produto,
            score=score,
            probabilidade=score / 100,
            classificacao=self._classificar_score(score),
            features_importantes=feature_imp
        )
    
    def salvar_modelos(self):
        """Save trained models to disk."""
        for produto, model in self.modelos.items():
            model_path = self.modelo_dir / f"propensity_{produto}.joblib"
            joblib.dump(model, model_path)
            
            if produto in self.scalers:
                scaler_path = self.modelo_dir / f"scaler_{produto}.joblib"
                joblib.dump(self.scalers[produto], scaler_path)
        
        # Save feature names
        meta_path = self.modelo_dir / "propensity_meta.joblib"
        joblib.dump(self.feature_names, meta_path)
        
        logger.info(f"Models saved to {self.modelo_dir}")
    
    def carregar_modelos(self):
        """Load trained models from disk."""
        # Load feature names
        meta_path = self.modelo_dir / "propensity_meta.joblib"
        if meta_path.exists():
            self.feature_names = joblib.load(meta_path)
        
        for produto in PRODUTOS_CREDITO:
            model_path = self.modelo_dir / f"propensity_{produto}.joblib"
            scaler_path = self.modelo_dir / f"scaler_{produto}.joblib"
            
            if model_path.exists():
                self.modelos[produto] = joblib.load(model_path)
                if scaler_path.exists():
                    self.scalers[produto] = joblib.load(scaler_path)
                logger.info(f"Loaded model for {produto}")
        
        self.is_trained = len(self.modelos) > 0


# Module-level instance
_propensity_model: Optional[PropensityModel] = None


def get_propensity_model() -> PropensityModel:
    """Get or create propensity model instance."""
    global _propensity_model
    if _propensity_model is None:
        _propensity_model = PropensityModel()
        _propensity_model.carregar_modelos()
    return _propensity_model


if __name__ == "__main__":
    print("PropensityModel - Multi-product credit propensity")
    print("=" * 50)
    print(f"Products: {PRODUTOS_CREDITO}")
    print(f"ML Available: {ML_AVAILABLE}")
    
    if ML_AVAILABLE:
        model = PropensityModel()
        print(f"Model directory: {model.modelo_dir}")
