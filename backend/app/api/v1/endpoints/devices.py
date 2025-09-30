from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.security import generate_api_key, hash_api_key
from app.models.device import Device, Alert
from app.models.user import User
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceApiKey,
    AlertResponse,
    AlertUpdate
)
from app.api.deps import get_current_user, get_current_active_superuser

router = APIRouter()


@router.post("/", response_model=DeviceApiKey)
async def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    import secrets
    device_id = f"rpi_{secrets.token_hex(8)}"
    
    new_device = Device(
        device_id=device_id,
        name=device_data.name,
        hostname=device_data.hostname,
        model=device_data.model,
        location=device_data.location,
        description=device_data.description,
        tags=device_data.tags,
        api_key_hash=api_key_hash,
        owner_id=current_user.id,
        alert_thresholds=device_data.alert_thresholds or {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
            "temperature_celsius": 75,
            "offline_minutes": 10
        },
        webhook_url=device_data.webhook_url,
        notification_channels=device_data.notification_channels
    )
    
    db.add(new_device)
    await db.commit()
    await db.refresh(new_device)
    
    return DeviceApiKey(
        device_id=new_device.id,
        api_key=api_key,
        created_at=new_device.created_at
    )


@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_online: Optional[bool] = None,
    tag: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Device).where(Device.owner_id == current_user.id)
    
    if is_online is not None:
        query = query.where(Device.is_online == is_online)
    
    if tag:
        query = query.where(Device.tags.contains([tag]))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device_put(
    device_id: UUID,
    device_update: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update device using PUT method"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    update_data = device_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    device.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(device)

    return device

@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    device_update: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    update_data = device_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    device.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(device)
    
    return device


@router.delete("/{device_id}")
async def delete_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    await db.delete(device)
    await db.commit()
    
    return {"message": "Device deleted successfully"}


@router.post("/{device_id}/regenerate-api-key", response_model=DeviceApiKey)
async def regenerate_api_key(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    api_key = generate_api_key()
    device.api_key_hash = hash_api_key(api_key)
    device.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return DeviceApiKey(
        device_id=device.id,
        api_key=api_key,
        created_at=datetime.utcnow()
    )


@router.get("/{device_id}/alerts", response_model=List[AlertResponse])
async def get_device_alerts(
    device_id: UUID,
    is_resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    device_result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    if not device_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    query = select(Alert).where(Alert.device_id == device_id)
    
    if is_resolved is not None:
        query = query.where(Alert.is_resolved == is_resolved)
    
    if severity:
        query = query.where(Alert.severity == severity)
    
    query = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return alerts


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    alert_update: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Alert)
        .join(Device)
        .where(
            Alert.id == alert_id,
            Device.owner_id == current_user.id
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    if alert_update.is_resolved is not None:
        alert.is_resolved = alert_update.is_resolved
        alert.resolved_at = datetime.utcnow() if alert_update.is_resolved else None
    
    if alert_update.acknowledged is not None:
        alert.acknowledged = alert_update.acknowledged
        alert.acknowledged_by = current_user.id if alert_update.acknowledged else None
        alert.acknowledged_at = datetime.utcnow() if alert_update.acknowledged else None
    
    alert.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alert)
    
    return alert