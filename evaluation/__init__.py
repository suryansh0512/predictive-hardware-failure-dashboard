"""Evaluation Package.

Reserved for Mission 4: Model Evaluation Harness & Benchmarking.
Architectural components to be added in Phase 4:
- Metrics: PR-AUC, F1-Score, Matthews Correlation Coefficient (MCC), Confusion Matrix
- Early-Warning Horizon: Lead time before failure analysis
- Edge Profiling: Memory footprint and inference latency benchmark
"""

from evaluation.evaluator import (
    evaluate_anomaly_detector,
    benchmark_edge_system,
    run_full_evaluation,
)

__all__ = [
    "evaluate_anomaly_detector",
    "benchmark_edge_system",
    "run_full_evaluation",
]

