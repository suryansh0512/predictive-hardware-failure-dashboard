import os
from pathlib import Path
from typing import Any, Dict
import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def load_config(config_path: Path | str | None = None) -> Dict[str, Any]:
    """Loads configuration from YAML file with environment variable overrides."""
    target_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not target_path.exists():
        # Fallback to defaults
        return {
            "mode": {"live_mode": True},
            "collector": {
                "interval_seconds": 10,
                "host_id": "auto",
                "smartctl": {"enabled": True, "binary_path": "smartctl", "device": "auto"},
            },
            "storage": {
                "db_path": "data/telemetry.db",
                "parquet": {"enabled": False, "export_dir": "data/parquet"},
            },
            "windowing": {"window_size": 12, "stride": 1},
            "api": {
                "host": "127.0.0.1",
                "port": 8000,
                "cors_origins": ["http://localhost:3000", "http://localhost:5173"],
            },
        }

    with open(target_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # Environment overrides
    if "LIVE_MODE" in os.environ:
        config.setdefault("mode", {})["live_mode"] = (
            os.environ["LIVE_MODE"].lower() in ("true", "1", "yes")
        )
    if "TELEMETRY_DB_PATH" in os.environ:
        config.setdefault("storage", {})["db_path"] = os.environ["TELEMETRY_DB_PATH"]

    return config
