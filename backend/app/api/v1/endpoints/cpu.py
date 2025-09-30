"""
CPU Monitoring API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.api.deps import get_current_user
from app.core.websocket_manager import ws_manager

router = APIRouter(prefix="/cpu", tags=["cpu"])
logger = logging.getLogger(__name__)


@router.get("/{device_id}/info")
async def get_cpu_info(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive CPU information"""
    try:
        command = {
            "type": "get_cpu_info",
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
        logger.error(f"Error getting CPU info for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/usage")
async def get_cpu_usage(
    device_id: str,
    current_user = Depends(get_current_user),
    per_cpu: bool = Query(False, description="Get per-CPU usage"),
    interval: float = Query(1.0, ge=0.1, le=10.0, description="Measurement interval in seconds")
) -> Dict[str, Any]:
    """Get current CPU usage"""
    try:
        command = {
            "type": "get_cpu_usage",
            "device_id": device_id,
            "parameters": {
                "per_cpu": per_cpu,
                "interval": interval
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
        logger.error(f"Error getting CPU usage for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/load")
async def get_cpu_load_average(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get CPU load average"""
    try:
        command = {
            "type": "get_cpu_load_average",
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
        logger.error(f"Error getting CPU load for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/temperature")
async def get_cpu_temperature(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get CPU temperature"""
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


@router.get("/{device_id}/top-processes")
async def get_top_cpu_processes(
    device_id: str,
    current_user = Depends(get_current_user),
    count: int = Query(10, ge=1, le=50, description="Number of top processes to return")
) -> Dict[str, Any]:
    """Get top CPU consuming processes"""
    try:
        command = {
            "type": "get_top_cpu_processes",
            "device_id": device_id,
            "parameters": {
                "count": count
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
        logger.error(f"Error getting top CPU processes for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/history")
async def get_cpu_history(
    device_id: str,
    current_user = Depends(get_current_user),
    minutes: int = Query(5, ge=1, le=60, description="Minutes of history to return")
) -> Dict[str, Any]:
    """Get CPU usage history"""
    try:
        command = {
            "type": "get_cpu_history",
            "device_id": device_id,
            "parameters": {
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
        logger.error(f"Error getting CPU history for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/alerts")
async def get_cpu_alerts(
    device_id: str,
    current_user = Depends(get_current_user),
    warning_threshold: float = Query(70.0, ge=0, le=100, description="Warning threshold percentage"),
    critical_threshold: float = Query(85.0, ge=0, le=100, description="Critical threshold percentage")
) -> Dict[str, Any]:
    """Get CPU usage alerts"""
    try:
        command = {
            "type": "get_cpu_alerts",
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
        logger.error(f"Error getting CPU alerts for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/monitoring/start")
async def start_cpu_monitoring(
    device_id: str,
    current_user = Depends(get_current_user),
    interval: float = Query(1.0, ge=0.1, le=60.0, description="Monitoring interval in seconds")
) -> Dict[str, Any]:
    """Start CPU monitoring"""
    try:
        command = {
            "type": "start_cpu_monitoring",
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
                "message": "CPU monitoring started",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error starting CPU monitoring for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/monitoring/stop")
async def stop_cpu_monitoring(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop CPU monitoring"""
    try:
        command = {
            "type": "stop_cpu_monitoring",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": "CPU monitoring stopped",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error stopping CPU monitoring for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))