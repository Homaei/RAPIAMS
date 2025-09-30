"""
Disk Monitoring API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.api.deps import get_current_user
from app.core.websocket_manager import ws_manager

router = APIRouter(prefix="/disk", tags=["disk"])
logger = logging.getLogger(__name__)


@router.get("/{device_id}/info")
async def get_disk_info(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive disk information"""
    try:
        command = {
            "type": "get_disk_info",
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
        logger.error(f"Error getting disk info for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/usage")
async def get_disk_usage(
    device_id: str,
    current_user = Depends(get_current_user),
    path: str = Query("/", description="Path to check disk usage")
) -> Dict[str, Any]:
    """Get disk usage for a specific path"""
    try:
        command = {
            "type": "get_disk_usage",
            "device_id": device_id,
            "parameters": {
                "path": path
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
        logger.error(f"Error getting disk usage for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/io-stats")
async def get_disk_io_stats(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get disk I/O statistics"""
    try:
        command = {
            "type": "get_disk_io_stats",
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
        logger.error(f"Error getting disk I/O stats for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/large-files")
async def get_large_files(
    device_id: str,
    current_user = Depends(get_current_user),
    path: str = Query("/", description="Path to search for large files"),
    min_size_mb: int = Query(100, ge=1, description="Minimum file size in MB"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of files to return")
) -> Dict[str, Any]:
    """Find large files in a directory"""
    try:
        command = {
            "type": "get_large_files",
            "device_id": device_id,
            "parameters": {
                "path": path,
                "min_size_mb": min_size_mb,
                "limit": limit
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
        logger.error(f"Error getting large files for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/directory-sizes")
async def get_directory_sizes(
    device_id: str,
    current_user = Depends(get_current_user),
    path: str = Query("/", description="Path to analyze directory sizes")
) -> Dict[str, Any]:
    """Get sizes of subdirectories"""
    try:
        command = {
            "type": "get_directory_sizes",
            "device_id": device_id,
            "parameters": {
                "path": path
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
        logger.error(f"Error getting directory sizes for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/alerts")
async def get_disk_alerts(
    device_id: str,
    current_user = Depends(get_current_user),
    warning_threshold: float = Query(80.0, ge=0, le=100, description="Warning threshold percentage"),
    critical_threshold: float = Query(90.0, ge=0, le=100, description="Critical threshold percentage")
) -> Dict[str, Any]:
    """Get disk usage alerts"""
    try:
        command = {
            "type": "get_disk_alerts",
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
        logger.error(f"Error getting disk alerts for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/recommendations")
async def get_disk_recommendations(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get disk health and optimization recommendations"""
    try:
        command = {
            "type": "get_disk_recommendations",
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
        logger.error(f"Error getting disk recommendations for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
