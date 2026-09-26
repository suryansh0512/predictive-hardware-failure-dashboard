"""FastAPI Backend Application Skeleton for Predictive Hardware Failure Monitoring.

Endpoints:
- GET /health: Health check, system status, record counts, and mode
- GET /telemetry/latest: Latest telemetry records (filterable by entity_class)
- GET /telemetry/history: Telemetry records over the past N hours
- WebSocket /ws/telemetry: Real-time telemetry streaming to connected clients
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import logging
import platform
import socket
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from configs import load_config
from collector.agent import TelemetryCollector
from features.windowing import compute_window_features, extract_sliding_windows
from storage.db import (
    get_db_connection,
    get_latest_telemetry,
    get_telemetry_history,
    get_telemetry_count,
    init_db,
)
from storage.models import TelemetryRecord

logger = logging.getLogger("api.app")

# System startup time for uptime metric
START_TIME = time.time()


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts telemetry updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected. Total clients: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected. Total clients: %d", len(self.active_connections))

    async def broadcast_json(self, data: Any):
        """Broadcasts payload to all connected clients; removes stale connections."""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.warning("Failed to send WebSocket message, dropping client: %s", e)
                self.disconnect(connection)


manager = ConnectionManager()
collector_instance: Optional[TelemetryCollector] = None
collector_task: Optional[asyncio.Task] = None


async def background_collector_loop(collector: TelemetryCollector, interval: float):
    """Background async worker that collects telemetry and broadcasts to WebSockets."""
    logger.info("Embedded collector loop started (interval: %.1fs)", interval)
    try:
        while True:
            records = collector.collect_once()
            if records:
                # Broadcast over WebSockets
                await manager.broadcast_json({
                    "event": "telemetry_update",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "records": records,
                })
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("Embedded collector loop received cancellation signal.")
    except Exception as e:
        logger.exception("Error in embedded collector loop: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI: initializes DB and runs background collector."""
    global collector_instance, collector_task

    config = load_config()
    db_path = config.get("storage", {}).get("db_path", "data/telemetry.db")
    init_db(db_path)

    # Initialize embedded collector
    collector_instance = TelemetryCollector()
    interval = collector_instance.interval_seconds

    # Start background task for collection + live WebSocket broadcast
    collector_task = asyncio.create_task(background_collector_loop(collector_instance, interval))
    logger.info("FastAPI service initialized with embedded telemetry collector.")

    yield

    # Shutdown
    if collector_task:
        collector_task.cancel()
        try:
            await collector_task
        except asyncio.CancelledError:
            pass
    logger.info("FastAPI service shut down.")


