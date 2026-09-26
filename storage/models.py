from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class TelemetryRecord(BaseModel):
    """Telemetry data model matching the schema contract."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(default=None, description="Auto-incremented primary key")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO-8601 timestamp string",
    )
    cpu_usage_pct: float = Field(..., ge=0.0, le=100.0, description="CPU usage percent")
    memory_usage_pct: float = Field(..., ge=0.0, le=100.0, description="RAM usage percent")
    temperature_c: Optional[float] = Field(default=None, description="Temperature in Celsius")
    reallocated_sectors: Optional[int] = Field(default=None, ge=0, description="SMART 5 count")
    pending_sectors: Optional[int] = Field(default=None, ge=0, description="SMART 197 count")
    read_error_rate: Optional[float] = Field(default=None, ge=0.0, description="SMART 1 rate")
    disk_temp_c: Optional[float] = Field(default=None, description="Disk temperature Celsius")
    disk_status: Optional[str] = Field(default=None, description="SMART overall health state")
    load_avg_1m: Optional[float] = Field(default=None, ge=0.0, description="1-min system load")
    load_avg_5m: Optional[float] = Field(default=None, ge=0.0, description="5-min system load")
    load_avg_15m: Optional[float] = Field(default=None, ge=0.0, description="15-min system load")
    entity_class: Literal["HDD", "RAM", "CPU"] = Field(..., description="Monitored subsystem")
    host_id: str = Field(..., min_length=1, description="Host/node identifier")

