"""
Metrics API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.api.deps import get_db, get_current_user, verify_device_api_key
from app.models.user import User
from app.models.device import Device
from app.models.metrics import Metrics
from app.schemas.metrics import MetricsCreate, MetricsResponse

router = APIRouter()

@router.post("/submit", response_model=dict)
async def submit_metrics(
    metrics: MetricsCreate,
    device: Device = Depends(verify_device_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit metrics from device agent
    Uses X-API-Key header for authentication
    """
    new_metric = Metrics(
        device_id=device.id,
        timestamp=metrics.timestamp or datetime.utcnow(),
        cpu_percent=metrics.cpu_percent,
        memory_percent=metrics.memory_percent,
        disk_percent=metrics.disk_percent,
        cpu_temperature=metrics.cpu_temperature,
        network_sent_bytes=metrics.network_sent_bytes,
        network_recv_bytes=metrics.network_recv_bytes,
        load_avg_1=metrics.load_avg_1,
        load_avg_5=metrics.load_avg_5,
        load_avg_15=metrics.load_avg_15,
        memory_used_mb=metrics.memory_used_mb,
        memory_available_mb=metrics.memory_available_mb,
        disk_used_gb=metrics.disk_used_gb,
        disk_available_gb=metrics.disk_available_gb,
        uptime_seconds=metrics.uptime_seconds,
    )
    
    db.add(new_metric)
    await db.commit()
    await db.refresh(new_metric)
    
    return {
        "status": "success",
        "message": "Metrics received",
        "device_id": device.id,
        "timestamp": new_metric.timestamp
    }

from uuid import UUID

@router.get("/device/{device_id}", response_model=List[MetricsResponse])
async def get_device_metrics(
    device_id: UUID,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get metrics for a specific device"""
    from sqlalchemy import select, desc
    
    # Check device ownership
    device_query = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    device = device_query.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get metrics
    result = await db.execute(
        select(Metrics)
        .where(Metrics.device_id == device_id)
        .order_by(desc(Metrics.timestamp))
        .limit(limit)
    )
    
    return result.scalars().all()
