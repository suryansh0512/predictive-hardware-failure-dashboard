# Predictive Hardware Failure Dashboard

Edge-ready predictive hardware monitoring, anomaly detection, and failure risk forecasting system.

---

## 🎯 6-Phase Architecture Overview

This project is organized into 6 modular missions:

| Phase | Description | Status |
|---|---|---|
| **Mission 1** | **Scaffold, Telemetry Schema, Collector Agent, SQLite Storage, FastAPI Skeleton, Sliding Window Pipeline** | **COMPLETE** |
| **Mission 2** | Synthetic Failure Dataset Generation (10-Day Horizon) & Feature Pipeline | Planned |
| **Mission 3** | Anomaly Detection (Isolation Forest, Autoencoder) & ML Predictors (LSTM-CNN, RF/LightGBM/XGBoost) | Planned |
| **Mission 4** | Model Evaluation Harness (PR-AUC, F1, MCC, Lead-Time Analysis) & Edge Latency Profiling | Planned |
| **Mission 5** | Interactive React Dashboard (Gauges, WebSocket streaming, Alerting & Remediation) | Planned |
| **Mission 6** | Edge Deployment Daemon, Automated Verification & Walkthrough | Planned |

---

## 📁 Repository Layout & Mission Contracts

```
predictive hardware failure dashboard/
├── api/                   # FastAPI backend skeleton & WebSocket streaming
│   ├── __init__.py
│   └── app.py
├── collector/             # On-device background telemetry collector
│   ├── __init__.py
│   ├── agent.py
│   └── readers.py
├── configs/               # Global and subsystem configuration
│   ├── __init__.py
│   └── config.yaml
├── dashboard/             # Reserved for Mission 5: React/Vite web UI
│   └── __init__.py
├── evaluation/            # Reserved for Mission 4: Metrics, PR-AUC, F1, MCC harness
│   └── __init__.py
├── features/              # Feature engineering & sliding windows (Chevtchenko et al.)
│   ├── __init__.py
│   └── windowing.py
├── models/                # Reserved for Mission 3: Anomaly & failure forecasting models
│   └── __init__.py
├── storage/               # SQLite edge storage engine, DDL schema, and migration
│   ├── __init__.py
│   ├── db.py
│   ├── init_db.py
│   ├── models.py
│   └── schema.sql
├── tests/                 # Automated test suite (Pytest)
│   ├── test_api.py
│   ├── test_collector.py
│   ├── test_storage.py
│   └── test_windowing.py
├── Makefile               # Task automation
├── pyproject.toml         # Packaging configuration
├── requirements.txt       # Core project dependencies
└── run.py                 # Cross-platform CLI task runner (Windows / Linux / macOS)
```

---

## 🗄️ Telemetry Schema Specification

SQLite was chosen as the operational edge storage engine due to zero configuration, low memory footprint, high write throughput with WAL (`Write-Ahead Logging`), and ACID transaction guarantees.

| Field | Type | Constraints / Description |
|---|---|---|
| `id` | `INTEGER` | Primary key, autoincrement |
| `timestamp` | `TEXT` | UTC ISO-8601 string (e.g., `2026-09-27T01:45:00.123456Z`) |
| `cpu_usage_pct` | `REAL` | Total CPU utilization percentage ($0.0 - 100.0$) |
| `memory_usage_pct` | `REAL` | Memory utilization percentage ($0.0 - 100.0$) |
| `temperature_c` | `REAL` | Hardware thermal reading in Celsius (nullable) |
| `reallocated_sectors` | `INTEGER` | SMART Attribute 5: Reallocated Sectors (nullable) |
| `pending_sectors` | `INTEGER` | SMART Attribute 197: Current Pending Sectors (nullable) |
| `read_error_rate` | `REAL` | SMART Attribute 1: Raw Read Error Rate (nullable) |
| `disk_temp_c` | `REAL` | SMART Attribute 194 / Airflow temperature (nullable) |
| `disk_status` | `TEXT` | SMART health state (`PASSED`, `FAILED`, `UNKNOWN`) (nullable) |
| `load_avg_1m` | `REAL` | 1-minute system load average (nullable on Windows) |
| `load_avg_5m` | `REAL` | 5-minute system load average (nullable on Windows) |
| `load_avg_15m` | `REAL` | 15-minute system load average (nullable on Windows) |
| `entity_class` | `TEXT` | Hardware entity domain: `HDD`, `RAM`, or `CPU` |
| `host_id` | `TEXT` | Monitored node or host identifier |

---

## ⏱️ Sliding Window Pipeline (Chevtchenko et al., arXiv:2310.14949)

Located in `features/windowing.py`, the module provides:
1. **`SlidingWindowBuffer`**: An edge-ready, circular memory buffer emitting windows of length $W$ with stride $S$.
2. **`extract_sliding_windows`**: Offline 3D sequence array extractor (`[N_windows, W, N_features]`) ready for Phase 3 deep learning models (LSTM-CNN).
3. **`compute_window_features`**: Computes rolling statistical indicators per window (mean, standard deviation, min, max, median, peak-to-peak amplitude, and linear trend slope) for tree-based ensembles (Random Forest, LightGBM, XGBoost).

---

## 🚀 Quickstart & Usage

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Initialize Database Schema
```bash
python run.py init-db
# or: make init-db
```

### 3. Run Telemetry Collector
```bash
# Continuous edge collection (every 10s by default)
python run.py collect

# Single sample pass (verification)
python run.py collect --once
```

### 4. Launch FastAPI Web Service
```bash
python run.py api --port 8000
# or: make api
```

Visit the interactive API docs at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 5. Run Test Suite
```bash
python run.py test
# or: pytest tests -v
```

### 6. Export to Parquet
```bash
python run.py export-parquet --output data/parquet/telemetry.parquet
```

---

## 🌐 API Endpoints

- `GET /health` — Service health, database status, record count, and mode.
- `GET /telemetry/latest?entity_class=CPU&limit=10` — Most recent samples filtered by subsystem.
- `GET /telemetry/history?hours=1.0` — Historical telemetry within specified lookback hours.
- `GET /window/latest?entity_class=CPU&window_size=12` — Current sliding window and extracted statistical features.
- `POST /telemetry/collect` — Trigger an immediate on-demand collection sample.
- `WebSocket /ws/telemetry` — Live WebSocket stream broadcasting new records in real time.
