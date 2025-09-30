"""
GPIO Control API endpoints
Unified GPIO control for devices (buzzers, relays, motors, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.api.deps import get_current_user
from app.core.websocket_manager import ws_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{device_id}/register")
async def register_gpio_device(
    device_id: str,
    device_name: str = Body(..., embed=True),
    config: Dict[str, Any] = Body(..., embed=True),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Register a new GPIO device

    Example config:
    {
        "pin": 17,
        "mode": "OUTPUT",
        "active_state": "HIGH",
        "initial_state": "LOW",
        "description": "Test buzzer",
        "max_runtime": 60,
        "device_type": "buzzer",
        "safety_features": {
            "cooldown_time": 0,
            "max_cycles_per_hour": 0
        }
    }
    """
    try:
        command = {
            "type": "gpio_register_device",
            "device_id": device_id,
            "parameters": {
                "device_name": device_name,
                "config": config
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
        logger.error(f"Error registering GPIO device for {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/devices")
async def list_gpio_devices(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """List all registered GPIO devices"""
    try:
        command = {
            "type": "gpio_list_devices",
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
        logger.error(f"Error listing GPIO devices for {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/device/{device_name}/info")
async def get_gpio_device_info(
    device_id: str,
    device_name: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed information about a GPIO device"""
    try:
        command = {
            "type": "gpio_get_device_info",
            "device_id": device_id,
            "parameters": {
                "device_name": device_name
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
        logger.error(f"Error getting GPIO device info for {device_id}/{device_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/device/{device_name}/on")
async def turn_on_device(
    device_id: str,
    device_name: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Turn on a GPIO device (buzzer, relay, etc.)"""
    try:
        command = {
            "type": "gpio_turn_on",
            "device_id": device_id,
            "parameters": {
                "device_name": device_name
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": f"Device '{device_name}' turned ON",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error turning on GPIO device {device_id}/{device_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/device/{device_name}/off")
async def turn_off_device(
    device_id: str,
    device_name: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Turn off a GPIO device (buzzer, relay, etc.)"""
    try:
        command = {
            "type": "gpio_turn_off",
            "device_id": device_id,
            "parameters": {
                "device_name": device_name
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": f"Device '{device_name}' turned OFF",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error turning off GPIO device {device_id}/{device_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/device/{device_name}/on-duration")
async def turn_on_device_duration(
    device_id: str,
    device_name: str,
    duration: float = Body(..., embed=True, description="Duration in seconds"),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Turn on a GPIO device for a specific duration
    Device will automatically turn off after the duration expires
    """
    try:
        if duration <= 0:
            raise HTTPException(
                status_code=400,
                detail="Duration must be greater than 0"
            )

        command = {
            "type": "gpio_turn_on_duration",
            "device_id": device_id,
            "parameters": {
                "device_name": device_name,
                "duration": duration
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": f"Device '{device_name}' turned ON for {duration} seconds",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error turning on GPIO device with duration {device_id}/{device_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/device/{device_name}/status")
async def get_device_status(
    device_id: str,
    device_name: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current status of a GPIO device"""
    try:
        command = {
            "type": "gpio_get_status",
            "device_id": device_id,
            "parameters": {
                "device_name": device_name
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
        logger.error(f"Error getting GPIO device status {device_id}/{device_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/device/{device_name}/statistics")
async def get_device_statistics(
    device_id: str,
    device_name: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get usage statistics for a GPIO device"""
    try:
        command = {
            "type": "gpio_get_statistics",
            "device_id": device_id,
            "parameters": {
                "device_name": device_name
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
        logger.error(f"Error getting GPIO device statistics {device_id}/{device_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/device/{device_name}/emergency-stop")
async def emergency_stop_device(
    device_id: str,
    device_name: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Emergency stop - immediately turn off a GPIO device"""
    try:
        command = {
            "type": "gpio_emergency_stop",
            "device_id": device_id,
            "parameters": {
                "device_name": device_name
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": f"Emergency stop executed for '{device_name}'",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error in emergency stop for {device_id}/{device_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/emergency-stop-all")
async def emergency_stop_all_devices(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Emergency stop - immediately turn off ALL GPIO devices"""
    try:
        command = {
            "type": "gpio_emergency_stop_all",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": "Emergency stop executed for all devices",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error in emergency stop all for {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Convenience endpoints for common devices

@router.post("/{device_id}/buzzer/beep")
async def buzzer_beep(
    device_id: str,
    duration: float = Query(1.0, ge=0.1, le=10.0, description="Beep duration in seconds"),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Quick beep command for buzzer"""
    return await turn_on_device_duration(device_id, "buzzer", duration, current_user)


@router.post("/{device_id}/pump/start")
async def start_pump(
    device_id: str,
    duration: Optional[float] = Query(None, ge=1, le=300, description="Run duration in seconds (optional)"),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Start water pump (with optional auto-stop duration)"""
    if duration:
        return await turn_on_device_duration(device_id, "pump_relay", duration, current_user)
    else:
        return await turn_on_device(device_id, "pump_relay", current_user)


@router.post("/{device_id}/pump/stop")
async def stop_pump(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop water pump"""
    return await turn_off_device(device_id, "pump_relay", current_user)


@router.get("/{device_id}/pump/status")
async def get_pump_status(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get water pump status"""
    return await get_device_status(device_id, "pump_relay", current_user)