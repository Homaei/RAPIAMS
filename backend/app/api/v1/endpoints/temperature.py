"""
Temperature Monitoring API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.api.deps import get_current_user
from app.core.websocket_manager import ws_manager

router = APIRouter(prefix="/temperature", tags=["temperature"])
logger = logging.getLogger(__name__)


@router.get("/{device_id}/all")
async def get_all_temperatures(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all available temperature sensors"""
    try:
        command = {
            "type": "get_all_temperatures",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error getting all temperatures for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/cpu")
async def get_cpu_temperature(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get CPU temperature specifically"""
    try:
        command = {
            "type": "get_cpu_temperature",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error getting CPU temperature for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/history")
async def get_temperature_history(
    device_id: str,
    current_user = Depends(get_current_user),
    sensor: Optional[str] = Query(None, description="Specific sensor to get history for"),
    minutes: int = Query(5, ge=1, le=60, description="Minutes of history to return")
) -> Dict[str, Any]:
    """Get temperature history"""
    try:
        command = {
            "type": "get_temperature_history",
            "device_id": device_id,
            "parameters": {
                "sensor": sensor,
                "minutes": minutes
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error getting temperature history for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/alerts")
async def get_temperature_alerts(
    device_id: str,
    current_user = Depends(get_current_user),
    warning_threshold: float = Query(70.0, ge=0, le=150, description="Warning threshold in Celsius"),
    critical_threshold: float = Query(80.0, ge=0, le=150, description="Critical threshold in Celsius")
) -> Dict[str, Any]:
    """Get temperature alerts"""
    try:
        command = {
            "type": "get_temperature_alerts",
            "device_id": device_id,
            "parameters": {
                "warning_threshold": warning_threshold,
                "critical_threshold": critical_threshold
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error getting temperature alerts for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/throttling")
async def get_thermal_throttling_status(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get thermal throttling status (Raspberry Pi specific)"""
    try:
        command = {
            "type": "get_thermal_throttling_status",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error getting thermal throttling status for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/monitoring/start")
async def start_temperature_monitoring(
    device_id: str,
    current_user = Depends(get_current_user),
    interval: float = Query(1.0, ge=0.1, le=60.0, description="Monitoring interval in seconds")
) -> Dict[str, Any]:
    """Start temperature monitoring"""
    try:
        command = {
            "type": "start_temperature_monitoring",
            "device_id": device_id,
            "parameters": {
                "interval": interval
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": "Temperature monitoring started",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error starting temperature monitoring for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/monitoring/stop")
async def stop_temperature_monitoring(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop temperature monitoring"""
    try:
        command = {
            "type": "stop_temperature_monitoring",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": "Temperature monitoring stopped",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error stopping temperature monitoring for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))