app = FastAPI(
    title="Predictive Hardware Failure Dashboard API",
    description="Edge telemetry ingestion, storage query, and real-time streaming API",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for future frontend (React/Vite/Next.js)
cfg = load_config()
cors_origins = cfg.get("api", {}).get("cors_origins", ["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary="Service Health and Status")
def health_check() -> Dict[str, Any]:
    """Returns the operational status of the edge telemetry API, database, and host."""
    config = load_config()
    db_path = config.get("storage", {}).get("db_path", "data/telemetry.db")
    total_records = get_telemetry_count(db_path)
    uptime = time.time() - START_TIME

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host_id": collector_instance.host_id if collector_instance else socket.gethostname(),
        "platform": f"{platform.system()} {platform.release()}",
        "live_mode": config.get("mode", {}).get("live_mode", True),
        "db_path": db_path,
        "total_records": total_records,
        "active_websocket_clients": len(manager.active_connections),
        "uptime_seconds": round(uptime, 2),
        "mission_phase": "Mission 1 of 6 (Scaffold, Storage, Collector, API)",
    }


@app.get("/telemetry/latest", summary="Retrieve latest telemetry")
def get_latest(
    entity_class: Optional[str] = Query(
        None, description="Filter by hardware entity: 'HDD', 'RAM', or 'CPU'"
    ),
    limit: int = Query(10, ge=1, le=100, description="Max number of records to return"),
) -> Dict[str, Any]:
    """Fetches the most recent telemetry samples recorded by the edge collector."""
    if entity_class and entity_class not in ("HDD", "RAM", "CPU"):
        raise HTTPException(status_code=400, detail="entity_class must be one of: 'HDD', 'RAM', 'CPU'")

    config = load_config()
    db_path = config.get("storage", {}).get("db_path", "data/telemetry.db")
    rows = get_latest_telemetry(entity_class=entity_class, limit=limit, db_path=db_path)
    return {
        "count": len(rows),
        "entity_class_filter": entity_class,
        "records": rows,
    }


@app.get("/telemetry/history", summary="Retrieve telemetry history")
def get_history(
    hours: float = Query(1.0, gt=0, le=168.0, description="Lookback window in hours (default 1.0)"),
    entity_class: Optional[str] = Query(
        None, description="Filter by hardware entity: 'HDD', 'RAM', or 'CPU'"
    ),
    limit: int = Query(5000, ge=1, le=10000, description="Maximum number of historical records"),
) -> Dict[str, Any]:
    """Fetches historical telemetry within the last N hours."""
    if entity_class and entity_class not in ("HDD", "RAM", "CPU"):
        raise HTTPException(status_code=400, detail="entity_class must be one of: 'HDD', 'RAM', 'CPU'")

    config = load_config()
    db_path = config.get("storage", {}).get("db_path", "data/telemetry.db")
    rows = get_telemetry_history(
        hours=hours, entity_class=entity_class, limit=limit, db_path=db_path
    )
    return {
        "hours": hours,
        "entity_class_filter": entity_class,
        "count": len(rows),
        "records": rows,
    }


@app.get("/window/latest", summary="Extract sliding window and statistical features")
def get_latest_window(
    entity_class: str = Query("CPU", description="Entity class: 'HDD', 'RAM', or 'CPU'"),
    window_size: int = Query(12, ge=2, le=120, description="Window size W"),
) -> Dict[str, Any]:
    """Demonstrates sliding window feature extraction (Chevtchenko et al.) on current telemetry."""
    if entity_class not in ("HDD", "RAM", "CPU"):
        raise HTTPException(status_code=400, detail="entity_class must be one of: 'HDD', 'RAM', 'CPU'")

    config = load_config()
    db_path = config.get("storage", {}).get("db_path", "data/telemetry.db")
    rows = get_latest_telemetry(entity_class=entity_class, limit=window_size, db_path=db_path)
    # Reverse to chronological order
    rows = list(reversed(rows))

    if not rows:
        return {"entity_class": entity_class, "window_size": 0, "features": {}, "samples": []}

    features = compute_window_features(rows)
    return {
        "entity_class": entity_class,
        "sample_count": len(rows),
        "window_size_requested": window_size,
        "statistical_features": features,
        "raw_samples": rows,
    }


@app.post("/telemetry/collect", summary="Trigger manual collection cycle")
def trigger_collection() -> Dict[str, Any]:
    """Manually triggers a collection cycle on demand."""
    if not collector_instance:
        raise HTTPException(status_code=500, detail="Collector not initialized")
    records = collector_instance.collect_once()
    return {
        "status": "success",
        "collected_records": len(records),
        "records": records,
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """WebSocket endpoint streaming live telemetry frames to frontend/dashboards."""
    await manager.connect(websocket)
    try:
        # Send initial greeting and recent snapshot
        config = load_config()
        db_path = config.get("storage", {}).get("db_path", "data/telemetry.db")
        latest = get_latest_telemetry(limit=3, db_path=db_path)
        await websocket.send_json({
            "event": "connected",
            "message": "Connected to edge telemetry real-time stream",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latest_snapshot": latest,
        })

        # Keep connection alive; handle incoming client pings or queries
        while True:
            data = await websocket.receive_text()
            # Client can ping or send commands
            if data.strip().lower() == "ping":
                await websocket.send_json({"event": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
            else:
                try:
                    payload = json.loads(data)
                    if payload.get("action") == "get_latest":
                        req_entity = payload.get("entity_class")
                        records = get_latest_telemetry(entity_class=req_entity, limit=5, db_path=db_path)
                        await websocket.send_json({"event": "snapshot", "records": records})
                except Exception:
                    await websocket.send_json({"event": "ack", "received": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
        manager.disconnect(websocket)
