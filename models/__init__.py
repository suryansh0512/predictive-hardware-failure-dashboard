"""Models Package.

Reserved for Mission 3: Machine Learning Model Zoo.
Architectural components to be added in Phase 3:
- Anomaly Detection: Isolation Forest baseline & PyTorch Autoencoder reconstruction
- Temporal Predictor: LSTM-CNN hybrid architecture operating on sliding windows
- Supervised Ensemble: Random Forest, LightGBM, and XGBoost classifiers
"""

from models.anomaly import IsolationForestAnomalyDetector, get_anomaly_detector
from models.risk_engine import HardwareRiskEngine, get_risk_engine

__all__ = [
    "IsolationForestAnomalyDetector",
    "get_anomaly_detector",
    "HardwareRiskEngine",
    "get_risk_engine",
]

