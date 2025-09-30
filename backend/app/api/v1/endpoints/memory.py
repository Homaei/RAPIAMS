"""
Memory Monitoring API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.api.deps import get_current_user
from app.core.websocket_manager import ws_manager

router = APIRouter(prefix="/memory", tags=["memory"])
logger = logging.getLogger(__name__)


@router.get("/{device_id}/info")
async def get_memory_info(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive memory information"""
    try:
        command = {
            "type": "get_memory_info",
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
        logger.error(f"Error getting memory info for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/usage")
async def get_memory_usage(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current memory usage"""
    try:
        command = {
            "type": "get_memory_usage",
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
        logger.error(f"Error getting memory usage for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/top-processes")
async def get_top_memory_processes(
    device_id: str,
    current_user = Depends(get_current_user),
    count: int = Query(10, ge=1, le=50, description="Number of top processes to return")
) -> Dict[str, Any]:
    """Get top memory consuming processes"""
    try:
        command = {
            "type": "get_top_memory_processes",
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
        logger.error(f"Error getting top memory processes for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/by-category")
async def get_memory_by_category(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get memory usage categorized by process types"""
    try:
        command = {
            "type": "get_memory_by_category",
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
        logger.error(f"Error getting memory by category for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/history")
async def get_memory_history(
    device_id: str,
    current_user = Depends(get_current_user),
    minutes: int = Query(5, ge=1, le=60, description="Minutes of history to return")
) -> Dict[str, Any]:
    """Get memory usage history"""
    try:
        command = {
            "type": "get_memory_history",
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
        logger.error(f"Error getting memory history for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/alerts")
async def get_memory_alerts(
    device_id: str,
    current_user = Depends(get_current_user),
    warning_threshold: float = Query(80.0, ge=0, le=100, description="Warning threshold percentage"),
    critical_threshold: float = Query(90.0, ge=0, le=100, description="Critical threshold percentage")
) -> Dict[str, Any]:
    """Get memory usage alerts"""
    try:
        command = {
            "type": "get_memory_alerts",
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
        logger.error(f"Error getting memory alerts for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/recommendations")
async def get_memory_recommendations(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get memory optimization recommendations"""
    try:
        command = {
            "type": "get_memory_recommendations",
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
        logger.error(f"Error getting memory recommendations for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/monitoring/start")
async def start_memory_monitoring(
    device_id: str,
    current_user = Depends(get_current_user),
    interval: float = Query(1.0, ge=0.1, le=60.0, description="Monitoring interval in seconds")
) -> Dict[str, Any]:
    """Start memory monitoring"""
    try:
        command = {
            "type": "start_memory_monitoring",
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
                "message": "Memory monitoring started",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error starting memory monitoring for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/monitoring/stop")
async def stop_memory_monitoring(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop memory monitoring"""
    try:
        command = {
            "type": "stop_memory_monitoring",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": "Memory monitoring stopped",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error stopping memory monitoring for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))