"""
System Monitoring API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.api.deps import get_current_user
from app.core.websocket_manager import ws_manager

router = APIRouter(prefix="/system", tags=["system"])
logger = logging.getLogger(__name__)


@router.get("/{device_id}/info")
async def get_system_info(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive system information"""
    try:
        # Send command to agent via WebSocket
        command = {
            "type": "get_system_info",
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
        logger.error(f"Error getting system info for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/health")
async def get_system_health(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get system health status"""
    try:
        command = {
            "type": "get_system_health",
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
        logger.error(f"Error getting system health for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/performance")
async def get_system_performance(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get system performance summary"""
    try:
        command = {
            "type": "get_system_performance",
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
        logger.error(f"Error getting system performance for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/uptime")
async def get_system_uptime(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get system uptime information"""
    try:
        command = {
            "type": "get_system_uptime",
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
        logger.error(f"Error getting system uptime for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/reboot")
async def reboot_system(
    device_id: str,
    current_user = Depends(get_current_user),
    confirm: bool = Query(False, description="Confirmation required for reboot")
) -> Dict[str, Any]:
    """Reboot the system"""
    try:
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Reboot confirmation required. Use ?confirm=true"
            )

        command = {
            "type": "system_reboot",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "initiated_by": current_user.get("username", "unknown")
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": "Reboot command sent successfully",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error rebooting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/shutdown")
async def shutdown_system(
    device_id: str,
    current_user = Depends(get_current_user),
    confirm: bool = Query(False, description="Confirmation required for shutdown")
) -> Dict[str, Any]:
    """Shutdown the system"""
    try:
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Shutdown confirmation required. Use ?confirm=true"
            )

        command = {
            "type": "system_shutdown",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "initiated_by": current_user.get("username", "unknown")
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": "Shutdown command sent successfully",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error shutting down device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/command")
async def execute_system_command(
    device_id: str,
    command_data: Dict[str, Any],
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Execute a safe system command"""
    try:
        command = {
            "type": "execute_system_command",
            "device_id": device_id,
            "command": command_data.get("command"),
            "timestamp": datetime.utcnow().isoformat(),
            "initiated_by": current_user.get("username", "unknown")
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
        logger.error(f"Error executing command on device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))