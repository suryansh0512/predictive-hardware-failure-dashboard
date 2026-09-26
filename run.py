#!/usr/bin/env python3
"""Cross-platform Task Runner for Predictive Hardware Failure Dashboard.

Works seamlessly across Windows, Linux, and macOS.
Usage:
    python run.py init-db
    python run.py collect [--once]
    python run.py api [--port 8000]
    python run.py test
    python run.py export-parquet [--output data/parquet/telemetry.parquet]
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def init_db():
    print("[*] Running database migration and initialization...")
    from storage.init_db import run_init
    run_init()


def run_collector(once: bool = False, interval: float | None = None):
    print(f"[*] Launching Telemetry Collector (once={once}, interval={interval})...")
    cmd = [sys.executable, str(PROJECT_ROOT / "collector" / "agent.py")]
    if once:
        cmd.append("--once")
    if interval:
        cmd.extend(["--interval", str(interval)])
    subprocess.run(cmd)


def run_api(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    print(f"[*] Starting FastAPI server on http://{host}:{port} (reload={reload})...")
    import uvicorn
    uvicorn.run("api.app:app", host=host, port=port, reload=reload)


def run_tests():
    print("[*] Running test suite with pytest...")
    cmd = [sys.executable, "-m", "pytest", "tests", "-v"]
    res = subprocess.run(cmd)
    sys.exit(res.returncode)


def export_parquet(output_path: str = "data/parquet/telemetry.parquet"):
    print(f"[*] Exporting SQLite telemetry to {output_path}...")
    from storage.db import export_to_parquet
    count = export_to_parquet(output_path)
    print(f"[+] Successfully exported {count} records to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Predictive Hardware Failure Dashboard Task Runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init-db
    subparsers.add_parser("init-db", help="Initialize SQLite telemetry schema")

    # collect
    collect_parser = subparsers.add_parser("collect", help="Run edge telemetry collector")
    collect_parser.add_argument("--once", action="store_true", help="Perform single sample and exit")
    collect_parser.add_argument("--interval", type=float, default=None, help="Sampling interval in seconds")

    # api
    api_parser = subparsers.add_parser("api", help="Launch FastAPI web service")
    api_parser.add_argument("--host", type=str, default="127.0.0.1", help="Bind host")
    api_parser.add_argument("--port", type=int, default=8000, help="Bind port")
    api_parser.add_argument("--no-reload", action="store_true", help="Disable auto-reloading")

    # test
    subparsers.add_parser("test", help="Run unit and integration tests")

    # export-parquet
    parquet_parser = subparsers.add_parser("export-parquet", help="Export telemetry table to Parquet")
    parquet_parser.add_argument("--output", type=str, default="data/parquet/telemetry.parquet")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
    elif args.command == "collect":
        run_collector(once=args.once, interval=args.interval)
    elif args.command == "api":
        run_api(host=args.host, port=args.port, reload=not args.no_reload)
    elif args.command == "test":
        run_tests()
    elif args.command == "export-parquet":
        export_parquet(output_path=args.output)


if __name__ == "__main__":
    main()
